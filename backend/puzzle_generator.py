# File: puzzle_generator.py
import logging
import random
from pydantic import BaseModel
from typing import List
from supabase import create_client
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Supabase setup
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG to capture detailed logs
    format="%(asctime)s - %(levelname)s - %(message)s",
)


# Define data models
class ThemeGroup(BaseModel):
    color: str
    emoji: str
    theme: str
    words: List[str]


# Define color categories
colors = [
    {
        "name": "Yellow",
        "description": "the easiest category",
        "color_code": "bg-yellow-200",
        "emoji": "🟨",
    },
    {
        "name": "Green",
        "description": "moderate difficulty",
        "color_code": "bg-green-200",
        "emoji": "🟩",
    },
    {
        "name": "Blue",
        "description": "fairly hard",
        "color_code": "bg-blue-200",
        "emoji": "🟦",
    },
    {
        "name": "Purple",
        "description": "the most challenging",
        "color_code": "bg-purple-200",
        "emoji": "🟪",
    },
]


# Function to load themes from a database
def load_themes_from_db():
    try:
        response = (
            supabase.table("themes")
            .select("*")
            .eq("validated_state", True)
            .eq("used_in_puzzle", False)
            .execute()
        )

        themes = [
            ThemeGroup(
                color=theme["color"],
                emoji=theme["emoji"],
                theme=theme["theme"],
                words=theme["words"],
            )
            for theme in response.data
        ]

        logging.info(f"Loaded {len(themes)} unused validated themes from database")
        return themes
    except Exception as e:
        logging.error(f"Error loading themes from database: {e}")
        return []


def mark_themes_as_used(themes):
    try:
        for theme in themes:
            supabase.table("themes").update({"used_in_puzzle": True}).eq(
                "theme", theme.theme
            ).execute()
        logging.info(f"Marked {len(themes)} themes as used")
    except Exception as e:
        logging.error(f"Error marking themes as used: {e}")


# Function to assemble puzzles from themes
def assemble_puzzles_from_themes(themes, num_puzzles):
    # Organize themes by color
    themes_by_color = {color["color_code"]: [] for color in colors}
    for theme in themes:
        themes_by_color[theme.color].append(theme)

    puzzles = []
    max_attempts_per_puzzle = 10

    while len(puzzles) < num_puzzles:
        selected_themes = []
        attempt_count = 0

        while attempt_count < max_attempts_per_puzzle:
            selected_themes = []
            valid_combination = True

            for color in colors:
                color_code = color["color_code"]
                available_themes = themes_by_color[color_code]

                if not available_themes:
                    valid_combination = False
                    logging.warning(f"No themes available for color {color['name']}")
                    break

                selected_theme = random.choice(available_themes)
                selected_themes.append(selected_theme)

            if not valid_combination:
                break

            # Check for overlapping players
            all_players = []
            for theme in selected_themes:
                all_players.extend(theme.words)

            if len(set(all_players)) == 16:
                puzzles.append({"groups": selected_themes})
                # Remove used themes from available pool only
                for theme in selected_themes:
                    themes_by_color[theme.color].remove(theme)
                logging.info(
                    f"Found valid puzzle combination after {attempt_count + 1} attempts"
                )
                break
            else:
                attempt_count += 1
                if attempt_count == max_attempts_per_puzzle:
                    logging.error(
                        f"Failed to find non-overlapping combination after {max_attempts_per_puzzle} attempts"
                    )

    return puzzles


# Function to save puzzles to a JSON file
def save_puzzles_to_json(puzzles):
    if not puzzles:
        logging.warning("No puzzles to save.")
        return

    try:
        # Convert puzzles to serializable format
        serializable_puzzles = []
        for puzzle in puzzles:
            serializable_groups = [
                {
                    "color": group.color,
                    "emoji": group.emoji,
                    "theme": group.theme,
                    "words": group.words,
                }
                for group in puzzle["groups"]
            ]
            serializable_puzzles.append({"groups": serializable_groups})

        with open("nba_puzzles.json", "w") as f:
            json.dump(serializable_puzzles, f, indent=2)

        logging.info(f"Saved {len(puzzles)} puzzles to nba_puzzles.json")
    except Exception as e:
        logging.error(f"Error saving to JSON file: {e}")


# Main execution
if __name__ == "__main__":
    themes = load_themes_from_db()
    if themes:
        number_of_puzzles = int(input("Enter the number of puzzles to generate: "))
        puzzles = assemble_puzzles_from_themes(themes, number_of_puzzles)
        if puzzles:
            # Only mark themes as used after successful puzzle generation
            for puzzle in puzzles:
                mark_themes_as_used(puzzle["groups"])
            save_puzzles_to_json(puzzles)
    else:
        logging.error("No themes available to generate puzzles.")
