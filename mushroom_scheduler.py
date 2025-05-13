import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.title("🍄 Nuvedo Mushroom Cultivation Scheduler")

# Species-specific parameters
species_data = {
    "Lion's Mane": {
        "colonization_days": 28,
        "first_harvest_week": 2,
        "flush_interval_weeks": 2,
        "flushes": 4,
        "yield_percents": [0.11, 0.11, 0.11, 0.11]
    },
    "Shiitake": {
        "colonization_days": 97,
        "first_harvest_offset_days": 14,
        "flush_interval_days": 14,
        "flushes": 2,
        "yield_percents": [0.15, 0.15]
    },
    "Reishi": {
        "colonization_days": 28,
        "first_harvest_week": 3,
        "flush_interval_weeks": 3,
        "flushes": 3,
        "yield_percents": [0.07, 0.07, 0.07]
    }
}

# Inputs
species = st.selectbox("🍄 Select Mushroom Species", list(species_data.keys()))
num_bags = st.number_input("🔢 Number of Fruiting Bags", min_value=1, value=10)
bag_weight = st.number_input("⚖️ Weight per Bag (kg)", min_value=0.1, step=0.1, value=1.0)
start_date = st.date_input("📅 Inoculation Start Date", datetime.today())

if st.button("📆 Generate 3-Month Schedule"):
    total_substrate = num_bags * bag_weight
    schedule = []

    # Fetch species parameters
    data = species_data[species]

    # Create harvest schedule
    if species == "Shiitake":
        colonization_complete = start_date + timedelta(days=data["colonization_days"])
        for i in range(data["flushes"]):
            flush_date = colonization_complete + timedelta(
                days=data["first_harvest_offset_days"] + i * data["flush_interval_days"]
            )
            week_num = ((flush_date - start_date).days // 7) + 1
            yield_kg = round(total_substrate * data["yield_percents"][i], 2)
            schedule.append({
                "Week": f"Week {week_num}",
                "Harvest Date": flush_date.strftime("%Y-%m-%d"),
                "Expected Yield (kg)": yield_kg
            })

    else:
        for i in range(data["flushes"]):
            flush_week = data["first_harvest_week"] + (i * data["flush_interval_weeks"])
            flush_date = start_date + timedelta(weeks=flush_week - 1)
            yield_kg = round(total_substrate * data["yield_percents"][i], 2)
            schedule.append({
                "Week": f"Week {flush_week}",
                "Harvest Date": flush_date.strftime("%Y-%m-%d"),
                "Expected Yield (kg)": yield_kg
            })

    # Display table
    df = pd.DataFrame(schedule)
    st.success("✅ Here's your cultivation and harvest schedule:")
    st.dataframe(df)

    # Yield breakdown
    per_bag_yield = bag_weight * data["yield_percents"][0]
    total_yield = per_bag_yield * num_bags
    st.markdown(
        f"📦 **Each bag yields:** {per_bag_yield:.2f} kg per flush  \n"
        f"📈 **Total per harvest:** {per_bag_yield:.2f} kg × {num_bags} bags = {total_yield:.2f} kg"
    )

    # Cumulative yield chart
    df["Cumulative Yield (kg)"] = df["Expected Yield (kg)"].cumsum()
    st.subheader("📊 Cumulative Yield Over Time")
    st.line_chart(df.set_index("Harvest Date")["Cumulative Yield (kg)"])

    # CSV download
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download as CSV", csv, "mushroom_schedule.csv", "text/csv")
