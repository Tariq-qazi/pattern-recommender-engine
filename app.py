import streamlit as st
import pandas as pd
import gdown
import os
import gc
from datetime import datetime

st.set_page_config(page_title="Dubai Real Estate Recommender", layout="wide")
st.title("🏙️ Dubai Real Estate Pattern Recommender")

# =======================
# 1. LOAD FILTER OPTIONS
# =======================
@st.cache_data
def get_filter_metadata():
    file_path = "transactions.parquet"
    if not os.path.exists(file_path):
        gdown.download("https://drive.google.com/uc?id=15kO9WvSnWbY4l9lpHwPYRhDmrwuiDjoI", file_path, quiet=False)
    df = pd.read_parquet(file_path, columns=[
        "area_name_en", "property_type_en", "rooms_en", "actual_worth", "instance_date", "offplan"
    ])
    df["instance_date"] = pd.to_datetime(df["instance_date"], errors="coerce")
    return {
        "areas": sorted(df["area_name_en"].dropna().unique()),
        "types": sorted(df["property_type_en"].dropna().unique()),
        "rooms": sorted(df["rooms_en"].dropna().unique()),
        "min_price": int(df["actual_worth"].min()),
        "max_price": int(df["actual_worth"].max()),
        "min_date": df["instance_date"].min(),
        "max_date": df["instance_date"].max()
    }

filters = get_filter_metadata()

# =======================
# 2. FILTER SIDEBAR
# =======================
st.sidebar.header("🔍 Property Filters")
with st.sidebar.form("filters_form"):
    selected_areas = st.multiselect("Area", filters["areas"])
    selected_types = st.multiselect("Property Type", filters["types"])
    selected_rooms = st.multiselect("Bedrooms", filters["rooms"])
    budget = st.slider("Max Budget (AED)", filters["min_price"], filters["max_price"], filters["max_price"])
    date_range = st.date_input("Transaction Date Range", [filters["min_date"], filters["max_date"]])
    submit = st.form_submit_button("Run Analysis")

# =======================
# 3. LOAD + FILTER DATA
# =======================
@st.cache_data
def load_and_filter_data(areas, types, rooms, max_price, date_start, date_end):
    df = pd.read_parquet("transactions.parquet")
    df["instance_date"] = pd.to_datetime(df["instance_date"], errors="coerce")

    if areas:
        df = df[df["area_name_en"].isin(areas)]
    if types:
        df = df[df["property_type_en"].isin(types)]
    if rooms:
        df = df[df["rooms_en"].isin(rooms)]
    df = df[df["actual_worth"] <= max_price]
    df = df[(df["instance_date"] >= date_start) & (df["instance_date"] <= date_end)]

    return df

# =======================
# 4. HELPER FUNCTIONS
# =======================
def classify_change(val):
    if val > 5:
        return "Up"
    elif val < -5:
        return "Down"
    else:
        return "Stable"

def classify_offplan(pct):
    if pct > 0.5:
        return "High"
    elif pct > 0.2:
        return "Medium"
    else:
        return "Low"

# =======================
# 5. PROCESS AFTER SUBMIT
# =======================
if submit:
    with st.spinner("🔎 Running analysis..."):
        gc.collect()
        try:
            df_filtered = load_and_filter_data(
                selected_areas, selected_types, selected_rooms,
                budget, pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
            )
        except Exception as e:
            st.error(f"Error filtering data: {e}")
            st.stop()

        st.success(f"✅ {len(df_filtered)} transactions matched.")

        if len(df_filtered) > 300_000:
            st.warning("🚨 Too many records. Please narrow your filters.")
            st.stop()

        # =======================
        # 6. METRIC SUMMARY TAGS
        # =======================
        st.subheader("📊 Market Tags Summary")
        grouped = df_filtered.groupby(pd.Grouper(key="instance_date", freq="Q")).agg({
            "actual_worth": "mean",
            "transaction_id": "count"
        }).rename(columns={"actual_worth": "avg_price", "transaction_id": "volume"}).dropna()

        if len(grouped) >= 2:
            latest, previous = grouped.iloc[-1], grouped.iloc[-2]
            qoq_price = ((latest["avg_price"] - previous["avg_price"]) / previous["avg_price"]) * 100
            qoq_volume = ((latest["volume"] - previous["volume"]) / previous["volume"]) * 100
            year_ago = grouped.iloc[-5] if len(grouped) >= 5 else previous
            yoy_price = ((latest["avg_price"] - year_ago["avg_price"]) / year_ago["avg_price"]) * 100
            yoy_volume = ((latest["volume"] - year_ago["volume"]) / year_ago["volume"]) * 100
            offplan_pct = df_filtered["offplan"].mean()

            tag_col1, tag_col2, tag_col3 = st.columns(3)
            tag_col1.metric("🏷️ Price QoQ", classify_change(qoq_price))
            tag_col1.metric("📈 Volume QoQ", classify_change(qoq_volume))
            tag_col2.metric("🏷️ Price YoY", classify_change(yoy_price))
            tag_col2.metric("📈 Volume YoY", classify_change(yoy_volume))
            tag_col3.metric("🏗️ Offplan Level", classify_offplan(offplan_pct))
        else:
            st.warning("Not enough quarterly data for trend metrics.")
else:
    st.info("🎯 Use the filters and click 'Run Analysis' to begin.")
