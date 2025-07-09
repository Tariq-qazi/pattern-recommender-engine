import streamlit as st
import pandas as pd
import gdown
import os

st.set_page_config(page_title="Dubai Real Estate Pattern Recommender", layout="wide")
st.title("🏙️ Dubai Real Estate Pattern Recommender")

# === Step 1: Load full data from Parquet ===
@st.cache_data
def load_data():
    file_path = "transactions_merged.parquet"
    if not os.path.exists(file_path):
        with st.spinner("🔁 Downloading full dataset from Google Drive..."):
            url = "https://drive.google.com/uc?id=15kO9WvSnWbY4l9lpHwPYRhDmrwuiDjoI"
            gdown.download(url, file_path, quiet=False)
    return pd.read_parquet(file_path)

# === Step 2: Read dataset ===
with st.spinner("📥 Loading data..."):
    df = load_data()

if df is not None and not df.empty:
    st.success("✅ Full Parquet dataset loaded successfully!")

    # === Step 3: Sidebar filters ===
    st.sidebar.header("🔍 Filter Properties")

    area = st.sidebar.multiselect("Area", sorted(df["area_name_en"].dropna().unique()))
    prop_type = st.sidebar.multiselect("Property Type", sorted(df["property_type_en"].dropna().unique()))
    bedrooms = st.sidebar.multiselect("Bedrooms", sorted(df["rooms_en"].dropna().unique()))
    max_price = int(df["actual_worth"].dropna().max())
    budget = st.sidebar.slider("Max Budget (AED)", 0, max_price, max_price)

    # === Step 4: Apply filters ===
    filtered = df.copy()
    if area:
        filtered = filtered[filtered["area_name_en"].isin(area)]
    if prop_type:
        filtered = filtered[filtered["property_type_en"].isin(prop_type)]
    if bedrooms:
        filtered = filtered[filtered["rooms_en"].isin(bedrooms)]
    filtered = filtered[filtered["actual_worth"] <= budget]

    # === Step 5: Display results ===
    st.subheader(f"🗂️ Filtered Results: {len(filtered)} Properties")

    if not filtered.empty:
        st.dataframe(filtered.head(1000))  # Display only first 1000 rows
    else:
        st.warning("⚠️ No properties found for the selected filters.")

else:
    st.error("❌ Failed to load data or data is empty.")
