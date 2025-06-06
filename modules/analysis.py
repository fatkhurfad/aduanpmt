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

    # Upload file terlebih dahulu
    data_file = st.file_uploader(t("upload_data"), type=["xlsx", "csv"])
    if not data_file:
        st.info(t("upload_first"))
        return

    # Jika XLSX, tampilkan pilihan sheet
    if data_file.name.endswith(".xlsx"):
        try:
            excel_obj = pd.ExcelFile(data_file)
            sheet_names = excel_obj.sheet_names
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
        try:
            df = pd.read_csv(data_file)
        except Exception as e:
            st.error(f"Error membaca file CSV: {e}")
            return

    # Simpan ringkasan missing dan tipe kolom untuk digunakan di beberapa submenu
    missing_count = df.isnull().sum()
    missing_pct = (missing_count / len(df) * 100).round(2)
    df_missing = pd.DataFrame({
        "Kolom": df.columns,
        "Missing Count": missing_count.values,
        "Missing (%)": missing_pct.values
    }).sort_values(by="Missing (%)", ascending=False)

    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    # --- Sub-menu ---
    submenu = st.radio(
        "Pilih Bagian Analisa:",
        (
            "Ringkasan Data",
            "Statistik Deskriptif",
            "Missing Values",
            "Korelasi Numerik",
            "Distribusi Numerik",
            "Distribusi Kategorikal",
            "Pivot Table",
            "Ekspor Ringkasan",
        ),
        index=0,
    )

    st.markdown("---")

    # 1. Ringkasan Data
    if submenu == "Ringkasan Data":
        st.subheader("ℹ️ Ringkasan Data")
        st.success(f"Data berhasil dimuat: {len(df)} baris, {len(df.columns)} kolom.")
        st.dataframe(df.head(10))

        csv_head = df.head(100).to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Unduh 100 Baris Pertama (CSV)",
            data=csv_head,
            file_name="data_head_100.csv",
            mime="text/csv",
        )

    # 2. Statistik Deskriptif
    elif submenu == "Statistik Deskriptif":
        st.subheader("📊 Statistik Deskriptif")

        # Numerik
        st.markdown("**Statistik Numerik**")
        if num_cols:
            desc_num = df[num_cols].describe().T
            st.dataframe(desc_num)
        else:
            st.info("Tidak ada kolom numerik.")

        # Kategorikal
        st.markdown("**Statistik Kategorikal**")
        if cat_cols:
            desc_cat = df[cat_cols].describe().T
            st.dataframe(desc_cat)
        else:
            st.info("Tidak ada kolom kategorikal.")

    # 3. Missing Values
    elif submenu == "Missing Values":
        st.subheader("🚨 Analisis Nilai Hilang")
        st.dataframe(df_missing)

        mis_nonzero = df_missing[df_missing["Missing (%)"] > 0]
        if not mis_nonzero.empty:
            fig_mis, ax_mis = plt.subplots(
                figsize=(6, min(0.5 * len(mis_nonzero), 8))
            )
            sns.barplot(
                x="Missing (%)",
                y="Kolom",
                data=mis_nonzero,
                palette="Reds_r",
                ax=ax_mis,
            )
            ax_mis.set_xlabel("Persentase Nilai Hilang (%)")
            ax_mis.set_ylabel("Kolom")
            ax_mis.set_title("Persentase Nilai Hilang per Kolom")
            st.pyplot(fig_mis)
        else:
            st.info("Tidak ada nilai hilang pada data.")

    # 4. Korelasi Numerik
    elif submenu == "Korelasi Numerik":
        st.subheader("🔗 Korelasi Kolom Numerik")
        if len(num_cols) >= 2:
            corr = df[num_cols].corr()
            st.dataframe(corr.round(2))

            fig_corr, ax_corr = plt.subplots(figsize=(8, 6))
            sns.heatmap(
                corr,
                annot=True,
                cmap="coolwarm",
                linewidths=0.5,
                ax=ax_corr,
            )
            ax_corr.set_title("Heatmap Korelasi Numerik")
            st.pyplot(fig_corr)
        else:
            st.info("Data tidak memiliki cukup kolom numerik untuk korelasi.")

    # 5. Distribusi Numerik
    elif submenu == "Distribusi Numerik":
        st.subheader("📈 Distribusi Kolom Numerik")
        if num_cols:
            col_num = st.selectbox(
                "Pilih kolom numerik untuk analisis distribusi", num_cols
            )
            bins = st.slider(
                "Jumlah Bin Histogram", min_value=5, max_value=100, value=30
            )
            col_data = df[col_num].dropna()

            if not col_data.empty:
                fig_hist, ax_hist = plt.subplots()
                ax_hist.hist(col_data, bins=bins, color="skyblue", edgecolor="black")
                ax_hist.set_title(f"Histogram: {col_num}")
                ax_hist.set_xlabel(col_num)
                ax_hist.set_ylabel("Frekuensi")
                st.pyplot(fig_hist)

                fig_box, ax_box = plt.subplots()
                sns.boxplot(x=col_data, ax=ax_box, color="lightgreen")
                ax_box.set_title(f"Boxplot: {col_num}")
                st.pyplot(fig_box)

                Q1 = col_data.quantile(0.25)
                Q3 = col_data.quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                outliers = col_data[
                    (col_data < lower_bound) | (col_data > upper_bound)
                ]
                st.markdown(
                    f"**Outlier (Nilai < {lower_bound.round(2)} atau > {upper_bound.round(2)}):** "
                    f"{len(outliers)} nilai"
                )
                if not outliers.empty:
                    st.write(outliers.values[:10])
            else:
                st.info(f"Kolom {col_num} hanya berisi nilai kosong.")
        else:
            st.info("Tidak ada kolom numerik untuk distribusi.")

    # 6. Distribusi Kategorikal
    elif submenu == "Distribusi Kategorikal":
        st.subheader("📊 Distribusi Kolom Kategorikal")
        if cat_cols:
            col_cat = st.selectbox("Pilih kolom kategorikal", cat_cols)
            top_n = st.slider(
                "Tampilkan Top N Kategori Teratas",
                min_value=1,
                max_value=20,
                value=5,
            )
            value_counts = df[col_cat].value_counts(dropna=False).head(top_n)
            df_cat = pd.DataFrame({col_cat: value_counts.index, "Count": value_counts.values})
            st.dataframe(df_cat)

            fig_cat, ax_cat = plt.subplots(
                figsize=(6, min(0.5 * top_n, 6))
            )
            sns.barplot(
                x=value_counts.values, y=value_counts.index, palette="viridis", ax=ax_cat
            )
            ax_cat.set_xlabel("Count")
            ax_cat.set_ylabel(col_cat)
            ax_cat.set_title(f"Top {top_n} Kategori: {col_cat}")
            st.pyplot(fig_cat)
        else:
            st.info("Tidak ada kolom kategorikal untuk dianalisa.")

    # 7. Pivot Table
    elif submenu == "Pivot Table":
        st.subheader("🧮 Pivot Table")
        all_columns = df.columns.tolist()
        if all_columns:
            idx_cols = st.multiselect(
                "Pilih Kolom untuk Index (Baris)", all_columns, default=all_columns[:1]
            )
            col_pivot = st.multiselect(
                "Pilih Kolom untuk Columns (Kolom)", all_columns, default=all_columns[1:2]
            )
            val_cols = st.multiselect(
                "Pilih Kolom Numerik untuk Values", num_cols, default=num_cols[:1]
            )

            agg_funcs = {
                "Sum": "sum",
                "Mean": "mean",
                "Count": "count",
                "Min": "min",
                "Max": "max",
            }
            agg_choice = st.selectbox("Pilih Fungsi Agregasi", list(agg_funcs.keys()), index=0)
            aggfunc = agg_funcs[agg_choice]

            if idx_cols and col_pivot and val_cols:
                try:
                    pivot_df = pd.pivot_table(
                        df,
                        index=idx_cols,
                        columns=col_pivot,
                        values=val_cols,
                        aggfunc=aggfunc,
                        fill_value=0,
                    )
                    st.dataframe(pivot_df)
                    csv_pivot = pivot_df.to_csv(index=True).encode("utf-8")
                    st.download_button(
                        "⬇️ Unduh Pivot (CSV)",
                        data=csv_pivot,
                        file_name="pivot_table.csv",
                        mime="text/csv",
                    )
                except Exception as e:
                    st.error(f"Gagal membuat Pivot Table: {e}")
            else:
                st.info("Pilih setidaknya satu kolom Index, kolom Columns, dan kolom Values.")

    # 8. Ekspor Ringkasan
    elif submenu == "Ekspor Ringkasan":
        st.subheader("⬇️ Unduh Ringkasan Analisa")
        missing_cols = df_missing[df_missing["Missing (%)"] > 0]["Kolom"].tolist()
        missing_cols_str = ", ".join(missing_cols) if missing_cols else "Tidak ada"

        summary_df = pd.DataFrame(
            {
                "Deskripsi": [
                    "Total Baris",
                    "Total Kolom",
                    "Jumlah Kolom Numerik",
                    "Jumlah Kolom Kategorikal",
                    "Kolom dengan Nilai Hilang (>0%)",
                ],
                "Nilai": [
                    len(df),
                    len(df.columns),
                    len(num_cols),
                    len(cat_cols),
                    missing_cols_str,
                ],
            }
        )
        csv_summary = summary_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Unduh Ringkasan Dasar (CSV)",
            data=csv_summary,
            file_name="ringkasan_analisa.csv",
            mime="text/csv",
        )
        st.markdown("---")
        st.markdown("✅ Analisa Data Lengkap Selesai.")
