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
        "area_name_en", "property_type_en", "rooms_en", "actual_worth", "instance_date"
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

# Persona selector (Investor vs EndUser)
persona = st.selectbox("🎯 You are an...", ["EndUser", "Investor"])

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
# 4. LOAD PATTERN MATRIX
# =======================
@st.cache_data
def load_pattern_matrix():
    url = "https://raw.githubusercontent.com/Tariq-qazi/Insights/refs/heads/main/PatternMatrix.csv"
    return pd.read_csv(url)

pattern_matrix = load_pattern_matrix()

# =======================
# 5. MATCHING LOGIC
# =======================
def classify_change(val):
    if val > 5:
        return "Up"
    elif val < -5:
        return "Down"
    else:
        return "Stable"

def get_pattern_insight(qoq_price, yoy_price, qoq_volume, yoy_volume, offplan_pct):
    pattern = {
        "QoQ_Price": classify_change(qoq_price),
        "YoY_Price": classify_change(yoy_price),
        "QoQ_Volume": classify_change(qoq_volume),
        "YoY_Vol": classify_change(yoy_volume),
        "Offplan_Level": "Medium"  # Fixed or from data
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
# 6. MAIN ANALYSIS BLOCK
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

        # ========== METRICS ==========
        st.subheader("📊 Market Summary Metrics")
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
        else:
            st.warning("Not enough data for trends.")
            st.stop()

        # ========== DASHBOARD BLOCK ==========
        st.subheader("📋 Market Dashboard Summary")

        avg_price = df_filtered["actual_worth"].mean()
        avg_area = df_filtered["procedure_area"].mean() if "procedure_area" in df_filtered.columns else None
        total_volume = len(df_filtered)
        price_per_sqm = avg_price / avg_area if avg_area and avg_area > 0 else None

        pattern = get_pattern_insight(qoq_price, yoy_price, qoq_volume, yoy_volume, offplan_pct=0.3)

        # Labels
        def color_text(val):
            return f":green[{val}]" if val == "Up" else f":red[{val}]" if val == "Down" else f":gray[{val}]"

        # Top Row
        c1, c2, c3, c4, c5 = st.columns([1.5, 1.2, 1.2, 1.5, 1.5])
        c1.markdown(f"### Quarter Price\n{color_text(classify_change(qoq_price))}")
        c2.markdown(f"### You are\n**{persona}**")
        c3.markdown(f"### Looking for\n**{', '.join(selected_rooms) or 'Any'}**")
        c4.markdown(f"### In\n**{', '.join(selected_areas) or 'All Areas'}**")
        c5.markdown(f"### Avg Price\n**{avg_price/1e6:.2f}M AED**")

        # Middle Row
        m1, m2, m3 = st.columns([1.5, 3, 1.5])
        m1.markdown(f"### Quarter Sales\n{color_text(classify_change(qoq_volume))}")
        m2.markdown("### **Insights**\n" + (pattern[f"Insight_{persona}"] if pattern is not None else "No insight available."))
        m3.markdown(f"### Volume\n**{total_volume}**")

        # Lower Row
        b1, b2, b3 = st.columns([1.5, 3, 1.5])
        b1.markdown(f"### Yearly Price\n{color_text(classify_change(yoy_price))}")
        b2.markdown("### **Recommendation**\n" + (f"✅ **{pattern[f'Recommendation_{persona}']}**" if pattern is not None else "No recommendation."))
        b3.markdown(f"### Avg Area\n**{avg_area:.2f} sqm**" if avg_area else "N/A")

        if price_per_sqm:
            st.markdown(f"### 💰 Price per Sqm: **{price_per_sqm:,.2f} AED**")
else:
    st.info("🎯 Use the filters and click 'Run Analysis' to begin.")
