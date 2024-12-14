import sys
import os
import logging
from datetime import datetime
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from nba_api.stats.endpoints import drafthistory
from supabase_client import supabase
from seasons import get_total_seasons
import time
import json
import logging


def setup_logging():
    logs_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs"
    )
    os.makedirs(logs_dir, exist_ok=True)

    log_filename = os.path.join(
        logs_dir, f"draft_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    )
    logging.basicConfig(
        filename=log_filename, level=logging.ERROR, format="%(asctime)s - %(message)s"
    )


def fetch_and_store_draft_history():
    seasons = get_total_seasons()

    total_seasons = len(seasons)
    for idx, season in enumerate(seasons, 1):
        print(f"Processing season {season} ({idx}/{total_seasons})")

        # Extract the starting year if season is in 'YYYY-YY' format
        if "-" in season:
            season_year = season.split("-")[0]
        else:
            season_year = season

        try:
            draft_history = drafthistory.DraftHistory(
                league_id="00", season_year_nullable=season_year
            )
            draft_data = draft_history.get_data_frames()[0]

            if not draft_data.empty:
                for _, row in draft_data.iterrows():
                    record = row.to_dict()
                    record["season"] = season_year

                    # Convert numeric fields to appropriate types
                    int_fields = [
                        "PERSON_ID",
                        "SEASON",
                        "ROUND_NUMBER",
                        "ROUND_PICK",
                        "OVERALL_PICK",
                        "TEAM_ID",
                    ]
                    for field in int_fields:
                        if field in record and record[field] is not None:
                            record[field] = int(record[field])

                    # Convert player_profile_flag to boolean if it's not already
                    if "player_profile_flag" in record:
                        record["player_profile_flag"] = bool(
                            record["player_profile_flag"]
                        )

                    # Convert column names to lowercase
                    record = {k.lower(): v for k, v in record.items()}

                    # Upsert the record into the Supabase table
                    response = supabase.table("draft_history").upsert(record).execute()

                    print(
                        f"Processed draft pick: {record.get('player_name', 'Unknown')} ({season_year})"
                    )
                    print(f"Upsert response: {response}")
                    print("\n")

                print(f"Processed draft history for season {season_year}")
            else:
                print(f"No draft data available for season {season_year}")

            time.sleep(1)  # To avoid hitting API rate limits

        except json.JSONDecodeError:
            logging.error(f"No valid data returned for season {season_year}.")
            print(f"No valid data returned for season {season_year}. Skipping...")
            continue
        except Exception as e:
            logging.error(f"Error fetching data for season {season_year}: {e}")
            print(f"Error fetching data for season {season_year}: {e}")
            continue

    print("Draft history data updated successfully.")


if __name__ == "__main__":
    setup_logging()
    fetch_and_store_draft_history()
