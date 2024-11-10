from collections import Counter
from typing import List, Dict, Union
from pydantic import BaseModel
import json
from datetime import datetime, timezone, timedelta
from supabase_client import supabase


class PuzzleGroup(BaseModel):
    color: str
    emoji: str
    theme: str
    words: List[str]


class Puzzle(BaseModel):
    groups: List[PuzzleGroup]


def validate_puzzle_structure(puzzle: Union[Dict, Puzzle]) -> Dict:
    errors = []
    groups = puzzle.get("groups", puzzle) if isinstance(puzzle, dict) else puzzle.groups

    # Validate group count
    if len(groups) != 4:
        errors.append(f"Puzzle must have exactly 4 themes (found {len(groups)})")

    # Validate words and uniqueness
    all_words = []
    for group in groups:
        words = (
            group.words if isinstance(group, PuzzleGroup) else group.get("words", [])
        )

        if len(words) != 4:
            errors.append(
                f"Theme '{group.theme}' must have exactly 4 words (found {len(words)})"
            )

        if len(set(words)) != len(words):
            errors.append(f"Theme '{group.theme}' contains duplicate words")

        all_words.extend(words)

    # Validate total uniqueness
    if len(set(all_words)) != 16:
        errors.append(
            f"Puzzle must have exactly 16 unique words (found {len(set(all_words))})"
        )

    # Validate colors
    colors = [
        group.color if isinstance(group, PuzzleGroup) else group.get("color", "")
        for group in groups
    ]
    required_colors = {"bg-yellow-200", "bg-green-200", "bg-blue-200", "bg-purple-200"}
    if set(colors) != required_colors:
        errors.append(f"Missing or invalid colors. Required: {required_colors}")

    return {"valid": len(errors) == 0, "errors": errors}


def validate_puzzles(puzzles: Union[List[Dict], List[Puzzle]]) -> List[Dict]:
    results = []
    print(f"\nValidating {len(puzzles)} puzzle(s)...")

    # Get start date for puzzle sequence
    start_date = get_latest_puzzle_date()

    for i, puzzle in enumerate(puzzles, 1):
        print(f"\nValidating Puzzle {i}...")

        validation = validate_puzzle_structure(puzzle)
        if not validation["valid"]:
            results.append(
                {
                    "puzzle_number": i,
                    "valid": False,
                    "errors": validation["errors"],
                    "inserted": False,
                }
            )
            print("❌ Structure validation failed:")
            for error in validation["errors"]:
                print(f"  - {error}")
            continue

        # Insert valid puzzle into database
        inserted = insert_puzzle(puzzle, i, start_date)

        results.append(
            {"puzzle_number": i, "valid": True, "errors": None, "inserted": inserted}
        )
        print("✅ Puzzle valid")

    return results


def get_latest_puzzle_date():
    try:
        response = (
            supabase.table("puzzles")
            .select("date")
            .order("date", desc=True)
            .limit(1)
            .execute()
        )
        if response.data:
            return datetime.fromisoformat(response.data[0]["date"])
        return datetime.now(timezone.utc)
    except Exception as e:
        print(f"❌ Error fetching latest date: {str(e)}")
        return datetime.now(timezone.utc)


def insert_puzzle(puzzle: Dict, puzzle_number: int, start_date: datetime) -> bool:
    try:
        # Use timedelta directly, not timezone.timedelta
        puzzle_date = start_date + timedelta(days=puzzle_number - 1)

        data = {
            "puzzle_id": puzzle_number,
            "date": puzzle_date.isoformat(),
            "groups": puzzle["groups"],
            "author": "admin",
        }

        response = supabase.table("puzzles").insert(data).execute()
        if response.data:
            print(
                f"✅ Puzzle {puzzle_number} inserted into database for {puzzle_date.date()}"
            )
            return True
        return False
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        return False


def main():
    # Load puzzles from JSON
    try:
        with open("nba_puzzles.json", "r") as f:
            puzzles = json.load(f)
    except FileNotFoundError:
        print("❌ nba_puzzles.json not found")
        return

    results = validate_puzzles(puzzles)

    # Print summary
    print("\n=== Validation Summary ===")
    valid_count = sum(1 for r in results if r["valid"])
    inserted_count = sum(1 for r in results if r["inserted"])
    print(f"Valid puzzles: {valid_count}/{len(results)}")
    print(f"Inserted puzzles: {inserted_count}/{valid_count}")

    if valid_count != len(results):
        print("\nInvalid puzzles:")
        for result in results:
            if not result["valid"]:
                print(f"\nPuzzle {result['puzzle_number']}:")
                for error in result["errors"]:
                    print(f"  - {error}")


if __name__ == "__main__":
    main()
