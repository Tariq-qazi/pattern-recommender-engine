import streamlit as st
import pandas as pd
import gdown

st.set_page_config(page_title="Dubai Real Estate Pattern Recommender", layout="wide")
st.title("🏙️ Dubai Real Estate Pattern Recommender")

# === Step 1: Load data from Google Drive ===
@st.cache_data
def load_data():
    file_id = "1R71kyvSYgRSMl8o4bfXhV9FH1N50D2uJ"
    url = f"https://drive.google.com/uc?id={file_id}"
    output = "transactions.xlsx"
    gdown.download(url, output, quiet=False)
    df = pd.read_excel(output, engine="openpyxl")
    return df

# === Step 2: Load and filter the data ===
df = load_data()

if df is not None:
    st.success("✅ Excel loaded from Google Drive")

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
    st.error("❌ Failed to load data.")
