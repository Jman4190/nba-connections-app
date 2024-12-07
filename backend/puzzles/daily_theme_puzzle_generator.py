import os
import random
import json
import openai
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
openai.api_key = os.getenv("OPENAI_API_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Define colors in the order you'd like them assigned
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


# You might want a function that picks the daily theme_description
def get_daily_theme_description(theme_description):
    try:
        resp = (
            supabase.table("new_themes")
            .select("theme_description")
            .eq("theme_description", theme_description)
            .eq("used_in_puzzle", False)
            .execute()
        )

        count = len(resp.data)

        if count < 4:
            raise ValueError(
                f"Not enough unused themes for '{theme_description}'. Found {count}, need 4."
            )

        return theme_description

    except Exception as e:
        raise ValueError(f"Error fetching theme descriptions: {str(e)}")


def fetch_four_themes(theme_description):
    try:
        resp = (
            supabase.table("new_themes")
            .select("*")
            .eq("theme_description", theme_description)
            .eq("used_in_puzzle", False)
            .limit(4)
            .execute()
        )

        if len(resp.data) < 4:
            raise ValueError("Not enough theme_ids for this theme_description")

        return resp.data[:4]
    except Exception as e:
        raise ValueError(f"Error fetching themes: {str(e)}")


def fetch_player_candidates(theme_id):
    try:
        resp = (
            supabase.table("theme_players")
            .select("player_name")
            .eq("theme_id", theme_id)
            .execute()
        )
        return [row["player_name"] for row in resp.data]
    except Exception as e:
        raise ValueError(f"Error fetching players for theme_id {theme_id}: {str(e)}")


def choose_best_four_players(theme, player_candidates, other_selected_players):
    MODEL = "gpt-4o-mini"
    client = openai.OpenAI()

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

    completion = client.chat.completions.create(
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


def update_themes_as_used(theme_ids):
    for tid in theme_ids:
        supabase.table("new_themes").update({"used_in_puzzle": True}).eq(
            "theme_id", tid
        ).execute()


def get_next_available_date():
    # Get the latest puzzle date
    resp = (
        supabase.table("puzzles")
        .select("date")
        .order("date", desc=True)
        .limit(1)
        .execute()
    )

    if not resp.data:
        # No puzzles exist yet, start from today
        from datetime import date

        return date.today()

    from datetime import datetime, timedelta

    latest_date = datetime.fromisoformat(resp.data[0]["date"].replace("Z", "+00:00"))
    return (latest_date + timedelta(days=1)).date()


def insert_puzzle_into_db(puzzle_groups, theme_description):
    next_date = get_next_available_date()

    # Get the next puzzle_id
    resp = (
        supabase.table("puzzles")
        .select("puzzle_id, id")
        .order("id", desc=True)
        .limit(1)
        .execute()
    )
    next_puzzle_id = 1 if not resp.data else resp.data[0]["puzzle_id"] + 1
    next_id = 1 if not resp.data else resp.data[0]["id"] + 1

    # Format the puzzle groups - uppercase all player names
    formatted_groups = []
    for group in puzzle_groups:
        formatted_groups.append(
            {
                "color": group["color"],
                "emoji": group["emoji"],
                "theme": group["theme"],
                "words": [word.upper() for word in group["words"]],
            }
        )

    resp = (
        supabase.table("puzzles")
        .insert(
            {
                "id": next_id,
                "puzzle_id": next_puzzle_id,
                "date": next_date.isoformat(),
                "groups": formatted_groups,  # Supabase will handle JSON serialization
                "author": "John Mannelly",
                "todays_theme": theme_description,
            }
        )
        .execute()
    )

    if not resp.data:
        raise ValueError("Error inserting puzzle")
    return resp.data


def main(theme_description):
    # 1. Verify we have enough unused themes for this description
    theme_description = get_daily_theme_description(theme_description)
    # 2. Fetch four unique theme_ids from that theme_description
    chosen_themes = fetch_four_themes(
        theme_description
    )  # returns a list of rows from new_themes

    # 3. For each theme_id, fetch player candidates
    # 4. Use OpenAI to pick the best 4 distinct players
    # Keep track of players used so far to avoid overlap
    all_selected_players = set()
    puzzle_groups = []

    for i, theme_row in enumerate(chosen_themes):
        theme_name = theme_row["theme"]  # The human-readable theme
        theme_id = theme_row["theme_id"]
        player_candidates = fetch_player_candidates(theme_id)

        # Assign color and emoji based on i (0=yellow,1=green,2=blue,3=purple)
        color_info = colors[i]

        # Prepare a minimal theme object for prompt
        theme_obj = {
            "theme": theme_name,
        }

        chosen_four = choose_best_four_players(
            theme_obj, player_candidates, all_selected_players
        )
        for p in chosen_four:
            all_selected_players.add(p.upper())  # Store in uppercase for consistency

        puzzle_groups.append(
            {
                "color": color_info["color_code"],
                "emoji": color_info["emoji"],
                "theme": theme_name,
                "words": chosen_four,
            }
        )

    # 5. Insert puzzle into puzzles table
    insert_puzzle_into_db(puzzle_groups, theme_description)

    # 6. Mark these theme_ids as used
    update_themes_as_used([t["theme_id"] for t in chosen_themes])


def generate_all_puzzles(theme_description):
    while True:
        try:
            # Check if we have enough themes left
            resp = (
                supabase.table("new_themes")
                .select("theme_description")
                .eq("theme_description", theme_description)
                .eq("used_in_puzzle", False)
                .execute()
            )

            if len(resp.data) < 4:
                print(
                    f"Stopping: Only {len(resp.data)} unused themes left for '{theme_description}'"
                )
                break

            # Generate one puzzle
            main(theme_description)
            print(f"Successfully generated puzzle for {theme_description}")

        except Exception as e:
            print(f"Stopped due to error: {str(e)}")
            break


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Please provide a theme description")
        sys.exit(1)

    generate_all_puzzles(sys.argv[1])
