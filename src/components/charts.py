import streamlit as st
import plotly.graph_objects as go
import altair as alt
import pandas as pd

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

def render_pie_charts(df_games):
    """
    Render the win/loss/draw pie charts.
    """
    if "result_for_me" in df_games.columns and "color" in df_games.columns:
        st.header("")
        
        col1, col2, col3 = st.columns(3)
        
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

def render_hourly_win_rate(df_games):
    """
    Render the hourly win rate chart.
    """
    st.header("Hourly Win Rate")
    
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
