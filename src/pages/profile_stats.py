import streamlit as st
import pandas as pd
from pathlib import Path
from components.sidebar import render_sidebar
from components.charts import render_pie_charts, render_hourly_win_rate
from components.heatmap import render_heatmap
from components.rating_graph import render_rating_graph

def render_profile_stats():
    # Add back button
    if st.button("← Back to Home"):
        st.session_state.page = "landing"
        st.session_state.show_welcome = True
        st.rerun()
    
    st.title("📊 Profile Stats")
    
    # Render Sidebar and get inputs
    username, start_year, start_month, end_year, end_month, game_type_filter = render_sidebar()
    
    # Display Results
    project_root = Path(__file__).resolve().parent.parent
    warehouse_dir = project_root / "data" / "warehouse" / username.lower()
    stats_path = warehouse_dir / "opening_winning_rates.parquet"
    games_path = warehouse_dir / "games.parquet"
    
    if games_path.exists():
        try:
            df_games = pd.read_parquet(games_path)
            
            # Apply game type filter
            if game_type_filter != "Overall":
                df_games = df_games[df_games["time_class"] == game_type_filter.lower()].copy()
            
            # Render Components
            render_pie_charts(df_games)
            render_heatmap(df_games, start_year, start_month, end_year, end_month)
            render_rating_graph(df_games)
            
        except Exception as e:
            st.error(f"Could not read games file: {e}")
    
    if stats_path.exists():
        st.header(f"Opening Stats for {username} ({start_year}-{start_month:02d} to {end_year}-{end_month:02d})")
        try:
            df = pd.read_parquet(stats_path)
            st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error(f"Could not read stats file: {e}")
    else:
        st.info("No stats available. Please search for a user.")
    
    if games_path.exists():
        try:
            df_games = pd.read_parquet(games_path)
            render_hourly_win_rate(df_games)
        except Exception as e:
            st.error(f"Could not read games file for graph: {e}")
