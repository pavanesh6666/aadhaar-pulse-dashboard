import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Aadhaar Pulse Dashboard", layout="wide")

@st.cache_data
def load_data():
    monthly = pd.read_csv("aadhaar_phase2_intelligence_dataset.csv")
    forecast = pd.read_csv("aadhaar_phase3_forecast.csv")
    return monthly, forecast

monthly, forecast_df = load_data()

st.title("🇮🇳 Aadhaar Pulse – District Intelligence & Forecasting System")
st.markdown("Interactive planning dashboard for UIDAI")

st.sidebar.header("Select Location")

states = sorted(monthly["state"].unique())
state_selected = st.sidebar.selectbox("State", states)

districts = sorted(monthly[monthly["state"] == state_selected]["district"].unique())
district_selected = st.sidebar.selectbox("District", districts)

district_data = monthly[
    (monthly["state"] == state_selected) &
    (monthly["district"] == district_selected)
].sort_values("month")

latest = district_data.iloc[-1]

col1, col2, col3, col4 = st.columns(4)

col1.metric("Stress Level", latest["stress_level"])
col2.metric("Maturity Category", latest["maturity_category"])
col3.metric("Confidence Score", round(latest["confidence_score"], 2))
col4.metric("Service Stress Score", int(latest["service_stress_score"]))

st.subheader("📈 Historical Update Trend")

fig1, ax1 = plt.subplots()
ax1.plot(district_data["month"], district_data["update_total"], marker="o")
plt.xticks(rotation=45)
st.pyplot(fig1)

st.subheader("🔮 Forecasted Update Demand")

forecast_data = forecast_df[
    (forecast_df["state"] == state_selected) &
    (forecast_df["district"] == district_selected)
]

if not forecast_data.empty:
    fig2, ax2 = plt.subplots()
    ax2.plot(forecast_data["forecast_month"], forecast_data["predicted_update_total"], marker="o", color="orange")
    plt.xticks(rotation=45)
    st.pyplot(fig2)
else:
    st.info("No forecast data available for this district.")

latest_month = monthly["month"].max()
latest_data = monthly[monthly["month"] == latest_month]
top_stress = latest_data.sort_values("service_stress_score", ascending=False).head(20)

st.subheader("🚨 Top 20 High-Risk Districts")
st.dataframe(top_stress[["state", "district", "service_stress_score", "stress_level"]])

st.markdown("---")
st.markdown("UIDAI Data Hackathon 2026 – Aadhaar Pulse")
