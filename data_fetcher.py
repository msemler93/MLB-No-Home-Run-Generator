import pybaseball as pyb
import pandas as pd


def get_elite_gb_pitchers(season: int):
    """
    Fetches qualified pitchers with elite Ground Ball % and low HR tendencies.
    Criteria: GB% >= 50%, HR/9 < 1.0, and HR/FB < 10%.
    """
    try:
        # Pull standard and advanced pitching stats from FanGraphs
        pitching_data = pyb.pitching_stats(season, qual=1)

        # Apply the Triple Threat Pitching Filters
        elite_pitchers = pitching_data[
            (pitching_data["GB%"] >= 0.50)
            & (pitching_data["HR/9"] < 1.0)
            & (pitching_data["HR/FB"] < 0.10)  # Added HR/FB for extra safety
        ].copy()

        # Return only the necessary columns to keep memory usage low
        return elite_pitchers[["Name", "Team", "GB%", "HR/9", "HR/FB"]]

        except Exception as e:
        print(f"Error fetching pitching data: {e}")
            return pd.DataFrame()


 def get_power_fade_teams(season: int):
            """
            Identifies the bottom third of MLB offenses in power metrics.
            Dynamically filters by the bottom 33rd percentile in ISO and HardHit%.
            """
        try:
                # Pull standard team batting stats
                team_batting = pyb.team_batting(season)

                # Calculate the 33rd percentile (bottom 1/3 threshold) dynamically
                iso_threshold = team_batting["ISO"].quantile(0.33)
                hardhit_threshold = team_batting["HardHit%"].quantile(0.33)

                # Filter teams that fall below the threshold for BOTH metrics
                weak_power_df = team_batting[
                    (team_batting["ISO"] <= iso_threshold) & 
                    (team_batting["HardHit%"] <= hardhit_threshold)
                ].copy()

                # Returning ISO, Slugging (SLG), and HardHit% to evaluate contact quality
                columns_to_return = ["Team", "ISO", "SLG", "HR", "HardHit%"]

                # Filter columns to only include those that exist in the dataframe (safeguard)
                available_columns = [
                    col for col in columns_to_return if col in weak_power_df.columns
                ]

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
        "Arizona Diamondbacks": 96,
        "Atlanta Braves": 105,
        "Baltimore Orioles": 80,
        "Boston Red Sox": 102,
        "Chicago Cubs": 98,
        "Chicago White Sox": 102,
        "Cincinnati Reds": 133,
        "Cleveland Guardians": 89,
        "Colorado Rockies": 115,
        "Detroit Tigers": 83,
        "Houston Astros": 102,
        "Kansas City Royals": 85,
        "Los Angeles Angels": 107,
        "Los Angeles Dodgers": 106,
        "Miami Marlins": 84,
        "Milwaukee Brewers": 105,
        "Minnesota Twins": 100,
        "New York Mets": 95,
        "New York Yankees": 113,
        "Oakland Athletics": 86,
        "Philadelphia Phillies": 109,
        "Pittsburgh Pirates": 89,
        "San Diego Padres": 92,
        "San Francisco Giants": 82,
        "Seattle Mariners": 91,
        "St. Louis Cardinals": 86,
        "Tampa Bay Rays": 94,
        "Texas Rangers": 100,
        "Toronto Blue Jays": 103,
        "Washington Nationals": 98,
    }


def get_safe_parks(threshold: int = 100):
    """
    Helper function to instantly return a list of teams playing in safe parks.
    """
    parks = get_park_factors()
    safe_parks = {team: factor for team, factor in parks.items() if factor < threshold}
    return safe_parks
    import requests

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
        # Open-Meteo URL for current Temp (Fahrenheit) and Wind (MPH)
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,wind_speed_10m&temperature_unit=fahrenheit&wind_speed_unit=mph"

        try:
            response = requests.get(url).json()
            temp = response["current"]["temperature_2m"]
            wind = response["current"]["wind_speed_10m"]

            # Determine if weather suppresses power (Temp under 65 OR High Wind)
            is_advantage = temp < 65 or wind > 10

            return {
                "temp": round(temp, 1),
                "wind": round(wind, 1),
                "advantage": is_advantage,
            }
        except Exception as e:
            return {"temp": "Error", "wind": "Error", "advantage": False}
            # Forcing GitHub to update
