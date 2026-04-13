import streamlit as st
import pandas as pd
from datetime import date
import analyzer
import data_fetcher
import odds_api

near_misses = []

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

# --- Underlying Data Display ---
st.write("### 📊 Underlying Data (Current Season)")
with st.expander("View Power-Fade Teams & Safe Parks"):
    data_col1, data_col2 = st.columns(2)

    with data_col1:
        st.write("**Top 10 Faded Power Teams (Bottom 3rd)**")
        weak_teams = data_fetcher.get_power_fade_teams(CURRENT_SEASON)
        if not weak_teams.empty:
            st.dataframe(weak_teams, hide_index=True)
        else:
            st.write("Data currently unavailable.")

    with data_col2:
        st.write("**Pitcher Friendly Parks (< 100)**")
        safe_parks = data_fetcher.get_safe_parks(100)
        safe_parks_df = pd.DataFrame(
            list(safe_parks.items()), columns=["Stadium", "HR Factor"]
        ).sort_values(by="HR Factor")
        st.dataframe(safe_parks_df, hide_index=True)
