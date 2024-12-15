import sys
import os
import logging
from datetime import datetime
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from supabase_client import supabase
from nba_api.stats.static import players
from nba_api.stats.endpoints import playercareerstats


def setup_logging():
    logs_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs"
    )
    os.makedirs(logs_dir, exist_ok=True)

    log_filename = os.path.join(
        logs_dir, f"player_career_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    )
    logging.basicConfig(
        filename=log_filename, level=logging.ERROR, format="%(asctime)s - %(message)s"
    )


def fetch_and_store_player_career_stats():
    setup_logging()
    all_nba_players = players.get_players()

    for player in all_nba_players:
        try:
            player_id = player["id"]

            retries = 3
            while retries > 0:
                try:
                    career_stats = playercareerstats.PlayerCareerStats(
                        player_id=player_id, per_mode36="Totals"
                    )
                    break
                except Exception as e:
                    retries -= 1
                    if retries == 0:
                        raise e
                    time.sleep(2 ** (3 - retries))

            career_totals = career_stats.get_data_frames()[1]

            if not career_totals.empty:
                career_data = career_totals.iloc[0].to_dict()
                career_data = {k.lower(): v for k, v in career_data.items()}
                career_data["player_id"] = player_id

                int_fields = [
                    "player_id",
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

                for field in int_fields:
                    if field in career_data:
                        career_data[field] = (
                            int(float(career_data[field]))
                            if career_data[field] is not None
                            else 0
                        )

                for field in float_fields:
                    if field in career_data:
                        career_data[field] = (
                            float(career_data[field])
                            if career_data[field] is not None
                            else 0.0
                        )

                try:
                    career_data.pop("team_id", None)
                    response = (
                        supabase.table("player_career_stats")
                        .upsert(career_data)
                        .execute()
                    )
                    print(
                        f"Successfully processed career stats for player: {player['full_name']}"
                    )
                    print(f"Upsert response: {response}\n")
                except Exception as insert_error:
                    error_msg = f"Supabase error for {player['full_name']} - Data: {career_data}\nError: {insert_error}"
                    print(error_msg)
                    logging.error(error_msg)
                    continue
            else:
                print(f"No career stats found for player: {player['full_name']}")

            time.sleep(0.6)

        except Exception as e:
            error_msg = f"Error processing player {player['full_name']}: {e}"
            print(error_msg)
            logging.error(error_msg)
            time.sleep(5)
            continue


if __name__ == "__main__":
    setup_logging()
    fetch_and_store_player_career_stats()
