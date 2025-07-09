import streamlit as st
import pandas as pd
import gdown
import os
import tempfile

st.set_page_config(page_title="Dubai Real Estate Pattern Recommender", layout="wide")
st.title("🏙️ Dubai Real Estate Pattern Recommender")

@st.cache_data
def load_data():
    file_path = os.path.join(tempfile.gettempdir(), "transactions_merged.parquet")
    if not os.path.exists(file_path):
        st.info("⏬ Downloading dataset from Google Drive...")
        url = "https://drive.google.com/uc?id=15kO9WvSnWbY4l9lpHwPYRhDmrwuiDjoI"
        gdown.download(url, file_path, quiet=False)
    if not os.path.exists(file_path):
        st.error("❌ File could not be loaded. Try again.")
        st.stop()
    df = pd.read_parquet(file_path)
    df['instance_date'] = pd.to_datetime(df['instance_date'], errors='coerce')
    df = df.dropna(subset=['instance_date'])
    return df


df = load_data()

if df is not None and not df.empty:
    st.success("✅ Data loaded successfully")

    # === Sidebar Filters ===
    st.sidebar.header("🔍 Filter Properties")

    # Date Filter
    min_date = df["instance_date"].min().date()
    max_date = df["instance_date"].max().date()
    start_date, end_date = st.sidebar.date_input("Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)

    # Other Filters
    area = st.sidebar.multiselect("Area", options=sorted(df["area_name_en"].dropna().unique()))
    prop_type = st.sidebar.multiselect("Property Type", options=sorted(df["property_type_en"].dropna().unique()))
    bedrooms = st.sidebar.multiselect("Bedrooms", options=sorted(df["rooms_en"].dropna().unique()))
    budget = st.sidebar.slider("Max Budget (AED)", int(df["actual_worth"].min()), int(df["actual_worth"].max()), int(df["actual_worth"].max()))

    # === Apply Filters ===
    filtered = df.copy()
    filtered = filtered[
        (filtered["instance_date"].dt.date >= start_date) &
        (filtered["instance_date"].dt.date <= end_date)
    ]
    if area:
        filtered = filtered[filtered["area_name_en"].isin(area)]
    if prop_type:
        filtered = filtered[filtered["property_type_en"].isin(prop_type)]
    if bedrooms:
        filtered = filtered[filtered["rooms_en"].isin(bedrooms)]
    filtered = filtered[filtered["actual_worth"] <= budget]

    st.subheader(f"🔎 {len(filtered)} Transactions After Filtering")
    st.caption("We skipped preview to ensure app performance.")

    # === Step 2: Prepare Monthly Aggregation ===
    filtered["year_month"] = filtered["instance_date"].dt.to_period("M")
    monthly = filtered.groupby("year_month").agg({
        "actual_worth": "mean",
        "transaction_id": "count"
    }).rename(columns={"actual_worth": "avg_price", "transaction_id": "volume"}).reset_index()

    # === Step 3: Calculate YoY and QoQ ===
    monthly["year_month"] = monthly["year_month"].astype(str)
    monthly["avg_price_yoy"] = monthly["avg_price"].pct_change(periods=12) * 100
    monthly["avg_price_qoq"] = monthly["avg_price"].pct_change(periods=3) * 100
    monthly["volume_yoy"] = monthly["volume"].pct_change(periods=12) * 100
    monthly["volume_qoq"] = monthly["volume"].pct_change(periods=3) * 100

    # === Show Sample Metrics ===
    st.markdown("### 📊 Filtered Market Metrics")
    latest = monthly.dropna().iloc[-1]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📈 Avg Price YoY", f"{latest['avg_price_yoy']:.2f}%")
    col2.metric("📉 Avg Price QoQ", f"{latest['avg_price_qoq']:.2f}%")
    col3.metric("🏘️ Volume YoY", f"{latest['volume_yoy']:.2f}%")
    col4.metric("📦 Volume QoQ", f"{latest['volume_qoq']:.2f}%")

else:
    st.error("❌ Failed to load or filter data.")
