import requests
import os
import streamlit as st

# We use The Odds API (https://the-odds-api.com/) to pull live lines.
# You will need to get a free API key and add it to your Replit "Secrets" tool.
API_KEY = os.environ.get("ODDS_API_KEY", "YOUR_API_KEY_HERE")

# Constants for the API call
SPORT = "baseball_mlb"
REGIONS = "us"
MARKETS = "totals"
BOOKMAKERS = "draftkings,fanduel"


def get_low_total_games(threshold: float = 8.0):
    """
    Fetches today's MLB games and returns a dictionary of teams
    playing in games where the Over/Under total is <= 8.0.
    """
    # Fail-safe for development mode
    if API_KEY == "YOUR_API_KEY_HERE" or not API_KEY:
        st.warning(
            "⚠️ Odds API Key not detected. Using mock data for testing. Please add 'ODDS_API_KEY' to Replit Secrets."
        )
        return {
            "Seattle Mariners": 7.0,
            "Houston Astros": 7.0,
            "Baltimore Orioles": 7.5,
            "New York Yankees": 7.5,
        }

    url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds/"
    params = {
        "apiKey": API_KEY,
        "regions": REGIONS,
        "markets": MARKETS,
        "bookmakers": BOOKMAKERS,
        "oddsFormat": "american",
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        low_total_teams = {}

        for game in data:
            home_team = game.get("home_team")
            away_team = game.get("away_team")

            # Loop through the bookmakers to find the Over/Under line
            for bookmaker in game.get("bookmakers", []):
                for market in bookmaker.get("markets", []):
                    if market.get("key") == "totals":
                        outcomes = market.get("outcomes", [])
                        if outcomes:
                            # The 'point' is the actual O/U line (e.g., 7.5, 8.0)
                            line = outcomes[0].get("point")

                            # If the line is 8.0 or lower, save both teams to our certified list
                            if line and line <= threshold:
                                low_total_teams[home_team] = line
                                low_total_teams[away_team] = line

        return low_total_teams

    except requests.exceptions.RequestException as e:
        print(f"Error fetching odds from API: {e}")
        return {}


def get_todays_schedule():
    """
    Fetches a clean DataFrame of today's matchups (Away vs Home)
    to be used by the Prime Environments dashboard.
    """
    import pandas as pd
    import requests

    # Fail-safe for development mode (reusing your existing logic)
    if API_KEY == "YOUR_API_KEY_HERE" or not API_KEY:
        # Mock matchup for testing
        return pd.DataFrame([{"Away": "Seattle Mariners", "Home": "San Diego Padres"}])

    url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds/"
    params = {
        "apiKey": API_KEY,
        "regions": REGIONS,
        "markets": MARKETS,
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()

        matchups = []
        for game in data:
            matchups.append(
                {"Away": game.get("away_team"), "Home": game.get("home_team")}
            )

        return pd.DataFrame(matchups)

    except Exception as e:
        return pd.DataFrame()
