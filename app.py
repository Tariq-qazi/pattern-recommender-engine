# app.py — Final Grouped Area Recommendation App

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Grouped Area Recommender", layout="wide")
st.title("📊 Dubai Smart Buy Zones – Grouped by Strategy")

# Load tagged patterns and pattern matrix
@st.cache_data
def load_data():
    tagged = pd.read_csv("batch_tagged_output.csv")
    matrix = pd.read_csv("PatternMatrix_with_Buckets.csv")

    # Fix line breaks in matrix columns
    for col in ["Insight_Investor", "Recommendation_Investor", "Insight_EndUser", "Recommendation_EndUser"]:
        matrix[col] = matrix[col].astype(str).apply(lambda x: x.replace("\\n", "\n"))

    # Merge bucket info
    merged = pd.merge(tagged, matrix[["PatternID", "Bucket"]], left_on="pattern_id", right_on="PatternID", how="left")
    return merged, matrix

df, pattern_matrix = load_data()

# Sidebar filters
st.sidebar.header("🎯 Filter Criteria")
unit_type = st.sidebar.selectbox("Unit Type", df["type"].unique())
room_count = st.sidebar.selectbox("Bedrooms", df["rooms"].unique())
view_mode = st.sidebar.radio("Insights For", ["Investor", "EndUser"])
submit = st.sidebar.button("🔍 Recommend Zones")

# Run analysis
if submit:
    filtered = df[
        (df["type"] == unit_type) &
        (df["rooms"] == room_count)
    ]

    if filtered.empty:
        st.warning("❌ No data matched your criteria.")
    else:
        st.success(f"✅ {len(filtered)} matched rows found.")
        grouped = filtered.groupby("Bucket")

        for bucket, group in grouped:
            st.subheader(f"{bucket} – {len(group)} matches")
            top = group.sort_values("quarter", ascending=False).drop_duplicates(subset=["area"]).head(10)

            st.markdown("**Top Area Picks:**")
            st.table(top[["area", "quarter", "pattern_id"]])

            sample_pid = top.iloc[0]["pattern_id"]
            row = pattern_matrix[pattern_matrix["PatternID"] == sample_pid].iloc[0]

            st.markdown(f"**Insight ({view_mode}):**\n\n" + row[f"Insight_{view_mode}"])
            st.markdown(f"**Recommendation ({view_mode}):**\n\n" + row[f"Recommendation_{view_mode}"])

else:
    st.info("Select your filters and click '🔍 Recommend Zones' to begin.")
