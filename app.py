import streamlit as st
import pandas as pd
import gdown
import os
import gc
from datetime import datetime

st.set_page_config(page_title="Dubai Real Estate Recommender", layout="wide")
st.sidebar.title("Choose Step")
step = st.sidebar.radio("Navigation", ["🧮 Filter", "📊 Analyze"])

@st.cache_data
def load_data():
    file_path = "transactions.parquet"
    if not os.path.exists(file_path):
        st.info("⬇️ Downloading full dataset from Drive...")
        gdown.download("https://drive.google.com/uc?id=15kO9WvSnWbY4l9lpHwPYRhDmrwuiDjoI", file_path, quiet=False)
    df = pd.read_parquet(file_path)
    df["instance_date"] = pd.to_datetime(df["instance_date"], errors="coerce")
    return df

df = load_data()

# Ensure safe session state init
if "filters" not in st.session_state:
    st.session_state["filters"] = {}

# === Step 1: FILTER DATA ===
if step == "🧮 Filter":
    st.title("Step 1: Filter Data")
    area = st.multiselect("Area", sorted(df["area_name_en"].dropna().unique()))
    prop_type = st.multiselect("Property Type", sorted(df["property_type_en"].dropna().unique()))
    bedrooms = st.multiselect("Bedrooms", sorted(df["rooms_en"].dropna().unique()))
    budget = st.slider("Max Budget (AED)", int(df["actual_worth"].min()), int(df["actual_worth"].max()), int(df["actual_worth"].max()))
    date_range = st.date_input("Transaction Date Range", [df["instance_date"].min(), df["instance_date"].max()])
    if st.button("Save Filters"):
        st.session_state["filters"] = {
            "area": area,
            "prop_type": prop_type,
            "bedrooms": bedrooms,
            "budget": budget,
            "date_range": date_range
        }
        st.success("✅ Filters saved. Go to the Analyze step.")


# === Step 2: ANALYZE ===
elif step == "📊 Analyze":
    st.title("Step 2: Analyze Market")

    filters = st.session_state.get("filters", {})
    if not filters:
        st.warning("⚠️ Please go to the 'Filter' step and apply filters first.")
        st.stop()

    with st.spinner("🔍 Filtering and analyzing data..."):
        gc.collect()
        filtered = df.copy()
        if filters.get("area"):
            filtered = filtered[filtered["area_name_en"].isin(filters["area"])]
        if filters.get("prop_type"):
            filtered = filtered[filtered["property_type_en"].isin(filters["prop_type"])]
        if filters.get("bedrooms"):
            filtered = filtered[filtered["rooms_en"].isin(filters["bedrooms"])]
        if filters.get("budget"):
            filtered = filtered[filtered["actual_worth"] <= filters["budget"]]
        if filters.get("date_range"):
            start, end = pd.to_datetime(filters["date_range"][0]), pd.to_datetime(filters["date_range"][1])
            filtered = filtered[(filtered["instance_date"] >= start) & (filtered["instance_date"] <= end)]

        if len(filtered) > 300_000:
            st.warning("🚨 Too many results. Please narrow your filters (area, type, budget).")
            st.stop()

        st.success(f"✅ {len(filtered)} properties matched.")

        # === Metrics Calculation ===
        st.subheader("📊 Market Summary Metrics")
        grouped = filtered.groupby(pd.Grouper(key="instance_date", freq="Q")).agg({
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

            col1, col2 = st.columns(2)
            col1.metric("🏷️ Price QoQ", f"{qoq_price:.1f}%")
            col1.metric("📈 Volume QoQ", f"{qoq_volume:.1f}%")
            col2.metric("🏷️ Price YoY", f"{yoy_price:.1f}%")
            col2.metric("📈 Volume YoY", f"{yoy_volume:.1f}%")
        else:
            st.warning("Not enough quarterly data for trend metrics.")
