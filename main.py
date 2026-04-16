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

    # Mapping to bridge the 3-letter codes from your power_fade table to the full stadium names
    abbr_to_full = {
        "ARI": "Arizona Diamondbacks",
        "ATL": "Atlanta Braves",
        "BAL": "Baltimore Orioles",
        "BOS": "Boston Red Sox",
        "CHC": "Chicago Cubs",
        "CHW": "Chicago White Sox",
        "CIN": "Cincinnati Reds",
        "CLE": "Cleveland Guardians",
        "COL": "Colorado Rockies",
        "DET": "Detroit Tigers",
        "HOU": "Houston Astros",
        "KCR": "Kansas City Royals",
        "LAA": "Los Angeles Angels",
        "LAD": "Los Angeles Dodgers",
        "MIA": "Miami Marlins",
        "MIL": "Milwaukee Brewers",
        "MIN": "Minnesota Twins",
        "NYM": "New York Mets",
        "NYY": "New York Yankees",
        "OAK": "Oakland Athletics",
        "PHI": "Philadelphia Phillies",
        "PIT": "Pittsburgh Pirates",
        "SDP": "San Diego Padres",
        "SEA": "Seattle Mariners",
        "SFG": "San Francisco Giants",
        "STL": "St. Louis Cardinals",
        "TBR": "Tampa Bay Rays",
        "TEX": "Texas Rangers",
        "TOR": "Toronto Blue Jays",
        "WSN": "Washington Nationals",
    }

    matches = []

    # Grab just the list of 3-letter team codes that made the bottom-third ISO cut
    weak_teams_list = weak_power_df["Team"].tolist()

    # Loop through today's games
    # NOTE: Adjust 'Away' and 'Home' depending on how your specific schedule dataframe is labeled
    for index, game in daily_games.iterrows():
        away_team_full = game["Away"]
        home_team_full = game["Home"]

        # 1. Check if the game is being played in a Pitcher-Friendly Park
        if home_team_full in safe_parks_dict:
            park_factor = safe_parks_dict[home_team_full]

            # 2. Check if the Away Team is a weak offense stepping into the bad park
            away_abbr = [k for k, v in abbr_to_full.items() if v == away_team_full]
            if away_abbr and away_abbr[0] in weak_teams_list:
                iso = weak_power_df.loc[
                    weak_power_df["Team"] == away_abbr[0], "ISO"
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

            # 3. Check if the Home Team is a weak offense (they have to hit in their own bad park!)
            home_abbr = [k for k, v in abbr_to_full.items() if v == home_team_full]
            if home_abbr and home_abbr[0] in weak_teams_list:
                iso = weak_power_df.loc[
                    weak_power_df["Team"] == home_abbr[0], "ISO"
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
        match_df = pd.DataFrame(matches)

        # Sort so the absolute best environments (lowest ISO + lowest park factor) are at the top
        match_df = match_df.sort_values(
            by=["Park Factor", "Team ISO"], ascending=[True, True]
        )

        st.dataframe(match_df)
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


# --- 2. DISPLAY THE NEW PRIME ENVIRONMENTS TABLE ---
# Now that the variables are defined, the function will work perfectly
if not weak_teams.empty and not daily_schedule_df.empty:
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
