import sys
import os
import logging
from datetime import datetime
import time
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from supabase_client import supabase
from nba_api.stats.endpoints import playerprofilev2
from nba_api.stats.static import players


def setup_logging():
    logs_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs"
    )
    os.makedirs(logs_dir, exist_ok=True)

    log_filename = os.path.join(
        logs_dir, f"player_season_totals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    )
    logging.basicConfig(
        filename=log_filename, level=logging.ERROR, format="%(asctime)s - %(message)s"
    )


def fetch_and_store_player_season_totals():
    setup_logging()
    all_players = players.get_players()
    total_players = len(all_players)

    for index, player in enumerate(all_players, 1):
        try:
            player_id = player["id"]
            full_name = player["full_name"]
            profile = playerprofilev2.PlayerProfileV2(
                player_id=player_id, per_mode36="Totals", league_id_nullable="00"
            )

            all_data_frames = profile.get_data_frames()

            if len(all_data_frames) < 3:
                print(f"[{index}/{total_players}] No data available for {full_name}")
                continue

            season_totals_df = all_data_frames[0]  # SeasonTotalsRegularSeason

            if (
                isinstance(season_totals_df, pd.DataFrame)
                and not season_totals_df.empty
            ):
                seasons_processed = 0
                for _, row in season_totals_df.iterrows():
                    record = row.to_dict()
                    record["player_id"] = player_id

                    # Convert column names to lowercase
                    record = {k.lower(): v for k, v in record.items()}

                    # Ensure correct data types
                    int_fields = [
                        "player_id",
                        "team_id",
                        "player_age",
                        "gp",
                        "gs",
                        "fgm",
                        "fga",
                        "fg3m",
                        "fg3a",
                        "ftm",
                        "fta",
                        "oreb",
                        "dreb",
                        "reb",
                        "ast",
                        "stl",
                        "blk",
                        "tov",
                        "pf",
                        "pts",
                    ]
                    float_fields = ["min", "fg_pct", "fg3_pct", "ft_pct"]
                    str_fields = ["season_id", "league_id", "team_abbreviation"]

                    for field in int_fields:
                        if field in record:
                            record[field] = (
                                int(float(record[field]))
                                if pd.notna(record[field])
                                else 0
                            )

                    for field in float_fields:
                        if field in record:
                            record[field] = (
                                float(record[field]) if pd.notna(record[field]) else 0.0
                            )

                    for field in str_fields:
                        if field in record:
                            record[field] = (
                                str(record[field]) if pd.notna(record[field]) else None
                            )

                    # Remove any fields that are not in the database table
                    valid_fields = set(int_fields + float_fields + str_fields)
                    record = {k: v for k, v in record.items() if k in valid_fields}

                    # Upsert the record into the Supabase table
                    supabase.table("season_totals_regular_season").upsert(
                        record
                    ).execute()
                    seasons_processed += 1

                print(
                    f"[{index}/{total_players}] Processed {seasons_processed} seasons for {full_name}"
                )
            else:
                print(
                    f"[{index}/{total_players}] No season totals data available for {full_name}"
                )

            time.sleep(0.6)  # To avoid hitting API rate limits

        except Exception as e:
            error_msg = f"[{index}/{total_players}] Error processing {player['full_name']}: {str(e)}"
            print(error_msg)
            logging.error(error_msg)
            continue

    print("All player season totals have been updated successfully.")


if __name__ == "__main__":
    setup_logging()
    fetch_and_store_player_season_totals()
