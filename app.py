import streamlit as st
import pandas as pd
import gdown
import os

st.set_page_config(page_title="🏙️ Dubai Real Estate Pattern Recommender", layout="wide")
st.title("🏙️ Dubai Real Estate Pattern Recommender")

# === Step 1: Load full parquet file from Google Drive (only once) ===
@st.cache_data
def load_data():
    file_path = "transactions_merged.parquet"
    if not os.path.exists(file_path):
        st.info("Downloading large dataset from Google Drive...")
        url = "https://drive.google.com/uc?id=15kO9WvSnWbY4l9lpHwPYRhDmrwuiDjoI"
        gdown.download(url, file_path, quiet=False)
    df = pd.read_parquet(file_path)
    return df

# === Step 2: Load ===
df = load_data()
st.success("✅ Full dataset loaded from cache")

# === Step 3: Sidebar Filters ===
st.sidebar.header("🔍 Filter Properties")

# Column mappings (based on your uploaded column headers)
area_col = "area_name_en"
prop_type_col = "property_type_en"
bedroom_col = "rooms_en"
price_col = "actual_worth"

area = st.sidebar.multiselect("Area", options=sorted(df[area_col].dropna().unique()))
prop_type = st.sidebar.multiselect("Property Type", options=sorted(df[prop_type_col].dropna().unique()))
bedrooms = st.sidebar.multiselect("Bedrooms", options=sorted(df[bedroom_col].dropna().unique()))
budget = st.sidebar.slider("Max Budget (AED)", 
                           int(df[price_col].min()), 
                           int(df[price_col].max()), 
                           int(df[price_col].max()))

# === Step 4: Apply filters ===
filtered = df.copy()
if area:
    filtered = filtered[filtered[area_col].isin(area)]
if prop_type:
    filtered = filtered[filtered[prop_type_col].isin(prop_type)]
if bedrooms:
    filtered = filtered[filtered[bedroom_col].isin(bedrooms)]
filtered = filtered[filtered[price_col] <= budget]

st.subheader(f"🗂️ Filtered Results: {len(filtered):,} properties")
if len(filtered) == 0:
    st.warning("❗ No matching properties found. Try adjusting your filters.")
else:
    st.dataframe(filtered, use_container_width=True)

    st.download_button(
        label="📥 Download Filtered Data as CSV",
        data=filtered.to_csv(index=False),
        file_name="filtered_properties.csv",
        mime="text/csv",
    )
