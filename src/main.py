import streamlit as st
from views.landing import render_landing_page
from views.profile_stats import render_profile_stats
from views.analyse_game import render_analyse_game
from views.chess_coach import render_chess_coach

st.set_page_config(page_title="Chess Analyzer", layout="wide", initial_sidebar_state="collapsed")

# Initialize session state for page navigation
if "page" not in st.session_state:
    st.session_state.page = "landing"
if "show_welcome" not in st.session_state:
    st.session_state.show_welcome = True

# Routing
if st.session_state.page == "landing":
    render_landing_page()
elif st.session_state.page == "profile_stats":
    render_profile_stats()
elif st.session_state.page == "analyse_game":
    render_analyse_game()
elif st.session_state.page == "chess_coach":
    render_chess_coach()
