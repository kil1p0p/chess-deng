import streamlit as st
import pandas as pd
from fetch_games import fetch_games_for_user
from process_games import process_all_games
from build_opening_games import build_opening_stats

def render_sidebar():
    """
    Render the sidebar with inputs and return the selected values.
    """
    with st.sidebar:
        st.header("")
        username = st.text_input("Username", value="AlekhSrivastava")
        
        st.subheader("Date Range")
        st.caption("Start Date")
        col1, col2 = st.columns([2, 1.5])
        with col1:
            start_year = st.selectbox("Start Year", range(2022, 2026), index=3, key="start_year", label_visibility="collapsed")
        with col2:
            start_month = st.selectbox("Start Month", range(1, 13), index=0, key="start_month", label_visibility="collapsed")

        st.caption("End Date")
        col3, col4 = st.columns([2, 1.5])
        with col3:
            end_year = st.selectbox("End Year", range(2022, 2026), index=3, key="end_year", label_visibility="collapsed")
        with col4:
            end_month = st.selectbox("End Month", range(1, 13), index=11, key="end_month", label_visibility="collapsed")

        # Validate date range
        start_date_val = pd.Timestamp(year=start_year, month=start_month, day=1)
        if end_month == 12:
            end_date_val = pd.Timestamp(year=end_year, month=12, day=31)
        else:
            end_date_val = pd.Timestamp(year=end_year, month=end_month + 1, day=1) - pd.Timedelta(days=1)
        
        if end_date_val < start_date_val:
            st.warning("⚠️ End date must be greater than or equal to start date!")

        # Game Type Filter
        st.subheader("Game Type")
        game_type_filter = st.selectbox(
            "Filter by game type",
            options=["Overall", "Blitz", "Bullet", "Rapid"],
            index=0,
            label_visibility="collapsed"
        )

        if st.button("Search Games"):
            if not username:
                st.error("Please enter a username.")
            else:
                with st.spinner(f"Fetching games for {username} ({start_year}-{start_month:02d} to {end_year}-{end_month:02d})..."):
                    try:
                        # 1. Fetch
                        fetch_games_for_user(
                            username.lower(), 
                            start_year=start_year, 
                            start_month=start_month,
                            end_year=end_year,
                            end_month=end_month
                        )
                        st.success("Games fetched!")
                        
                        # 2. Process
                        with st.spinner("Processing games..."):
                            process_all_games(username.lower())
                        st.success("Games processed!")
                        
                        # 3. Build Stats
                        with st.spinner("Building opening stats..."):
                            build_opening_stats(username.lower())
                        st.success("Stats built!")
                        
                    except Exception as e:
                        st.error(f"An error occurred: {e}")
        
        return username, start_year, start_month, end_year, end_month, game_type_filter
