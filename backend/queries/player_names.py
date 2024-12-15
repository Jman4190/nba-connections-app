import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from supabase_client import supabase

LAST_NAMES = [
    "Williams",
    "Johnson",
    "Smith",
    "Brown",
    "Davis",
    "Jackson",
    "Green",
    "Thomas",
    "Robinson",
    "Thompson",
    "Miller",
]


def get_players_by_lastname(last_name):
    try:
        # First get all players with this last name from roster
        roster_result = (
            supabase.from_("common_team_roster")
            .select(
                """
                player_id,
                player,
                season,
                num,
                leagueid
                """
            )
            .eq("leagueid", "00")
        ).execute()

        # Filter by last name using common_player_info
        player_info = (
            supabase.from_("common_player_info")
            .select("player_id, display_first_last")
            .eq("last_name", last_name)
            .execute()
        )

        # Get all matching player_ids
        valid_player_ids = {p["player_id"] for p in player_info.data}

        # Group by player and calculate games
        player_games = {}
        for row in roster_result.data:
            if row["player_id"] in valid_player_ids:
                player_id = row["player_id"]
                if player_id not in player_games:
                    player_games[player_id] = {
                        "name": next(
                            p["display_first_last"]
                            for p in player_info.data
                            if p["player_id"] == player_id
                        ),
                        "games": 0,
                    }
                player_games[player_id]["games"] += 1

        # Get career minutes
        player_ids = list(player_games.keys())
        if not player_ids:
            return []

        minutes_result = (
            supabase.from_("player_career_stats")
            .select("player_id, min")
            .in_("player_id", player_ids)
            .execute()
        )

        qualified_players = []
        for player_id, data in player_games.items():
            if player_id in [r["player_id"] for r in minutes_result.data]:
                minutes = next(
                    r["min"] for r in minutes_result.data if r["player_id"] == player_id
                )
                if minutes >= 10000:  # Using 10000 minutes as in your original query
                    qualified_players.append(data["name"])

        return qualified_players

    except Exception as e:
        print(f"Error fetching players with last name {last_name}: {e}")
        return []


def insert_theme(last_name):
    sql_query = f"""
    WITH player_seasons AS (
        SELECT
            ctr.player_id,
            ctr.season,
            ctr.num AS jersey_number,
            strs.gp AS games_played,
            cpi.display_first_last,
            cpi.last_name
        FROM common_team_roster ctr
        JOIN season_totals_regular_season strs 
            ON ctr.player_id = strs.player_id 
            AND ctr.season = strs.season_id
            AND strs.league_id = '00'
        JOIN common_player_info cpi 
            ON ctr.player_id = cpi.player_id
        WHERE cpi.last_name = '{last_name}'
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
                    "theme": f"Players with last name {last_name}",
                    "theme_description": "Last Name",
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
    for last_name in LAST_NAMES:
        print(f"\nProcessing last name {last_name}...")

        theme_id = insert_theme(last_name)
        if not theme_id:
            continue

        players = get_players_by_lastname(last_name)
        if not players:
            continue

        processed_players = process_players(players)
        if processed_players:
            insert_theme_players(theme_id, processed_players)
            print(f"Successfully processed last name {last_name}")
        else:
            print(f"No valid players found for last name {last_name}")


if __name__ == "__main__":
    main()
