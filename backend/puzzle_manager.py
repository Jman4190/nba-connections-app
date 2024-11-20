import logging
from theme_generator import MODEL
from puzzle_generator import load_themes_from_db, assemble_puzzles_from_themes
from puzzle_validator import validate_puzzles, get_latest_puzzle_date, insert_puzzle
from datetime import datetime, timedelta
from supabase_client import supabase

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def run_puzzle_pipeline(puzzles_to_generate: int):
    """
    Run the puzzle generation pipeline:
    1. Generate puzzles from themes
    2. Validate and insert puzzles
    """
    try:
        # Step 1: Load themes and generate puzzles
        validated_themes = load_themes_from_db()
        theme_count = len(validated_themes)
        logging.info(f"Loaded {theme_count} validated themes from database")

        if not validated_themes:
            raise Exception("No validated themes available")

        if theme_count < puzzles_to_generate * 4:
            raise Exception(
                f"Not enough themes. Need {puzzles_to_generate * 4}, have {theme_count}"
            )

        logging.info(f"Attempting to generate {puzzles_to_generate} puzzles...")
        puzzles = assemble_puzzles_from_themes(
            validated_themes, puzzles_to_generate, max_attempts=50
        )

        if not puzzles:
            raise Exception("Failed to generate any valid puzzles")

        # Step 2: Validate puzzles
        logging.info("Validating and inserting puzzles...")
        results = validate_puzzles(puzzles)

        # Step 3: Insert valid puzzles and mark themes as used
        start_date = get_latest_puzzle_date() + timedelta(days=1)

        for i, result in enumerate(results):
            if result.get("valid", False):
                puzzle = puzzles[i]
                puzzle["author"] = MODEL
                success = insert_puzzle(puzzle, i + 1, start_date)
                result["inserted"] = success

                if success:
                    # Mark themes as used in database
                    for group in puzzle["groups"]:
                        try:
                            supabase.table("themes").update(
                                {"used_in_puzzle": True}
                            ).eq("theme", group["theme"]).execute()
                            logging.info(f"✓ Marked theme '{group['theme']}' as used")
                        except Exception as e:
                            logging.error(f"✗ Failed to mark theme as used: {e}")

        # Summary
        valid_count = sum(1 for r in results if r.get("valid", False))
        inserted_count = sum(1 for r in results if r.get("inserted", False))

        logging.info("\n=== Pipeline Summary ===")
        logging.info(f"Valid puzzles: {valid_count}/{len(results)}")
        logging.info(f"Inserted puzzles: {inserted_count}/{valid_count}")

        return True

    except Exception as e:
        logging.error(f"Pipeline failed: {str(e)}")
        return False


def main():
    print("\n=== NBA Connections Puzzle Manager ===")
    print("This script will generate puzzles and validate them.")

    try:
        puzzles_to_generate = int(input("Enter number of puzzles to generate: "))

        if puzzles_to_generate < 1:
            raise ValueError("Number must be positive")

        success = run_puzzle_pipeline(puzzles_to_generate)

        if success:
            print("\n✅ Pipeline completed successfully!")
        else:
            print("\n❌ Pipeline failed. Check logs for details.")

    except ValueError as e:
        print(f"\n❌ Invalid input: {str(e)}")
    except KeyboardInterrupt:
        print("\n\n⚠️ Process interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")


if __name__ == "__main__":
    main()
