import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import plotly.express as px
from io import BytesIO

# Jika Anda ingin tetap pakai t(“…”), impor config:
# from modules.config import t

sns.set_style("whitegrid")

@st.cache_data(show_spinner=False)
def load_excel(file_bytes: bytes, sheet_name: str | None = None, nrows: int | None = None) -> pd.DataFrame:
    buf = BytesIO(file_bytes)
    if sheet_name:
        return pd.read_excel(buf, sheet_name=sheet_name, nrows=nrows)
    return pd.read_excel(buf, nrows=nrows)

@st.cache_data(show_spinner=False)
def load_csv(file_bytes: bytes, nrows: int | None = None) -> pd.DataFrame:
    buf = BytesIO(file_bytes)
    return pd.read_csv(buf, nrows=nrows)

def page_explorer():
    st.title("📊 Data Explorer")

    # 1. Upload atau Pilih Contoh
    st.sidebar.header("1. Pilih Dataset")
    data_source = st.sidebar.radio("Sumber data:", ("Contoh Seaborn", "Unggah File Anda"))

    df = None
    if data_source == "Contoh Seaborn":
        sample_name = st.sidebar.selectbox("Pilih contoh dataset Seaborn:", ("iris", "penguins", "titanic", "tips", "diamonds"))
        with st.spinner("Memuat dataset…"):
            df = getattr(sns, sample_name).load_dataset(sample_name)
    else:
        uploaded = st.sidebar.file_uploader("Unggah CSV atau Excel (xlsx)", type=["csv", "xlsx"])
        if uploaded:
            with st.sidebar.expander("📋 Opsi Pemuatan File", expanded=False):
                if uploaded.name.lower().endswith(".xlsx"):
                    excel_obj = pd.ExcelFile(uploaded)
                    sheet_names = excel_obj.sheet_names
                    selected_sheet = st.sidebar.selectbox("Pilih Sheet", sheet_names)
                else:
                    selected_sheet = None

                max_rows = st.sidebar.number_input(
                    "Jumlah baris yang dimuat", 100, 500_000, 50_000, step=100,
                    help="Hanya memuat n baris pertama untuk pratinjau ringan."
                )

            try:
                if uploaded.name.lower().endswith(".xlsx"):
                    df = load_excel(uploaded.read(), sheet_name=selected_sheet, nrows=int(max_rows))
                else:
                    df = load_csv(uploaded.read(), nrows=int(max_rows))
            except Exception as e:
                st.sidebar.error(f"Gagal memuat file: {e}")
                return

    if df is None:
        st.warning("Silakan pilih sumber data di sidebar.")
        return

    st.success(f"Dataset dimuat: {df.shape[0]} baris × {df.shape[1]} kolom.")

    # 2. Preview Data
    st.subheader("1. Pratinjau Data")
    st.dataframe(df.head(10), use_container_width=True)

    # 3. Filter Data
    st.sidebar.header("2. Filter Data")
    all_cols = df.columns.tolist()
    filter_values = {}
    with st.sidebar.expander("Filter per Kolom", expanded=False):
        for col in all_cols:
            unique_vals = df[col].dropna().unique()
            if 1 < len(unique_vals) <= 10 and df[col].dtype == object:
                sel = st.multiselect(f"{col}", options=list(unique_vals), default=None)
                if sel:
                    filter_values[col] = sel
            elif np.issubdtype(df[col].dtype, np.number):
                mi, ma = float(df[col].min()), float(df[col].max())
                r_min, r_max = st.slider(f"{col}", mi, ma, (mi, ma))
                filter_values[col] = (r_min, r_max)

    df_filtered = df.copy()
    for col, cond in filter_values.items():
        if isinstance(cond, list):
            df_filtered = df_filtered[df_filtered[col].isin(cond)]
        else:
            lo, hi = cond
            df_filtered = df_filtered[df_filtered[col].between(lo, hi)]

    st.info(f"Data setelah filter: {df_filtered.shape[0]} baris × {df_filtered.shape[1]} kolom.")

    # 4. Pilih Kolom untuk Visualisasi
    st.sidebar.header("3. Pilih Kolom")
    numeric_cols = df_filtered.select_dtypes(include=np.number).columns.tolist()
    categorical_cols = df_filtered.select_dtypes(include=["object", "category", "bool"]).columns.tolist()

    sel_num_cols = st.sidebar.multiselect("Kolom Numerik", options=numeric_cols, default=numeric_cols[:3])
    sel_cat_cols = st.sidebar.multiselect("Kolom Kategorikal", options=categorical_cols, default=categorical_cols[:3])

    # 5. Sampling (jika >5000 baris)
    if df_filtered.shape[0] > 5000:
        df_sample = df_filtered.sample(5000, random_state=42)
        st.info("🔹 Tampilan diambil dari sampel 5.000 baris.")
    else:
        df_sample = df_filtered

    # 6. Hitung Missing Values
    missing_count = df_sample.isnull().sum()
    missing_pct = (missing_count / df_sample.shape[0] * 100).round(2)
    df_missing = pd.DataFrame({
        "Kolom": df_sample.columns,
        "Missing Count": missing_count.values,
        "Missing (%)": missing_pct.values
    }).sort_values(by="Missing (%)", ascending=False)

    # 7. Tab Layout
    tabs = st.tabs([
        "📋 Ringkasan",
        "📊 Statistik",
        "📈 Visualisasi",
        "🔗 Korelasi",
        "🧮 Pivot"
    ])

    # Tab Ringkasan
    with tabs[0]:
        st.subheader("📋 Ringkasan Data")
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Baris", f"{df_filtered.shape[0]:,}")
        c2.metric("Total Kolom", f"{df_filtered.shape[1]:,}")
        c3.metric("Kolom Numerik", len(numeric_cols))

        c4, c5 = st.columns(2)
        c4.metric("Kolom Kategorikal", len(categorical_cols))
        total_missing = df_filtered.isnull().sum().sum()
        c5.metric("Total Nilai Hilang", f"{total_missing:,}")

        st.markdown("---")
        st.subheader("🔍 10 Baris Pertama")
        st.dataframe(df_filtered.head(10), use_container_width=True)
        csv_head = df_filtered.head(10).to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Unduh 10 Baris (CSV)", data=csv_head, file_name="head10.csv", mime="text/csv")

    # Tab Statistik
    with tabs[1]:
        st.subheader("📊 Statistik Deskriptif")
        if sel_num_cols:
            st.markdown("**Numerik**")
            st.dataframe(df_sample[sel_num_cols].describe().T, use_container_width=True)
        else:
            st.info("Pilih kolom numerik di sidebar.")

        if sel_cat_cols:
            st.markdown("**Kategorikal**")
            st.dataframe(df_sample[sel_cat_cols].describe().T, use_container_width=True)
        else:
            st.info("Pilih kolom kategorikal di sidebar.")

    # Tab Visualisasi
    with tabs[2]:
        st.subheader("📈 Visualisasi Interaktif")
        if sel_num_cols:
            st.markdown("### Histogram & Boxplot (Numerik)")
            col_hist = st.selectbox("Pilih Kolom Numerik", sel_num_cols, key="hist_col")
            bins = st.slider("Jumlah Bin", 5, 100, 30, key="hist_bins")
            data_hist = df_sample[col_hist].dropna()
            if data_hist.shape[0] > 5000:
                data_hist = data_hist.sample(5000, random_state=42)
                st.info("🔹 Sampel 5.000 baris untuk histogram.")

            fig_hist = px.histogram(data_hist, nbins=bins, title=f"Histogram {col_hist}", labels={col_hist: col_hist})
            st.plotly_chart(fig_hist, use_container_width=True)

            fig_box = px.box(data_hist, points="all", title=f"Boxplot {col_hist}", labels={col_hist: col_hist})
            st.plotly_chart(fig_box, use_container_width=True)
        else:
            st.info("Pilih kolom numerik di sidebar.")

        st.markdown("---")
        if sel_cat_cols:
            st.markdown("### Bar Chart (Kategorikal)")
            col_bar = st.selectbox("Pilih Kolom Kategorikal", sel_cat_cols, key="bar_col")
            top_n = st.slider("Top N Kategori", 1, 20, 5, key="bar_top")
            vc = df_filtered[col_bar].value_counts(dropna=False).head(top_n)
            df_vc = pd.DataFrame({col_bar: vc.index.astype(str), "Count": vc.values})

            fig_bar = px.bar(df_vc, x="Count", y=col_bar, orientation="h",
                              title=f"Top {top_n} {col_bar}", labels={"Count": "Jumlah", col_bar: col_bar},
                              color="Count", color_continuous_scale="Viridis")
            fig_bar.update_layout(yaxis=dict(autorange="reversed"), height=400)
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Pilih kolom kategorikal di sidebar.")

    # Tab Korelasi
    with tabs[3]:
        st.subheader("🔗 Korelasi & Heatmap")
        if len(numeric_cols) >= 2:
            if len(numeric_cols) > 20:
                top20 = df_filtered[numeric_cols].var().sort_values(ascending=False).index.tolist()[:20]
                corr_cols = st.multiselect("Pilih hingga 20 kolom", options=top20, default=top20[:5], key="corr_cols")
            else:
                corr_cols = numeric_cols

            if corr_cols:
                df_corr = df_filtered[corr_cols]
                if df_corr.shape[0] > 5000:
                    df_corr = df_corr.sample(5000, random_state=42)
                    st.info("🔹 Sampel 5.000 baris untuk korelasi.")
                corr_m = df_corr.corr()
                st.dataframe(corr_m.round(2), use_container_width=True)

                fig_corr = px.imshow(corr_m, text_auto=".2f", aspect="auto",
                                     color_continuous_scale="RdBu_r", title="Heatmap Korelasi")
                fig_corr.update_layout(height=500)
                st.plotly_chart(fig_corr, use_container_width=True)
            else:
                st.info("Pilih setidaknya satu kolom untuk korelasi.")
        else:
            st.info("Perlu setidaknya 2 kolom numerik.")

    # Tab Pivot
    with tabs[4]:
        st.subheader("🧮 Pivot Table")
        all_cols = df_filtered.columns.tolist()

        idx_cols = st.multiselect("Index (Baris)", all_cols, default=all_cols[:1], key="pivot_idx")
        col_piv = st.multiselect("Columns", all_cols, default=all_cols[1:2], key="pivot_cols")
        val_cols = st.multiselect("Values (Numerik)", numeric_cols, default=numeric_cols[:1], key="pivot_vals")

        agg_funcs = {"Sum": "sum", "Mean": "mean", "Count": "count", "Min": "min", "Max": "max"}
        agg_choice = st.selectbox("Pilih Agregasi", list(agg_funcs.keys()), index=0, key="pivot_agg")
        aggfunc = agg_funcs[agg_choice]

        if idx_cols and col_piv and val_cols:
            with st.spinner("Menghitung Pivot…"):
                try:
                    pivot_df = pd.pivot_table(
                        df_filtered,
                        index=idx_cols,
                        columns=col_piv,
                        values=val_cols,
                        aggfunc=aggfunc,
                        fill_value=0
                    )
                except Exception as e:
                    st.error(f"Gagal membuat pivot: {e}")
                    return
            st.dataframe(pivot_df, use_container_width=True)

            csv_piv = pivot_df.to_csv(index=True).encode("utf-8")
            st.download_button("⬇️ Unduh Pivot CSV", data=csv_piv, file_name="pivot.csv", mime="text/csv")

            if len(val_cols) == 1 and len(col_piv) == 1:
                st.markdown("---")
                st.subheader("📊 Visualisasi Pivot")
                piv_vis = pivot_df[val_cols[0]].reset_index()
                piv_vis.columns = idx_cols + [col_piv[0], val_cols[0]]
                try:
                    fig_piv = px.bar(piv_vis, x=idx_cols, y=val_cols[0], color=col_piv[0],
                                    barmode="group", title="Visualisasi Pivot")
                    st.plotly_chart(fig_piv, use_container_width=True)
                except Exception:
                    st.info("Tidak bisa tampilkan chart untuk kombinasi pivot ini.")
        else:
            st.info("Pilih Index, Columns, dan Values minimal satu kolom masing-masing.")

    # Sidebar: Unduh semua data hasil filter
    st.sidebar.header("4. Unduh Hasil Filter")
    csv_all = df_filtered.to_csv(index=False).encode("utf-8")
    st.sidebar.download_button("⬇️ Unduh CSV Terfilter", data=csv_all, file_name="data_filtered.csv", mime="text/csv")


if __name__ == "__main__":
    main()
