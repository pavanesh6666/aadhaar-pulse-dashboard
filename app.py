import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(page_title="Aadhaar Pulse Dashboard", layout="wide")

# =========================
# Differential Privacy util
# =========================
def apply_dp_noise(value, epsilon=1.0):
    noise = np.random.laplace(0, 1/epsilon)
    return max(0, value + noise)

@st.cache_data
def load_data():
    monthly = pd.read_csv("aadhaar_phase2_intelligence_dataset.csv")
    forecast = pd.read_csv("aadhaar_phase3_forecast.csv")
    return monthly, forecast

monthly, forecast_df = load_data()

# =====================================================
# Data Quality Check – Administrative mismatch
# =====================================================
monthly["data_quality_flag"] = False

mask = (
    (monthly["district"].str.lower() == "hyderabad") &
    (monthly["state"].str.lower() != "telangana")
)

monthly.loc[mask, "data_quality_flag"] = True
dq_count = monthly["data_quality_flag"].sum()

# =========================
# UI Header
# =========================
st.title("🇮🇳 Aadhaar Pulse – District Intelligence & Forecasting System")
st.markdown("Interactive planning dashboard for UIDAI")

# =========================
# Data quality warning
# =========================
if dq_count > 0:
    st.warning(
        f"⚠ Detected {dq_count} records with possible administrative mismatch "
        f"(e.g., Hyderabad mapped outside Telangana). Legacy UIDAI coding suspected."
    )

show_dq = st.checkbox("Show administrative mismatch records")
if show_dq:
    st.dataframe(
        monthly[monthly["data_quality_flag"]][
            ["state", "district", "month", "update_total", "service_stress_score"]
        ]
    )

# =========================
# Privacy Toggle
# =========================
st.sidebar.header("Privacy Controls")

use_dp = st.sidebar.checkbox("Enable Differential Privacy")
epsilon = 1.0

if use_dp:
    st.sidebar.success(f"ε = {epsilon} (Laplace mechanism enabled)")
else:
    st.sidebar.info("Privacy OFF (raw aggregates shown)")

# =========================
# Location Selection
# =========================
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

# =========================
# Apply DP if enabled
# =========================
stress_score = latest["service_stress_score"]
update_total = latest["update_total"]

if use_dp:
    stress_score = apply_dp_noise(stress_score, epsilon)
    update_total = apply_dp_noise(update_total, epsilon)

# =========================
# Metrics
# =========================
col1, col2, col3, col4 = st.columns(4)

col1.metric("Stress Level", latest["stress_level"])
col2.metric("Maturity Category", latest["maturity_category"])
col3.metric("Confidence Score", round(latest["confidence_score"], 2))
col4.metric("Service Stress Score", int(stress_score))

# =========================
# Historical Trend
# =========================
st.subheader("📈 Historical Update Trend")

fig1, ax1 = plt.subplots()
ax1.plot(district_data["month"], district_data["update_total"], marker="o")
plt.xticks(rotation=45)
st.pyplot(fig1)

# =========================
# Forecast Plot
# =========================
st.subheader("🔮 Forecasted Update Demand")

forecast_data = forecast_df[
    (forecast_df["state"] == state_selected) &
    (forecast_df["district"] == district_selected)
]

if not forecast_data.empty:
    fig2, ax2 = plt.subplots()
    ax2.plot(
        forecast_data["forecast_month"],
        forecast_data["predicted_update_total"],
        marker="o",
        color="orange"
    )
    plt.xticks(rotation=45)
    st.pyplot(fig2)
else:
    st.info("No forecast data available for this district.")

# =========================
# Top Risk Districts
# =========================
latest_month = monthly["month"].max()
latest_data = monthly[monthly["month"] == latest_month]
top_stress = latest_data.sort_values("service_stress_score", ascending=False).head(20)

st.subheader("🚨 Top 20 High-Risk Districts")
st.dataframe(top_stress[["state", "district", "service_stress_score", "stress_level"]])

# =========================
# Footer
# =========================
st.markdown("---")
st.markdown("Privacy: ε-Differential Privacy (Laplace) | Aggregation Level: District-Month")
st.markdown("UIDAI Data Hackathon 2026 – Aadhaar Pulse")
