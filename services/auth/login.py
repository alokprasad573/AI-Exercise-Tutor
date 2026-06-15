import streamlit as st 


def login_form():
    
    if st.session_state.get("user_id") is not None:
        return True
    
    st.title("AI Gym Trainer")
    st.markdown("Please Enter your username to start")
    
    with st.form("login_form"):
        username = st.text_input("Enter username", placeholder='alok1234')
        login_button = st.form_submit_button("Start Session")
        
    if login_button:
        if not username:
            st.error("Enter Username")
            return False
        
        st.session_state['username'] = username
        st.session_state['user_id'] = '1'
        st.rerun()
    
    return False
    

        