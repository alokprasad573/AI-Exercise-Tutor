import streamlit as st 
from services.persistence.exercise_repository import get_or_create_user

def login_form():
    
    if st.session_state.get("user_id") is not None:
        return True
    
    st.title("GymGenie")
    st.subheader("Personal AI based Exercise Tutor")

    
    with st.form("login_form"):
        username = st.text_input("Enter username", placeholder='alok1234')
        login_button = st.form_submit_button("Start Session")
        
    if login_button:
        if not username:
            st.error("Enter Username")
            return False
        
        user = get_or_create_user(username)
        st.session_state['username'] = user['username']
        st.session_state['user_id'] = user['id']
        st.rerun()
    
    return False
    

        