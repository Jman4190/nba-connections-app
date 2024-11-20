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
def assemble_puzzles_from_themes(themes, num_puzzles, max_attempts=50):
    # Organize themes by color
    themes_by_color = {color["color_code"]: [] for color in colors}
    for theme in themes:
        themes_by_color[theme.color].append(theme)

    puzzles = []
    attempts_per_puzzle = max_attempts

    for puzzle_num in range(num_puzzles):
        for attempt in range(attempts_per_puzzle):
            selected_themes = []
            valid_combination = True
            all_players = set()

            # Try to build a valid puzzle
            for color in colors:
                color_code = color["color_code"]
                available_themes = themes_by_color[color_code]

                if not available_themes:
                    valid_combination = False
                    logging.warning(f"No themes available for color {color['name']}")
                    break

                # Try multiple themes for this color until we find one without overlap
                for _ in range(len(available_themes)):
                    theme = random.choice(available_themes)
                    if not any(player in all_players for player in theme.words):
                        selected_themes.append(theme)
                        all_players.update(theme.words)
                        break
                    available_themes.remove(theme)
                else:
                    valid_combination = False
                    break

            if valid_combination and len(all_players) == 16:
                # Convert ThemeGroup objects to dictionaries
                serialized_groups = [
                    {
                        "color": theme.color,
                        "emoji": theme.emoji,
                        "theme": theme.theme,
                        "words": theme.words,
                    }
                    for theme in selected_themes
                ]

                puzzles.append({"groups": serialized_groups})

                # Remove used themes
                for theme in selected_themes:
                    themes_by_color[theme.color].remove(theme)

                logging.info(
                    f"Found valid puzzle {puzzle_num + 1} after {attempt + 1} attempts"
                )
                break

            if attempt == attempts_per_puzzle - 1:
                logging.error(
                    f"Failed to generate puzzle {puzzle_num + 1} after {attempts_per_puzzle} attempts"
                )

    logging.info(f"Successfully generated {len(puzzles)}/{num_puzzles} puzzles")
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
