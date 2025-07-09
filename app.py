import streamlit as st
import pandas as pd
import gdown
import os
import tempfile

st.set_page_config(page_title="Dubai Real Estate Pattern Recommender", layout="wide")
st.title("🏙️ Dubai Real Estate Pattern Recommender")

@st.cache_data
def load_data():
    file_path = os.path.join(tempfile.gettempdir(), "transactions_merged.parquet")
    if not os.path.exists(file_path):
        st.info("⏬ Downloading dataset from Google Drive...")
        url = "https://drive.google.com/uc?id=15kO9WvSnWbY4l9lpHwPYRhDmrwuiDjoI"
        gdown.download(url, file_path, quiet=False)
    df = pd.read_parquet(file_path)
    df['instance_date'] = pd.to_datetime(df['instance_date'], errors='coerce')
    df = df.dropna(subset=['instance_date'])
    return df

# Step 1: Load file (but don’t run filters until user clicks)
with st.spinner("Loading data..."):
    df = load_data()
    st.success("✅ Dataset loaded successfully.")

# Step 2: Wait for user trigger
run_app = st.button("🚀 Start Exploring & Filtering")

if run_app:
    st.sidebar.header("🔍 Filter Properties")
    area = st.sidebar.multiselect("Area", options=sorted(df["area_name_en"].dropna().unique()))
    prop_type = st.sidebar.multiselect("Property Type", options=sorted(df["property_type_en"].dropna().unique()))
    bedrooms = st.sidebar.multiselect("Bedrooms", options=sorted(df["rooms_en"].dropna().unique()))
    budget = st.sidebar.slider("Max Budget (AED)", int(df["actual_worth"].min()), int(df["actual_worth"].max()), int(df["actual_worth"].max()))

    filtered = df.copy()
    if area:
        filtered = filtered[filtered["area_name_en"].isin(area)]
    if prop_type:
        filtered = filtered[filtered["property_type_en"].isin(prop_type)]
    if bedrooms:
        filtered = filtered[filtered["rooms_en"].isin(bedrooms)]
    filtered = filtered[filtered["actual_worth"] <= budget]

    st.subheader(f"🗂️ Filtered Results: {len(filtered)} Properties")

    if len(filtered) > 0:
        st.dataframe(filtered.sample(min(1000, len(filtered))))  # show sample only
    else:
        st.warning("No matching properties found.")

else:
    st.info("Click the **Start** button above to explore properties.")
