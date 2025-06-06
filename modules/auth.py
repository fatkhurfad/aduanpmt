import streamlit as st
from modules.config import t

def show_login():
    st.title(t("welcome"))
    st.markdown(t("login"))
    with st.form("login_form"):
        username = st.text_input(t("username"))
        password = st.text_input(t("password"), type="password")
        submitted = st.form_submit_button(t("login_button"))
        if submitted:
            if username == "aku" and password == "adalah":
                st.session_state.login_state = True
                st.session_state.username = username
                st.session_state.logout_message = False
                st.experimental_rerun()
            else:
                st.error(t("login_fail"))

def show_logout():
    if st.sidebar.button(t("logout_button")):
        st.session_state.logout_message = True
        st.session_state.login_state = False
        st.session_state.username = ""
        st.experimental_rerun()
