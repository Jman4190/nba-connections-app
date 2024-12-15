import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from supabase_client import supabase


def get_draft_class(season):
    try:
        result = (
            supabase.table("draft_history")
            .select("player_name, season, team_name")
            .eq("season", season)
            .eq("round_number", 1)
            .order("overall_pick")
            .execute()
        )
        return [
            (row["player_name"], row["season"], row["team_name"]) for row in result.data
        ]
    except Exception as e:
        print(f"Error fetching draft class: {e}")
        return []


def insert_theme(season):
    sql_query = f"""
        SELECT
            player_name,
            season,
            overall_pick,
            team_name,
            organization
        FROM
            public.draft_history
        WHERE
            season = {season}
            AND round_number = 1
        ORDER BY
            overall_pick;
    """

    try:
        result = (
            supabase.table("new_themes")
            .insert(
                {
                    "theme": f"{season} Draft Class",
                    "theme_description": f"Draft Class",
                    "sql_query": sql_query,
                    "used_in_puzzle": False,
                }
            )
            .execute()
        )
        return result.data[0]["theme_id"]
    except Exception as e:
        print(f"Error inserting theme: {e}")
        return None


def get_player_id(player_name):
    try:
        result = (
            supabase.table("common_player_info")
            .select("player_id")
            .eq("display_first_last", player_name)
            .limit(1)
            .execute()
        )
        return result.data[0]["player_id"] if result.data else None
    except Exception as e:
        print(f"Error getting player ID: {e}")
        return None


def process_players(players):
    unique_players = set()
    for player_name, _, _ in players:
        player_id = get_player_id(player_name)
        if player_id:
            unique_players.add((player_name, player_id))
    return list(unique_players)


def insert_theme_players(theme_id, players):
    try:
        for player_name, player_id in players:
            supabase.table("theme_players").insert(
                {
                    "theme_id": theme_id,
                    "player_name": player_name,
                    "player_id": player_id,
                }
            ).execute()
    except Exception as e:
        print(f"Error inserting theme players: {e}")


def main():
    # Loop through seasons from 1980 to 2023
    for season in range(1980, 2024):
        print(f"\nProcessing {season} draft class...")

        theme_id = insert_theme(season)
        if not theme_id:
            continue

        players = get_draft_class(season)
        if not players:
            continue

        processed_players = process_players(players)
        if processed_players:
            insert_theme_players(theme_id, processed_players)
            print(f"Successfully processed {season} draft class")
        else:
            print(f"No valid players found for {season} draft class")


if __name__ == "__main__":
    main()
