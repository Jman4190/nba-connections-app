import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from supabase_client import supabase

COLLEGES = [
    "Kentucky",
    "California-Los Angeles",
    "North Carolina",
    "Duke",
    "Kansas",
    "Louisville",
    "Indiana",
    "Arizona",
    "Michigan",
    "Michigan State",
    "Syracuse",
    "Connecticut",
    "Texas",
    "Georgetown",
    "Ohio State",
    "Notre Dame",
    "Gonzaga",
    "UNLV",
    "Florida",
    "Wake Forest",
    "Oregon",
    "Villanova",
]


def get_college_players(college):
    sql_query = f"""
    WITH career_minutes AS (
        SELECT 
            player_id,
            SUM(min) AS total_minutes
        FROM
            player_career_stats
        GROUP BY
            player_id
        HAVING
            SUM(min) > 15000
    )
    """
    try:
        result = (
            supabase.from_("draft_history")
            .select("player_name, season, team_name")
            .eq("organization", college)
            .execute()
        )

        return [
            (row["player_name"], row["season"], row["team_name"]) for row in result.data
        ]
    except Exception as e:
        print(f"Error fetching {college} players: {e}")
        return []


def insert_theme(college, sql_query):
    try:
        result = (
            supabase.table("new_themes")
            .insert(
                {
                    "theme": f"{college} Alumni",
                    "theme_description": "College Alumni",
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
    for college in COLLEGES:
        print(f"\nProcessing {college} alumni...")

        sql_query = f"""
        WITH career_minutes AS (
            SELECT player_id, SUM(min) AS total_minutes
            FROM player_career_stats
            GROUP BY player_id
            HAVING SUM(min) > 15000
        )
        SELECT
            dh.player_name,
            dh.season AS draft_year,
            dh.team_name AS drafting_team,
            ROUND(cm.total_minutes) AS career_minutes
        FROM public.draft_history dh
        JOIN career_minutes cm ON dh.person_id = cm.player_id
        WHERE dh.organization = '{college}'
        ORDER BY cm.total_minutes DESC, dh.season DESC;
        """

        theme_id = insert_theme(college, sql_query)
        if not theme_id:
            continue

        players = get_college_players(college)
        if not players:
            continue

        processed_players = process_players(players)
        if processed_players:
            insert_theme_players(theme_id, processed_players)
            print(f"Successfully processed {college} alumni")
        else:
            print(f"No valid players found for {college}")


if __name__ == "__main__":
    main()
