import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from supabase_client import supabase


def get_championship_teams():
    try:
        return (
            supabase.table("team_championships")
            .select("team_id, team_name, year_awarded")
            .gt("year_awarded", 1984)
            .execute()
        )
    except Exception as e:
        print(f"Error fetching championship teams: {e}")
        return []


def insert_theme(team_name, year):
    season = f"{year-1}-{str(year)[2:].zfill(2)}"
    sql_query = f"""
    WITH championship_team AS (
        SELECT team_id
        FROM team_championships
        WHERE year_awarded = {year}
        AND team_name = '{team_name}'
    ),
    championship_roster AS (
        SELECT DISTINCT
            ctr.player_id,
            ctr.player,
            ctr.team_id
        FROM common_team_roster ctr
        JOIN championship_team ct ON ctr.team_id = ct.team_id
        WHERE ctr.season = '{season}'
    ),
    player_stats AS (
        SELECT
            player_id,
            pts::float / NULLIF(gp, 0) AS points_per_game
        FROM season_totals_regular_season
        WHERE season_id = '{season}'
        AND league_id = '00'
    )
    SELECT
        cr.player,
        ROUND(ps.points_per_game::numeric, 1) AS ppg
    FROM championship_roster cr
    JOIN player_stats ps ON cr.player_id = ps.player_id
    WHERE ps.points_per_game > 7
    ORDER BY ps.points_per_game DESC;
    """

    try:
        result = (
            supabase.table("new_themes")
            .insert(
                {
                    "theme": f"{year} {team_name} Championship Roster",
                    "theme_description": "Championship Roster",
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


def get_championship_roster(team_id, season):
    try:
        result = (
            supabase.table("common_team_roster")
            .select("player, player_id")
            .eq("team_id", team_id)
            .eq("season", season)
            .execute()
        )
        return [(row["player"], row["player_id"]) for row in result.data]
    except Exception as e:
        print(f"Error fetching roster: {e}")
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
    championships = get_championship_teams()
    if not championships.data:
        return

    for champ in championships.data:
        print(f"\nProcessing {champ['year_awarded']} {champ['team_name']}...")

        theme_id = insert_theme(champ["team_name"], champ["year_awarded"])
        if not theme_id:
            continue

        season = f"{champ['year_awarded']-1}-{str(champ['year_awarded'])[2:].zfill(2)}"
        players = get_championship_roster(champ["team_id"], season)

        if players:
            insert_theme_players(theme_id, players)
            print(
                f"Successfully processed {champ['year_awarded']} {champ['team_name']}"
            )
        else:
            print(f"No players found for {champ['year_awarded']} {champ['team_name']}")


if __name__ == "__main__":
    main()
