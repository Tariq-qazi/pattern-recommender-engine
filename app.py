import streamlit as st
import pandas as pd
import gdown
import os

st.set_page_config(page_title="Dubai Real Estate Pattern Recommender", layout="wide")
st.title("🏙️ Dubai Real Estate Pattern Recommender")

# === Step 1: Load data from Google Drive as .parquet ===
@st.cache_data(show_spinner="📥 Loading real estate data from Drive...")
def load_data():
    file_path = "transactions_merged.parquet"
    if not os.path.exists(file_path):
        st.info("Downloading Parquet file...")
        url = "https://drive.google.com/uc?id=15kO9WvSnWbY4l9lpHwPYRhDmrwuiDjoI"
        gdown.download(url, file_path, quiet=False)
    return pd.read_parquet(file_path)

# === Step 2: Load data ===
try:
    df = load_data()
    st.success(f"✅ Loaded {len(df):,} rows of real estate data")

    # === Step 3: Sidebar filters ===
    st.sidebar.header("🔍 Filter Properties")
    if "area_name_en" in df.columns:
        area = st.sidebar.multiselect("Area", sorted(df["area_name_en"].dropna().unique()))
    else:
        st.sidebar.warning("⚠️ 'area_name_en' not found in dataset")
        area = []

    if "property_type_en" in df.columns:
        prop_type = st.sidebar.multiselect("Property Type", sorted(df["property_type_en"].dropna().unique()))
    else:
        prop_type = []

    if "rooms_en" in df.columns:
        bedrooms = st.sidebar.multiselect("Bedrooms", sorted(df["rooms_en"].dropna().unique()))
    else:
        bedrooms = []

    if "actual_worth" in df.columns:
        max_price = int(df["actual_worth"].dropna().max())
        budget = st.sidebar.slider("Max Budget (AED)", 0, max_price, max_price)
    else:
        budget = None

    # === Step 4: Apply filters ===
    filtered = df.copy()
    if area:
        filtered = filtered[filtered["area_name_en"].isin(area)]
    if prop_type:
        filtered = filtered[filtered["property_type_en"].isin(prop_type)]
    if bedrooms:
        filtered = filtered[filtered["rooms_en"].isin(bedrooms)]
    if budget is not None:
        filtered = filtered[filtered["actual_worth"] <= budget]

    st.subheader(f"🗂️ Filtered Results: {len(filtered):,} properties")
    st.dataframe(filtered)

except Exception as e:
    st.error("❌ Error loading Parquet file.")
    st.exception(e)
