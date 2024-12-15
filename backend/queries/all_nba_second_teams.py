import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from supabase_client import supabase


def get_all_nba_second_teams():
    try:
        result = (
            supabase.table("player_awards")
            .select("season")
            .eq("description", "All-NBA")
            .eq("all_nba_team_number", 2)
            .gte("season", "1979-80")
            .execute()
        )

        data = result.data
        if not data:
            return []

        # Deduplicate seasons
        unique_seasons = []
        seen = set()
        for row in data:
            season = row["season"]
            if season not in seen:
                seen.add(season)
                unique_seasons.append(row)

        return unique_seasons

    except Exception as e:
        print(f"Error fetching All-NBA Second Teams: {e}")
        return []


def insert_theme(season):
    sql_query = f"""
    SELECT DISTINCT
        first_name || ' ' || last_name AS player,
        person_id
    FROM player_awards
    WHERE description = 'All-NBA'
      AND all_nba_team_number = 2
      AND season = '{season}'
    ORDER BY player;
    """

    try:
        result = (
            supabase.table("new_themes")
            .insert(
                {
                    "theme": f"{season} Second Team All-NBA",
                    "theme_description": "All-NBA Second Teams",
                    "sql_query": sql_query,
                    "used_in_puzzle": False,
                }
            )
            .execute()
        )
        return result.data[0]["theme_id"] if result.data else None
    except Exception as e:
        print(f"Error inserting theme: {e}")
        return None


def get_second_team_players(season):
    try:
        print(f"Attempting to fetch players for season {season}")
        result = (
            supabase.table("player_awards")
            .select("first_name, last_name, person_id")
            .eq("description", "All-NBA")
            .eq("all_nba_team_number", 2)
            .eq("season", season)
            .execute()
        )
        print(f"Raw result: {result.data}")
        return [
            (f"{row['first_name']} {row['last_name']}", row["person_id"])
            for row in result.data
        ]
    except Exception as e:
        print(f"Error fetching players: {str(e)}")
        return []


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
    seasons = get_all_nba_second_teams()
    if not seasons:
        print("No seasons data returned")
        return

    print(f"Found {len(seasons)} seasons to process")
    for season_data in seasons:
        season = season_data["season"]
        print(f"\nProcessing {season} Second Team All-NBA...")

        theme_id = insert_theme(season)
        print(f"Generated theme_id: {theme_id}")
        if not theme_id:
            continue

        players = get_second_team_players(season)
        print(f"Found {len(players)} players for season {season}")

        if players:
            insert_theme_players(theme_id, players)
            print(f"Successfully processed {season} Second Team All-NBA")
        else:
            print(f"No players found for {season} Second Team All-NBA")


if __name__ == "__main__":
    main()
