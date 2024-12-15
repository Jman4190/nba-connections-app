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
    setup_logging()
    seasons = get_total_seasons()
    total_seasons = len(seasons)

    for idx, season in enumerate(seasons, 1):
        # Extract the starting year if season is in 'YYYY-YY' format
        season_year = season.split("-")[0] if "-" in season else season

        try:
            draft_history = drafthistory.DraftHistory(
                league_id="00", season_year_nullable=season_year
            )
            draft_data = draft_history.get_data_frames()[0]

            if not draft_data.empty:
                picks_processed = 0
                for _, row in draft_data.iterrows():
                    record = row.to_dict()
                    record["season"] = season_year

                    # Convert numeric fields to appropriate types
                    int_fields = [
                        "person_id",
                        "season",
                        "round_number",
                        "round_pick",
                        "overall_pick",
                        "team_id",
                    ]
                    for field in int_fields:
                        if field in record and record[field] is not None:
                            record[field] = int(record[field])

                    # Convert player_profile_flag to boolean
                    if "player_profile_flag" in record:
                        record["player_profile_flag"] = bool(
                            record["player_profile_flag"]
                        )

                    # Convert column names to lowercase
                    record = {k.lower(): v for k, v in record.items()}

                    try:
                        response = (
                            supabase.table("draft_history").upsert(record).execute()
                        )
                        picks_processed += 1
                        print(
                            f"[{idx}/{total_seasons}] Processed draft pick: {record.get('player_name', 'Unknown')} ({season_year})"
                        )
                    except Exception as insert_error:
                        error_msg = f"Supabase error for {record.get('player_name', 'Unknown')} - Data: {record}\nError: {insert_error}"
                        print(error_msg)
                        logging.error(error_msg)
                        continue

                print(
                    f"[{idx}/{total_seasons}] Processed {picks_processed} draft picks for season {season_year}"
                )
            else:
                print(
                    f"[{idx}/{total_seasons}] No draft data available for season {season_year}"
                )

            time.sleep(1)  # To avoid hitting API rate limits

        except Exception as e:
            error_msg = f"[{idx}/{total_seasons}] Error processing season {season_year}: {str(e)}"
            print(error_msg)
            logging.error(error_msg)
            continue

    print("Draft history data updated successfully.")


if __name__ == "__main__":
    fetch_and_store_draft_history()
