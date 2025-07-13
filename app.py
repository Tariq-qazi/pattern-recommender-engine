import streamlit as st
import pandas as pd

st.set_page_config(page_title="🏙️ Batch Real Estate Recommendation", layout="wide")

@st.cache_data
def load_tagged_data():
    df = pd.read_csv("batch_tagged_output.csv")
    return df

df = load_tagged_data()

st.title("🏙️ Dubai Batch Real Estate Recommender")

st.sidebar.header("🔍 Filter by Attributes")
area = st.sidebar.multiselect("Area", df["area"].unique())
ptype = st.sidebar.multiselect("Type", df["type"].unique())
rooms = st.sidebar.multiselect("Rooms", sorted(df["rooms"].unique()))
quarter = st.sidebar.multiselect("Quarter", sorted(df["quarter"].unique(), reverse=True))
audience = st.radio("🎯 Show Insight For", ["Investor", "EndUser"])

filtered = df.copy()
if area: filtered = filtered[filtered["area"].isin(area)]
if ptype: filtered = filtered[filtered["type"].isin(ptype)]
if rooms: filtered = filtered[filtered["rooms"].isin(rooms)]
if quarter: filtered = filtered[filtered["quarter"].isin(quarter)]

st.write(f"✅ {len(filtered)} matched combinations")

if not filtered.empty:
    insight_col = f"Insight_{audience}"
    reco_col = f"Recommendation_{audience}"

    for i, row in filtered.iterrows():
        st.markdown(f"### 📍 {row['area']} | {row['type']} | {row['rooms']} BR | {row['quarter']}")
        st.markdown(f"**Pattern Tags**: QoQ Price: `{row['QoQ_Price']}`, YoY Price: `{row['YoY_Price']}`, QoQ Vol: `{row['QoQ_Volume']}`, YoY Vol: `{row['YoY_Vol']}`, Offplan: `{row['Offplan_Level']}`")
        st.markdown(f"**🧠 Insight ({audience})**:\n\n{row[insight_col]}")
        st.markdown(f"**✅ Recommendation ({audience})**:\n\n{row[reco_col]}")
        st.markdown("---")
else:
    st.warning("No matching records found.")
