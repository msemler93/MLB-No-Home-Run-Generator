import pybaseball as pyb
import pandas as pd

def get_elite_gb_pitchers(season: int):
    """
    Fetches qualified pitchers with elite Ground Ball % and low HR tendencies.
    Criteria: GB% >= 45%, HR/9 < 1.0, and HR/FB < 10%.
    """
    try:
        # Pull standard and advanced pitching stats from FanGraphs
        pitching_data = pyb.pitching_stats(season, qual=1)

        # Apply the Triple Threat Pitching Filters
        elite_pitchers = pitching_data[
            (pitching_data['GB%'] >= 0.45) & 
            (pitching_data['HR/9'] < 1.0) &
            (pitching_data['HR/FB'] < 0.10) # Added HR/FB for extra safety
        ].copy()

        # Return only the necessary columns to keep memory usage low
        return elite_pitchers[['Name', 'Team', 'GB%', 'HR/9', 'HR/FB']]

    except Exception as e:
        print(f"Error fetching pitching data: {e}")
        return pd.DataFrame()

def get_power_fade_teams(season: int):
    """
    Identifies the bottom third of MLB offenses in power metrics.
    Currently filters by the lowest 10 teams in ISO.
    """
    try:
        # Pull standard team batting stats
        team_batting = pyb.team_batting(season)

        # Sort by ISO to find the bottom 10 (bottom third of the league)
        weak_power_df = team_batting.sort_values(by='ISO', ascending=True).head(10)

        # Returning ISO, Slugging (SLG), and HardHit% to evaluate contact quality
        columns_to_return = ['Team', 'ISO', 'SLG', 'HR', 'HardHit%']

        # Filter columns to only include those that exist in the dataframe (safeguard)
        available_columns = [col for col in columns_to_return if col in weak_power_df.columns]

        return weak_power_df[available_columns]

    except Exception as e:
        print(f"Error fetching batting data: {e}")
        return pd.DataFrame()

def get_park_factors():
    """
    Returns stadium HR park factors. 100 is neutral. 
    Below 100 suppresses Home Runs.
    """
    return {
        "Arizona Diamondbacks": 96, "Atlanta Braves": 105, "Baltimore Orioles": 80, 
        "Boston Red Sox": 102, "Chicago Cubs": 98, "Chicago White Sox": 102, 
        "Cincinnati Reds": 133, "Cleveland Guardians": 89, "Colorado Rockies": 115, 
        "Detroit Tigers": 83, "Houston Astros": 102, "Kansas City Royals": 85, 
        "Los Angeles Angels": 107, "Los Angeles Dodgers": 106, "Miami Marlins": 84, 
        "Milwaukee Brewers": 105, "Minnesota Twins": 100, "New York Mets": 95, 
        "New York Yankees": 113, "Oakland Athletics": 86, "Philadelphia Phillies": 109, 
        "Pittsburgh Pirates": 89, "San Diego Padres": 92, "San Francisco Giants": 82, 
        "Seattle Mariners": 91, "St. Louis Cardinals": 86, "Tampa Bay Rays": 94, 
        "Texas Rangers": 100, "Toronto Blue Jays": 103, "Washington Nationals": 98
    }

def get_safe_parks(threshold: int = 100):
    """
    Helper function to instantly return a list of teams playing in safe parks.
    """
    parks = get_park_factors()
    safe_parks = {team: factor for team, factor in parks.items() if factor < threshold}
    return safe_parks