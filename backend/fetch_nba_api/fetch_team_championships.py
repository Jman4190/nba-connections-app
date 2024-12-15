import sys
import os
import logging
from datetime import datetime
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from nba_api.stats.endpoints import teamdetails
from supabase_client import supabase
from nba_api.stats.static import teams


def setup_logging():
    logs_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs"
    )
    os.makedirs(logs_dir, exist_ok=True)

    log_filename = os.path.join(
        logs_dir, f"team_championships_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    )
    logging.basicConfig(
        filename=log_filename, level=logging.ERROR, format="%(asctime)s - %(message)s"
    )


def fetch_and_store_team_championships():
    setup_logging()
    nba_teams = teams.get_teams()

    for team in nba_teams:
        try:
            team_id = team["id"]
            team_name = team["full_name"]

            retries = 3
            while retries > 0:
                try:
                    team_details = teamdetails.TeamDetails(team_id=team_id)
                    championships = team_details.team_awards_championships.get_dict()[
                        "data"
                    ]
                    break
                except Exception as e:
                    retries -= 1
                    if retries == 0:
                        raise e
                    time.sleep(2 ** (3 - retries))

            for championship in championships:
                record = {
                    "team_id": team_id,
                    "team_name": team_name,
                    "year_awarded": championship[0],
                    "opposite_team": championship[1],
                }

                try:
                    response = (
                        supabase.table("team_championships").upsert(record).execute()
                    )
                    print(
                        f"Processed championship for {team_name}: {record['year_awarded']}"
                    )
                    print(f"Upsert response: {response}\n")
                except Exception as e:
                    error_msg = (
                        f"Supabase error for {team_name} - Data: {record}\nError: {e}"
                    )
                    print(error_msg)
                    logging.error(error_msg)
                    continue

            time.sleep(1)  # Rate limiting

        except Exception as e:
            error_msg = f"Error fetching data for {team_name}: {e}"
            print(error_msg)
            logging.error(error_msg)
            time.sleep(5)
            continue

    print(
        "Team championships data has been successfully fetched and stored in the database."
    )


if __name__ == "__main__":
    setup_logging()
    fetch_and_store_team_championships()
