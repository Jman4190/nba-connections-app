import os
import json
import openai
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import List

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


class PuzzleGroup(BaseModel):
    color: str
    emoji: str
    theme: str
    words: List[str]


def choose_best_four_players(theme, player_candidates, other_selected_players):
    MODEL = "gpt-4o-mini"  # Replace with a valid model name
    # Ensure `openai.api_key` is set above
    prompt = f"""
You are helping generate a puzzle of NBA players grouped by a theme.
You are given a theme: "{theme['theme']}".
Below is a list of candidate players for this theme:
{json.dumps(player_candidates, indent=2)}

Select exactly 4 players that best represent this theme. They must be distinct and well-known examples fitting the theme.

Constraints:
- The 4 players you choose cannot include any players in this list:
{json.dumps(list(other_selected_players), indent=2)}

IMPORTANT: Return ONLY a JSON array of 4 player names, nothing else. For example:
["Player 1", "Player 2", "Player 3", "Player 4"]
"""

    completion = openai.ChatCompletion.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200,
        temperature=0,
    )

    chosen_players = completion.choices[0].message.content.strip()
    cleaned_content = chosen_players.replace("```json", "").replace("```", "").strip()

    try:
        chosen_list = json.loads(cleaned_content)
        if isinstance(chosen_list, dict):
            chosen_list = chosen_list.get("players", [])
        if len(chosen_list) != 4:
            raise ValueError("Did not return exactly 4 players.")
        return chosen_list
    except:
        raise ValueError("OpenAI response not valid JSON or not 4 players")


def assign_color_and_emoji_to_puzzles(puzzles):
    # According to rules:
    #  - Yellow = easiest (🟨)
    #  - Green = moderate (🟩)
    #  - Blue = fairly hard (🟦)
    #  - Purple = most challenging (🟪)
    #
    # Difficulty is influenced by popularity and date:
    # If using dates before 2000 or more obscure, it's harder.
    # We need one of each color exactly once per puzzle set.
    #
    # For simplicity, let's just assign them in order, ensuring no repeats:
    # We'll create a simple heuristic:
    # Themes with older drafts = more challenging.
    # Let's say:
    #   #3 Overall, #4 Overall: older, harder -> Purple or Blue
    #   #6 Overall, #13 Overall: more recent or mixed -> Green or Yellow
    # We'll ensure one of each color in the final result.

    colors = [
        {"color_code": "bg-yellow-200", "emoji": "🟨"},
        {"color_code": "bg-green-200", "emoji": "🟩"},
        {"color_code": "bg-blue-200", "emoji": "🟦"},
        {"color_code": "bg-purple-200", "emoji": "🟪"},
    ]

    result = []
    for i, puzzle in enumerate(puzzles):
        c = colors[i % len(colors)]  # Cycle through colors
        pg = PuzzleGroup(
            color=c["color_code"],
            emoji=c["emoji"],
            theme=puzzle["theme"],
            words=puzzle["words"],
        )
        result.append(pg.dict())
    return result


def get_eligible_puzzle():
    response = supabase.table("eligible_puzzles").select("*").execute()
    if not response.data:
        raise ValueError("No eligible puzzles found")
    return response.data[0]  # Get the first eligible puzzle


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
    data = {
        "puzzle_id": get_next_puzzle_id(),
        "groups": puzzle_groups,
        "todays_theme": todays_theme,
        "author": "John Mannelly",
        "date": get_next_available_date().isoformat(),
    }
    return supabase.table("puzzles").insert(data).execute()


if __name__ == "__main__":
    eligible_puzzle = get_eligible_puzzle()
    puzzles = eligible_puzzle["puzzle_players"]
    todays_theme = eligible_puzzle["daily_theme"]

    # Process the puzzles
    final_puzzles = assign_color_and_emoji_to_puzzles(puzzles)

    # Insert into puzzles table
    result = insert_puzzle(final_puzzles, todays_theme)
    print(f"Inserted puzzle with theme: {todays_theme}")
