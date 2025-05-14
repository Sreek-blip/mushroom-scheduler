import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import math
import gspread
from google.oauth2.service_account import Credentials

# Species-specific parameters
species_params = {
    "Lion's Mane": {
        "yield_per_flush_per_kg_substrate": [0.3, 0.25, 0.2],
        "colonization_days": 14,
        "fruiting_days": 7,
        "substrate_type": "Hardwood Sawdust",
        "spawn_ratio": 0.05
    },
    "Oyster": {
        "yield_per_flush_per_kg_substrate": [0.4, 0.3, 0.2],
        "colonization_days": 10,
        "fruiting_days": 5,
        "substrate_type": "Wheat Straw",
        "spawn_ratio": 0.04
    },
    "Reishi": {
        "yield_per_flush_per_kg_substrate": [0.25, 0.2],
        "colonization_days": 30,
        "fruiting_days": 30,
        "substrate_type": "Hardwood Sawdust",
        "spawn_ratio": 0.03
    }
}

st.set_page_config(page_title="Mushroom Scheduler", layout="centered")
st.title("🍄 Mushroom Cultivation Planner & Logger")

mode = st.radio("Select Mode", ["📅 Plan Backward from Final Harvest", "📝 Log Actual Cultivation Data"])

# Function to log to Google Sheet
def append_to_google_sheet(data: pd.DataFrame):
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
    )
    client = gspread.authorize(creds)
    sheet = client.open("Nuvedo Cultivation Log").sheet1
    sheet.append_rows(data.values.tolist(), value_input_option="USER_ENTERED")

if mode == "📅 Plan Backward from Final Harvest":
    species = st.selectbox("Select Mushroom Species", list(species_params.keys()))
    total_yield = st.number_input("Total Yield Required (kg)", min_value=0.0, value=10.0, step=0.1)
    flushes = st.selectbox("Number of Flushes", [1, 2, 3])
    final_harvest_date = st.date_input("Final Harvest Date", datetime.today())
    batch_number = st.text_input("Batch / Lot Number")

    if st.button("Generate Plan"):
        params = species_params[species]
        yield_per_kg_sub = sum(params['yield_per_flush_per_kg_substrate'][:flushes])

        substrate_needed_kg = total_yield / yield_per_kg_sub
        spawn_needed_kg = substrate_needed_kg * params['spawn_ratio']
        kits_required = math.ceil(substrate_needed_kg)

        total_days = params['colonization_days'] + (params['fruiting_days'] * flushes)
        inoculation_date = final_harvest_date - timedelta(days=total_days)
        spawn_prep_date = inoculation_date - timedelta(days=2)

        harvest_schedule = []
        harvest_date = inoculation_date + timedelta(days=params['colonization_days'] + params['fruiting_days'])
        flush_yields = [round(y * substrate_needed_kg, 2) for y in params['yield_per_flush_per_kg_substrate'][:flushes]]

        for i, flush_yield in enumerate(flush_yields):
            harvest_schedule.append({
                "Batch Number": batch_number,
                "Species": species,
                "Flush": i + 1,
                "Harvest Date": harvest_date.strftime("%Y-%m-%d"),
                "Expected Yield (kg)": flush_yield,
                "B.E. (%)": round((flush_yield / substrate_needed_kg) * 100, 2)
            })
            harvest_date += timedelta(days=params['fruiting_days'])

        be_percentage = round((total_yield / substrate_needed_kg) * 100, 2)

        st.subheader("🧾 Summary")
        st.write(f"**Batch Number**: {batch_number}")
        st.write(f"**Species**: {species}")
        st.write(f"**Kits Required**: {kits_required}")
        st.write(f"**Substrate Type**: {params['substrate_type']}")
        st.write(f"**Substrate Required**: {round(substrate_needed_kg, 2)} kg (dry)")
        st.write(f"**Spawn Required**: {round(spawn_needed_kg * 1000)} g ({round(spawn_needed_kg, 2)} kg)")
        st.write(f"**Spawn Preparation Date**: {spawn_prep_date.strftime('%Y-%m-%d')}")
        st.write(f"**Inoculation Date**: {inoculation_date.strftime('%Y-%m-%d')}")
        st.write(f"**Final Harvest Date**: {final_harvest_date.strftime('%Y-%m-%d')}")
        st.write(f"**Biological Efficiency**: {be_percentage} %")

        df_schedule = pd.DataFrame(harvest_schedule)
        st.subheader("📆 Harvesting Schedule")
        st.dataframe(df_schedule)

        if st.button("📤 Sync to Google Sheets"):
            append_to_google_sheet(df_schedule)
            st.success("Data synced to Google Sheets ✅")

        st.download_button("📥 Download CSV", df_schedule.to_csv(index=False), file_name=f"{batch_number}_harvest_schedule.csv")

elif mode == "📝 Log Actual Cultivation Data":
    st.subheader("🧾 Enter Completed Batch Data")

    with st.form("log_form"):
        batch = st.text_input("Batch Number")
        species = st.selectbox("Species", list(species_params.keys()), key="log_species")
        harvest_date = st.date_input("Harvest Date")
        flush_number = st.number_input("Flush Number", min_value=1, step=1)
        dry_substrate = st.number_input("Dry Substrate Used (kg)", min_value=0.1)
        harvested_kg = st.number_input("Actual Harvested Yield (kg)", min_value=0.1)

        submitted = st.form_submit_button("Log Entry")

    if submitted:
        be_actual = round((harvested_kg / dry_substrate) * 100, 2)
        row = pd.DataFrame([{
            "Batch Number": batch,
            "Species": species,
            "Flush": flush_number,
            "Harvest Date": harvest_date.strftime("%Y-%m-%d"),
            "Expected Yield (kg)": harvested_kg,
            "B.E. (%)": be_actual
        }])

        append_to_google_sheet(row)
        st.success("✅ Data logged and synced to Google Sheets")
        st.dataframe(row)
