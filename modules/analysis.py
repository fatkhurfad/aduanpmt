import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from modules.config import t

def page_analysis():
    st.title(t("analysis_title"))

    data_file = st.file_uploader(t("upload_data"), type=["xlsx", "csv"])
    if data_file:
        try:
            if data_file.name.endswith(".csv"):
                df = pd.read_csv(data_file)
            else:
                df = pd.read_excel(data_file)
        except Exception as e:
            st.error(f"Error membaca file: {e}")
            return

        st.success(f"Data berhasil dimuat, {len(df)} baris.")
        st.dataframe(df)

        st.markdown("### Statistik Deskriptif")
        st.write(df.describe())

        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        if numeric_cols:
            col = st.selectbox("Pilih kolom untuk histogram", numeric_cols)
            bins = st.slider("Jumlah bin", 5, 100, 20)

            fig, ax = plt.subplots()
            ax.hist(df[col].dropna(), bins=bins, color="skyblue", edgecolor="black")
            ax.set_title(f"Histogram kolom {col}")
            ax.set_xlabel(col)
            ax.set_ylabel("Frekuensi")
            st.pyplot(fig)
        else:
            st.info("Tidak ada kolom numerik untuk histogram.")
    else:
        st.info(t("upload_first"))
