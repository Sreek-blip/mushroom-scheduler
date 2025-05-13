import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Mushroom Cultivation Scheduler", layout="centered")
st.title("🍄 Nuvedo Mushroom Cultivation Scheduler")

# Species configuration
default_species_data = {
    "Lion's Mane": {
        "flush_weeks": [2, 4, 6, 8],
        "default_BE": [0.12, 0.11, 0.10, 0.09]
    },
    "Shiitake": {
        "flush_weeks": [15, 17],  # 97 days colonization + 14 + 14 days
        "default_BE": [0.15, 0.15]
    },
    "Reishi": {
        "flush_weeks": [3, 6, 9],
        "default_BE": [0.07, 0.07, 0.07]
    }
}

# ----------------------
# User Inputs
# ----------------------
species = st.selectbox("🍄 Select Mushroom Species", list(default_species_data.keys()))
num_bags = st.number_input("🔢 Number of Fruiting Bags", min_value=1, value=10)
dry_weight_per_bag = st.number_input("⚖️ Dry Weight per Bag (kg)", min_value=0.1, step=0.1, value=1.0)
start_date = st.date_input("📅 Inoculation Start Date", datetime.today())

species_config = default_species_data[species]
flush_weeks = species_config["flush_weeks"]
default_BE = species_config["default_BE"]

st.markdown("🧪 **Enter B.E. (Biological Efficiency) per flush:**")
custom_be = []
for i, week in enumerate(flush_weeks):
    be = st.number_input(
        f"Flush in Week {week}",
        min_value=0.01,
        max_value=1.0,
        step=0.01,
        value=float(default_BE[i]),
        key=f"be_week_{week}"
    )
    custom_be.append(be)

# ----------------------
# Generate Schedule
# ----------------------
if st.button("📆 Generate 3-Month Schedule"):
    total_dry_weight = num_bags * dry_weight_per_bag
    schedule = []

    for i, week in enumerate(flush_weeks):
        flush_date = start_date + timedelta(weeks=week - 1)
        be = custom_be[i]
        fresh_weight = total_dry_weight * be  # BE is a fraction
        schedule.append({
            "Week": f"Week {week}",
            "Harvest Week": week,
            "Harvest Date": flush_date.strftime("%Y-%m-%d"),
            "BE (%)": round(be * 100, 1),
            "Fresh Yield (kg)": round(fresh_weight, 2),
            "Month": ((flush_date - start_date).days // 30) + 1
        })

    df = pd.DataFrame(schedule)

    # Display yield summary
    st.success("✅ Here's your cultivation and harvest schedule:")
    st.dataframe(df[["Week", "Harvest Date", "BE (%)", "Fresh Yield (kg)"]])

    # Yield summary
    per_bag_yield = dry_weight_per_bag * custom_be[0]
    total_per_flush = per_bag_yield * num_bags
    st.markdown(
        f"📦 **Each bag yields ~ {per_bag_yield:.2f} kg fresh mushrooms per flush**  \n"
        f"📈 **Total per flush:** {total_per_flush:.2f} kg (× {num_bags} bags)"
    )

    # ----------------------
    # Charts
    # ----------------------
    st.subheader("📊 Weekly Fresh Yield")
    st.bar_chart(df.set_index("Week")["Fresh Yield (kg)"])

    # Monthly yield
    st.subheader("📅 Monthly Yield Summary")
    monthly = df.groupby("Month")["Fresh Yield (kg)"].sum().reset_index()
    st.dataframe(monthly)

    # ----------------------
    # CSV Download
    # ----------------------
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Full Schedule as CSV", csv, "mushroom_schedule.csv", "text/csv")
