import streamlit as st
import pandas as pd
from pathlib import Path
import time

# Import our refactored modules
from fetch_games import fetch_games_for_user
from process_games import process_all_games
from build_opening_games import build_opening_stats

st.set_page_config(page_title="Chess Game Analyzer", layout="wide")

st.title("Chess.com Game Analyzer")

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

# Display Results
project_root = Path(__file__).resolve().parent
warehouse_dir = project_root / "data" / "warehouse" / username.lower()
stats_path = warehouse_dir / "opening_winning_rates.parquet"
games_path = warehouse_dir / "games.parquet"

if games_path.exists():
    try:
        df_games = pd.read_parquet(games_path)
        
        # Apply game type filter
        if game_type_filter != "Overall":
            df_games = df_games[df_games["time_class"] == game_type_filter.lower()].copy()
        
        # Pie Chart: Total Games, Won, Lost, Draw
        if "result_for_me" in df_games.columns and "color" in df_games.columns:
            st.header("")
            
            col1, col2, col3 = st.columns(3)
            
            import plotly.graph_objects as go
            
            def create_3d_pie_chart(df, title):
                if df.empty:
                    return None
                
                result_counts = df["result_for_me"].value_counts()
                
                # Define colors
                color_map = {
                    "win": "#A8EB96",   # green
                    "loss": "#EB9696",  # red
                    "draw": "#6c757d"   # grey
                }
                
                colors = [color_map.get(result, "#999999") for result in result_counts.index]
                
                fig = go.Figure(data=[go.Pie(
                    labels=result_counts.index,
                    values=result_counts.values,
                    marker=dict(colors=colors),
                    hole=0,
                    pull=[0.05 if i == 0 else 0 for i in range(len(result_counts))],  # Pull out the largest slice
                    textinfo='label+percent',
                    textposition='inside'
                )])
                
                fig.update_layout(
                    title=f"{title}<br>({len(df)} games)",
                    title_x=0.5,
                    showlegend=True,
                    height=400,
                    margin=dict(l=20, r=20, t=60, b=20)
                )
                
                return fig

            with col1:
                chart_overall = create_3d_pie_chart(df_games, "Overall")
                if chart_overall:
                    st.plotly_chart(chart_overall, use_container_width=True)

            with col2:
                df_white = df_games[df_games["color"] == "white"]
                chart_white = create_3d_pie_chart(df_white, "White")
                if chart_white:
                    st.plotly_chart(chart_white, use_container_width=True)
                else:
                    st.info("No games as White.")

            with col3:
                df_black = df_games[df_games["color"] == "black"]
                chart_black = create_3d_pie_chart(df_black, "Black")
                if chart_black:
                    st.plotly_chart(chart_black, use_container_width=True)
                else:
                    st.info("No games as Black.")
            
            total_games = len(df_games)
            st.caption(f"Total Games Played: {total_games}")
        
        # Heatmap: Games played per day
        if "end_date" in df_games.columns:
            st.header("Games Played Per Day")
            
            # Count games per day
            daily_counts = df_games.groupby("end_date").size().reset_index(name="count")
            daily_counts["end_date"] = pd.to_datetime(daily_counts["end_date"])
            
            # Create a complete date range based on selected dates
            start_date = pd.Timestamp(year=start_year, month=start_month, day=1)
            # Get last day of end_month
            if end_month == 12:
                end_date = pd.Timestamp(year=end_year, month=12, day=31)
            else:
                end_date = pd.Timestamp(year=end_year, month=end_month + 1, day=1) - pd.Timedelta(days=1)
            
            date_range = pd.date_range(start=start_date, end=end_date, freq="D")
            
            # Merge to include days with 0 games
            complete_df = pd.DataFrame({"end_date": date_range})
            complete_df = complete_df.merge(daily_counts, on="end_date", how="left").fillna(0)
            
            # Calculate continuous position
            complete_df["day_of_week"] = complete_df["end_date"].dt.dayofweek
            complete_df["date_str"] = complete_df["end_date"].dt.strftime("%Y-%m-%d")
            complete_df["year_month"] = complete_df["end_date"].dt.to_period("M").astype(str)
            
            # Calculate week position (continuous, accounting for starting day)
            complete_df["week_position"] = (complete_df.index + complete_df["day_of_week"].iloc[0]) // 7
            
            # Create month labels
            month_changes = complete_df[complete_df["end_date"].dt.day == 1].copy()
            month_positions = []
            for _, row in month_changes.iterrows():
                month_positions.append((row["week_position"], row["year_month"]))
            
            # Create heatmap
            fig = go.Figure(data=go.Heatmap(
                x=complete_df["week_position"],
                y=complete_df["day_of_week"],
                z=complete_df["count"],
                text=complete_df["date_str"],
                hovertemplate="Date: %{text}<br>Games: %{z}<extra></extra>",
                colorscale="Greens",
                colorbar=dict(title="Games"),
                xgap=1,
                ygap=1
            ))
            
            fig.update_layout(
                title="Activity Calendar",
                xaxis=dict(
                    title="",
                    tickmode="array",
                    tickvals=[pos[0] for pos in month_positions] if month_positions else [],
                    ticktext=[pos[1] for pos in month_positions] if month_positions else [],
                    tickangle=-45
                ),
                yaxis=dict(
                    title="",
                    tickmode="array",
                    tickvals=[0, 1, 2, 3, 4, 5, 6],
                    ticktext=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                    autorange="reversed"
                ),
                height=350
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Rating Progression Graph
        if "my_rating" in df_games.columns and "time_class" in df_games.columns:
            st.header("Rating Progression")
            
            # Get available time classes
            available_time_classes = sorted(df_games["time_class"].dropna().unique())
            
            if available_time_classes:
                # Dropdown for time control selection (constrained width)
                col_dropdown, col_spacer = st.columns([1, 3])
                with col_dropdown:
                    selected_time_class = st.selectbox(
                        "Select Time Control",
                        options=available_time_classes,
                        index=0 if "rapid" in available_time_classes else 0
                    )
                
                # Filter by selected time class
                df_filtered = df_games[df_games["time_class"] == selected_time_class].copy()
                
                if len(df_filtered) > 0:
                    # Sort by end_time to show progression
                    df_filtered = df_filtered.sort_values("end_time")
                    df_filtered["game_number"] = range(1, len(df_filtered) + 1)
                    
                    # Create line chart
                    fig = go.Figure()
                    
                    fig.add_trace(go.Scatter(
                        x=df_filtered["end_date"],
                        y=df_filtered["my_rating"],
                        mode="lines+markers",
                        name="Rating",
                        line=dict(color="#4CAF50", width=2),
                        marker=dict(size=4),
                        hovertemplate="Date: %{x}<br>Rating: %{y}<extra></extra>"
                    ))
                    
                    fig.update_layout(
                        title=f"{selected_time_class.capitalize()} Rating Over Time",
                        xaxis=dict(title="Date"),
                        yaxis=dict(title="Rating"),
                        height=400,
                        hovermode="x unified"
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Show stats
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Current Rating", int(df_filtered["my_rating"].iloc[-1]))
                    with col2:
                        rating_change = int(df_filtered["my_rating"].iloc[-1] - df_filtered["my_rating"].iloc[0])
                        st.metric("Total Change", rating_change, delta=rating_change)
                    with col3:
                        peak_rating = int(df_filtered["my_rating"].max())
                        st.metric("Peak Rating", peak_rating)
                else:
                    st.info(f"No games found for {selected_time_class}")
            else:
                st.info("No time class data available")
            
    except Exception as e:
        st.error(f"Could not read games file for pie chart: {e}")

if stats_path.exists():
    st.header(f"Opening Stats for {username} ({start_year}-{start_month:02d} to {end_year}-{end_month:02d})")
    try:
        df = pd.read_parquet(stats_path)
        st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.error(f"Could not read stats file: {e}")
else:
    st.info("No stats available. Please search for a user.")

# Hourly Win Rate Graph
games_path = warehouse_dir / "games.parquet"
if games_path.exists():
    st.header("Hourly Win Rate")
    try:
        df_games = pd.read_parquet(games_path)
        
        # Ensure end_hour is present (it should be from process_games.py)
        if "end_hour" in df_games.columns:
            # Group by hour
            hourly_stats = (
                df_games.groupby("end_hour")
                .agg(
                    games=("game_id", "count"),
                    wins=("result_for_me", lambda s: (s == "win").sum())
                )
                .reindex(range(24), fill_value=0) # Ensure all 24 hours exist
            )
            
            # Calculate win percentage
            # Avoid division by zero
            hourly_stats["win_percent"] = hourly_stats.apply(
                lambda row: (row["wins"] / row["games"] * 100) if row["games"] > 0 else 0, axis=1
            )
            
            import altair as alt
            
            # Reset index to make end_hour a column for Altair
            chart_data = hourly_stats.reset_index()
            
            c = (
                alt.Chart(chart_data)
                .mark_bar()
                .encode(
                    x=alt.X("end_hour:O", title="Hour of Day", axis=alt.Axis(labelAngle=0)),
                    y=alt.Y("win_percent:Q", title="Win %"),
                    tooltip=[
                        alt.Tooltip("end_hour", title="Hour"),
                        alt.Tooltip("win_percent", title="Win %", format=".1f"),
                        alt.Tooltip("games", title="Total Games"),
                        alt.Tooltip("wins", title="Games Won")
                    ]
                )
            )
            
            st.altair_chart(c, use_container_width=True)
            
        else:
            st.warning("Hourly data not available in games file.")
            
    except Exception as e:
        st.error(f"Could not read games file for graph: {e}")
