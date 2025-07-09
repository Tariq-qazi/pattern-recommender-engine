import streamlit as st
import pandas as pd
import requests
import io

# === Load Excel from Google Drive ===
FILE_ID = "1R71kyvSYgRSMl8o4bfXhV9FH1N50D2uJ"
url = f"https://drive.google.com/uc?export=download&id={FILE_ID}"

@st.cache_data
def load_data():
    response = requests.get(url)
    if response.status_code != 200:
        st.error("Failed to fetch the data from Google Drive.")
        return None
    file_bytes = io.BytesIO(response.content)
    df = pd.read_excel(file_bytes)
    return df

# === Load data ===
df = load_data()
if df is not None:
    st.title("Dubai Real Estate Pattern Recommender")
    st.success("Data loaded successfully from Google Drive!")

    # === Show filters ===
    st.sidebar.header("Apply Filters")
    area = st.sidebar.multiselect("Area", options=sorted(df["area"].dropna().unique()))
    property_type = st.sidebar.multiselect("Property Type", options=sorted(df["property_type"].dropna().unique()))
    bedrooms = st.sidebar.multiselect("Bedrooms", options=sorted(df["bedrooms"].dropna().unique()))
    budget = st.sidebar.slider("Max Budget (AED)", int(df["price"].min()), int(df["price"].max()), int(df["price"].max()))

    # === Apply filters ===
    filtered = df.copy()
    if area: filtered = filtered[filtered["area"].isin(area)]
    if property_type: filtered = filtered[filtered["property_type"].isin(property_type)]
    if bedrooms: filtered = filtered[filtered["bedrooms"].isin(bedrooms)]
    filtered = filtered[filtered["price"] <= budget]

    # === Display results ===
    st.subheader(f"Filtered Properties: {len(filtered)}")
    st.dataframe(filtered)

    # (Next: Add QoQ/YoY logic, match pattern, return recommendation...)

else:
    st.warning("Waiting for data to load...")
