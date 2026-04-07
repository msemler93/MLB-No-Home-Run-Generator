import statsapi
from datetime import date
import data_fetcher
import odds_api

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
                    "reason": f"Fading {home_team} (Bottom 10 Power)"
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
                    "reason": f"Fading {away_team} (Bottom 10 Power)"
                })

    return certified_plays