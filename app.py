import streamlit as st
from modules.auth import show_login, show_logout
from modules.generate import page_generate
from modules.dashboard import page_dashboard
from modules.analysis import page_analysis
from modules.config import t

def check_session_timeout():
    from datetime import datetime, timedelta
    SESSION_TIMEOUT = timedelta(minutes=15)
    if "last_active" in st.session_state:
        if datetime.now() - st.session_state.last_active > SESSION_TIMEOUT:
            st.session_state.clear()
            st.experimental_rerun()
    st.session_state.last_active = datetime.now()

def show_main_app():
    check_session_timeout()
    show_logout()

    st.sidebar.title(t("choose_language", st.session_state.lang))
    lang = st.sidebar.selectbox(
        "",
        ["id", "en"],
        index=0 if st.session_state.get("lang", "id") == "id" else 1,
        format_func=lambda x: "Indonesia" if x == "id" else "English",
    )
    st.session_state.lang = lang

    st.sidebar.title("Menu")
    page = st.sidebar.radio(
        "Navigasi",
        [
            t("dashboard_title", st.session_state.lang),
            t("generate_title", st.session_state.lang),
            t("analysis_title", st.session_state.lang),
        ],
    )

    if page == t("dashboard_title", st.session_state.lang):
        page_dashboard()
    elif page == t("generate_title", st.session_state.lang):
        page_generate()
    else:
        page_analysis()

if __name__ == "__main__":
    if "login_state" not in st.session_state:
        st.session_state.login_state = False
    if "lang" not in st.session_state:
        st.session_state.lang = "id"
    if st.session_state.get("logout_message", False):
        st.title(t("logout_msg", st.session_state.lang))
        st.markdown(t("logout_submsg", st.session_state.lang))
        if st.button(t("back_login", st.session_state.lang)):
            st.session_state.logout_message = False
            st.experimental_rerun()
    elif st.session_state.login_state:
        show_main_app()
    else:
        show_login()
