import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO, StringIO

from modules.config import t

# Tetap gunakan style default Matplotlib/Seaborn
sns.set_style("whitegrid")


def page_analysis():
    st.title(t("analysis_title"))

    data_file = st.file_uploader(t("upload_data"), type=["xlsx", "csv"])
    if not data_file:
        st.info(t("upload_first"))
        return

    # --- 1. Pilih Sheet (jika XLSX) ---
    if data_file.name.endswith(".xlsx"):
        try:
            excel_obj = pd.ExcelFile(data_file)
            sheet_names = excel_obj.sheet_names  # Daftar nama sheet
        except Exception as e:
            st.error(f"Error membaca file Excel: {e}")
            return

        selected_sheet = st.selectbox("Pilih Sheet untuk Analisis", sheet_names)
        try:
            df = pd.read_excel(data_file, sheet_name=selected_sheet)
        except Exception as e:
            st.error(f"Error membaca sheet '{selected_sheet}': {e}")
            return

    else:
        # Baca CSV secara langsung
        try:
            df = pd.read_csv(data_file)
        except Exception as e:
            st.error(f"Error membaca file CSV: {e}")
            return

    st.success(f"Data berhasil dimuat: {len(df)} baris, {len(df.columns)} kolom.")
    st.dataframe(df.head(10))

    # Tombol unduh 100 baris pertama
    csv_head = df.head(100).to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Unduh 100 Baris Pertama (CSV)",
        data=csv_head,
        file_name="data_head_100.csv",
        mime="text/csv",
    )

    st.markdown("---")

    # --- 2. Info Dasar & Struktur Data ---
    st.subheader("ℹ️ Struktur Data & Tipe Kolom")
    buf = StringIO()
    df.info(buf=buf)
    s = buf.getvalue()
    st.text(s)

    st.markdown("---")

    # --- 3. Statistik Deskriptif ---
    st.subheader("📊 Statistik Deskriptif")

    # Statistik numerik
    st.markdown("**Statistik Numerik**")
    desc_num = df.describe().T
    st.dataframe(desc_num)

    # Statistik kategorikal
    st.markdown("**Statistik Kategorikal**")
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    if cat_cols:
        desc_cat = df[cat_cols].describe().T
        st.dataframe(desc_cat)
    else:
        st.info("Tidak ada kolom kategorikal.")

    st.markdown("---")

    # --- 4. Analisis Nilai Hilang (Missing Values) ---
    st.subheader("🚨 Analisis Nilai Hilang")
    missing_count = df.isnull().sum()
    missing_pct = (missing_count / len(df) * 100).round(2)
    df_missing = pd.DataFrame({
        "Kolom": df.columns,
        "Missing Count": missing_count.values,
        "Missing (%)": missing_pct.values
    }).sort_values(by="Missing (%)", ascending=False)
    st.dataframe(df_missing)

    # Plot missingness bar chart
    mis_nonzero = df_missing[df_missing["Missing (%)"] > 0]
    if not mis_nonzero.empty:
        fig_mis, ax_mis = plt.subplots(figsize=(6, min(0.5 * len(mis_nonzero), 8)))
        sns.barplot(
            x="Missing (%)", y="Kolom",
            data=mis_nonzero,
            palette="Reds_r",
            ax=ax_mis
        )
        ax_mis.set_xlabel("Persentase Nilai Hilang (%)")
        ax_mis.set_ylabel("Kolom")
        ax_mis.set_title("Persentase Nilai Hilang per Kolom")
        st.pyplot(fig_mis)
    else:
        st.info("Tidak ada nilai hilang pada data.")

    st.markdown("---")

    # --- 5. Korelasi & Heatmap (hanya numerik) ---
    st.subheader("🔗 Korelasi Kolom Numerik")
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if len(num_cols) >= 2:
        corr = df[num_cols].corr()
        st.dataframe(corr.round(2))

        fig_corr, ax_corr = plt.subplots(figsize=(8, 6))
        sns.heatmap(corr, annot=True, cmap="coolwarm", linewidths=0.5, ax=ax_corr)
        ax_corr.set_title("Heatmap Korelasi Numerik")
        st.pyplot(fig_corr)
    else:
        st.info("Data tidak memiliki cukup kolom numerik untuk korelasi.")

    st.markdown("---")

    # --- 6. Distribusi Kolom Numerik ---
    st.subheader("📈 Distribusi Kolom Numerik")
    if num_cols:
        col_num = st.selectbox("Pilih kolom numerik untuk analisis distribusi", num_cols)
        bins = st.slider("Jumlah Bin Histogram", min_value=5, max_value=100, value=30)

        col_data = df[col_num].dropna()
        if not col_data.empty:
            fig_hist, ax_hist = plt.subplots()
            ax_hist.hist(col_data, bins=bins, color="skyblue", edgecolor="black")
            ax_hist.set_title(f"Histogram: {col_num}")
            ax_hist.set_xlabel(col_num)
            ax_hist.set_ylabel("Frekuensi")
            st.pyplot(fig_hist)

            # Boxplot
            fig_box, ax_box = plt.subplots()
            sns.boxplot(x=col_data, ax=ax_box, color="lightgreen")
            ax_box.set_title(f"Boxplot: {col_num}")
            st.pyplot(fig_box)

            # Analisis Outlier Sederhana (IQR)
            Q1 = col_data.quantile(0.25)
            Q3 = col_data.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            outliers = col_data[(col_data < lower_bound) | (col_data > upper_bound)]
            st.markdown(
                f"**Outlier (Nilai < {lower_bound.round(2)} atau > {upper_bound.round(2)}):** "
                f"{len(outliers)} nilai"
            )
            if not outliers.empty:
                st.write(outliers.values[:10])  # tampilkan 10 outlier pertama
        else:
            st.info(f"Kolom {col_num} hanya berisi nilai kosong.")
    else:
        st.info("Tidak ada kolom numerik untuk distribusi.")

    st.markdown("---")

    # --- 7. Distribusi Kolom Kategorikal ---
    st.subheader("📊 Distribusi Kolom Kategorikal")
    if cat_cols:
        col_cat = st.selectbox("Pilih kolom kategorikal", cat_cols)
        top_n = st.slider("Tampilkan Top N Kategori Teratas", min_value=1, max_value=20, value=5)
        value_counts = df[col_cat].value_counts(dropna=False).head(top_n)
        df_cat = pd.DataFrame({col_cat: value_counts.index, "Count": value_counts.values})
        st.dataframe(df_cat)

        fig_cat, ax_cat = plt.subplots(figsize=(6, min(0.5 * top_n, 6)))
        sns.barplot(x=value_counts.values, y=value_counts.index, palette="viridis", ax=ax_cat)
        ax_cat.set_xlabel("Count")
        ax_cat.set_ylabel(col_cat)
        ax_cat.set_title(f"Top {top_n} Kategori: {col_cat}")
        st.pyplot(fig_cat)
    else:
        st.info("Tidak ada kolom kategorikal untuk dianalisa.")

    st.markdown("---")

    # --- 8. Ekspor Ringkasan Analisa ---
    st.subheader("⬇️ Unduh Ringkasan Analisa")
    # Daftar kolom dengan missing > 0%
    missing_cols = df_missing[df_missing["Missing (%)"] > 0]["Kolom"].tolist()
    missing_cols_str = ", ".join(missing_cols) if missing_cols else "Tidak ada"

    summary_df = pd.DataFrame({
        "Deskripsi": [
            "Total Baris",
            "Total Kolom",
            "Jumlah Kolom Numerik",
            "Jumlah Kolom Kategorikal",
            "Kolom dengan Nilai Hilang (>0%)"
        ],
        "Nilai": [
            len(df),
            len(df.columns),
            len(num_cols),
            len(cat_cols),
            missing_cols_str
        ]
    })
    csv_summary = summary_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Unduh Ringkasan Dasar (CSV)",
        data=csv_summary,
        file_name="ringkasan_analisa.csv",
        mime="text/csv",
    )

    st.markdown("---")
    st.markdown("✅ Analisa Data Lengkap Selesai.")
