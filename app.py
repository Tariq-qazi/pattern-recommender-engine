import streamlit as st
import pandas as pd
import gdown
import os

st.set_page_config(page_title="🏙️ Dubai Real Estate Pattern Recommender", layout="wide")
st.title("🏙️ Dubai Real Estate Pattern Recommender")

@st.cache_data(show_spinner="📥 Loading real estate data...")
def load_data():
    file_path = "transactions.parquet"
    if not os.path.exists(file_path):
        st.info("Downloading dataset from Google Drive...")
        url = "https://drive.google.com/uc?id=1R71kyvSYgRSMl8o4bfXhV9FH1N50D2uJ"
        gdown.download(url, file_path, quiet=False)
    return pd.read_parquet(file_path)

df = load_data()

if df.empty:
    st.error("❌ Dataframe is empty. Please check your source file or format.")
    st.stop()

st.success("✅ Data loaded successfully from cache or Drive")

# Debug: Show available columns
st.write("🧾 Available columns:", df.columns.tolist())

# Sidebar filters (updated)
st.sidebar.header("🔍 Filter Properties")
area = st.sidebar.multiselect("Area", sorted(df["area_name_en"].dropna().unique()))
prop_type = st.sidebar.multiselect("Property Type", sorted(df["property_type_en"].dropna().unique()))
bedrooms = st.sidebar.multiselect("Bedrooms", sorted(df["rooms_en"].dropna().unique()))
budget = st.sidebar.slider("Max Budget (AED)",
                           int(df["actual_worth"].min()),
                           int(df["actual_worth"].max()),
                           int(df["actual_worth"].max()))

# Apply filters
filtered = df.copy()
if area:
    filtered = filtered[filtered["area_name_en"].isin(area)]
if prop_type:
    filtered = filtered[filtered["property_type_en"].isin(prop_type)]
if bedrooms:
    filtered = filtered[filtered["rooms_en"].isin(bedrooms)]
filtered = filtered[filtered["actual_worth"] <= budget]

st.subheader(f"🗂️ Filtered Results: {len(filtered)} Properties")
st.dataframe(filtered, use_container_width=True)
