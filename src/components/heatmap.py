import streamlit as st
import pandas as pd
import plotly.graph_objects as go

def render_heatmap(df_games, start_year, start_month, end_year, end_month):
    """
    Render the calendar heatmap of games played.
    """
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
