# used for an ad hoc insert of themes into the database
import json
from supabase_client import supabase


def insert_themes():
    # Read the JSON file
    with open("nba_themes.json", "r") as file:
        themes = json.load(file)

    # Insert each theme and print status
    for theme in themes:
        data = {
            "theme": theme["theme"],
            "words": theme["words"],
            "color": theme["color"],
            "emoji": theme["emoji"],
        }
        try:
            supabase.table("themes").insert(data).execute()
            print(f"✓ Inserted: {data['theme']}")
        except Exception as e:
            print(f"✗ Error inserting {data['theme']}: {e}")


if __name__ == "__main__":
    insert_themes()
