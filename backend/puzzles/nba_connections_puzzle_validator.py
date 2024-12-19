import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def validate_puzzles():
    # Get unverified puzzles
    unverified = (
        supabase.table("eligible_puzzles")
        .select("*")
        .eq("is_verified", False)
        .execute()
    )
    print(f"Found {len(unverified.data)} unverified puzzles")

    for puzzle in unverified.data:
        print(f"\nValidating puzzle ID: {puzzle['id']}")
        is_valid = True

        # Check 1: Theme validation
        themes = (
            supabase.table("new_themes")
            .select("*")
            .eq("theme_description", puzzle["daily_theme"])
            .execute()
        )
        if not themes.data:
            print(
                f"❌ Theme description '{puzzle['daily_theme']}' not found in new_themes"
            )
            is_valid = False

        # Check 2 & 3: Player uniqueness and theme count
        all_players = set()
        themes_in_puzzle = set()

        for group in puzzle["puzzle_players"]:
            themes_in_puzzle.add(group["theme"])
            all_players.update(group["words"])

        if len(all_players) != 16:
            print(f"❌ Expected 16 unique players, found {len(all_players)}")
            is_valid = False

        if len(themes_in_puzzle) != 4:
            print(f"❌ Expected 4 unique themes, found {len(themes_in_puzzle)}")
            is_valid = False

        # Update verification status if all checks pass
        if is_valid:
            print(f"✅ Puzzle {puzzle['id']} passed all validation checks")
            supabase.table("eligible_puzzles").update({"is_verified": True}).eq(
                "id", puzzle["id"]
            ).execute()
        else:
            print(f"❌ Puzzle {puzzle['id']} failed validation")


if __name__ == "__main__":
    validate_puzzles()
