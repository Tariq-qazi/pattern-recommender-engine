import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

st.set_page_config(layout="wide")

@st.cache_data
def load_data():
    df = pd.read_parquet("transactions.parquet")
    df = df[df["actual_worth"].notna()]
    df["month"] = pd.to_datetime(df["instance_date"]).dt.month
    df["year"] = pd.to_datetime(df["instance_date"]).dt.year
    df["price_per_sqm"] = df["actual_worth"] / df["area_size"]
    df["offplan_flag"] = df["reg_type_en"] == "Off-Plan Properties"
    return df

@st.cache_data
def load_pattern_matrix():
    return pd.read_csv("PatternMatrix.csv")

def classify_change(val):
    if val > 5:
        return "Up"
    elif val < -5:
        return "Down"
    else:
        return "Flat"

def classify_offplan(pct):
    if pct > 0.5:
        return "High"
    elif pct > 0.2:
        return "Medium"
    else:
        return "Low"

def get_pattern_insight(qoq_price, yoy_price, qoq_volume, yoy_volume, offplan_pct):
    pattern = {
        "QoQ_Price": classify_change(qoq_price),
        "YoY_Price": classify_change(yoy_price),
        "QoQ_Volume": classify_change(qoq_volume),
        "YoY_Vol": classify_change(yoy_volume),
        "Offplan_Level": classify_offplan(offplan_pct),
    }
    match = pattern_matrix[
        (pattern_matrix["QoQ_Price"] == pattern["QoQ_Price"]) &
        (pattern_matrix["YoY_Price"] == pattern["YoY_Price"]) &
        (pattern_matrix["QoQ_Volume"] == pattern["QoQ_Volume"]) &
        (pattern_matrix["YoY_Vol"] == pattern["YoY_Vol"]) &
        (pattern_matrix["Offplan_Level"] == pattern["Offplan_Level"])
    ]
    return match.iloc[0] if not match.empty else None

# Load data
df = load_data()
pattern_matrix = load_pattern_matrix()

# Sidebar filters
st.sidebar.title("Filters")
areas = st.sidebar.multiselect("Area", options=sorted(df["area_name_en"].unique()))
property_types = st.sidebar.multiselect("Property Type", options=sorted(df["property_type_en"].unique()))
rooms = st.sidebar.multiselect("Rooms", options=sorted(df["rooms_en"].dropna().unique()))
year_range = st.sidebar.slider("Year Range", int(df["year"].min()), int(df["year"].max()), (2023, 2025))
month_range = st.sidebar.slider("Month Range", 1, 12, (1, 12))
budget = st.sidebar.slider("Budget AED", 500000, 10000000, (500000, 5000000))
user_type = st.sidebar.selectbox("User Type", ["Investor", "EndUser"])

# Filter data
filtered = df[
    df["year"].between(*year_range) &
    df["month"].between(*month_range) &
    df["actual_worth"].between(*budget)
]
if areas:
    filtered = filtered[filtered["area_name_en"].isin(areas)]
if property_types:
    filtered = filtered[filtered["property_type_en"].isin(property_types)]
if rooms:
    filtered = filtered[filtered["rooms_en"].isin(rooms)]

# Show match count
st.success(f"✅ {len(filtered):,} transactions matched.")

if len(filtered) < 20:
    st.warning("Not enough data to generate insights.")
    st.stop()

# KPI calculations
current = filtered[(filtered["year"] == year_range[1]) & (filtered["month"] == month_range[1])]
prev_q = filtered[(filtered["year"] == year_range[1]) & (filtered["month"] == month_range[0])]
prev_y = filtered[(filtered["year"] == year_range[0]) & (filtered["month"] == month_range[1])]

kpis = {
    "Price QoQ": 100 * ((current["actual_worth"].mean() - prev_q["actual_worth"].mean()) / prev_q["actual_worth"].mean()),
    "Price YoY": 100 * ((current["actual_worth"].mean() - prev_y["actual_worth"].mean()) / prev_y["actual_worth"].mean()),
    "Volume QoQ": 100 * ((len(current) - len(prev_q)) / len(prev_q)),
    "Volume YoY": 100 * ((len(current) - len(prev_y)) / len(prev_y)),
    "Offplan Level": current["offplan_flag"].mean()
}

# Display Market Summary
tags = {
    "Price QoQ": classify_change(kpis["Price QoQ"]),
    "Price YoY": classify_change(kpis["Price YoY"]),
    "Volume QoQ": classify_change(kpis["Volume QoQ"]),
    "Volume YoY": classify_change(kpis["Volume YoY"]),
    "Offplan": classify_offplan(kpis["Offplan Level"])
}

st.header("🏙️ Dubai Real Estate Pattern Recommender")
st.subheader("📊 Market Tags")

cols = st.columns(5)
cols[0].metric("🏷️ Price QoQ", tags["Price QoQ"])
cols[1].metric("🏷️ Price YoY", tags["Price YoY"])
cols[2].metric("🏷️ Volume QoQ", tags["Volume QoQ"])
cols[3].metric("🏷️ Volume YoY", tags["Volume YoY"])
cols[4].metric("🏷️ Offplan Level", tags["Offplan"])

# Match pattern
matched_pattern = get_pattern_insight(kpis["Price QoQ"], kpis["Price YoY"], kpis["Volume QoQ"], kpis["Volume YoY"], kpis["Offplan Level"])

if matched_pattern is not None:
    st.subheader("💡 Insights")
    st.markdown(matched_pattern[f"Insight_{user_type}"])
else:
    st.warning("No matching pattern found for current market metrics.")
