import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from supabase_client import supabase

# Simpler logging setup - only INFO level and above
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.FileHandler("jersey_numbers.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

JERSEY_NUMBERS = [
    "12",
    "11",
    "5",
    "3",
    "20",
    "15",
    "14",
    "10",
    "7",
    "22",
    "1",
    "6",
    "2",
    "34",
    "33",
    "21",
]


def get_jersey_players(jersey_number):
    try:
        # First get the roster data
        roster_result = (
            supabase.from_("common_team_roster")
            .select("player_id, season")
            .eq("num", jersey_number)
            .gte("season", "1990")
            .execute()
        )

        # Get unique player IDs
        player_ids = list(set(row["player_id"] for row in roster_result.data))

        if not player_ids:
            return []

        # Then get player names
        player_result = (
            supabase.from_("common_player_info")
            .select("player_id, display_first_last")
            .in_("player_id", player_ids)
            .execute()
        )

        # Create player ID to name mapping
        player_names = {
            p["player_id"]: p["display_first_last"] for p in player_result.data
        }

        # Count seasons per player
        player_seasons = {}
        for row in roster_result.data:
            name = player_names.get(row["player_id"])
            if name:
                if name not in player_seasons:
                    player_seasons[name] = 0
                player_seasons[name] += 1

        # Return players with 10+ seasons
        return [name for name, count in player_seasons.items() if count >= 10]

    except Exception as e:
        print(f"Error fetching players for jersey #{jersey_number}: {e}")
        return []


def insert_theme(jersey_number):
    sql_query = f"""
    WITH player_seasons AS (
        SELECT
            ctr.player_id,
            ctr.season,
            ctr.num AS jersey_number,
            strs.gp AS games_played,
            cpi.display_first_last
        FROM common_team_roster ctr
        JOIN season_totals_regular_season strs 
            ON ctr.player_id = strs.player_id 
            AND ctr.season = strs.season_id
            AND strs.league_id = '00'
        JOIN common_player_info cpi 
            ON ctr.player_id = cpi.player_id
        WHERE ctr.num = '{jersey_number}'
    )
    SELECT
        display_first_last,
        STRING_AGG(season || ': ' || games_played::text, ', ' ORDER BY season) as seasons
    FROM player_seasons
    GROUP BY player_id, display_first_last
    HAVING COUNT(*) >= 5
    ORDER BY COUNT(*) DESC;
    """

    try:
        result = (
            supabase.table("new_themes")
            .insert(
                {
                    "theme": f"Players that wore #{jersey_number}",
                    "theme_description": f"Jersey Number",
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
    for jersey_number in JERSEY_NUMBERS:
        print(f"\nProcessing jersey #{jersey_number}...")

        theme_id = insert_theme(jersey_number)
        if not theme_id:
            continue

        players = get_jersey_players(jersey_number)
        if not players:
            continue

        processed_players = process_players(players)
        if processed_players:
            insert_theme_players(theme_id, processed_players)
            print(f"Successfully processed jersey #{jersey_number}")
        else:
            print(f"No valid players found for jersey #{jersey_number}")


if __name__ == "__main__":
    main()
