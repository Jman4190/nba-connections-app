# this works by getting player_id separately and then inserting them into the theme_players table
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from supabase_client import supabase  # Import the supabase client


def insert_theme(theme, theme_description, sql_query, used_in_puzzle=False):
    """Inserts a new theme into the themes table and returns the generated theme_id."""
    try:
        print("Inserting theme...")
        result = (
            supabase.table("new_themes")
            .insert(
                {
                    "theme": theme,
                    "theme_description": theme_description,
                    "sql_query": sql_query,
                    "used_in_puzzle": used_in_puzzle,
                }
            )
            .execute()
        )

        theme_id = result.data[0]["theme_id"]
        print(f"Inserted theme with ID: {theme_id}")
        return theme_id
    except Exception as e:
        print(f"Error inserting theme: {e}")
        return None


def get_players(sql_query):
    """Executes the SQL query to retrieve players."""
    try:
        print("Executing player retrieval query...")
        result = (
            supabase.table("all_time_leaders")
            .select("player_name")
            .eq("stat_category", sql_query)
            .order("stat_value", desc=True)
            .limit(4)
            .execute()
        )

        return [row["player_name"] for row in result.data]
    except Exception as e:
        print(f"Error fetching players: {e}")
        return []


def insert_theme_players(theme_id, players):
    """Inserts players into the theme_players table."""
    try:
        print("Inserting theme players...")
        for player_name, player_id in players:
            supabase.table("theme_players").insert(
                {
                    "theme_id": theme_id,
                    "player_name": player_name,
                    "player_id": player_id,
                }
            ).execute()
        print(f"Inserted {len(players)} players for theme_id {theme_id}")
    except Exception as e:
        print(f"Error inserting theme players: {e}")


def get_player_id(player_name):
    """Fetch player_id based on player_name from common_player_info table."""
    try:
        result = (
            supabase.table("common_player_info")
            .select("player_id")
            .eq("display_first_last", player_name)
            .limit(1)
            .execute()
        )

        if result.data:
            print(f"Found ID {result.data[0]['player_id']} for player {player_name}")
            return result.data[0]["player_id"]
        print(f"No ID found for player {player_name}")
        return None
    except Exception as e:
        print(f"Error getting player ID: {e}")
        return None


def process_players(players):
    """Process the players data to extract unique players with their IDs."""
    unique_players = set()
    for player_name in players:
        player_id = get_player_id(player_name)
        print(f"Processing player: {player_name}, got ID: {player_id}")
        unique_players.add((player_name, player_id))
    processed = list(unique_players)
    print(f"Processed players: {processed}")
    return processed


def main():
    # Get categories from fetch_all_time_leaders
    categories = {
        "pts": "Points",
        "ast": "Assists",
        "reb": "Rebounds",
        "blk": "Blocks",
        "stl": "Steals",
        "fg_pct": "Field Goal %",
        "ft_pct": "Free Throw %",
        "fg3_pct": "3-Point %",
        "gp": "Games Played",
        "dreb": "Defensive Rebounds",
        "oreb": "Offensive Rebounds",
        "fg3a": "3-Point Attempts",
        "fg3m": "3-Point Makes",
        "fga": "Field Goal Attempts",
        "fgm": "Field Goals Made",
        "fta": "Free Throw Attempts",
        "ftm": "Free Throws Made",
        "pf": "Personal Fouls",
        "tov": "Turnovers",
    }

    for stat_code, stat_name in categories.items():
        theme_data = {
            "theme": f"All-Time {stat_name} Leaders",
            "theme_description": f"All-Time Leaders",
            "sql_query": stat_code,  # Just pass the stat_code instead of full SQL
        }

        try:
            print(f"\nProcessing {stat_name} leaders...")
            theme_id = insert_theme(
                theme_data["theme"],
                theme_data["theme_description"],
                theme_data["sql_query"],
            )

            if theme_id:
                players = get_players(theme_data["sql_query"])
                if players:
                    processed_players = process_players(players)
                    if processed_players and len(processed_players) >= 4:
                        insert_theme_players(theme_id, processed_players)
                    else:
                        print(f"Not enough players for {stat_name}")
                else:
                    print(f"No players found for {stat_name}")
        except Exception as e:
            print(f"Error processing {stat_name}: {e}")


if __name__ == "__main__":
    main()
