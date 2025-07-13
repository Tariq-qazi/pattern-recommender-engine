import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Grouped Area Recommendation", layout="wide")
st.title("🏘️ Dubai Real Estate – Smart Buy Groups")

# Load pattern matrix with buckets
@st.cache_data
def load_data():
    tagged = pd.read_csv("batch_tagged_output.csv")
    matrix = pd.read_csv("PatternMatrix_with_Buckets.csv")
    merged = pd.merge(tagged, matrix[["PatternID", "Bucket"]], left_on="pattern_id", right_on="PatternID", how="left")
    return merged, matrix

df, pattern_matrix = load_data()

# Sidebar filters
st.sidebar.header("🔍 Choose Buyer Criteria")
with st.sidebar.form("filter_form"):
    unit_type = st.selectbox("Unit Type", sorted(df["type"].dropna().unique()))
    room_count = st.selectbox("Bedrooms", sorted(df["rooms"].dropna().unique()))
    view_mode = st.radio("Insights For", ["Investor", "EndUser"])
    submitted = st.form_submit_button("Get Area Picks")

if submitted:
    # 📆 Get last two quarters
    all_quarters = sorted(df["quarter"].unique())
    latest_two = all_quarters[-2:]

    filtered = df[
        (df["type"] == unit_type) &
        (df["rooms"] == room_count) &
        (df["quarter"].isin(latest_two))
    ]

    if filtered.empty:
        st.warning("❌ No matching zones found for the latest quarters.")
    else:
        st.success(f"✅ {len(filtered)} zones matched for the last two quarters ({', '.join(latest_two)}).")

        # Rank and sort by pattern bucket
        bucket_order = [
            "🟢 Strong Buy",
            "🟡 Cautious Buy / Watch",
            "🟠 Hold / Neutral",
            "🔁 Rotation Candidate",
            "🧭 Strategic Waitlist",
            "🔴 Caution / Avoid",
            "❓ Unclassified"
        ]
        filtered["bucket_rank"] = filtered["Bucket"].apply(lambda b: bucket_order.index(b) if b in bucket_order else len(bucket_order))
        filtered = filtered.sort_values("bucket_rank")

        for bucket in bucket_order:
            group = filtered[filtered["Bucket"] == bucket]
            if not group.empty:
                st.subheader(f"{bucket} ({len(group)} areas)")
                for area in group["area"].drop_duplicates():
                    st.markdown(f"- {area}")

                sample = group.iloc[0]
                p_row = pattern_matrix[pattern_matrix["PatternID"] == sample["pattern_id"]].iloc[0]

                st.markdown(f"### 🧠 Insight ({view_mode}):")
                st.markdown(p_row[f"Insight_{view_mode}"])

                st.markdown(f"### ✅ Recommendation ({view_mode}):")
                import re
                
                raw_reco = p_row[f"Recommendation_{view_mode}"]
                cleaned_reco = raw_reco.replace("\\n", "\n")
                
                # Improved split: only split before emojis that typically start a new tip
                tip_lines = re.split(r"(?=\n?[🟢🟡🟠🔴🔁🧭✅🔍👉🏽📍🏠📦📈💡📌📊📣🛑⏳💰🧠🎯📎💼🏗️🏡🌟🧾📣🔍🧭🏞️🔓🔒🚀🔑🎯🧱🏢🏙️🛒🌆🗺️📦📈📉📄📂📎📊📉📈📌💼🪙🔍👀🎯🏗️📊🧭])", cleaned_reco)
                
                # Display tips
                for tip in tip_lines:
                    line = tip.strip()
                    if line:
                        st.write("• " + line)


                st.markdown("---")

else:
    st.info("🎯 Select filters and click 'Get Area Picks' to explore opportunities.")
