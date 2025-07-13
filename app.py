import streamlit as st
import pandas as pd
import plotly.express as px
import gdown
import os

st.set_page_config(page_title="Grouped Area Recommendation", layout="wide")
st.title("🏘️ Dubai Real Estate – Smart Buy Groups")

# Load filtered metadata
@st.cache_data
def get_filter_metadata():
    file_path = "transactions.parquet"
    if not os.path.exists(file_path):
        gdown.download("https://drive.google.com/uc?id=15kO9WvSnWbY4l9lpHwPYRhDmrwuiDjoI", file_path, quiet=False)
    df = pd.read_parquet(file_path, columns=["area_name_en", "property_type_en", "rooms_en", "actual_worth"])
    return {
        "areas": sorted(df["area_name_en"].dropna().unique()),
        "types": sorted(df["property_type_en"].dropna().unique()),
        "rooms": sorted(df["rooms_en"].dropna().unique()),
        "min_price": int(df["actual_worth"].min()),
        "max_price": int(df["actual_worth"].max())
    }

filters = get_filter_metadata()

# Sidebar filters
st.sidebar.header("🔍 Choose Buyer Criteria")
with st.sidebar.form("filter_form"):
    unit_type = st.selectbox("Unit Type", filters["types"])
    room_count = st.selectbox("Bedrooms", filters["rooms"])
    budget = st.number_input("Max Budget (AED)", value=filters["max_price"], step=100000)
    view_mode = st.radio("Insights For", ["Investor", "EndUser"])
    submitted = st.form_submit_button("Get Area Picks")

# Load pattern matrix with bucket
@st.cache_data
def load_matrix():
    df = pd.read_csv("PatternMatrix_with_Buckets.csv")
    df.columns = df.columns.str.strip()  # Remove leading/trailing spaces
    for col in ["Insight_Investor", "Recommendation_Investor", "Insight_EndUser", "Recommendation_EndUser"]:
        df[col] = df[col].astype(str).apply(lambda x: x.replace("\\n", "\n"))
    return df

pattern_df = load_matrix()

# Load area patterns and merge buckets
@st.cache_data
def load_area_patterns():
    tagged = pd.read_csv("batch_tagged_output.csv")
    tagged.columns = tagged.columns.str.strip()
    if "pattern_id" not in tagged.columns:
        raise ValueError("❌ 'pattern_id' column not found in batch_tagged_output.csv")

    matrix = pd.read_csv("PatternMatrix_with_Buckets.csv")
    matrix.columns = matrix.columns.str.strip()

    merged = pd.merge(
        tagged,
        matrix[["PatternID", "Bucket"]],
        how="left",
        left_on="pattern_id",
        right_on="PatternID"
    )
    return merged

area_data = load_area_patterns()

# Filter by unit type and room
if submitted:
    matched = area_data[
        (area_data["unit_type"] == unit_type) &
        (area_data["bedrooms"] == room_count)
    ]

    if matched.empty:
        st.warning("❌ No matching zones found within your criteria.")
    else:
        st.success(f"✅ {len(matched)} zones matched your filters.")

        # Group by bucket
        grouped = matched.groupby("Bucket")
        for bucket, group in grouped:
            st.subheader(f"{bucket} ({len(group)} zones)")

            top = group.sort_values("area").head(10)
            st.markdown("**Top Recommendations:**")
            st.table(top[["area", "pattern_id"]])

            sample_pid = top.iloc[0]["pattern_id"]
            p_row = pattern_df[pattern_df["PatternID"] == sample_pid].iloc[0]
            st.markdown(f"**Representative Insight ({view_mode}):**\n\n" + p_row[f"Insight_{view_mode}"])
            st.markdown(f"**Recommendation ({view_mode}):**\n\n" + p_row[f"Recommendation_{view_mode}"])

else:
    st.info("🎯 Select filters and click 'Get Area Picks' to explore opportunities.")
