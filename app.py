import streamlit as st
from services.auth.login import login_form

def app():
    st.set_page_config(page_title="AI Gym Coach",page_icon="💪")
    
    if not login_form():
        return
    
    st.title("Hello")
    


if __name__=="__main__":
    app()


