import os
import json
import openai
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import List
from openai import OpenAI

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Please set the OPENAI_API_KEY environment variable.")

openai.api_key = OPENAI_API_KEY


class PuzzleGroup(BaseModel):
    color: str
    emoji: str
    theme: str
    words: List[str]


def choose_best_four_players(theme, player_candidates, all_puzzles):
    MODEL = "gpt-4o-mini-2024-07-18"

    # We now include the entire puzzles data in the prompt for context
    # Removed references to uniqueness of colors
    prompt = f"""
You are an AI assistant tasked with generating a connections puzzle of NBA players grouped by themes. Your job is to analyze the given puzzle data and assign difficulty levels (represented by colors and emojis) to each theme based on the players in that theme.

Here's the puzzle data:

<puzzle_data>
{json.dumps(all_puzzles, indent=2)}
</puzzle_data>

Your task is to assign a color and emoji to each theme based on the difficulty of the players in the theme. Here are the difficulty levels and their corresponding color+emoji pairs:

- Yellow (🟨) = easiest
- Green (🟩) = moderate difficulty
- Blue (🟦) = fairly hard
- Purple (🟪) = most challenging

Guidelines for assessing difficulty:
- Recognizable NBA player names are considered the easiest (Yellow)
- Pre-2000 dates are considered fairly hard or most challenging (Blue or Purple)
- Obscure stats (e.g., steals) are harder than well-known stats (e.g., points)

Important: Each theme must be assigned a unique color. No two themes should have the same color.

Before providing your final output, think through the following analysis on your own internal scratchpad:
1. List all themes and their players.
2. For each theme, assess the difficulty of each player and provide a brief justification.
3. Rank the themes from easiest to hardest based on your player assessments.
4. Assign colors to the ranked themes, ensuring uniqueness.

Your final output must be a JSON object in the following format:

{{
   "color": "bg-yellow-200",
   "emoji": "🟨",
   "theme": "Example Theme",
   "words": ["Player1", "Player2", "Player3", "Player4"]
}}

Please begin internal scratchpad analysis, then provide the JSON output.
""".strip()

    client = OpenAI()
    completion = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=4000,
        temperature=0,
    )

    cleaned_content = completion.choices[0].message.content.strip()

    # Add debug logging
    print("Raw OpenAI response:", cleaned_content)

    # Parse and validate the structured output
    try:
        puzzle_group = json.loads(cleaned_content)
        print(puzzle_group)
        validated_group = PuzzleGroup(**puzzle_group)  # Use Pydantic for validation
        print(validated_group)
        return validated_group
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON: {e}")
    except ValidationError as e:
        raise ValueError(f"Validation error: {e}")


def get_eligible_puzzle():
    response = (
        supabase.table("eligible_puzzles")
        .select("*")
        .eq("is_verified", True)
        .eq("add_to_puzzles", False)
        .execute()
    )
    if not response.data:
        raise ValueError("No eligible puzzles found")
    return response.data[0]


def get_next_puzzle_id():
    response = (
        supabase.table("puzzles")
        .select("puzzle_id")
        .order("puzzle_id", desc=True)
        .limit(1)
        .execute()
    )
    return 1 if not response.data else response.data[0]["puzzle_id"] + 1


def get_next_available_date():
    response = (
        supabase.table("puzzles")
        .select("date")
        .order("date", desc=True)
        .limit(1)
        .execute()
    )
    if not response.data:
        return datetime.now().date()
    last_date = datetime.strptime(response.data[0]["date"], "%Y-%m-%d").date()
    return last_date + timedelta(days=1)


def insert_puzzle(puzzle_groups, todays_theme):
    eligible_puzzle_id = get_eligible_puzzle()["id"]

    data = {
        "puzzle_id": get_next_puzzle_id(),
        "groups": puzzle_groups,
        "todays_theme": todays_theme,
        "author": "John Mannelly",
        "date": get_next_available_date().isoformat(),
    }
    puzzle_result = supabase.table("puzzles").insert(data).execute()

    supabase.table("eligible_puzzles").update({"add_to_puzzles": True}).eq(
        "id", eligible_puzzle_id
    ).execute()

    return puzzle_result


if __name__ == "__main__":
    eligible_puzzle = get_eligible_puzzle()
    puzzles = eligible_puzzle["puzzle_players"]
    todays_theme = eligible_puzzle["daily_theme"]

    updated_puzzles = []
    for puzzle in puzzles:
        updated_puzzle = choose_best_four_players(puzzle, puzzle["words"], puzzles)
        updated_puzzles.append(updated_puzzle)

    result = insert_puzzle(updated_puzzles, todays_theme)
    print(f"Inserted puzzle with theme: {todays_theme}")
