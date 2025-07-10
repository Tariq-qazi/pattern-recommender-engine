import streamlit as st
import pandas as pd
import numpy as np
import gdown
import os
from datetime import datetime

st.set_page_config(page_title="Dubai Real Estate Recommender", layout="wide")

# ========= Load Metadata =========
@st.cache_data
def get_filter_metadata():
    file_path = "transactions.parquet"
    if not os.path.exists(file_path):
        gdown.download("https://drive.google.com/uc?id=15kO9WvSnWbY4l9lpHwPYRhDmrwuiDjoI", file_path, quiet=False)
    df = pd.read_parquet(file_path, columns=[
        "area_name_en", "property_type_en", "rooms_en", "actual_worth", "instance_date", "size_sqm", "offplan"
    ])
    df["instance_date"] = pd.to_datetime(df["instance_date"], errors="coerce")
    return df

df = get_filter_metadata()

# ========= Sidebar Filters =========
st.sidebar.header("📊 Filter Options")
areas = st.sidebar.multiselect("Select Area", sorted(df["area_name_en"].dropna().unique()))
types = st.sidebar.multiselect("Property Type", sorted(df["property_type_en"].dropna().unique()))
rooms = st.sidebar.multiselect("Bedrooms", sorted(df["rooms_en"].dropna().unique()))
persona = st.sidebar.radio("Are you an:", ["EndUser", "Investor"])

min_year, max_year = df["instance_date"].dt.year.min(), df["instance_date"].dt.year.max()
year_from = st.sidebar.slider("From Year", min_year, max_year, min_year)
year_to = st.sidebar.slider("To Year", min_year, max_year, max_year)
month_from = st.sidebar.slider("From Month", 1, 12, 1)
month_to = st.sidebar.slider("To Month", 1, 12, 12)

budget = st.sidebar.number_input("Max Budget (AED)", min_value=100000, max_value=10000000, value=5000000, step=100000)

run = st.sidebar.button("🚀 Run Analysis")

# ========= Data Filtering =========
if run:
    st.title("🏙️ Dubai Real Estate Market Dashboard")

    mask = (df["actual_worth"] <= budget) & \
           (df["instance_date"].dt.year.between(year_from, year_to)) & \
           (df["instance_date"].dt.month.between(month_from, month_to))

    if areas: mask &= df["area_name_en"].isin(areas)
    if types: mask &= df["property_type_en"].isin(types)
    if rooms: mask &= df["rooms_en"].isin(rooms)

    filtered = df[mask].copy()
    filtered["quarter"] = filtered["instance_date"].dt.to_period("Q")
    filtered["year"] = filtered["instance_date"].dt.to_period("Y")

    # ========= Metrics Calculation =========
    grouped = filtered.groupby("quarter").agg({
        "actual_worth": "mean",
        "transaction_id": "count"
    }).rename(columns={"actual_worth": "avg_price", "transaction_id": "volume"}).dropna()

    if len(grouped) >= 2:
        qoq_price = grouped["avg_price"].pct_change().iloc[-1] * 100
        qoq_vol = grouped["volume"].pct_change().iloc[-1] * 100
    else:
        qoq_price, qoq_vol = 0, 0

    grouped_y = filtered.groupby("year").agg({
        "actual_worth": "mean",
        "transaction_id": "count"
    }).rename(columns={"actual_worth": "avg_price", "transaction_id": "volume"}).dropna()

    if len(grouped_y) >= 2:
        yoy_price = grouped_y["avg_price"].pct_change().iloc[-1] * 100
        yoy_vol = grouped_y["volume"].pct_change().iloc[-1] * 100
    else:
        yoy_price, yoy_vol = 0, 0

    avg_price = filtered["actual_worth"].mean()
    avg_size = filtered["size_sqm"].mean()
    price_per_sqm = avg_price / avg_size if avg_size else 0
    total_vol = filtered.shape[0]

    # ========= Dashboard =========
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📈 Quarter Price Movement", "Up" if qoq_price > 0 else "Down", f"{qoq_price:.1f}%")
    col2.metric("📉 Quarter Sales Movement", "Up" if qoq_vol > 0 else "Down", f"{qoq_vol:.1f}%")
    col3.metric("📈 Yearly Price Movement", "Up" if yoy_price > 0 else "Down", f"{yoy_price:.1f}%")
    col4.metric("📉 Yearly Sales Movement", "Up" if yoy_vol > 0 else "Down", f"{yoy_vol:.1f}%")

    st.markdown("---")

    col5, col6, col7 = st.columns(3)
    col5.metric("💰 Avg. Price", f"{avg_price/1e6:.2f}M AED")
    col6.metric("📊 Total Volume", total_vol)
    col7.metric("📐 Avg. Size", f"{avg_size:.2f} sqm")

    col8, col9 = st.columns(2)
    col8.metric("🏷️ Price per Sqm", f"{price_per_sqm/1e3:.2f}K AED")
    
    if persona == "EndUser":
        col9.markdown("### ✅ Recommendation")
        col9.success("Buy – Ideal Moment")
        st.info("💡 *Ideal personal entry window — prices rising but not inflated.*")
    else:
        col9.markdown("### 📊 Recommendation")
        col9.warning("Monitor – Volume Weak")
        st.info("💡 *Prices improving but volume soft — track market confidence before entry.*")
else:
    st.info("ℹ️ Adjust filters on the left and click **Run Analysis** to begin.")
