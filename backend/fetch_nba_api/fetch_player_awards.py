import sys
import os
import logging
from datetime import datetime
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from supabase_client import supabase
from nba_api.stats.endpoints import PlayerAwards
from nba_api.stats.static import players


def setup_logging():
    logs_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs"
    )
    os.makedirs(logs_dir, exist_ok=True)

    log_filename = os.path.join(
        logs_dir, f"player_awards_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    )
    logging.basicConfig(
        filename=log_filename, level=logging.ERROR, format="%(asctime)s - %(message)s"
    )


def fetch_and_store_player_awards():
    setup_logging()
    all_players = players.get_players()

    # Get all award winners first
    award_winners = set()
    for player in all_players:
        try:
            awards = PlayerAwards(player_id=player["id"])
            df = awards.player_awards.get_data_frame()

            if not df.empty:
                # Filter out Player of the Month and Week awards
                df = df[~df["TYPE"].str.contains("Month|Week", case=False, na=False)]
                if not df.empty:
                    award_winners.add(player["id"])
            time.sleep(0.6)  # Avoid API rate limits
        except Exception as e:
            logging.error(f"Error checking awards for {player['full_name']}: {str(e)}")
            continue

    # Filter players list to only include award winners
    award_winning_players = [p for p in all_players if p["id"] in award_winners]
    total_players = len(award_winning_players)

    for index, player in enumerate(award_winning_players, 1):
        try:
            player_id = player["id"]
            full_name = player["full_name"]

            awards = PlayerAwards(player_id=player_id)
            df = awards.player_awards.get_data_frame()

            if df.empty:
                print(f"[{index}/{total_players}] No awards for {full_name}")
                continue

            # Filter out Player of the Month and Week awards
            df = df[~df["TYPE"].str.contains("Month|Week", case=False, na=False)]

            awards_processed = 0
            for _, row in df.iterrows():
                record = {
                    "person_id": int(row["PERSON_ID"]),
                    "first_name": row["FIRST_NAME"],
                    "last_name": row["LAST_NAME"],
                    "team": row["TEAM"],
                    "description": row["DESCRIPTION"],
                    "all_nba_team_number": (
                        int(row["ALL_NBA_TEAM_NUMBER"])
                        if row["ALL_NBA_TEAM_NUMBER"]
                        else None
                    ),
                    "season": row["SEASON"],
                    "month": int(row["MONTH"]) if row["MONTH"] else None,
                    "week": int(row["WEEK"]) if row["WEEK"] else None,
                    "conference": row["CONFERENCE"],
                    "award_type": row["TYPE"],
                    "subtype1": row["SUBTYPE1"],
                    "subtype2": row["SUBTYPE2"],
                    "subtype3": row["SUBTYPE3"],
                }

                # Upsert the record into Supabase
                supabase.table("player_awards").upsert(record).execute()
                awards_processed += 1

            print(
                f"[{index}/{total_players}] Processed {awards_processed} awards for {full_name}"
            )
            time.sleep(0.6)  # Avoid API rate limits

        except Exception as e:
            error_msg = f"[{index}/{total_players}] Error processing {player['full_name']}: {str(e)}"
            print(error_msg)
            logging.error(error_msg)
            continue

    print("All player awards have been updated successfully.")


if __name__ == "__main__":
    setup_logging()
    fetch_and_store_player_awards()
