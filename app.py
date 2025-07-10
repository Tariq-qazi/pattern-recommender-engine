import streamlit as st
import pandas as pd
import os
import gdown
from datetime import datetime
import gc

st.set_page_config(page_title="Dubai Real Estate", layout="wide")

@st.cache_data(ttl=300)
def load_data():
    file_path = "transactions.parquet"
    if not os.path.exists(file_path):
        gdown.download("https://drive.google.com/uc?id=15kO9WvSnWbY4l9lpHwPYRhDmrwuiDjoI", file_path, quiet=False)
    df = pd.read_parquet(file_path)
    df["instance_date"] = pd.to_datetime(df["instance_date"], errors="coerce")
    return df

df = load_data()

# === Step Manager ===
step = st.sidebar.radio("Choose Step", ["🧮 Filter", "📊 Analyze"])

# === Filter Step ===
if step == "🧮 Filter":
    st.title("Step 1: Filter Data")
    with st.form("filters"):
        area = st.multiselect("Area", sorted(df["area_name_en"].dropna().unique()))
        prop_type = st.multiselect("Property Type", sorted(df["property_type_en"].dropna().unique()))
        bedrooms = st.multiselect("Bedrooms", sorted(df["rooms_en"].dropna().unique()))
        budget = st.slider("Max Budget (AED)", int(df["actual_worth"].min()), int(df["actual_worth"].max()), int(df["actual_worth"].max()))
        date_range = st.date_input("Transaction Date Range", [df["instance_date"].min(), df["instance_date"].max()])
        submitted = st.form_submit_button("Save Filters")
    
    if submitted:
        st.session_state.filters = {
            "area": area,
            "prop_type": prop_type,
            "bedrooms": bedrooms,
            "budget": budget,
            "date_range": date_range,
        }
        st.success("✅ Filters saved. Proceed to 'Analyze' step.")

# === Analysis Step ===
elif step == "📊 Analyze":
    st.title("Step 2: Analyze Market")
    
    if "filters" not in st.session_state:
        st.warning("⚠️ Please apply filters first.")
        st.stop()
    
    filters = st.session_state.filters
    filtered = df.copy()
    if filters["area"]:
        filtered = filtered[filtered["area_name_en"].isin(filters["area"])]
    if filters["prop_type"]:
        filtered = filtered[filtered["property_type_en"].isin(filters["prop_type"])]
    if filters["bedrooms"]:
        filtered = filtered[filtered["rooms_en"].isin(filters["bedrooms"])]
    filtered = filtered[filtered["actual_worth"] <= filters["budget"]]
    filtered = filtered[
        (filtered["instance_date"] >= pd.to_datetime(filters["date_range"][0])) &
        (filtered["instance_date"] <= pd.to_datetime(filters["date_range"][1]))
    ]
    
    st.success(f"✅ {len(filtered)} records loaded.")
    
    if len(filtered) > 300_000:
        st.warning("🚨 Too many results. Please go back and narrow filters.")
        st.stop()
    
    # === Metrics Section ===
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
        st.warning("⚠️ Not enough data for trend metrics.")

    gc.collect()
