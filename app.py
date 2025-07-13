# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import gdown
import os

st.set_page_config(page_title="📊 Smart Buy Recommender", layout="wide")
st.title("🏙️ Dubai Real Estate - Smart Buy Recommender")

# =====================
# Load Dataset
# =====================
@st.cache_data
def load_data():
    path = "pattern_tagged_data.csv"
    if not os.path.exists(path):
        gdown.download("https://drive.google.com/uc?id=1ZPTeDNj_7Dg9R5cysYF_6RZtaHOD6WxZ", path, quiet=False)
    df = pd.read_csv(path, parse_dates=["Quarter"])
    return df

# =====================
# Pattern Buckets Mapping
# =====================
def assign_bucket(pattern_id):
    p = int(pattern_id.replace("P", ""))
    if p in [1, 50, 51, 52, 53]: return "🟢 Strong Buy"
    elif p in range(2,6) or p in range(30,35) or p in [38, 39, 40]: return "🟡 Cautious Buy / Watch"
    elif p in range(6,11) or p in [32, 41, 54, 55, 56, 57]: return "🟠 Hold / Neutral"
    elif p in range(11,16) or p in range(35,38) or p in range(43,50) or p in range(58,64): return "🔴 Caution / Avoid"
    elif p in range(16,21) or p in [42, 44, 60, 61]: return "🔁 Rotation Candidate"
    elif p in range(21,30) or p in [62]: return "🧭 Strategic Waitlist"
    else: return "❓ Unclassified"

# =====================
# Sidebar Filters
# =====================
df = load_data()
df["PatternBucket"] = df["PatternID"].apply(assign_bucket)

st.sidebar.header("🎯 Filter Options")
all_unit_types = sorted(df["property_type_en"].dropna().unique())
all_room_counts = sorted(df["rooms_en"].dropna().unique())

selected_type = st.sidebar.selectbox("Unit Type", options=all_unit_types)
selected_rooms = st.sidebar.selectbox("Bedrooms", options=all_room_counts)
max_budget = st.sidebar.number_input("Max Budget (AED)", value=2_000_000, step=100_000)

# =====================
# Filter Data
# =====================
filtered = df[
    (df["property_type_en"] == selected_type) &
    (df["rooms_en"] == selected_rooms) &
    (df["actual_worth"] <= max_budget)
]

latest_quarter = filtered["Quarter"].max()
latest = filtered[filtered["Quarter"] == latest_quarter]

st.subheader(f"📅 Recommendations for {selected_rooms} BR {selected_type} (Q{latest_quarter.quarter}/ {latest_quarter.year})")
st.caption(f"Showing zones within your budget — grouped by pattern intelligence bucket")

# =====================
# Grouped Output
# =====================
for bucket in ["🟢 Strong Buy", "🟡 Cautious Buy / Watch", "🧭 Strategic Waitlist", "🔁 Rotation Candidate", "🟠 Hold / Neutral", "🔴 Caution / Avoid"]:
    sub = latest[latest["PatternBucket"] == bucket]
    if not sub.empty:
        top = sub.sort_values("actual_worth").groupby("area_name_en").first().reset_index()
        top = top.sort_values("actual_worth").head(10)
        with st.expander(f"{bucket} — Top {len(top)} Areas"):
            st.dataframe(top[["area_name_en", "actual_worth", "PatternID", "PatternBucket"]], use_container_width=True)
            fig = px.bar(top, x="area_name_en", y="actual_worth", title=f"{bucket} — Top Affordables", text_auto=True)
            st.plotly_chart(fig, use_container_width=True)

# =====================
# Footer
# =====================
st.markdown("""
---
Built with ❤️ using pattern intelligence. Want to explore more patterns or areas? [Contact us](mailto:info@serdal.ai)
""")
