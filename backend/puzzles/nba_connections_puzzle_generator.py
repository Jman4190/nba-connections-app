import os
import random
import json
import openai
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_themes():
    themes_res = supabase.table("new_themes").select("*").execute()
    themes = themes_res.data if themes_res.data else []

    theme_map = {}
    for t in themes:
        desc = t["theme_description"]
        theme_map.setdefault(desc, []).append(t)
    return theme_map


def get_unused_players(theme_id):
    res = (
        supabase.table("theme_players")
        .select("*")
        .eq("theme_id", theme_id)
        .eq("used_in_puzzle", False)
        .execute()
    )
    return res.data if res.data else []


def pick_four_unused_players(theme_id):
    unused = get_unused_players(theme_id)
    if len(unused) < 4:
        return None
    return unused[:4]


def mark_players_used(player_ids):
    # Mark given players as used
    supabase.table("theme_players").update({"used_in_puzzle": True}).in_(
        "player_id", player_ids
    ).execute()


def mark_theme_if_exhausted(theme_id):
    remaining = get_unused_players(theme_id)
    if len(remaining) < 4:
        supabase.table("new_themes").update({"used_in_puzzle": True}).eq(
            "theme_id", theme_id
        ).execute()


def create_puzzles(max_puzzles=100):
    theme_map = get_themes()
    puzzles_created = 0

    # Group themes by description first
    theme_desc_groups = {}
    for theme_desc, theme_list in theme_map.items():
        viable_themes = []
        for th in theme_list:
            if not th["used_in_puzzle"]:
                unused_count = len(get_unused_players(th["theme_id"]))
                if unused_count >= 4:
                    viable_themes.append(th)
        if len(viable_themes) >= 4:  # Need at least 4 viable themes per description
            theme_desc_groups[theme_desc] = viable_themes

    print(f"Found {len(theme_desc_groups)} viable theme descriptions")

    while puzzles_created < max_puzzles and theme_desc_groups:
        print(f"\nAttempting puzzle {puzzles_created + 1}...")

        # Pick a random theme description that has enough viable themes
        viable_descriptions = [
            desc for desc, themes in theme_desc_groups.items() if len(themes) >= 4
        ]
        if not viable_descriptions:
            break

        chosen_desc = random.choice(viable_descriptions)
        chosen_themes = random.sample(theme_desc_groups[chosen_desc], 4)
        print(f"Selected theme description: {chosen_desc}")
        print(f"Selected theme IDs: {[t['theme_id'] for t in chosen_themes]}")

        puzzle_groups = []
        all_player_ids = set()

        valid_puzzle = True
        for ct in chosen_themes:
            selected_players = pick_four_unused_players(ct["theme_id"])
            if not selected_players:
                print(f"Failed to get players for theme {ct['theme_id']}")
                valid_puzzle = False
                break

            current_player_ids = {p["player_id"] for p in selected_players}
            if len(current_player_ids) != 4:
                print(f"Duplicate players in theme {ct['theme_id']}")
                valid_puzzle = False
                break

            if any(pid in all_player_ids for pid in current_player_ids):
                print(f"Player overlap detected with theme {ct['theme_id']}")
                valid_puzzle = False
                break

            all_player_ids.update(current_player_ids)
            puzzle_groups.append((ct, selected_players))

        if not valid_puzzle:
            print("Puzzle invalid, removing themes and trying again")
            # Remove used themes from the description group
            theme_desc_groups[chosen_desc] = [
                t
                for t in theme_desc_groups[chosen_desc]
                if t["theme_id"] not in [ct["theme_id"] for ct in chosen_themes]
            ]
            # Remove description if not enough themes left
            if len(theme_desc_groups[chosen_desc]) < 4:
                del theme_desc_groups[chosen_desc]
            continue

        try:
            save_puzzle_to_db(puzzle_groups)

            # Only mark as used if save was successful
            for _, players in puzzle_groups:
                player_ids = [p["player_id"] for p in players]
                print(f"Marking players as used: {player_ids}")
                mark_players_used(player_ids)

            # Mark themes as used if they're exhausted
            for theme, _ in puzzle_groups:
                print(f"Checking if theme {theme['theme_id']} is exhausted")
                mark_theme_if_exhausted(theme["theme_id"])

            puzzles_created += 1
            print(f"Puzzle {puzzles_created} successfully created and saved!")

            # Update viable themes for this description
            theme_desc_groups[chosen_desc] = [
                t
                for t in theme_desc_groups[chosen_desc]
                if t["theme_id"] not in [ct["theme_id"] for ct in chosen_themes]
            ]
            if len(theme_desc_groups[chosen_desc]) < 4:
                del theme_desc_groups[chosen_desc]

        except Exception as e:
            print(f"Failed to save puzzle: {e}")
            continue

    print(f"\nCreated {puzzles_created} puzzles")


def save_puzzle_to_db(puzzle_groups):
    formatted_groups = [
        {"theme": theme["theme"], "words": [p["player_name"].upper() for p in players]}
        for theme, players in puzzle_groups
    ]

    puzzle_data = {
        "created_at": datetime.now().isoformat(),
        "puzzle_players": formatted_groups,
        "daily_theme": puzzle_groups[0][0]["theme_description"],
        "is_verified": False,
    }

    result = supabase.table("eligible_puzzles").insert(puzzle_data).execute()
    print(
        f"Saved puzzle to database with ID: {result.data[0]['id'] if result.data else 'unknown'}"
    )
    return result


if __name__ == "__main__":
    create_puzzles(max_puzzles=10)
