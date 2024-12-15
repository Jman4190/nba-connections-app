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


def get_franchise_leaders(team_name):
    try:
        result = (
            supabase.table("franchise_leaders")
            .select("pts_player, reb_player, ast_player, stl_player, blk_player")
            .eq("team_name", team_name)
            .execute()
        )
        if result.data:
            return [
                result.data[0]["pts_player"],
                result.data[0]["reb_player"],
                result.data[0]["ast_player"],
                result.data[0]["stl_player"],
                result.data[0]["blk_player"],
            ]
        return []
    except Exception as e:
        print(f"Error fetching franchise leaders: {e}")
        return []


def insert_theme(team_name):
    sql_query = f"""
        select
            team_name,
            pts_player,
            reb_player,
            ast_player,
            stl_player,
            blk_player
        from
            franchise_leaders
        where
            team_name = '{team_name}';
    """

    try:
        result = (
            supabase.table("new_themes")
            .insert(
                {
                    "theme": f"{team_name} Franchise Leaders",
                    "theme_description": f"Franchise Leaders",
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
    teams = get_all_teams()

    for team_name in teams:
        print(f"\nProcessing {team_name}...")

        theme_id = insert_theme(team_name)
        if not theme_id:
            continue

        players = get_franchise_leaders(team_name)
        if not players:
            continue

        processed_players = process_players(players)
        if processed_players:
            insert_theme_players(theme_id, processed_players)
            print(f"Successfully processed {team_name}")
        else:
            print(f"No valid players found for {team_name}")


if __name__ == "__main__":
    main()
