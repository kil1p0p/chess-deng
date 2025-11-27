import streamlit as st
import plotly.graph_objects as go

def render_rating_graph(df_games):
    """
    Render the rating progression graph.
    """
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
