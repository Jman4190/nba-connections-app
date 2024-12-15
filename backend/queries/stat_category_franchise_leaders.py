import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from supabase_client import supabase


def get_all_teams():
    try:
        result = supabase.table("franchise_leaders").select("team_name").execute()
        return [row["team_name"] for row in result.data]
    except Exception as e:
        print(f"Error fetching teams: {e}")
        return []


def get_franchise_leaders(stat_category):
    try:
        result = (
            supabase.table("franchise_leaders")
            .select(f"{stat_category}_player")
            .execute()
        )
        if result.data:
            return [row[f"{stat_category}_player"] for row in result.data]
        return []
    except Exception as e:
        print(f"Error fetching franchise leaders: {e}")
        return []


def get_pretty_stat_name(stat_category):
    stat_names = {
        "pts": "Points",
        "reb": "Rebounds",
        "ast": "Assists",
        "stl": "Steals",
        "blk": "Blocks",
    }
    return stat_names.get(stat_category, stat_category)


def insert_theme(stat_category):
    sql_query = """
    SELECT 
        stat_category,
        CASE stat_category
            WHEN 'pts' THEN pts_player
            WHEN 'ast' THEN ast_player
            WHEN 'reb' THEN reb_player
            WHEN 'stl' THEN stl_player
            WHEN 'blk' THEN blk_player
        END AS leader_player,
        CASE stat_category
            WHEN 'pts' THEN pts
            WHEN 'ast' THEN ast
            WHEN 'reb' THEN reb
            WHEN 'stl' THEN stl
            WHEN 'blk' THEN blk
        END AS leader_stat
    FROM franchise_leaders
    CROSS JOIN (
        SELECT unnest(ARRAY['pts', 'ast', 'reb', 'stl', 'blk']) AS stat_category
    ) categories;
    """

    try:
        result = (
            supabase.table("new_themes")
            .insert(
                {
                    "theme": f"Franchise Leaders in {get_pretty_stat_name(stat_category)}",
                    "theme_description": "Franchise Stat Leaders",
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
    for player_name in players:
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
    stat_categories = ["pts", "ast", "reb", "stl", "blk"]

    for stat_category in stat_categories:
        print(f"\nProcessing {get_pretty_stat_name(stat_category)}...")

        theme_id = insert_theme(stat_category)
        if not theme_id:
            continue

        players = get_franchise_leaders(stat_category)
        if not players:
            continue

        processed_players = process_players(players)
        if processed_players:
            insert_theme_players(theme_id, processed_players)
            print(f"Successfully processed {get_pretty_stat_name(stat_category)}")
        else:
            print(f"No valid players found for {get_pretty_stat_name(stat_category)}")


if __name__ == "__main__":
    main()
