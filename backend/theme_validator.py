import os
from langchain_openai import ChatOpenAI
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
from langchain_community.utilities import SearchApiAPIWrapper
from langchain.tools import Tool
from dotenv import load_dotenv
from time import sleep
import logging
from supabase_client import supabase

# Suppress logging
logging.getLogger("langchain").setLevel(logging.ERROR)

load_dotenv()

# Set up OpenAI API key
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("Please set OPENAI_API_KEY")

# Initialize the OpenAI LLM
llm = ChatOpenAI(temperature=0)

# Initialize SearchAPI
search = SearchApiAPIWrapper(searchapi_api_key=os.getenv("SEARCHAPI_API_KEY"))


def create_nba_search_tool():
    search = SearchApiAPIWrapper(
        searchapi_api_key=os.getenv("SEARCHAPI_API_KEY"),
        engine="google",  # Using Google engine for better site-specific searches
    )

    def search_nba_stats(query: str) -> str:
        """Search for NBA statistics and facts from reliable sources."""
        refined_query = (
            f"(site:basketball-reference.com OR "
            f"site:nba.com/stats OR "
            f"site:statmuse.com/nba OR "
            f"site:espn.com/nba/stats) "
            f"{query}"
        )
        try:
            results = search.run(refined_query)
            return results[:1000]  # Limit response length
        except Exception as e:
            return f"Error performing search: {str(e)}"

    return Tool(
        name="NBA_Search",
        description=(
            "Search for NBA player statistics, awards, and historical facts. "
            "Only uses official sources like basketball-reference.com, nba.com/stats, and statmuse.com"
        ),
        func=search_nba_stats,
    )


# Define the tools
tools = [create_nba_search_tool()]

# Update the prompt template
prompt = PromptTemplate.from_template(
    """Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Question: {input}
{agent_scratchpad}"""
)

# Rest of the initialization remains the same
agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)
agent_executor = AgentExecutor.from_agent_and_tools(
    agent=agent, tools=tools, handle_parsing_errors=True, verbose=True
)


def validate_player_theme(player, theme):
    max_retries = 5
    retry_delay = 5

    for attempt in range(max_retries):
        try:
            print(f"\n🤔 Analyzing if {player} fits theme: {theme}")
            prompt = (
                f"Using the search tool, verify if the NBA player '{player}' fits the theme '{theme}'. "
                "Provide evidence from the search results. Answer 'Yes' or 'No' followed by a brief explanation."
            )
            result = agent_executor.invoke({"input": prompt})
            response = result.get("output", "").strip()
            print(f"🎯 Final Answer: {response}\n")

            if response.lower().startswith("yes"):
                return "Yes - " + response[3:]
            elif response.lower().startswith("no"):
                return "No - " + response[2:]
            else:
                return "No - Unable to verify"

        except Exception as e:
            print(f"❌ Attempt {attempt + 1} failed: {str(e)}")
            if "rate limit" in str(e).lower() and attempt < max_retries - 1:
                print(f"⏳ Rate limited. Waiting {retry_delay} seconds...")
                sleep(retry_delay)
                retry_delay *= 2
                continue
            elif attempt < max_retries - 1:
                continue
            else:
                return "No - Validation failed after retries"


def validate_themes():
    print("\nValidating themes from Supabase...")

    # Fetch unvalidated themes
    response = (
        supabase.table("themes")
        .select("theme_id, theme, words, validated_state, color, emoji")
        .eq("validated_state", False)
        # .limit(5) # when testing limit to 5
        .execute()
    )
    themes = response.data

    print(f"Found {len(themes)} themes to validate")

    for theme in themes:
        print(f"\nValidating Theme: {theme['theme']}")
        is_valid = True

        for player in theme["words"]:
            result = validate_player_theme(player, theme["theme"])
            print(f"Player '{player}': {result}")

            if not result.strip().lower().startswith("yes"):
                is_valid = False
                break

        # Update using theme_id instead of id
        supabase.table("themes").update({"validated_state": is_valid}).eq(
            "theme_id", theme["theme_id"]
        ).execute()

        print(f"Theme validation result: {'✅ Valid' if is_valid else '❌ Invalid'}")


def main():
    validate_themes()


if __name__ == "__main__":
    main()
