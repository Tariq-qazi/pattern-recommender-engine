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
        "area_name_en", "property_type_en", "rooms_en", "actual_worth", "instance_date", "transaction_id"
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

    st.markdown("**💰 Budget (AED)**")
    min_budget = st.number_input("Min Budget", value=filters["min_price"], step=10000)
    max_budget = st.number_input("Max Budget", value=filters["max_price"], step=10000)

    st.markdown("**📆 Date Range**")
    start_year = st.slider("Start Year", 2015, 2025, filters["min_date"].year)
    start_month = st.slider("Start Month", 1, 12, filters["min_date"].month)
    end_year = st.slider("End Year", 2015, 2025, filters["max_date"].year)
    end_month = st.slider("End Month", 1, 12, filters["max_date"].month)

    user_type = st.radio("🔘 I am a...", ["Investor", "End User"])

    submit = st.form_submit_button("Run Analysis")

# =======================
# 3. DATA LOADER
# =======================
@st.cache_data
def load_and_filter_data(areas, types, rooms, min_price, max_price, start_date, end_date):
    df = pd.read_parquet("transactions.parquet")
    df["instance_date"] = pd.to_datetime(df["instance_date"], errors="coerce")
    if areas:
        df = df[df["area_name_en"].isin(areas)]
    if types:
        df = df[df["property_type_en"].isin(types)]
    if rooms:
        df = df[df["rooms_en"].isin(rooms)]
    df = df[(df["actual_worth"] >= min_price) & (df["actual_worth"] <= max_price)]
    df = df[(df["instance_date"] >= start_date) & (df["instance_date"] <= end_date)]
    return df

@st.cache_data
def load_pattern_matrix():
    url = "https://raw.githubusercontent.com/Tariq-qazi/Insights/refs/heads/main/PatternMatrix.csv"
    return pd.read_csv(url)

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

# =======================
# 4. ANALYSIS EXECUTION
# =======================
if submit:
    start_date = datetime(start_year, start_month, 1)
    end_date = datetime(end_year, end_month, 28)

    with st.spinner("🔎 Running analysis..."):
        gc.collect()
        try:
            df_filtered = load_and_filter_data(
                selected_areas, selected_types, selected_rooms,
                min_budget, max_budget,
                start_date, end_date
            )
        except Exception as e:
            st.error(f"Error filtering data: {e}")
            st.stop()

        st.success(f"✅ {len(df_filtered)} transactions matched.")

        if len(df_filtered) > 300_000:
            st.warning("🚨 Too many records. Please narrow your filters.")
            st.stop()

        # =======================
        # 5. METRIC SUMMARY
        # =======================
        st.subheader("📊 Market Summary")
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

            col1, col2 = st.columns(2)
            col1.metric("🏷️ Price QoQ", f"{qoq_price:.1f}%")
            col1.metric("📈 Volume QoQ", f"{qoq_volume:.1f}%")
            col2.metric("🏷️ Price YoY", f"{yoy_price:.1f}%")
            col2.metric("📈 Volume YoY", f"{yoy_volume:.1f}%")
        else:
            st.warning("Not enough data to calculate QoQ/YoY trends.")

        # =======================
        # 6. PATTERN MATCH
        # =======================
        pattern_matrix = load_pattern_matrix()
        offplan_pct = 0.3  # Placeholder (can update later with actual logic)
        pattern = get_pattern_insight(qoq_price, yoy_price, qoq_volume, yoy_volume, offplan_pct)

        if pattern is not None:
            st.markdown("---")
            st.subheader("📌 Matched Market Pattern")
            st.markdown(f"**Pattern ID:** `{pattern['PatternID']}`")

            colL, colR = st.columns([1, 1])
            if user_type == "Investor":
                colL.markdown("#### 🧠 Investor Insight")
                colL.markdown(f"<div style='font-size:17px'>{pattern['Insight_Investor']}</div>", unsafe_allow_html=True)
                colR.markdown("#### ✅ Investor Recommendation")
                colR.markdown(f"<div style='font-size:17px'>{pattern['Recommendation_Investor']}</div>", unsafe_allow_html=True)
            else:
                colL.markdown("#### 🧠 End User Insight")
                colL.markdown(f"<div style='font-size:17px'>{pattern['Insight_EndUser']}</div>", unsafe_allow_html=True)
                colR.markdown("#### ✅ End User Recommendation")
                colR.markdown(f"<div style='font-size:17px'>{pattern['Recommendation_EndUser']}</div>", unsafe_allow_html=True)
        else:
            st.warning("No matching pattern found for current market metrics.")
else:
    st.info("🎯 Use the filters and click 'Run Analysis' to begin.")
