import streamlit as st
import pandas as pd
from pathlib import Path
import time

# Import our refactored modules
from fetch_games import fetch_games_for_user
from process_games import process_all_games
from build_opening_games import build_opening_stats

st.set_page_config(page_title="Chess Analyzer", layout="wide", initial_sidebar_state="collapsed")

# Initialize session state for page navigation
if "page" not in st.session_state:
    st.session_state.page = "landing"
if "show_welcome" not in st.session_state:
    st.session_state.show_welcome = True

# Landing Page
if st.session_state.page == "landing":
    # Welcome Animation
    if st.session_state.show_welcome:
        st.markdown("""
        <style>
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .welcome-title {
            font-size: 4rem;
            font-weight: bold;
            text-align: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: fadeIn 1.5s ease-out;
            margin-top: 100px;
            margin-bottom: 50px;
        }
        .subtitle {
            font-size: 1.5rem;
            text-align: center;
            color: #666;
            animation: fadeIn 2s ease-out;
            margin-bottom: 80px;
        }
        </style>
        <div class="welcome-title">♟️ Welcome to Chess Analyzer ♟️</div>
        <div class="subtitle">Your Personal Chess Performance Dashboard</div>
        """, unsafe_allow_html=True)
        
        time.sleep(0.5)
        st.session_state.show_welcome = False
        st.rerun()
    
    # Navigation Cards
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Profile Stats", use_container_width=True, key="profile_stats", type="primary"):
            st.session_state.page = "profile_stats"
            st.rerun()
        st.markdown("""
        <div style='text-align: center; padding: 20px; color: #666;'>
            <p>View your game statistics, ratings, and performance metrics</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if st.button("🔍 Analyse Game", use_container_width=True, key="analyse_game", type="primary"):
            st.session_state.page = "analyse_game"
            st.rerun()
        st.markdown("""
        <div style='text-align: center; padding: 20px; color: #666;'>
            <p>Deep dive into individual game analysis with engine evaluation</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        if st.button("🎓 Chess Coach", use_container_width=True, key="chess_coach", type="primary"):
            st.session_state.page = "chess_coach"
            st.rerun()
        st.markdown("""
        <div style='text-align: center; padding: 20px; color: #666;'>
            <p>Get personalized coaching tips and improvement suggestions</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.stop()

# Analyse Game Page
elif st.session_state.page == "analyse_game":
    if st.button("← Back to Home"):
        st.session_state.page = "landing"
        st.session_state.show_welcome = True
        st.rerun()
    
    st.title("🔍 Analyse Game")
    
    # Username input
    username = st.text_input(
        "Username",
        value="AlekhSrivastava",
        help="Enter the username whose games database to search"
    )
    
    # Game URL input
    game_url = st.text_input(
        "Enter Chess.com Game URL",
        placeholder="https://www.chess.com/game/live/145613797338",
        help="Paste the URL of a Chess.com game you want to analyze"
    )
    
    if st.button("Analyze Game", type="primary"):
        if not game_url:
            st.error("Please enter a game URL")
        elif not username:
            st.error("Please enter a username")
        else:
            try:
                with st.spinner("Searching for game in local database..."):
                    # Import required modules
                    from fetch_single_game import fetch_game_from_url
                    from game_analyser import analyze_single_game, compute_accuracy, classify
                    
                    # Fetch game data from local parquet file
                    game_data = fetch_game_from_url(game_url, username.lower())
                    
                    # Store in session state
                    st.session_state.game_data = game_data
                    st.session_state.username = username.lower()
                    
            except FileNotFoundError as e:
                st.error(f"Games database not found: {e}")
                st.info("Please fetch and process games for this user first using the Profile Stats page.")
            except ValueError as e:
                st.error(f"Game not found: {e}")
                st.info("This game is not in your local database. Make sure you've fetched games that include this game's date.")
            except Exception as e:
                st.error(f"An error occurred: {e}")
                import traceback
                st.code(traceback.format_exc())
    
    # Display game info and player selection if game data is loaded
    if "game_data" in st.session_state:
        game_data = st.session_state.game_data
        username = st.session_state.username
        
        # Extract PGN and player info
        pgn = game_data.get("pgn")
        white_player = game_data.get("white", {}).get("username", "").lower()
        black_player = game_data.get("black", {}).get("username", "").lower()
        
        if not pgn:
            st.error("Could not retrieve PGN from this game")
        else:
            # Ask user which player to analyze
            st.info(f"**White**: {white_player} | **Black**: {black_player}")
            player_to_analyze = st.radio(
                "Which player do you want to analyze?",
                options=[white_player, black_player],
                format_func=lambda x: f"{x} (White)" if x == white_player else f"{x} (Black)",
                key="player_selection"
            )
            
            if st.button("Run Analysis", type="primary", key="run_analysis"):
                me_white = (player_to_analyze == white_player)
                
                try:
                    from game_analyser import analyze_single_game, compute_accuracy
                    import plotly.graph_objects as go
                    
                    with st.spinner(f"Analyzing {player_to_analyze}'s moves with Stockfish... This may take a minute."):
                        # Analyze the game
                        df_moves = analyze_single_game(pgn, me_white)
                        
                        # Compute accuracy and rating
                        accuracy, rating_equiv = compute_accuracy(df_moves)
                        
                        # Store results in session state
                        st.session_state.analysis_results = {
                            "df_moves": df_moves,
                            "accuracy": accuracy,
                            "rating_equiv": rating_equiv,
                            "player": player_to_analyze
                        }
                        
                except Exception as e:
                    st.error(f"Analysis error: {e}")
                    import traceback
                    st.code(traceback.format_exc())
            
            # Display results if analysis is complete
            if "analysis_results" in st.session_state:
                results = st.session_state.analysis_results
                df_moves = results["df_moves"]
                accuracy = results["accuracy"]
                rating_equiv = results["rating_equiv"]
                player = results["player"]
                
                # Display results
                st.success(f"Analysis Complete for {player}!")
                
                # Overall metrics
                st.header("📊 Overall Performance")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Accuracy Score", f"{accuracy:.1f}%")
                with col2:
                    st.metric("Game Strength Rating", rating_equiv)
                with col3:
                    st.metric("Total Moves Analyzed", len(df_moves))
                
                # Move classification breakdown
                st.header("🎯 Move Classification")
                
                move_counts = df_moves["category"].value_counts()
                
                # Create columns for each category
                cols = st.columns(6)
                categories = ["brilliant", "great", "good", "inaccuracy", "mistake", "blunder"]
                colors = ["🌟", "✨", "✅", "⚠️", "❌", "💥"]
                
                for i, (cat, emoji) in enumerate(zip(categories, colors)):
                    with cols[i]:
                        count = move_counts.get(cat, 0)
                        st.metric(f"{emoji} {cat.capitalize()}", count)
                
                # Detailed move-by-move analysis
                with st.expander("📋 Detailed Move Analysis"):
                    st.dataframe(
                        df_moves[["category", "eval_before", "eval_after", "eval_drop"]].rename(columns={
                            "category": "Classification",
                            "eval_before": "Eval Before",
                            "eval_after": "Eval After",
                            "eval_drop": "Eval Change"
                        }),
                        use_container_width=True
                    )
                
                # Visualization
                st.header("📈 Evaluation Over Time")
                import plotly.graph_objects as go
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    y=df_moves["eval_after"],
                    mode="lines+markers",
                    name="Position Evaluation",
                    line=dict(color="#4CAF50", width=2),
                    marker=dict(
                        size=8,
                        color=df_moves["category"].map({
                            "brilliant": "#FFD700",
                            "great": "#90EE90",
                            "good": "#87CEEB",
                            "inaccuracy": "#FFA500",
                            "mistake": "#FF6347",
                            "blunder": "#DC143C"
                        })
                    ),
                    hovertemplate="Move %{x}<br>Eval: %{y:.2f}<extra></extra>"
                ))
                
                fig.update_layout(
                    title="Position Evaluation Throughout the Game",
                    xaxis_title="Move Number",
                    yaxis_title="Evaluation (pawns)",
                    height=400,
                    hovermode="x unified"
                )
                
                st.plotly_chart(fig, use_container_width=True)

# Chess Coach Page
elif st.session_state.page == "chess_coach":
    if st.button("← Back to Home"):
        st.session_state.page = "landing"
        st.session_state.show_welcome = True
        st.rerun()
    
    st.title("🎓 Chess Coach")
    st.info("Chess coaching feature coming soon!")
    st.stop()

# Profile Stats Page
elif st.session_state.page == "profile_stats":
    # Add back button
    if st.button("← Back to Home"):
        st.session_state.page = "landing"
        st.session_state.show_welcome = True
        st.rerun()
    
    st.title("📊 Profile Stats")
    
    # Import the entire app.py content for Profile Stats
    # We'll embed the existing dashboard here
    exec(open("src/app.py").read().replace("st.title(\"Chess.com Game Analyzer\")", ""))
