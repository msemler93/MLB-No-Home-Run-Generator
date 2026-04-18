import streamlit as st
import pandas as pd
from datetime import date
import analyzer
import data_fetcher
import odds_api

near_misses = []


def display_prime_environments(daily_games, weak_power_df, safe_parks_dict):
    import pandas as pd
    import streamlit as st

    # Map full team names to all possible variations they might appear as in your tables
    # This makes the app bulletproof whether you use 3-letter codes or BRef city names
    # Master Standardizer: Map every possible short name directly to the full name
    name_standardizer = {
        "Arizona": "Arizona Diamondbacks",
        "ARI": "Arizona Diamondbacks",
        "Atlanta": "Atlanta Braves",
        "ATL": "Atlanta Braves",
        "Baltimore": "Baltimore Orioles",
        "BAL": "Baltimore Orioles",
        "Boston": "Boston Red Sox",
        "BOS": "Boston Red Sox",
        "Chicago": "Chicago Cubs",
        "CHC": "Chicago Cubs",
        "Chicago White Sox": "Chicago White Sox",
        "CHW": "Chicago White Sox",
        "Cincinnati": "Cincinnati Reds",
        "CIN": "Cincinnati Reds",
        "Cleveland": "Cleveland Guardians",
        "CLE": "Cleveland Guardians",
        "Colorado": "Colorado Rockies",
        "COL": "Colorado Rockies",
        "Detroit": "Detroit Tigers",
        "DET": "Detroit Tigers",
        "Houston": "Houston Astros",
        "HOU": "Houston Astros",
        "Kansas City": "Kansas City Royals",
        "KCR": "Kansas City Royals",
        "Los Angeles": "Los Angeles Angels",
        "LAA": "Los Angeles Angels",
        "Los Angeles Dodgers": "Los Angeles Dodgers",
        "LAD": "Los Angeles Dodgers",
        "Miami": "Miami Marlins",
        "MIA": "Miami Marlins",
        "Milwaukee": "Milwaukee Brewers",
        "MIL": "Milwaukee Brewers",
        "Minnesota": "Minnesota Twins",
        "MIN": "Minnesota Twins",
        "New York": "New York Mets",
        "NYM": "New York Mets",
        "New York Yankees": "New York Yankees",
        "NYY": "New York Yankees",
        "Athletics": "Oakland Athletics",
        "Oakland": "Oakland Athletics",
        "OAK": "Oakland Athletics",
        "Philadelphia": "Philadelphia Phillies",
        "PHI": "Philadelphia Phillies",
        "Pittsburgh": "Pittsburgh Pirates",
        "PIT": "Pittsburgh Pirates",
        "San Diego": "San Diego Padres",
        "SDP": "San Diego Padres",
        "San Francisco": "San Francisco Giants",
        "SFG": "San Francisco Giants",
        "Seattle": "Seattle Mariners",
        "SEA": "Seattle Mariners",
        "St. Louis": "St. Louis Cardinals",
        "STL": "St. Louis Cardinals",
        "Tampa Bay": "Tampa Bay Rays",
        "TBR": "Tampa Bay Rays",
        "TB": "Tampa Bay Rays",
        "Texas": "Texas Rangers",
        "TEX": "Texas Rangers",
        "Toronto": "Toronto Blue Jays",
        "TOR": "Toronto Blue Jays",
        "Washington": "Washington Nationals",
        "WSN": "Washington Nationals",
        "WSH": "Washington Nationals",
    }

    matches = []
    weak_teams_list = weak_power_df["Team"].tolist()

    for index, game in daily_games.iterrows():
        # Standardize names immediately before doing any checks
        raw_away = game["Away"]
        raw_home = game["Home"]

        # If the name isn't in the standardizer, it just keeps the raw name (like full names)
        away_team_full = name_standardizer.get(raw_away, raw_away)
        home_team_full = name_standardizer.get(raw_home, raw_home)

        # 1. Check if the game is being played in a Pitcher-Friendly Park
        if home_team_full in safe_parks_dict:
            park_factor = safe_parks_dict[home_team_full]

            # 2. Check if the Away Team is a weak offense stepping into the bad park
            if away_team_full in weak_teams_list:
                iso = weak_power_df.loc[
                    weak_power_df["Team"] == away_team_full, "ISO"
                ].values[0]
                matches.append(
                    {
                        "Target Offense": away_team_full,
                        "Team ISO": iso,
                        "Stadium": home_team_full,
                        "Park Factor": park_factor,
                        "Fade Angle": "Away Team",
                    }
                )

            # 3. Check if the Home Team is a weak offense (hitting in their own bad park)
            if home_team_full in weak_teams_list:
                iso = weak_power_df.loc[
                    weak_power_df["Team"] == home_team_full, "ISO"
                ].values[0]
                matches.append(
                    {
                        "Target Offense": home_team_full,
                        "Team ISO": iso,
                        "Stadium": home_team_full,
                        "Park Factor": park_factor,
                        "Fade Angle": "Home Team",
                    }
                )

    # Render the new table in Streamlit
    st.write("### 🎯 Prime Environments (Weak Offense in Safe Park)")
    if matches:
        match_df = pd.DataFrame(matches).drop_duplicates()

        # Sort so the absolute best environments (lowest ISO + lowest park factor) are at the top
        match_df = match_df.sort_values(
            by=["Park Factor", "Team ISO"], ascending=[True, True]
        )

        st.dataframe(match_df, hide_index=True)
    else:
        st.info(
            "No prime environment matchups today. The weak offenses are either resting or playing in hitter-friendly parks."
        )


# --- Page Configuration ---
st.set_page_config(page_title="No-HR Triple Threat", page_icon="⚾", layout="wide")

today_date = date.today().strftime("%A, %B %d, %Y")
CURRENT_SEASON = 2026

# --- Header Section ---
st.title("⚾ MLB No-HR Triple Threat Analyzer")
st.info(f"📅 **Analyzing Slate For:** {today_date}")
st.write("""
**The Strict Filter Protocol:**
1. **Pitching:** 50%+ GB%, < 1.0 HR/9, < 10% HR/FB.
2. **Environment:** Park Factor < 100 (Pitcher Friendly).
3. **Offense:** Fading Bottom 33rd Percentile in ISO & HardContact.
4. **Oddsmakers:** O/U Game Total must be 8.0 or lower.
""")

st.divider()

# --- Main Action Button ---
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    analyze_button = st.button(
        "🚀 Run Today's Triple Threat Analysis", use_container_width=True
    )

if analyze_button:
    with st.spinner(
        "Cross-referencing Statcast, Matchups, Park Factors, and Live Odds..."
    ):
        # Run the engine
        certified_plays, near_misses = analyzer.find_certified_plays(
            season_year=CURRENT_SEASON
        )

        st.divider()

        # --- Output Logic ---
        if len(certified_plays) > 0:
            st.success(
                f"🔥 Found {len(certified_plays)} High-Probability Leg(s) for {today_date}."
            )

            # Display plays in a clean grid
            cols = st.columns(len(certified_plays) if len(certified_plays) < 3 else 3)

            for i, play in enumerate(certified_plays):
                with cols[i % 3]:
                    st.container(border=True)
                    st.subheader(f"✅ {play['pitcher']}")
                    st.write(f"**Matchup:** {play['pitcher']} vs {play['vs']}")
                    st.write(f"**Opponent:** {play['vs']}")
                    st.write(f"**Reason:** {play['reason']}")
                    st.metric(
                        label="Park Factor",
                        value=play["park_factor"],
                        delta="Safe",
                        delta_color="normal",
                    )
                    st.metric(label="Vegas O/U Total", value=play["game_total"])
                    # --- NEW WEATHER UI ---
                    st.markdown("---")
                    st.write("**Stadium Weather:**")

                    weather_col1, weather_col2 = st.columns(2)
                    with weather_col1:
                        st.metric(label="Temp", value=f"{play['weather_temp']} °F")
                    with weather_col2:
                        st.metric(label="Wind", value=f"{play['weather_wind']} mph")

                    if play["weather_advantage"]:
                        st.success("🧊 Cold/Windy: Favorable for No-HR.")
                    else:
                        st.info("🌤️ Neutral Weather.")

            st.warning(
                "These plays meet all Ground-Ball, Power-Fade, Oddsmaker, and Environment criteria."
            )

        else:
            # The Skip Protocol
            st.error(
                f"❌ **Skip Protocol Activated:** No matchups today hit the strict No-HR threshold. Do not force a bet."
            )

    if len(near_misses) > 0:
        st.divider()
        st.subheader("⚠️ The 'Near Miss' Board")
        st.info(
            "These games hit 3/4 filters. Great for finding outliers or 'gut' plays."
        )
        st.table(near_misses)


st.divider()

# --- 1. FETCH ALL REQUIRED DATA FIRST ---
# Get the weak teams
weak_teams = data_fetcher.get_power_fade_teams(CURRENT_SEASON)

# Get the safe parks
safe_parks = data_fetcher.get_safe_parks(100)

# Get today's schedule (UPDATE THIS LINE to match your actual odds_api function)
daily_schedule_df = odds_api.get_todays_schedule()

# 🚨 ADD THIS LINE TEMPORARILY RIGHT HERE:
st.write("### 🕵️ Raw API Data Check", daily_schedule_df)

# --- 2. DISPLAY THE NEW PRIME ENVIRONMENTS TABLE ---
if not weak_teams.empty:
    display_prime_environments(daily_schedule_df, weak_teams, safe_parks)

    
# --- 2. DISPLAY THE NEW PRIME ENVIRONMENTS TABLE ---
if not weak_teams.empty:
    display_prime_environments(daily_schedule_df, weak_teams, safe_parks)

st.divider()


# --- 3. DISPLAY THE UNDERLYING DATA EXPANDER ---
st.write("### 📊 Underlying Data (Current Season)")
with st.expander("View Power-Fade Teams & Safe Parks"):
    data_col1, data_col2 = st.columns(2)

    with data_col1:
        st.write("**Top 10 Faded Power Teams (Bottom 3rd)**")
        if not weak_teams.empty:
            st.dataframe(weak_teams, hide_index=True)
        else:
            st.write("Data currently unavailable.")

    with data_col2:
        st.write("**Pitcher Friendly Parks (< 100)**")
        safe_parks_df = pd.DataFrame(
            list(safe_parks.items()), columns=["Stadium", "HR Factor"]
        ).sort_values(by="HR Factor")
        st.dataframe(safe_parks_df, hide_index=True)
