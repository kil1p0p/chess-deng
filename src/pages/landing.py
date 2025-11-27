import streamlit as st
import time

def render_landing_page():
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
