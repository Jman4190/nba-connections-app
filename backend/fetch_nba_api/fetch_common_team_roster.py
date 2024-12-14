import sys
import os
import logging
from datetime import datetime
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from supabase_client import supabase
from nba_api.stats.endpoints import commonteamroster
from nba_api.stats.static import teams
from supabase_client import supabase
from seasons import get_total_seasons
import time


def setup_logging():
    log_filename = f"failed_seasons_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        filename=log_filename, level=logging.ERROR, format="%(asctime)s - %(message)s"
    )


def fetch_and_store_common_team_roster():
    all_teams = teams.get_teams()
    seasons = get_total_seasons()

    for team in all_teams:
        team_id = team["id"]
        for season in seasons:
            try:
                roster = commonteamroster.CommonTeamRoster(
                    team_id=team_id, season=season
                )
                # Add exponential backoff retry
                retries = 3
                while retries > 0:
                    try:
                        players_data = roster.get_data_frames()[0]
                        coaches_data = roster.get_data_frames()[1]
                        break
                    except Exception as e:
                        retries -= 1
                        if retries == 0:
                            raise e
                        time.sleep(2 ** (3 - retries))  # 2, 4, 8 seconds backoff

                if not players_data.empty:
                    for _, player in players_data.iterrows():
                        player_record = player.to_dict()
                        player_record["team_id"] = team_id
                        player_record["team_name"] = team["full_name"]
                        player_record["season"] = season

                        # Convert column names to lowercase
                        player_record = {k.lower(): v for k, v in player_record.items()}

                        # Remove 'teamid' if it exists to prevent schema mismatch
                        player_record.pop("teamid", None)

                        # Define allowed columns based on your schema
                        allowed_columns = {
                            "team_id",
                            "team_name",
                            "season",
                            "leagueid",
                            "player",
                            "player_slug",
                            "num",
                            "position",
                            "height",
                            "weight",
                            "birth_date",
                            "age",
                            "exp",
                            "school",
                            "player_id",
                            "how_acquired",
                            "nickname",
                        }

                        # Filter to include only allowed columns
                        player_record = {
                            k: v
                            for k, v in player_record.items()
                            if k in allowed_columns
                        }

                        # Ensure correct data types
                        int_fields = ["team_id", "player_id", "age"]
                        for field in int_fields:
                            if (
                                field in player_record
                                and player_record[field] is not None
                            ):
                                try:
                                    player_record[field] = int(player_record[field])
                                except ValueError:
                                    # If conversion fails, keep the original value
                                    pass

                        # Before player upsert
                        print(f"Attempting to insert player record: {player_record}")
                        try:
                            supabase.table("common_team_roster").upsert(
                                player_record
                            ).execute()
                        except Exception as e:
                            error_msg = f"Supabase error for {team['full_name']} in season {season} - Player data: {player_record}\nError: {e}"
                            print(error_msg)
                            logging.error(error_msg)
                            continue

                if not coaches_data.empty:
                    for _, coach in coaches_data.iterrows():
                        coach_record = coach.to_dict()
                        coach_record["team_id"] = team_id
                        coach_record["team_name"] = team["full_name"]
                        coach_record["season"] = season

                        # Convert column names to lowercase
                        coach_record = {k.lower(): v for k, v in coach_record.items()}

                        # Handle nan values
                        for key, value in coach_record.items():
                            if pd.isna(value):  # This checks for nan values
                                coach_record[key] = None

                        # Define allowed columns for coaches
                        allowed_coach_columns = {
                            "team_id",
                            "team_name",
                            "season",
                            "coach_id",
                            "first_name",
                            "last_name",
                            "coach_name",
                            "is_assistant",
                            "coach_type",
                            "sort_sequence",
                        }

                        # Filter to include only allowed columns
                        coach_record = {
                            k: v
                            for k, v in coach_record.items()
                            if k in allowed_coach_columns
                        }

                        # Ensure correct data types
                        int_fields = ["team_id", "coach_id", "sort_sequence"]
                        for field in int_fields:
                            if (
                                field in coach_record
                                and coach_record[field] is not None
                            ):
                                try:
                                    coach_record[field] = int(coach_record[field])
                                except ValueError:
                                    pass

                        # Convert boolean field
                        coach_record["is_assistant"] = bool(
                            coach_record.get("is_assistant", False)
                        )

                        # Before coach upsert
                        print(f"Attempting to insert coach record: {coach_record}")
                        try:
                            supabase.table("common_team_roster_coaches").upsert(
                                coach_record
                            ).execute()
                        except Exception as e:
                            error_msg = f"Supabase error for {team['full_name']} in season {season} - Coach data: {coach_record}\nError: {e}"
                            print(error_msg)
                            logging.error(error_msg)
                            continue

                print(f"Processed roster for {team['full_name']} in season {season}")
                time.sleep(1)  # To avoid hitting API rate limits

            except Exception as e:
                error_msg = f"Error fetching data for {team['full_name']} in season {season}: {e}"
                print(error_msg)
                logging.error(error_msg)
                time.sleep(5)
                continue

    print("Common team roster data updated successfully.")


if __name__ == "__main__":
    setup_logging()
    fetch_and_store_common_team_roster()
