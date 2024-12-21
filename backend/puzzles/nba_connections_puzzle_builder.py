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

    print("\n=== Input Puzzle Data ===")
    print(json.dumps(all_puzzles, indent=2))

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
- Players, teams, and stats from before the 1999 season are considered fairly hard or most challenging (Blue or Purple)
- Obscure stats (e.g., steals) are harder than well-known stats (e.g., points)

Important: Each theme must be assigned a unique color. No two themes should have the same color.

Your final output must be a JSON object in the following format:

[
  {{
    "color": "bg-yellow-200",
    "emoji": "🟨",
    "theme": "Example Theme 1",
    "words": [
      "Player1",
      "Player2",
      "Player3",
      "Player4"
    ]
  }},
  {{
    "color": "bg-green-200",
    "emoji": "🟩",
    "theme": "Example Theme 2",
    "words": [
      "Player5",
      "Player6",
      "Player7",
      "Player8"
    ]
  }},
  {{
    "color": "bg-blue-200",
    "emoji": "🟦",
    "theme": "Example Theme 3",
    "words": [
      "Player9",
      "Player10",
      "Player11",
      "Player12"
    ]
  }},
  {{
    "color": "bg-purple-200",
    "emoji": "🟪",
    "theme": "Example Theme 4",
    "words": [
      "Player13",
      "Player14",
      "Player15",
      "Player16"
    ]
  }}
]
""".strip()

    client = OpenAI()
    completion = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=4000,
        temperature=0,
    )

    cleaned_content = completion.choices[0].message.content.strip()
    print("\n=== GPT Response ===")
    print(cleaned_content)

    try:
        json_start = cleaned_content.find("```json\n") + 8
        json_end = cleaned_content.rfind("```")
        json_str = cleaned_content[json_start:json_end].strip()

        print("\n=== Parsed JSON ===")
        print(json_str)

        puzzle_groups = [PuzzleGroup(**group) for group in json.loads(json_str)]
        print(f"\n=== Number of Puzzle Groups: {len(puzzle_groups)} ===")
        for i, group in enumerate(puzzle_groups, 1):
            print(f"\nGroup {i}:")
            print(f"Color: {group.color}")
            print(f"Emoji: {group.emoji}")
            print(f"Theme: {group.theme}")
            print(f"Words: {group.words}")

        return puzzle_groups
    except (json.JSONDecodeError, IndexError) as e:
        raise ValueError(f"Failed to parse JSON: {e}\nContent: {cleaned_content}")


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
    print("\n=== Inserting Puzzle ===")
    print(f"Theme: {todays_theme}")
    print(f"Number of groups being inserted: {len(puzzle_groups)}")

    eligible_puzzle_id = get_eligible_puzzle()["id"]
    serialized_groups = [group.model_dump() for group in puzzle_groups]

    print("\n=== Serialized Groups ===")
    print(json.dumps(serialized_groups, indent=2))

    data = {
        "puzzle_id": get_next_puzzle_id(),
        "groups": serialized_groups,  # Use serialized groups instead of PuzzleGroup objects
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
    print("\n=== Starting Puzzle Generation ===")
    eligible_puzzle = get_eligible_puzzle()
    puzzles = eligible_puzzle["puzzle_players"]
    todays_theme = eligible_puzzle["daily_theme"]

    print(f"\nToday's Theme: {todays_theme}")
    all_puzzle_groups = choose_best_four_players(None, None, puzzles)
    result = insert_puzzle(all_puzzle_groups, todays_theme)
    print("\n=== Puzzle Generation Complete ===")
