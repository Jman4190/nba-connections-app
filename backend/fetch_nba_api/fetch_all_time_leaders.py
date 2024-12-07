import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from nba_api.stats.endpoints import alltimeleadersgrids
from supabase_client import supabase


def fetch_and_store_all_time_leaders():
    # Fetch all-time leaders data
    leaders = alltimeleadersgrids.AllTimeLeadersGrids(
        league_id="00", per_mode_simple="Totals", season_type="Regular Season", topx=10
    )

    # Define the categories and their corresponding dataset names
    categories = {
        "pts": "PTSLeaders",
        "ast": "ASTLeaders",
        "reb": "REBLeaders",
        "blk": "BLKLeaders",
        "stl": "STLLeaders",
        "fg_pct": "FG_PCTLeaders",
        "ft_pct": "FT_PCTLeaders",
        "fg3_pct": "FG3_PCTLeaders",
        "gp": "GPLeaders",
        "dreb": "DREBLeaders",
        "oreb": "OREBLeaders",
        "fg3a": "FG3ALeaders",
        "fg3m": "FG3MLeaders",
        "fga": "FGALeaders",
        "fgm": "FGMLeaders",
        "fta": "FTALeaders",
        "ftm": "FTMLeaders",
        "pf": "PFLeaders",
        "tov": "TOVLeaders",
    }

    # Process and store data for each category
    for stat, dataset in categories.items():
        data = leaders.get_dict()["resultSets"][
            leaders.get_dict()["resultSets"].index(
                next(
                    item
                    for item in leaders.get_dict()["resultSets"]
                    if item["name"] == dataset
                )
            )
        ]

        for row in data["rowSet"]:
            record = {
                "player_id": row[0],
                "player_name": row[1],
                "stat_value": row[2],
                "stat_rank": row[3],
                "stat_category": stat,
            }

            # Upsert the record into the Supabase table
            supabase.table("all_time_leaders").upsert(record).execute()

    print("All-time leaders data updated successfully.")


if __name__ == "__main__":
    fetch_and_store_all_time_leaders()
