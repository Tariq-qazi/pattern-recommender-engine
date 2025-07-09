import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Dubai Real Estate Pattern Recommender", layout="wide")
st.title("🏙️ Dubai Real Estate Pattern Recommender")

# === Step 1: Load data from local Parquet file ===
@st.cache_data
def load_data():
    file_path = "transactions_merged.parquet"
    if not os.path.exists(file_path):
        st.error("❌ Parquet file not found. Please upload 'transactions_merged.parquet' to the app folder.")
        return None
    df = pd.read_parquet(file_path)
    return df

# === Step 2: Load and filter the data ===
df = load_data()

if df is not None:
    st.success("✅ Parquet loaded from local cache")

    # Sidebar Filters
    st.sidebar.header("🔍 Filter Properties")
    area = st.sidebar.multiselect("Area", options=sorted(df["area"].dropna().unique()))
    prop_type = st.sidebar.multiselect("Property Type", options=sorted(df["property_type"].dropna().unique()))
    bedrooms = st.sidebar.multiselect("Bedrooms", options=sorted(df["bedrooms"].dropna().unique()))
    budget = st.sidebar.slider("Max Budget (AED)", int(df["price"].min()), int(df["price"].max()), int(df["price"].max()))

    # Apply filters
    filtered = df.copy()
    if area:
        filtered = filtered[filtered["area"].isin(area)]
    if prop_type:
        filtered = filtered[filtered["property_type"].isin(prop_type)]
    if bedrooms:
        filtered = filtered[filtered["bedrooms"].isin(bedrooms)]
    filtered = filtered[filtered["price"] <= budget]

    st.subheader(f"🗂️ Filtered Results: {len(filtered)} Properties")
    st.dataframe(filtered)
else:
    st.stop()
