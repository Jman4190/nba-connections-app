import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from supabase_client import supabase

STAT_CATEGORIES = {
    "pts": "Points",
    "ast": "Assists",
    "reb": "Rebounds",
    "stl": "Steals",
    "blk": "Blocks",
}


def get_league_leaders(stat_category):
    try:
        print(f"Fetching leaders for {stat_category}...")
        result = (
            supabase.table("league_leaders")
            .select("player")
            .eq("rank", 1)
            .ilike("stat_category", stat_category.upper())
            .execute()
        )
        seen = set()
        players = []
        for row in result.data:
            if row["player"] not in seen:
                seen.add(row["player"])
                players.append(row["player"])
        print(f"Found {len(players)} players for {stat_category}: {players}")
        return players
    except Exception as e:
        print(f"Error fetching league leaders: {e}")
        print(f"Full error details: {str(e)}")
        return []


def insert_theme(stat_category):
    sql_query = f"""
    SELECT
        player,
        season,
        stat_category,
        CASE stat_category
            WHEN '{stat_category}' THEN {stat_category}
            ELSE NULL
        END AS stat_value
    FROM
        public.league_leaders
    WHERE
        rank = 1
        AND stat_category = '{stat_category}'
    ORDER BY
        season;
    """

    try:
        result = (
            supabase.table("new_themes")
            .insert(
                {
                    "theme": f"League Leaders in {STAT_CATEGORIES[stat_category]}",
                    "theme_description": "League Leaders",
                    "sql_query": sql_query,
                    "used_in_puzzle": False,
                }
            )
            .execute()
        )
        print(
            f"Created theme for {stat_category} with ID: {result.data[0]['theme_id']}"
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
    print(f"Processing players: {players}")
    unique_players = set()
    for player_name in players:
        player_id = get_player_id(player_name)
        print(f"Got ID {player_id} for player {player_name}")
        if player_id:
            unique_players.add((player_name, player_id))
    result = list(unique_players)
    print(f"Processed players result: {result}")
    return result


def insert_theme_players(theme_id, players):
    try:
        print(f"Inserting {len(players)} players for theme {theme_id}")
        for player_name, player_id in players:
            print(f"Inserting {player_name} ({player_id})")
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
    for stat_category in STAT_CATEGORIES:
        print(f"\nProcessing {STAT_CATEGORIES[stat_category]}...")

        theme_id = insert_theme(stat_category)
        if not theme_id:
            continue

        players = get_league_leaders(stat_category)
        if not players:
            continue

        processed_players = process_players(players)
        if processed_players:
            insert_theme_players(theme_id, processed_players)
            print(f"Successfully processed {STAT_CATEGORIES[stat_category]}")
        else:
            print(f"No valid players found for {STAT_CATEGORIES[stat_category]}")


if __name__ == "__main__":
    main()
