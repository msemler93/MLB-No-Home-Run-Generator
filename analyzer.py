import statsapi
from datetime import date
import data_fetcher
import odds_api
import requests  # <--- Make sure this is here!

# Dictionary mapping teams to their stadium latitude and longitude
STADIUM_COORDS = {
    "Arizona Diamondbacks": (33.4455, -112.0667),
    "Atlanta Braves": (33.8908, -84.4678),
    "Baltimore Orioles": (39.2840, -76.6215),
    "Boston Red Sox": (42.3467, -71.0972),
    "Chicago Cubs": (41.9484, -87.6553),
    "Chicago White Sox": (41.8299, -87.6338),
    "Cincinnati Reds": (39.0979, -84.5072),
    "Cleveland Guardians": (41.4962, -81.6852),
    "Colorado Rockies": (39.7559, -104.9942),
    "Detroit Tigers": (42.3390, -83.0485),
    "Houston Astros": (29.7573, -95.3555),
    "Kansas City Royals": (39.0517, -94.4803),
    "Los Angeles Angels": (33.8003, -117.8827),
    "Los Angeles Dodgers": (34.0739, -118.2400),
    "Miami Marlins": (25.7783, -80.2195),
    "Milwaukee Brewers": (43.0280, -87.9712),
    "Minnesota Twins": (44.9817, -93.2778),
    "New York Mets": (40.7571, -73.8458),
    "New York Yankees": (40.8296, -73.9262),
    "Oakland Athletics": (37.7516, -122.2005),
    "Philadelphia Phillies": (39.9061, -75.1665),
    "Pittsburgh Pirates": (40.4469, -80.0057),
    "San Diego Padres": (32.7076, -117.1570),
    "San Francisco Giants": (37.7786, -122.3893),
    "Seattle Mariners": (47.5914, -122.3325),
    "St. Louis Cardinals": (38.6226, -90.1928),
    "Tampa Bay Rays": (27.7682, -82.6534),
    "Texas Rangers": (32.7373, -97.0845),
    "Toronto Blue Jays": (43.6414, -79.3894),
    "Washington Nationals": (38.8730, -77.0074),
}


def get_stadium_weather(home_team_name):
    """Fetches live temperature and wind speed for the home stadium."""
    if home_team_name not in STADIUM_COORDS:
        return {"temp": "N/A", "wind": "N/A", "advantage": False}

    lat, lon = STADIUM_COORDS[home_team_name]
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,wind_speed_10m&temperature_unit=fahrenheit&wind_speed_unit=mph"

    try:
        response = requests.get(url).json()
        temp = response["current"]["temperature_2m"]
        wind = response["current"]["wind_speed_10m"]
        is_advantage = temp < 65 or wind > 10
        return {
            "temp": round(temp, 1),
            "wind": round(wind, 1),
            "advantage": is_advantage,
        }
    except Exception as e:
        return {"temp": "Error", "wind": "Error", "advantage": False}


# Standardizing team names between APIs using universal aliases
TEAM_ALIASES = {
    "Arizona Diamondbacks": ["Arizona", "ARI"],
    "Atlanta Braves": ["Atlanta", "ATL"],
    "Baltimore Orioles": ["Baltimore", "BAL"],
    "Boston Red Sox": ["Boston", "BOS"],
    "Chicago Cubs": ["Chicago", "CHC"],
    "Chicago White Sox": ["Chicago White Sox", "CHW"],
    "Cincinnati Reds": ["Cincinnati", "CIN"],
    "Cleveland Guardians": ["Cleveland", "CLE"],
    "Colorado Rockies": ["Colorado", "COL"],
    "Detroit Tigers": ["Detroit", "DET"],
    "Houston Astros": ["Houston", "HOU"],
    "Kansas City Royals": ["Kansas City", "KCR"],
    "Los Angeles Angels": ["Los Angeles", "LAA"],
    "Los Angeles Dodgers": ["Los Angeles", "LAD"],
    "Miami Marlins": ["Miami", "MIA"],
    "Milwaukee Brewers": ["Milwaukee", "MIL"],
    "Minnesota Twins": ["Minnesota", "MIN"],
    "New York Mets": ["New York", "NYM"],
    "New York Yankees": ["New York", "NYY"],
    "Oakland Athletics": ["Athletics", "Oakland", "OAK"],
    "Philadelphia Phillies": ["Philadelphia", "PHI"],
    "Pittsburgh Pirates": ["Pittsburgh", "PIT"],
    "San Diego Padres": ["San Diego", "SDP"],
    "San Francisco Giants": ["San Francisco", "SFG"],
    "Seattle Mariners": ["Seattle", "SEA"],
    "St. Louis Cardinals": ["St. Louis", "STL"],
    "Tampa Bay Rays": ["Tampa Bay", "TBR"],
    "Texas Rangers": ["Texas", "TEX"],
    "Toronto Blue Jays": ["Toronto", "TOR"],
    "Washington Nationals": ["Washington", "WSN"],
}


def find_certified_plays(season_year=2026):
    """
    Cross-references daily matchups with strict pitching, hitting,
    environment, and oddsmaker filters to find No-HR opportunities.
    """
    today = date.today().strftime("%Y-%m-%d")
    games = statsapi.schedule(date=today)

    # --- 1. Load Data Modules ---
    elite_pitchers_df = data_fetcher.get_elite_gb_pitchers(season_year)
    # Extract just the last names for easier matching with statsapi data
    elite_pitcher_names = (
        [name.split()[-1] for name in elite_pitchers_df["Name"].tolist()]
        if not elite_pitchers_df.empty
        else []
    )

    weak_power_df = data_fetcher.get_power_fade_teams(season_year)
    weak_power_teams = weak_power_df["Team"].tolist() if not weak_power_df.empty else []

    safe_parks = data_fetcher.get_safe_parks(100)
    low_total_games = odds_api.get_low_total_games(8.0)

    certified_plays = []
    near_misses = []

    # --- 2. Matchup Engine ---
    for game in games:
        away_team = game.get("away_name")
        home_team = game.get("home_name")
        away_p = game.get("away_probable_pitcher", "")
        home_p = game.get("home_probable_pitcher", "")

        # --- Start the Scorecard for this game ---
        score = 0
        passed_filters = []

        # 1. Weather Check (Fetch this first so we have the data)
        weather_data = get_stadium_weather(home_team)
        if weather_data["advantage"]:
            score += 1
            passed_filters.append("🧊 Weather")

        # 2. Environment Check
        park_score = safe_parks.get(home_team, 100)
        if home_team in safe_parks:
            score += 1
            passed_filters.append("🏟️ Park")

        # 3. Odds Check
        game_total = low_total_games.get(home_team, 9.0)
        if home_team in low_total_games:
            score += 1
            passed_filters.append("🎰 Vegas O/U")

        # 4. Pitcher & Offense Matchup Check
        # Check if the pitchers are elite ground-ball guys
        is_elite_away = away_p and any(name in away_p for name in elite_pitcher_names)
        is_elite_home = home_p and any(name in home_p for name in elite_pitcher_names)

        # Check if the offenses are weak power teams using the universal aliases
        is_weak_home = any(
            alias in weak_power_teams
            for alias in TEAM_ALIASES.get(home_team, [home_team])
        )
        is_weak_away = any(
            alias in weak_power_teams
            for alias in TEAM_ALIASES.get(away_team, [away_team])
        )

        # Logic for "Certified" Matchup
        if (is_elite_away and is_weak_home) or (is_elite_home and is_weak_away):
            score += 1
            passed_filters.append("🎯 Matchup")
            reason = "✅ Certified Matchup"
        else:
            # Logic for "Near Miss" reasoning
            if is_elite_away or is_elite_home:
                reason = "⚠️ Offense too dangerous"
            elif is_weak_home or is_weak_away:
                reason = "⚠️ Pitcher not elite enough"
        # Check if the offenses are weak power teams using the universal aliases
        is_weak_home = any(
            alias in weak_power_teams
            for alias in TEAM_ALIASES.get(home_team, [home_team])
        )
        is_weak_away = any(
            alias in weak_power_teams
            for alias in TEAM_ALIASES.get(away_team, [away_team])
        )

        data_to_save = {
            "pitcher": away_p if "Fading" in reason and home_team in reason else home_p,
            "vs": home_team if home_p == "" else away_team,
            "reason": reason,
            "park_factor": park_score,
            "game_total": game_total,
            "weather_temp": weather_data["temp"],
            "weather_wind": weather_data["wind"],
            "weather_advantage": weather_data["advantage"],
            "score": score,
            "passed": ", ".join(passed_filters),
        }

        if score >= 4:
            certified_plays.append(data_to_save)
        elif score == 3:
            near_misses.append(data_to_save)

    return certified_plays, near_misses
