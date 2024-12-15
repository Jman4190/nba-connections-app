import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from supabase_client import supabase

STAT_CATEGORIES = {
    "PTS": "Points",
    "AST": "Assists",
    "REB": "Rebounds",
    "STL": "Steals",
    "BLK": "Blocks",
    "FG3M": "Three Pointers Made",
}


def get_seasons():
    try:
        result = supabase.table("league_leaders").select("season").execute()
        return sorted(list(set(row["season"] for row in result.data)))
    except Exception as e:
        print(f"Error fetching seasons: {e}")
        return []


def get_season_leaders(season, stat_category):
    try:
        result = (
            supabase.table("league_leaders")
            .select("player")
            .eq("season", season)
            .eq("stat_category", stat_category)
            .order(stat_category.lower(), desc=True)
            .limit(4)
            .execute()
        )
        return [row["player"] for row in result.data]
    except Exception as e:
        print(f"Error fetching leaders: {e}")
        return []


def insert_theme(season, stat_name):
    sql_query = f"""
        SELECT
            player,
            season,
            {stat_name.lower()} as value
        FROM
            league_leaders
        WHERE
            season = '{season}'
            AND stat_category = '{stat_name}'
        ORDER BY
            {stat_name.lower()} DESC
        LIMIT 4;
    """

    try:
        result = (
            supabase.table("new_themes")
            .insert(
                {
                    "theme": f"{season} {STAT_CATEGORIES[stat_name]} Leaders",
                    "theme_description": f"Season League Leaders",
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
    seasons = get_seasons()

    for season in seasons:
        for stat_category in STAT_CATEGORIES:
            print(f"\nProcessing {season} {STAT_CATEGORIES[stat_category]} leaders...")

            theme_id = insert_theme(season, stat_category)
            if not theme_id:
                continue

            players = get_season_leaders(season, stat_category)
            if not players:
                continue

            processed_players = process_players(players)
            if processed_players and len(processed_players) >= 4:
                insert_theme_players(theme_id, processed_players)
                print(
                    f"Successfully processed {season} {STAT_CATEGORIES[stat_category]} leaders"
                )
            else:
                print(
                    f"Not enough players found for {season} {STAT_CATEGORIES[stat_category]}"
                )


if __name__ == "__main__":
    main()
