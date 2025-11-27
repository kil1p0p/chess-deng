import streamlit as st

def render_chess_coach():
    if st.button("← Back to Home"):
        st.session_state.page = "landing"
        st.session_state.show_welcome = True
        st.rerun()
    
    st.title("🎓 Chess Coach")
    st.info("Chess coaching feature coming soon!")
