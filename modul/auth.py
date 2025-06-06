import streamlit as st
from modules.config import t

def show_login():
    st.title(t("welcome", st.session_state.lang))
    st.markdown(t("login", st.session_state.lang))
    with st.form("login_form"):
        username = st.text_input(t("username", st.session_state.lang))
        password = st.text_input(t("password", st.session_state.lang), type="password")
        submitted = st.form_submit_button(t("login_button", st.session_state.lang))
        if submitted:
            if username == "admin" and password == "surat123":
                st.session_state.login_state = True
                st.session_state.username = username
                st.session_state.logout_message = False
                st.experimental_rerun()
            else:
                st.error(t("login_fail", st.session_state.lang))

def show_logout():
    if st.sidebar.button(t("logout_button", st.session_state.lang)):
        st.session_state.logout_message = True
        st.session_state.login_state = False
        st.session_state.username = ""
        st.experimental_rerun()