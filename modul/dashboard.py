import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from modules.config import t

def page_dashboard():
    st.title(t("dashboard_title", st.session_state.lang))
    st.markdown(f"{t('welcome', st.session_state.lang)}, **{st.session_state.username}**!")

    with st.expander(t("tips", st.session_state.lang), expanded=True):
        st.write(t("tips_content", st.session_state.lang))

    st.markdown("---")

    generate_log = st.session_state.get("generate_log", [])

    total_surat = len(generate_log)
    berhasil = sum(1 for item in generate_log if item["Status"].startswith("✅"))
    gagal = total_surat - berhasil

    template_tersedia = st.session_state.get("template_count", 1)
    data_peserta_terakhir = st.session_state.get("last_data_rows", 0)

    statistik_data = {
        "Statistik": [
            t("total_letters", st.session_state.lang),
            t("letters_success", st.session_state.lang),
            t("letters_failed", st.session_state.lang),
            t("templates_available", st.session_state.lang),
            t("last_data_rows", st.session_state.lang),
        ],
        "Jumlah": [
            total_surat,
            berhasil,
            gagal,
            template_tersedia,
            data_peserta_terakhir,
        ],
    }
    df_statistik = pd.DataFrame(statistik_data)
    st.table(df_statistik)

    st.markdown("---")

    st.markdown("### " + t("letters_success_vs_failed", st.session_state.lang))
    fig, ax = plt.subplots()
    ax.bar([t("letters_success", st.session_state.lang), t("letters_failed", st.session_state.lang)], [berhasil, gagal], color=["green", "red"])
    ax.set_ylabel(t("total_letters", st.session_state.lang))
    ax.set_title(t("letters_success_vs_failed", st.session_state.lang))
    st.pyplot(fig)

    st.markdown("---")

    st.markdown("### " + t("percentage_letters", st.session_state.lang))
    fig2, ax2 = plt.subplots()
    if total_surat > 0:
        ax2.pie(
            [berhasil, gagal],
            labels=[t("letters_success", st.session_state.lang), t("letters_failed", st.session_state.lang)],
            autopct="%1.1f%%",
            colors=["green", "red"],
            startangle=90,
            wedgeprops={"edgecolor": "black"},
        )
        ax2.axis("equal")
        st.pyplot(fig2)
    else:
        st.write(t("no_data", st.session_state.lang))

    st.markdown("---")

    st.markdown("### " + t("last_activity", st.session_state.lang))
    aktivitas = []
    for item in reversed(generate_log[-5:]):
        aktivitas.append({"Aktivitas": f"{t('generate_title', st.session_state.lang)} untuk {item['Nama']}", "Status": item["Status"]})
    if aktivitas:
        df_aktivitas = pd.DataFrame(aktivitas)
        st.table(df_aktivitas)
    else:
        st.write(t("no_activity", st.session_state.lang))

    st.markdown("---")

    st.markdown(t("app_version", st.session_state.lang))
    st.markdown(t("no_maintenance", st.session_state.lang))