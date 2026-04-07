import statsapi
from datetime import date
import data_fetcher
import odds_api
import requests

import statsapi
from datetime import date
import data_fetcher
import odds_api
import requests # <--- Make sure this is here!

# Dictionary mapping teams to their stadium latitude and longitude
STADIUM_COORDS = {
    "Arizona Diamondbacks": (33.4455, -112.0667), "Atlanta Braves": (33.8908, -84.4678),
    "Baltimore Orioles": (39.2840, -76.6215), "Boston Red Sox": (42.3467, -71.0972),
    "Chicago Cubs": (41.9484, -87.6553), "Chicago White Sox": (41.8299, -87.6338),
    "Cincinnati Reds": (39.0979, -84.5072), "Cleveland Guardians": (41.4962, -81.6852),
    "Colorado Rockies": (39.7559, -104.9942), "Detroit Tigers": (42.3390, -83.0485),
    "Houston Astros": (29.7573, -95.3555), "Kansas City Royals": (39.0517, -94.4803),
    "Los Angeles Angels": (33.8003, -117.8827), "Los Angeles Dodgers": (34.0739, -118.2400),
    "Miami Marlins": (25.7783, -80.2195), "Milwaukee Brewers": (43.0280, -87.9712),
    "Minnesota Twins": (44.9817, -93.2778), "New York Mets": (40.7571, -73.8458),
    "New York Yankees": (40.8296, -73.9262), "Oakland Athletics": (37.7516, -122.2005),
    "Philadelphia Phillies": (39.9061, -75.1665), "Pittsburgh Pirates": (40.4469, -80.0057),
    "San Diego Padres": (32.7076, -117.1570), "San Francisco Giants": (37.7786, -122.3893),
    "Seattle Mariners": (47.5914, -122.3325), "St. Louis Cardinals": (38.6226, -90.1928),
    "Tampa Bay Rays": (27.7682, -82.6534), "Texas Rangers": (32.7373, -97.0845),
    "Toronto Blue Jays": (43.6414, -79.3894), "Washington Nationals": (38.8730, -77.0074)
}

def get_stadium_weather(home_team_name):
    """Fetches live temperature and wind speed for the home stadium."""
    if home_team_name not in STADIUM_COORDS:
        return {"temp": "N/A", "wind": "N/A", "advantage": False}

    lat, lon = STADIUM_COORDS[home_team_name]
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,wind_speed_10m&temperature_unit=fahrenheit&wind_speed_unit=mph"

    try:
        response = requests.get(url).json()
        temp = response['current']['temperature_2m']
        wind = response['current']['wind_speed_10m']
        is_advantage = temp < 65 or wind > 10
        return {"temp": round(temp, 1), "wind": round(wind, 1), "advantage": is_advantage}
    except Exception as e:
        return {"temp": "Error", "wind": "Error", "advantage": False}

# --- Your existing code continues below ---
TEAM_MAPPING = { ...
# Standardizing team names between APIs
TEAM_MAPPING = {
    "Arizona Diamondbacks": "ARI", "Atlanta Braves": "ATL", "Baltimore Orioles": "BAL", 
    "Boston Red Sox": "BOS", "Chicago Cubs": "CHC", "Chicago White Sox": "CHW", 
    "Cincinnati Reds": "CIN", "Cleveland Guardians": "CLE", "Colorado Rockies": "COL", 
    "Detroit Tigers": "DET", "Houston Astros": "HOU", "Kansas City Royals": "KCR", 
    "Los Angeles Angels": "LAA", "Los Angeles Dodgers": "LAD", "Miami Marlins": "MIA", 
    "Milwaukee Brewers": "MIL", "Minnesota Twins": "MIN", "New York Mets": "NYM", 
    "New York Yankees": "NYY", "Oakland Athletics": "OAK", "Philadelphia Phillies": "PHI", 
    "Pittsburgh Pirates": "PIT", "San Diego Padres": "SDP", "San Francisco Giants": "SFG", 
    "Seattle Mariners": "SEA", "St. Louis Cardinals": "STL", "Tampa Bay Rays": "TBR", 
    "Texas Rangers": "TEX", "Toronto Blue Jays": "TOR", "Washington Nationals": "WSN"
}

def find_certified_plays(season_year=2026):
    """
    Cross-references daily matchups with strict pitching, hitting, 
    environment, and oddsmaker filters to find No-HR opportunities.
    """
    today = date.today().strftime('%Y-%m-%d')
    games = statsapi.schedule(date=today)

    # --- 1. Load Data Modules ---
    elite_pitchers_df = data_fetcher.get_elite_gb_pitchers(season_year)
    # Extract just the last names for easier matching with statsapi data
    elite_pitcher_names = [name.split()[-1] for name in elite_pitchers_df['Name'].tolist()] if not elite_pitchers_df.empty else []

    weak_power_df = data_fetcher.get_power_fade_teams(season_year)
    weak_power_teams = weak_power_df['Team'].tolist() if not weak_power_df.empty else []

    safe_parks = data_fetcher.get_safe_parks(100)
    low_total_games = odds_api.get_low_total_games(8.0)

    certified_plays = []

    # --- 2. Matchup Engine ---
    for game in games:
        away_team = game.get('away_name')
        home_team = game.get('home_name')
        away_p = game.get('away_probable_pitcher', '')
        home_p = game.get('home_probable_pitcher', '')

        # Environment Check: Is the stadium safe?
        if home_team not in safe_parks:
            continue
            # Check the weather for the stadium
            weather_data = get_stadium_weather(home_team)
        park_score = safe_parks[home_team]

        # Oddsmaker Check: Is the O/U Total 8.0 or lower?
        if home_team not in low_total_games:
            continue
        game_total = low_total_games[home_team]

        # --- Evaluate Away Pitcher vs. Home Offense ---
        if away_p and any(name in away_p for name in elite_pitcher_names):
            mapped_home_team = TEAM_MAPPING.get(home_team)
            if mapped_home_team in weak_power_teams:
                certified_plays.append({
                    "pitcher": away_p,
                    "pitcher_team": away_team,
                    "vs": home_team,
                    "park_factor": park_score,
                    "game_total": game_total,
                    "reason": f"Fading {home_team} (Bottom 10 Power)",
                    "weather_temp": weather_data["temp"],
                    "weather_wind": weather_data["wind"],
                    "weather_advantage": weather_data["advantage"]
                })

        # --- Evaluate Home Pitcher vs. Away Offense ---
        if home_p and any(name in home_p for name in elite_pitcher_names):
            mapped_away_team = TEAM_MAPPING.get(away_team)
            if mapped_away_team in weak_power_teams:
                certified_plays.append({
                    "pitcher": home_p,
                    "pitcher_team": home_team,
                    "vs": away_team,
                    "park_factor": park_score,
                    "game_total": game_total,
                    "reason": f"Fading {away_team} (Bottom 10 Power)",
                    "weather_temp": weather_data["temp"],
                    "weather_wind": weather_data["wind"],
                    "weather_advantage": weather_data["advantage"]
                })

    return certified_plays