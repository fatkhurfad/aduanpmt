import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO, StringIO

from modules.config import t

# Jika ingin seaborn styling untuk Matplotlib juga, tapi di sini kita fokus Plotly
import seaborn as sns
sns.set_style("whitegrid")


def page_analysis():
    st.title(t("analysis_title"))

    # ----- Upload dan Pilih Sheet -----
    data_file = st.file_uploader(t("upload_data"), type=["xlsx", "csv"])
    if not data_file:
        st.info(t("upload_first"))
        return

    if data_file.name.endswith(".xlsx"):
        try:
            excel_obj = pd.ExcelFile(data_file)
            sheet_names = excel_obj.sheet_names
        except Exception as e:
            st.error(f"Error membaca file Excel: {e}")
            return

        selected_sheet = st.selectbox("📑 Pilih Sheet untuk Analisis", sheet_names)
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

    # ----- Sidebar Filters (mirip slicer di Power BI) -----
    st.sidebar.markdown("## 🔍 Filter Data")
    # Contoh filter: pilih kolom, nilai tertentu
    filter_cols = df.columns.tolist()
    with st.sidebar.expander("Filter Baris:"):
        selected_filters = {}
        for col in filter_cols:
            if df[col].nunique() <= 10:  # hanya kolom dengan kategori terbatas
                vals = st.sidebar.multiselect(
                    f"{col}", options=df[col].dropna().unique().tolist(), default=None
                )
                if vals:
                    selected_filters[col] = vals

    # Terapkan filter
    df_filtered = df.copy()
    for col, vals in selected_filters.items():
        df_filtered = df_filtered[df_filtered[col].isin(vals)]

    # ----- Hitung statistik dasar sekali (digunakan di banyak tab) -----
    total_rows = len(df_filtered)
    total_cols = len(df_filtered.columns)
    num_cols = df_filtered.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df_filtered.select_dtypes(include=["object", "category"]).columns.tolist()

    # Missing values summary
    missing_count = df_filtered.isnull().sum()
    missing_pct = (missing_count / total_rows * 100).round(2)
    df_missing = pd.DataFrame({
        "Kolom": df_filtered.columns,
        "Missing Count": missing_count.values,
        "Missing (%)": missing_pct.values
    }).sort_values(by="Missing (%)", ascending=False)

    # ----- Tab Layout (mirip page di Power BI) -----
    tabs = st.tabs([
        "📋 Overview",
        "🔍 Missing Values",
        "🔗 Korelasi",
        "📈 Distribusi Numerik",
        "📊 Distribusi Kategorikal",
        "🧮 Pivot Table"
    ])

    # -------------------- Tab 1: Overview --------------------
    with tabs[0]:
        st.subheader("📋 Ringkasan Data")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Baris", total_rows)
        col2.metric("Total Kolom", total_cols)
        col3.metric("Kolom Numerik", len(num_cols))

        col4, col5 = st.columns(2)
        col4.metric("Kolom Kategorikal", len(cat_cols))
        col5.metric("Kolom Hilang (>0%)", (df_missing["Missing (%)"] > 0).sum())

        st.markdown("---")
        st.subheader("🔎 Preview Data (10 Baris Pertama)")
        st.dataframe(df_filtered.head(10), use_container_width=True)

        # Tombol unduh seluruh data yang sudah difilter
        csv_all = df_filtered.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Unduh Semua Data (CSV)",
            data=csv_all,
            file_name="data_filtered.csv",
            mime="text/csv",
        )

    # -------------------- Tab 2: Missing Values --------------------
    with tabs[1]:
        st.subheader("🚨 Analisis Nilai Hilang")
        st.dataframe(df_missing, use_container_width=True)

        mis_nonzero = df_missing[df_missing["Missing (%)"] > 0]
        if not mis_nonzero.empty:
            fig_mis = px.bar(
                mis_nonzero,
                x="Missing (%)",
                y="Kolom",
                orientation="h",
                title="Persentase Nilai Hilang per Kolom",
                text="Missing (%)",
                color="Missing (%)",
                color_continuous_scale="Reds",
            )
            fig_mis.update_layout(yaxis=dict(autorange="reversed"), height=400)
            st.plotly_chart(fig_mis, use_container_width=True)
        else:
            st.info("Tidak ada nilai hilang pada data.")

    # -------------------- Tab 3: Korelasi --------------------
    with tabs[2]:
        st.subheader("🔗 Korelasi Kolom Numerik")
        if len(num_cols) >= 2:
            corr = df_filtered[num_cols].corr()

            st.dataframe(corr.round(2), use_container_width=True)

            fig_corr = px.imshow(
                corr,
                text_auto=".2f",
                aspect="auto",
                color_continuous_scale="RdBu_r",
                title="Heatmap Korelasi Numerik",
            )
            fig_corr.update_layout(height=500)
            st.plotly_chart(fig_corr, use_container_width=True)
        else:
            st.info("Data tidak memiliki cukup kolom numerik untuk korelasi.")

    # -------------------- Tab 4: Distribusi Numerik --------------------
    with tabs[3]:
        st.subheader("📈 Distribusi Kolom Numerik")
        if num_cols:
            col_num = st.selectbox("🏷️ Pilih Kolom Numerik", num_cols, key="dist_num")
            bins = st.slider("Jumlah Bin Histogram", min_value=5, max_value=100, value=30, key="dist_bins")

            col_data = df_filtered[col_num].dropna()
            if not col_data.empty:
                # Histogram interaktif
                fig_hist = px.histogram(
                    col_data,
                    nbins=bins,
                    title=f"Histogram: {col_num}",
                    labels={ "value": col_num },
                )
                st.plotly_chart(fig_hist, use_container_width=True)

                # Boxplot
                fig_box = px.box(
                    col_data,
                    points="all",
                    title=f"Boxplot: {col_num}",
                    labels={ "value": col_num },
                )
                st.plotly_chart(fig_box, use_container_width=True)

                # Outlier (IQR)
                Q1 = col_data.quantile(0.25)
                Q3 = col_data.quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                outliers = col_data[(col_data < lower_bound) | (col_data > upper_bound)]
                st.markdown(
                    f"**Outlier (Nilai < {lower_bound:.2f} atau > {upper_bound:.2f}):** "
                    f"{len(outliers)} nilai"
                )
                if not outliers.empty:
                    st.write(outliers.values[:10])
            else:
                st.info(f"Kolom {col_num} hanya berisi nilai kosong.")
        else:
            st.info("Tidak ada kolom numerik untuk distribusi.")

    # -------------------- Tab 5: Distribusi Kategorikal --------------------
    with tabs[4]:
        st.subheader("📊 Distribusi Kolom Kategorikal")
        if cat_cols:
            col_cat = st.selectbox("🏷️ Pilih Kolom Kategorikal", cat_cols, key="dist_cat")
            top_n = st.slider(
                "Tampilkan Top N Kategori Teratas", min_value=1, max_value=20, value=5, key="dist_topn"
            )
            value_counts = df_filtered[col_cat].value_counts(dropna=False).head(top_n)
            df_cat = pd.DataFrame({col_cat: value_counts.index, "Count": value_counts.values})
            st.dataframe(df_cat, use_container_width=True)

            fig_cat = px.bar(
                df_cat,
                x="Count",
                y=col_cat,
                orientation="h",
                title=f"Top {top_n} Kategori: {col_cat}",
                labels={ "Count": "Jumlah", col_cat: col_cat },
                color="Count",
                color_continuous_scale="Viridis",
            )
            fig_cat.update_layout(yaxis=dict(autorange="reversed"), height=400)
            st.plotly_chart(fig_cat, use_container_width=True)
        else:
            st.info("Tidak ada kolom kategorikal untuk dianalisa.")

    # -------------------- Tab 6: Pivot Table --------------------
    with tabs[5]:
        st.subheader("🧮 Pivot Table")
        all_columns = df_filtered.columns.tolist()

        idx_cols = st.multiselect(
            "📂 Pilih Kolom untuk Index (Baris)", all_columns, default=all_columns[:1], key="pivot_idx"
        )
        col_pivot = st.multiselect(
            "📑 Pilih Kolom untuk Columns", all_columns, default=all_columns[1:2], key="pivot_cols"
        )
        val_cols = st.multiselect(
            "🔢 Pilih Kolom Numerik untuk Values", num_cols, default=num_cols[:1], key="pivot_vals"
        )

        agg_funcs = {
            "Sum": "sum",
            "Mean": "mean",
            "Count": "count",
            "Min": "min",
            "Max": "max",
        }
        agg_choice = st.selectbox("⚙️ Pilih Fungsi Agregasi", list(agg_funcs.keys()), index=0, key="pivot_agg")
        aggfunc = agg_funcs[agg_choice]

        if idx_cols and col_pivot and val_cols:
            try:
                pivot_df = pd.pivot_table(
                    df_filtered,
                    index=idx_cols,
                    columns=col_pivot,
                    values=val_cols,
                    aggfunc=aggfunc,
                    fill_value=0,
                )
                st.dataframe(pivot_df, use_container_width=True)

                # Unduh pivot
                csv_pivot = pivot_df.to_csv(index=True).encode("utf-8")
                st.download_button(
                    "⬇️ Unduh Pivot (CSV)",
                    data=csv_pivot,
                    file_name="pivot_table.csv",
                    mime="text/csv",
                )

                # Pilihan visualisasi pivot sederhana
                if len(val_cols) == 1 and len(col_pivot) == 1:
                    st.markdown("---")
                    st.subheader("📊 Visualisasi Pivot (Chart)")
                    pivot_chart = pivot_df[val_cols[0]]
                    # Flatten MultiIndex untuk chart
                    pivot_chart = pivot_chart.reset_index()
                    pivot_chart.columns = idx_cols + [col_pivot[0], val_cols[0]]
                    fig_pivot = px.bar(
                        pivot_chart,
                        x=idx_cols,
                        y=val_cols[0],
                        color=col_pivot[0],
                        barmode="group",
                        title="Visualisasi Pivot Table",
                    )
                    st.plotly_chart(fig_pivot, use_container_width=True)
            except Exception as e:
                st.error(f"Gagal membuat Pivot Table: {e}")
        else:
            st.info("Pilih setidaknya satu kolom Index, Columns, dan Values.")

    # -------------------- Footer Akhir --------------------
    st.markdown("---")
    st.caption("✅ Analisa Data Lengkap (Power BI-Style) Selesai.")
