import sys
import os
import logging
from datetime import datetime
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from supabase_client import supabase
from nba_api.stats.endpoints import leagueleaders
from seasons import get_total_seasons
from supabase_client import supabase
import time


def setup_logging():
    logs_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs"
    )
    os.makedirs(logs_dir, exist_ok=True)

    log_filename = os.path.join(
        logs_dir, f"league_leaders_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    )
    logging.basicConfig(
        filename=log_filename, level=logging.ERROR, format="%(asctime)s - %(message)s"
    )


def fetch_and_store_league_leaders():
    setup_logging()
    seasons = get_total_seasons()
    stat_categories = [
        "PTS",
        "AST",
        "REB",
        "STL",
        "BLK",
        "FG3M",
        "FG_PCT",
        "FG3_PCT",
        "FT_PCT",
    ]

    for season in seasons:
        print(f"\nProcessing season: {season}")
        for category in stat_categories:
            print(f"\nAttempting to fetch {category} leaders for {season}")
            try:
                leaders = leagueleaders.LeagueLeaders(
                    league_id="00",
                    per_mode48="PerGame",
                    scope="S",
                    season=season,
                    season_type_all_star="Regular Season",
                    stat_category_abbreviation=category,
                ).get_data_frames()[0]

                if leaders.empty:
                    print(f"No data returned for {category} in {season}")
                    logging.warning(
                        f"Empty dataset received for {category} in {season}"
                    )
                    continue

                print(f"Found {len(leaders)} records for {category}")
                print(f"Sample data for {category}:")
                print(leaders.head(1))

                if not leaders.empty:
                    for _, row in leaders.iterrows():
                        if row["RANK"] > 4:  # Skip if rank is greater than 4
                            continue

                        record = row.to_dict()
                        record["season"] = season
                        record["stat_category"] = category

                        # Convert numeric fields to appropriate types
                        for field in record:
                            if field in ["PLAYER_ID", "RANK", "GP"]:
                                record[field] = int(record[field])
                            elif field not in [
                                "PLAYER",
                                "TEAM",
                                "season",
                                "stat_category",
                            ]:
                                try:
                                    record[field] = float(record[field])
                                except ValueError as e:
                                    logging.error(
                                        f"Value conversion failed for {field}: {record[field]} in {season} {category}"
                                    )
                                    # If conversion fails, keep the original value
                                    pass

                        # Convert column names to lowercase
                        record = {k.lower(): v for k, v in record.items()}

                        # Remove 'team_id' if it exists (since it's not in our schema)
                        record.pop("team_id", None)

                        # Add 'stat_category' to schema_columns
                        schema_columns = [
                            "player_id",
                            "rank",
                            "player",
                            "team",
                            "gp",
                            "min",
                            "fgm",
                            "fga",
                            "fg_pct",
                            "fg3m",
                            "fg3a",
                            "fg3_pct",
                            "ftm",
                            "fta",
                            "ft_pct",
                            "oreb",
                            "dreb",
                            "reb",
                            "ast",
                            "stl",
                            "blk",
                            "tov",
                            "pf",
                            "pts",
                            "eff",
                            "ast_tov",
                            "stl_tov",
                            "season",
                            "stat_category",
                        ]

                        record = {
                            k: record.get(k) for k in schema_columns if k in record
                        }

                        # Print an example record
                        print(f"Example record for {category} in {season}:")
                        print(record)
                        print("\n")

                        # Upsert the record into the Supabase table
                        response = (
                            supabase.table("league_leaders").upsert(record).execute()
                        )

                        # Print the response to see if the upsert was successful
                        print(f"Upsert response for {category} in {season}:")
                        print(response)
                        print("\n")

                else:
                    print(f"No data available for {category} in season {season}")

                time.sleep(1)  # To avoid hitting API rate limits

            except Exception as e:
                if "Expecting value" in str(e):
                    print(f"No data available for {category} in {season}")
                    continue
                else:
                    raise e

    print("League leaders data updated successfully.")


if __name__ == "__main__":
    fetch_and_store_league_leaders()
