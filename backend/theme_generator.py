# File: theme_generator.py
import os
import openai
import json
from dotenv import load_dotenv
import logging
from pydantic import BaseModel
from typing import List
from supabase_client import supabase

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG to capture detailed logs
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Load API key from .env file
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Please set the OPENAI_API_KEY environment variable.")
openai.api_key = OPENAI_API_KEY

# Constants
MODEL = "gpt-4o-mini"
# Define prompt template
PROMPT_TEMPLATE = """<context>
NBA Connections is a word game that challenges users to find themes between NBA players. Users are given 16 players and find groups of four items that share something in common.

For example:
1. Los Angeles Lakers Franchise Leaders: Kobe Bryant, Elgin Baylor, Magic Johnson, Kareem Abdul-Jabbar
2. Top 4 Picks from the 1996 NBA Draft: Allen Iverson, Marcus Camby, Shareef Abdur-Rahim, Stephon Marbury

Each group is assigned a color (Yellow, Green, Blue, or Purple), with Yellow being the easiest category and Purple being the trickiest.

Each puzzle has exactly one solution and is meant to be tricky by having players that could fit into multiple categories.

</context>

<requirements>
Your task is to come up with {n} unique themes for the {color_name} category. Each theme should have exactly 4 distinct NBA Player Names.

Requirements:

1. Each theme must be unique and not overlap with other themes.
2. The players in each theme must be distinct and fit the theme accurately.
3. All player names should be recognizable and use their full names (no nicknames).
4. Make sure there are 4 players in each theme.
5. The themes should be appropriate for the {color_name} category, which is considered {color_description}.

The final output should be a JSON array of themes, like:

[
    {{
        "color": "{color_code}",
        "emoji": "{emoji}",
        "theme": "Describe the theme here",
        "words": ["PLAYER ONE", "PLAYER TWO", "PLAYER THREE", "PLAYER FOUR"]
    }},
    ...
]

</requirements>
"""


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


# Function to generate themes for a specific color
def generate_themes_for_color(n, color):
    prompt = PROMPT_TEMPLATE.format(
        n=n,
        color_name=color["name"],
        color_description=color["description"],
        color_code=color["color_code"],
        emoji=color["emoji"],
    )

    logging.info(f"Generating {n} themes for {color['name']} category")

    from openai import OpenAI

    client = OpenAI()

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    raw_content = response.choices[0].message.content
    logging.debug(f"Raw response for {color['name']}:\n{raw_content}")

    # Clean up the response by removing markdown and code block markers
    cleaned_content = raw_content.replace("```json", "").replace("```", "").strip()

    # Parse the response into a list of ThemeGroup objects
    try:
        themes_data = json.loads(cleaned_content)
        themes = [ThemeGroup(**theme) for theme in themes_data]
        return themes
    except Exception as e:
        logging.error(f"Error parsing themes for {color['name']}: {e}")
        return []


# Function to generate all themes
def generate_all_themes(n):
    all_themes = []
    for color in colors:
        themes = generate_themes_for_color(n, color)
        all_themes.extend(themes)
    return all_themes


# Function to save themes to a JSON file
def save_themes_to_file(themes, filename="nba_themes.json"):
    if themes:
        themes_data = [theme.dict() for theme in themes]
        with open(filename, "w") as file:
            json.dump(themes_data, file, indent=4)
        logging.info(f"Themes saved to {filename}")
    else:
        logging.warning("No themes to save.")


# Add new function to save themes to Supabase
def save_themes_to_supabase(themes):
    if not themes:
        logging.warning("No themes to save to Supabase.")
        return

    for theme in themes:
        data = {
            "theme": theme.theme,
            "words": theme.words,
            "color": theme.color,
            "emoji": theme.emoji,
        }
        try:
            supabase.table("themes").insert(data).execute()
            logging.info(f"✓ Inserted into Supabase: {data['theme']}")
        except Exception as e:
            logging.error(f"✗ Error inserting {data['theme']}: {e}")


# Main execution
if __name__ == "__main__":
    number_of_themes_per_color = int(
        input("Enter the number of themes to generate per color category: ")
    )
    themes = generate_all_themes(number_of_themes_per_color)
    save_themes_to_file(themes)
    save_themes_to_supabase(themes)
