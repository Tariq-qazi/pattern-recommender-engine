import streamlit as st
import pandas as pd

st.set_page_config(page_title="🏙️ Real Estate Grouped Recommendations", layout="wide")
st.title("🏙️ Real Estate Recommendation Explorer")

# ============
# Load Data
# ============
@st.cache_data
def load_data():
    tagged = pd.read_csv("batch_tagged_output.csv")
    matrix = pd.read_csv("PatternMatrix_with_Buckets.csv")
    matrix = matrix.rename(columns={"Bucket": "Pattern_Bucket"})  # Normalize column
    merged = pd.merge(tagged, matrix[["PatternID", "Pattern_Bucket"]], on="PatternID", how="left")
    return merged

df = load_data()

# =================
# Sidebar Filters
# =================
st.sidebar.header("🔍 Filters")

all_unit_types = df["UnitType"].dropna().unique().tolist()
unit_type = st.sidebar.selectbox("Unit Type", ["All"] + sorted(all_unit_types))

all_rooms = df["Rooms"].dropna().unique().tolist()
room = st.sidebar.selectbox("Bedrooms", ["All"] + sorted(all_rooms))

budget = st.sidebar.number_input("Max Budget (AED)", value=5_000_000, step=100_000)

run = st.sidebar.button("Run Analysis")

# ======================
# Main Recommendation
# ======================
if run:
    df_filtered = df.copy()
    if unit_type != "All":
        df_filtered = df_filtered[df_filtered["UnitType"] == unit_type]
    if room != "All":
        df_filtered = df_filtered[df_filtered["Rooms"] == room]
    df_filtered = df_filtered[df_filtered["Price_AED"] <= budget]

    st.success(f"✅ {len(df_filtered)} matching entries found.")

    grouped = df_filtered.groupby("Pattern_Bucket")

    for bucket, group in grouped:
        st.subheader(f"{bucket} — {len(group)} options")
        top_areas = group.groupby("Area").size().sort_values(ascending=False).head(10).reset_index()
        top_areas.columns = ["Area", "Matches"]
        st.write(top_areas)

        with st.expander("View Full Table"):
            st.dataframe(group.sort_values("Price_AED").reset_index(drop=True))
else:
    st.info("🎯 Select filters and click **Run Analysis** to begin.")
