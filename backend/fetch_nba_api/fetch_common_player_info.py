import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from supabase_client import supabase
from nba_api.stats.static import players
from nba_api.stats.endpoints import commonplayerinfo
from datetime import datetime


def fetch_and_store_common_player_info():
    all_players = players.get_players()
    for player in all_players:
        try:
            player_id = player["id"]
            info = (
                commonplayerinfo.CommonPlayerInfo(
                    player_id=player_id,
                    league_id_nullable="00",  # '00' is the NBA league ID
                )
                .get_data_frames()[0]
                .to_dict(orient="records")[0]
            )

            # Convert all keys to lowercase
            info = {k.lower(): v for k, v in info.items()}

            # Ensure player_id is set
            info["player_id"] = player_id

            # Handle specific fields
            if "birthdate" in info:
                try:
                    info["birthdate"] = datetime.strptime(
                        info["birthdate"], "%Y-%m-%d"
                    ).date()
                except ValueError:
                    info["birthdate"] = None

            # Convert boolean fields
            bool_fields = [
                "roster_status",
                "dleague_flag",
                "nba_flag",
                "games_played_flag",
            ]
            for field in bool_fields:
                if field in info:
                    info[field] = bool(info[field])

            # Convert integer fields
            int_fields = [
                "player_id",
                "weight",
                "season_exp",
                "team_id",
                "from_year",
                "to_year",
                "draft_year",
                "draft_round",
                "draft_number",
            ]
            for field in int_fields:
                if field in info:
                    try:
                        info[field] = int(info[field])
                    except ValueError:
                        info[field] = None

            # Remove any keys not in the table schema
            valid_columns = [
                "player_id",
                "first_name",
                "last_name",
                "display_first_last",
                "display_last_comma_first",
                "display_fi_last",
                "player_slug",
                "birthdate",
                "school",
                "country",
                "last_affiliation",
                "height",
                "weight",
                "season_exp",
                "jersey",
                "position",
                "roster_status",
                "team_id",
                "team_name",
                "team_abbreviation",
                "team_code",
                "team_city",
                "playercode",
                "from_year",
                "to_year",
                "dleague_flag",
                "nba_flag",
                "games_played_flag",
                "draft_year",
                "draft_round",
                "draft_number",
            ]
            info = {k: v for k, v in info.items() if k in valid_columns}

            supabase.table("common_player_info").upsert(info).execute()
            print(f"Successfully processed player: {info['display_first_last']}")
        except Exception as e:
            print(f"Error processing player {player['full_name']}: {str(e)}")


fetch_and_store_common_player_info()
