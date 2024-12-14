import sys
import os
import logging
from datetime import datetime
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from supabase_client import supabase
from nba_api.stats.endpoints import franchiseleaders
from nba_api.stats.static import teams
from supabase_client import supabase
import time


def setup_logging():
    logs_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs"
    )
    os.makedirs(logs_dir, exist_ok=True)

    log_filename = os.path.join(
        logs_dir, f"franchise_leaders_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    )
    logging.basicConfig(
        filename=log_filename, level=logging.ERROR, format="%(asctime)s - %(message)s"
    )


def fetch_and_store_franchise_leaders():
    setup_logging()
    all_teams = teams.get_teams()

    for team in all_teams:
        try:
            team_id = team["id"]

            # Add exponential backoff retry
            retries = 3
            while retries > 0:
                try:
                    leaders = franchiseleaders.FranchiseLeaders(team_id=team_id)
                    data = leaders.get_data_frames()[0]
                    break
                except Exception as e:
                    retries -= 1
                    if retries == 0:
                        raise e
                    time.sleep(2 ** (3 - retries))

            if not data.empty:
                record = data.iloc[0].to_dict()
                record["team_id"] = team_id
                record["team_name"] = team["full_name"]

                record = {k.lower(): v for k, v in record.items()}

                int_fields = [
                    "team_id",
                    "pts",
                    "pts_person_id",
                    "ast",
                    "ast_person_id",
                    "reb",
                    "reb_person_id",
                    "blk",
                    "blk_person_id",
                    "stl",
                    "stl_person_id",
                ]

                for field in int_fields:
                    if field in record and record[field] is not None:
                        record[field] = int(record[field])

                print(f"Attempting to insert record: {record}")
                try:
                    supabase.table("franchise_leaders").upsert(record).execute()
                except Exception as e:
                    error_msg = f"Supabase error for {team['full_name']} - Data: {record}\nError: {e}"
                    print(error_msg)
                    logging.error(error_msg)
                    continue

                print(f"Processed franchise leaders for {team['full_name']}")
            else:
                error_msg = f"No data available for {team['full_name']}"
                print(error_msg)
                logging.error(error_msg)

            time.sleep(1)

        except Exception as e:
            error_msg = f"Error fetching data for {team['full_name']}: {e}"
            print(error_msg)
            logging.error(error_msg)
            time.sleep(5)
            continue

    print("Franchise leaders data updated successfully.")


if __name__ == "__main__":
    setup_logging()
    fetch_and_store_franchise_leaders()
