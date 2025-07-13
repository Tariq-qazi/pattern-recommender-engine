import streamlit as st
import pandas as pd

st.set_page_config(page_title="🏙️ Serdal Grouped Real Estate Advisor", layout="wide")
st.title("🏙️ Dubai Real Estate Grouped Recommendation Advisor")

# === STEP 1: Load Precomputed Pattern CSV ===
@st.cache_data

def load_data():
    url = "https://raw.githubusercontent.com/Tariq-qazi/Insights/main/PatternTaggedDatabase.csv"
    df = pd.read_csv(url)
    df = df.dropna(subset=["PatternID"])
    return df

# === STEP 2: Define Grouping Logic for PatternID Sets ===
pattern_groups = {
    "✅ Strong Buy Zones": {
        "patterns": ["P001", "P050", "P051", "P052", "P053"],
        "summary": "These areas show strong alignment across price, volume, and off-plan confidence. Best suited for immediate action."
    },
    "📈 Emerging Opportunity": {
        "patterns": ["P030", "P033", "P034", "P048"],
        "summary": "Market signals are forming or volume is recovering. Early entry could pay off — but requires active tracking."
    },
    "🕰️ Watchlist Zones": {
        "patterns": ["P032", "P038", "P054", "P057", "P060"],
        "summary": "Not a time to enter. These zones show early or unclear momentum. Keep an eye but don’t commit yet."
    },
    "⚠️ Caution Required": {
        "patterns": ["P031", "P035", "P041", "P044", "P055"],
        "summary": "These areas may seem attractive but have underlying weaknesses — either in volume, demand, or exit liquidity."
    },
    "❌ Avoid Zones": {
        "patterns": ["P036", "P046", "P056", "P063"],
        "summary": "Dead or artificial zones — no healthy activity or unsafe entry conditions. Capital should be deployed elsewhere."
    },
    "🔄 Transitional Zones": {
        "patterns": ["P039", "P040", "P042", "P043"],
        "summary": "Mixed signals — may be heading toward growth or decline. Decisions should be context-specific and cautious."
    }
}

# === STEP 3: Sidebar Filters ===
st.sidebar.header("🔍 Filter Your Preferences")
room_options = ["Studio", "1BR", "2BR", "3BR", "4BR+"]
selected_room = st.sidebar.selectbox("Bedrooms", room_options)
unit_type = st.sidebar.selectbox("Unit Type", ["Apartment", "Villa", "Townhouse"])
budget = st.sidebar.number_input("Max Budget (AED)", value=3000000, step=100000)

submit = st.sidebar.button("Find Zones")

# === STEP 4: Main Logic ===
if submit:
    df = load_data()
    
    # Apply filters
    filtered = df[
        (df["rooms_en"] == selected_room) &
        (df["property_type_en"] == unit_type) &
        (df["actual_worth"] <= budget)
    ]

    if filtered.empty:
        st.warning("❌ No matching areas found for the selected filters.")
    else:
        st.success(f"✅ {len(filtered)} matching transactions found.")

        # Assign group
        grouped = []
        for group, content in pattern_groups.items():
            matches = filtered[filtered["PatternID"].isin(content["patterns"])]
            if not matches.empty:
                area_counts = matches["area_name_en"].value_counts().reset_index()
                area_counts.columns = ["Area", "Matches"]
                grouped.append((group, content["summary"], area_counts))

        for group_name, summary, df_area in grouped:
            st.markdown(f"### {group_name}")
            st.markdown(f"*{summary}*")
            st.dataframe(df_area)

else:
    st.info("🎯 Select your filters and press 'Find Zones' to start.")
