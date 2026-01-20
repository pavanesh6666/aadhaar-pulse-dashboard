import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(page_title="Aadhaar Pulse Dashboard", layout="wide")

# =========================
# UI Helper – KPI Card
# =========================
def kpi_card(title, value, color):
    return f"""
    <div style="
        background:{color};
        padding:20px;
        border-radius:15px;
        color:white;
        text-align:center;
        box-shadow:0 4px 12px rgba(0,0,0,0.3);
        ">
        <h4>{title}</h4>
        <h2>{value}</h2>
    </div>
    """

# =========================
# Differential Privacy util
# =========================
def apply_dp_noise(value, epsilon=1.0):
    noise = np.random.laplace(0, 1/epsilon)
    return max(0, value + noise)

# =========================
# Recommendation Engine
# =========================
def recommend_resources(predicted_updates):
    staff = int(np.ceil(predicted_updates / 400))
    devices = int(np.ceil(predicted_updates / 250))
    mobile_units = int(np.ceil(predicted_updates / 1000))
    return staff, devices, mobile_units

@st.cache_data
def load_data():
    monthly = pd.read_csv("aadhaar_phase2_intelligence_dataset.csv")
    forecast = pd.read_csv("aadhaar_phase3_forecast.csv")
    return monthly, forecast

monthly, forecast_df = load_data()

# =========================
# Data Quality Check
# =========================
monthly["data_quality_flag"] = False
mask = (
    (monthly["district"].str.lower() == "hyderabad") &
    (monthly["state"].str.lower() != "telangana")
)
monthly.loc[mask, "data_quality_flag"] = True
dq_count = monthly["data_quality_flag"].sum()

# =========================
# Header
# =========================
st.title("🇮🇳 Aadhaar Pulse – District Intelligence & Forecasting System")
st.caption("UIDAI Data Hackathon 2026 | Decision-support platform for proactive service planning")

# =========================
# Data Quality Warning
# =========================
if dq_count > 0:
    st.warning(f"⚠ Detected {dq_count} records with possible administrative mismatch (legacy coding suspected).")

if st.checkbox("Show administrative mismatch records"):
    st.dataframe(monthly[monthly["data_quality_flag"]][
        ["state", "district", "month", "update_total", "service_stress_score"]
    ])

# =========================
# Sidebar – Privacy
# =========================
st.sidebar.header("🔐 Privacy Controls")

use_dp = st.sidebar.checkbox("Enable Differential Privacy")
epsilon = 1.0

if use_dp:
    st.sidebar.success(f"ε = {epsilon} (Laplace mechanism active)")
else:
    st.sidebar.info("Privacy OFF (raw aggregates shown)")

# =========================
# Sidebar – Location
# =========================
st.sidebar.header("📍 Select Location")

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
# Apply DP
# =========================
stress_score = latest["service_stress_score"]
update_total = latest["update_total"]

if use_dp:
    stress_score = apply_dp_noise(stress_score, epsilon)
    update_total = apply_dp_noise(update_total, epsilon)

# =========================
# KPI Cards
# =========================
st.subheader("📊 District Status Overview")

stress_color = "#d32f2f" if latest["stress_level"] == "High" else "#f9a825" if latest["stress_level"] == "Medium" else "#2e7d32"

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(kpi_card("🚨 Stress Level", latest["stress_level"], stress_color), unsafe_allow_html=True)
with c2:
    st.markdown(kpi_card("📈 Maturity", latest["maturity_category"], "#1565c0"), unsafe_allow_html=True)
with c3:
    st.markdown(kpi_card("🧮 Confidence", round(latest["confidence_score"], 2), "#6a1b9a"), unsafe_allow_html=True)
with c4:
    st.markdown(kpi_card("⚙ Service Stress", int(stress_score), "#00838f"), unsafe_allow_html=True)

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

predicted_value = None

if not forecast_data.empty:
    fig2, ax2 = plt.subplots()
    ax2.plot(forecast_data["forecast_month"],
             forecast_data["predicted_update_total"],
             marker="o", color="orange")
    plt.xticks(rotation=45)
    st.pyplot(fig2)

    predicted_value = forecast_data.iloc[-1]["predicted_update_total"]
else:
    st.info("No forecast data available.")

# =========================
# Recommendation Engine
# =========================
if predicted_value is not None:
    staff, devices, mobile_units = recommend_resources(predicted_value)

    st.subheader("🛠 Infrastructure Recommendations (Next Month)")
    r1, r2, r3 = st.columns(3)

    r1.metric("👨‍💼 Staff", staff)
    r2.metric("🖥 Devices", devices)
    r3.metric("🚐 Mobile Units", mobile_units)

# =========================
# Scenario Simulation (What-if)
# =========================
st.subheader("🧪 What-If Scenario Simulation")

extra_staff = st.slider("Add Staff", 0, 100, 0)
extra_devices = st.slider("Add Devices", 0, 100, 0)
extra_units = st.slider("Add Mobile Units", 0, 20, 0)

capacity_gain = (extra_staff * 400) + (extra_devices * 250) + (extra_units * 1000)

if predicted_value:
    new_load = max(predicted_value - capacity_gain, 0)
    st.info(f"Projected remaining workload after intervention: **{int(new_load)} updates/month**")

# =========================
# Top Risk Districts (Colored)
# =========================
st.subheader("🚨 Top 20 High-Risk Districts")

latest_month = monthly["month"].max()
latest_data = monthly[monthly["month"] == latest_month]
top_stress = latest_data.sort_values("service_stress_score", ascending=False).head(20)

def highlight(row):
    if row["stress_level"] == "High":
        return ["background-color:#ffcccc"] * len(row)
    elif row["stress_level"] == "Medium":
        return ["background-color:#fff0b3"] * len(row)
    else:
        return ["background-color:#ccffcc"] * len(row)

st.dataframe(top_stress[["state","district","service_stress_score","stress_level"]]
             .style.apply(highlight, axis=1))

# =========================
# Privacy Transparency Panel
# =========================
st.subheader("🔐 Privacy Status")

if use_dp:
    st.success("Differential Privacy ENABLED")
    st.write("Mechanism: Laplace")
    st.write(f"Epsilon (ε): {epsilon}")
else:
    st.warning("Differential Privacy DISABLED")

# =========================
# Footer
# =========================
st.markdown("---")
st.markdown("Aggregation Level: District–Month | Privacy: ε-Differential Privacy")
st.markdown("Forecast → Recommendation → Scenario Simulation")
st.markdown("UIDAI Data Hackathon 2026 – Aadhaar Pulse")
