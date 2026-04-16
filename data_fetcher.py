import pybaseball as pyb
import pandas as pd
import requests


def get_elite_gb_pitchers(season: int):
    """
    Pivots to Baseball Reference to bypass the FanGraphs ban.
    Filters strictly for pitchers allowing less than 1.0 HR/9 by calculating it manually.
    """
    import streamlit as st
    import pandas as pd
    import pybaseball as pyb

    try:
        # Pull pitching stats from Baseball Reference
        pitching_data = pyb.pitching_stats_bref(season)

        # 1. Rename 'Tm' to 'Team'
        if "Tm" in pitching_data.columns:
            pitching_data.rename(columns={"Tm": "Team"}, inplace=True)

        # 2. Bulletproof HR/9 Calculation
        # BRef doesn't always provide a clean HR9 column, so we calculate it from scratch
        # using Total Home Runs (HR) and Innings Pitched (IP).

        # Convert baseball IP (e.g., 50.1) to true decimals (50.333)
        ip_whole = pitching_data["IP"].fillna(0).astype(int)
        ip_frac = (pitching_data["IP"].fillna(0) - ip_whole) * 3.333
        pitching_data["IP_True"] = ip_whole + ip_frac

        # Prevent division by zero for guys who just got called up and have 0 IP
        pitching_data["IP_True"] = pitching_data["IP_True"].replace(0, 0.1)

        # Do the math: (HR / IP) * 9
        pitching_data["Calc_HR9"] = (
            pitching_data["HR"].fillna(0) / pitching_data["IP_True"]
        ) * 9

        # 3. Filter for elite pitchers (< 1.0 HR/9)
        elite_pitchers = pitching_data[(pitching_data["Calc_HR9"] < 1.0)].copy()

        # 4. Clean up the output columns for the dashboard
        elite_pitchers["HR9"] = elite_pitchers["Calc_HR9"].round(2)

        return elite_pitchers[["Name", "Team", "HR9"]]

    except Exception as e:
        st.error(f"🚨 PITCHING DATA CRASH: {type(e).__name__} - {e}")
        return pd.DataFrame()


def get_power_fade_teams(season: int):
    import streamlit as st
    import pandas as pd
    import pybaseball as pyb

    try:
        bref_data = pyb.batting_stats_bref(season)

        # 1. Standardize Team column name
        if "Tm" in bref_data.columns:
            bref_data.rename(columns={"Tm": "Team"}, inplace=True)

        # 2. Filter out traded players to prevent double-counting
        bref_data = bref_data[~bref_data["Team"].str.contains(",", na=False)]
        bref_data = bref_data[bref_data["Team"] != "TOT"]

        # 3. Fix the Two-Team Cities and Standardize Names
        def map_team_names(row):
            team = str(row.get("Team", "")).strip()
            lg = str(row.get("Lg", "")).strip().upper()

            # Split the shared cities by American League (AL) vs National League (NL)
            if team == "Chicago":
                return "CHW" if lg == "AL" else "CHC"
            if team == "New York":
                return "NYY" if lg == "AL" else "NYM"
            if team == "Los Angeles":
                return "LAA" if lg == "AL" else "LAD"

            # Standardize the rest to 3-letter abbreviations so your app merges work downstream
            mapping = {
                "Arizona": "ARI",
                "Atlanta": "ATL",
                "Baltimore": "BAL",
                "Boston": "BOS",
                "Cincinnati": "CIN",
                "Cleveland": "CLE",
                "Colorado": "COL",
                "Detroit": "DET",
                "Houston": "HOU",
                "Kansas City": "KCR",
                "Miami": "MIA",
                "Milwaukee": "MIL",
                "Minnesota": "MIN",
                "Philadelphia": "PHI",
                "Pittsburgh": "PIT",
                "San Diego": "SDP",
                "San Francisco": "SFG",
                "Seattle": "SEA",
                "St. Louis": "STL",
                "Tampa Bay": "TBR",
                "Texas": "TEX",
                "Toronto": "TOR",
                "Washington": "WSN",
                "Athletics": "OAK",
            }
            return mapping.get(team, team)

        # Apply the mapping
        bref_data["Team"] = bref_data.apply(map_team_names, axis=1)

        # 4. Mathematically correct aggregation: Sum the raw counting stats
        team_stats = (
            bref_data.groupby("Team")[["AB", "H", "2B", "3B", "HR"]].sum().reset_index()
        )
        team_stats["AB"] = team_stats["AB"].replace(0, 1)

        # 5. Calculate proper Team SLG and ISO
        team_stats["TB"] = (
            team_stats["H"]
            + team_stats["2B"]
            + (2 * team_stats["3B"])
            + (3 * team_stats["HR"])
        )
        team_stats["SLG"] = (team_stats["TB"] / team_stats["AB"]).round(3)
        team_stats["AVG"] = (team_stats["H"] / team_stats["AB"]).round(3)
        team_stats["ISO"] = (team_stats["SLG"] - team_stats["AVG"]).round(3)

        # 6. Filter for the bottom third of the league
        iso_threshold = team_stats["ISO"].quantile(0.33)
        weak_power_df = team_stats[team_stats["ISO"] <= iso_threshold].copy()
        weak_power_df = weak_power_df.sort_values("ISO", ascending=True)

        return weak_power_df[["Team", "ISO", "SLG", "HR"]]

    except Exception as e:
        st.error(f"🚨 BATTING DATA CRASH: {e}")
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
