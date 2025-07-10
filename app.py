import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

st.set_page_config(layout="wide")

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

# Load the pattern matrix CSV from GitHub
@st.cache_data

def load_pattern_matrix():
    url = "https://raw.githubusercontent.com/Tariq-qazi/Insights/refs/heads/main/PatternMatrix.csv"
    pattern_df = pd.read_csv(url)
    return pattern_df

pattern_matrix = load_pattern_matrix()

# Helper to bin percentage changes
def classify_change(val):
    if val > 5:
        return "Up"
    elif val < -5:
        return "Down"
    else:
        return "Stable"

# Helper to bin off-plan levels
def classify_offplan(pct):
    if pct > 0.5:
        return "High"
    elif pct > 0.2:
        return "Medium"
    else:
        return "Low"

# Function to generate a PatternID and get insight
@st.cache_data

def get_pattern_insight(qoq_price, yoy_price, qoq_volume, yoy_volume, offplan_pct):
    pattern = {
        "QoQ_Price": classify_change(qoq_price),
        "YoY_Price": classify_change(yoy_price),
        "QoQ_Volume": classify_change(qoq_volume),
        "YoY_Vol": classify_change(yoy_volume),
        "Offplan_Level": classify_offplan(offplan_pct),
    }

    match = pattern_matrix[
        (pattern_matrix["QoQ_Price"] == pattern["QoQ_Price"])
        & (pattern_matrix["YoY_Price"] == pattern["YoY_Price"])
        & (pattern_matrix["QoQ_Volume"] == pattern["QoQ_Volume"])
        & (pattern_matrix["YoY_Vol"] == pattern["YoY_Vol"])
        & (pattern_matrix["Offplan_Level"] == pattern["Offplan_Level"])
    ]

    if not match.empty:
        return match.iloc[0]
    else:
        return None

st.title("🏙️ Dubai Real Estate Pattern Recommender")

# Filters
st.sidebar.header("🔍 Property Filters")
areas = st.sidebar.multiselect("Area", options=df["area"].unique())
unit_types = st.sidebar.multiselect("Property Type", options=df["unit_type"].unique())
beds = st.sidebar.multiselect("Bedrooms", options=df["bedrooms"].unique())
max_price = st.sidebar.slider("Max Budget (AED)", 1, int(df["price_aed"].max()), int(df["price_aed"].max()))
date_range = st.sidebar.date_input("Transaction Date Range", value=(df["instance_date"].min(), df["instance_date"].max()))

# Apply filters
filtered_df = df.copy()
if areas:
    filtered_df = filtered_df[filtered_df["area"].isin(areas)]
if unit_types:
    filtered_df = filtered_df[filtered_df["unit_type"].isin(unit_types)]
if beds:
    filtered_df = filtered_df[filtered_df["bedrooms"].isin(beds)]
if max_price:
    filtered_df = filtered_df[filtered_df["price_aed"] <= max_price]
if date_range:
    filtered_df = filtered_df[(filtered_df["instance_date"] >= pd.to_datetime(date_range[0])) & (filtered_df["instance_date"] <= pd.to_datetime(date_range[1]))]

# Show summary
st.success(f"✅ {len(filtered_df)} transactions matched.")

# Calculate metrics
qoq_price = filtered_df["price_aed"].pct_change(1).mean() * 100
qoq_volume = filtered_df.resample("Q", on="instance_date").size().pct_change(1).mean() * 100
yoy_price = filtered_df["price_aed"].pct_change(4).mean() * 100
yoy_volume = filtered_df.resample("Y", on="instance_date").size().pct_change(1).mean() * 100
offplan_pct = filtered_df["offplan"].mean()

# Show summary metrics
st.subheader("📊 Market Summary Metrics")
col1, col2, col3, col4 = st.columns(4)
col1.metric("🟧 Price QoQ", f"{qoq_price:.1f}%")
col2.metric("🟨 Price YoY", f"{yoy_price:.1f}%")
col3.metric("🟪 Volume QoQ", f"{qoq_volume:.1f}%")
col4.metric("📈 Volume YoY", f"{yoy_volume:.1f}%")

# Pattern recommendation
pattern = get_pattern_insight(qoq_price, yoy_price, qoq_volume, yoy_volume, offplan_pct)

if pattern is not None:
    st.subheader("📌 Matched Market Pattern")
    st.markdown(f"**Pattern ID:** `{pattern['PatternID']}`")
    st.markdown(f"**Investor Insight:** {pattern['Insight_Investor']}")
    st.markdown(f"**Investor Recommendation:** {pattern['Recommendation_Investor']}")
    st.markdown(f"**End User Insight:** {pattern['Insight_EndUser']}")
    st.markdown(f"**End User Recommendation:** {pattern['Recommendation_EndUser']}")
else:
    st.warning("No matching pattern found for the given market conditions.")
