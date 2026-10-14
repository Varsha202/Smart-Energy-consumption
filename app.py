import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests

# ---------------- CONFIGURATION ----------------
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Smart Energy AI",
    page_icon="⚡",
    layout="wide"
)

# ---------------- PREMIUM CSS (Preserved & Enhanced) ----------------
st.markdown("""
<style>

/* Background */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #1e293b, #0f172a);
    color: #ffffff;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #111827;
}
section[data-testid="stSidebar"] * {
    color: white !important;
    font-size: 16px;
}

/* Title */
.title {
    text-align: center;
    font-size: 42px;
    font-weight: bold;
    color: #38bdf8;
}
.subtitle {
    text-align: center;
    color: #cbd5f1;
    font-size: 18px;
    margin-bottom: 20px;
}

/* Cards */
.card {
    background: rgba(255,255,255,0.08);
    padding: 20px;
    border-radius: 15px;
    backdrop-filter: blur(10px);
    text-align: center;
    font-size: 18px;
    font-weight: 500;
    border: 1px solid rgba(255, 255, 255, 0.1);
    margin-bottom: 15px;
}
.card-highlight {
    border-color: #38bdf8;
    background: rgba(56, 189, 248, 0.1);
}

.rec-card {
    background: rgba(255,255,255,0.06);
    border-left: 4px solid #38bdf8;
    padding: 16px 20px;
    border-radius: 8px;
    margin-bottom: 16px;
    text-align: left;
}

.rec-high {
    border-left-color: #f43f5e;
}
.rec-medium {
    border-left-color: #f59e0b;
}

/* Status Pill */
.status-pill {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 9999px;
    font-size: 13px;
    font-weight: 600;
    margin-top: 10px;
}
.status-healthy {
    background-color: rgba(16, 185, 129, 0.2);
    color: #34d399 !important;
    border: 1px solid #10b981;
}
.status-degraded {
    background-color: rgba(245, 158, 11, 0.2);
    color: #fbbf24 !important;
    border: 1px solid #f59e0b;
}
.status-error {
    background-color: rgba(239, 68, 68, 0.2);
    color: #f87171 !important;
    border: 1px solid #ef4444;
}

/* File Uploader */
[data-testid="stFileUploader"] label {
    color: #ffffff !important;
    font-size: 16px !important;
    font-weight: 600 !important;
}
[data-testid="stFileUploader"] section {
    border: 2px dashed #38bdf8 !important;
    border-radius: 12px !important;
    background: rgba(255,255,255,0.05) !important;
    padding: 20px !important;
}
[data-testid="stFileUploader"] section div {
    color: #e2e8f0 !important;
}
[data-testid="stFileUploader"] button {
    background-color: #38bdf8 !important;
    color: black !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
}
[data-testid="stFileUploader"] button:hover {
    background-color: #0ea5e9 !important;
    color: white !important;
}

/* Dataframe text fix */
[data-testid="stDataFrame"] {
    color: black;
}

</style>
""", unsafe_allow_html=True)


# ---------------- API CLIENT HELPERS ----------------

def check_backend_health():
    """Verify FastAPI backend reachability and return health payload or None."""
    try:
        res = requests.get(f"{API_BASE_URL}/health", timeout=2.5)
        if res.status_code == 200:
            return res.json()
    except requests.exceptions.RequestException:
        pass
    return None


@st.cache_data(ttl=30)
def fetch_api_data(endpoint: str):
    """Generic cached API fetcher with error trapping."""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        res = requests.get(url, timeout=5.0)
        if res.status_code == 200:
            return res.json(), None
        return None, f"API returned status {res.status_code}: {res.text}"
    except requests.exceptions.RequestException as e:
        return None, f"Could not reach backend API at {API_BASE_URL}: {str(e)}"


# ---------------- TITLE ----------------
st.markdown('<div class="title">⚡ Smart Campus Energy AI Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Predict • Analyze • Optimize Energy Usage</div>', unsafe_allow_html=True)

# ---------------- SIDEBAR ----------------
menu = st.sidebar.radio("📌 Navigation", [
    "📤 Upload Data",
    "📊 Dashboard",
    "📈 Analytics",
    "💡 Insights"
])

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔌 System Connectivity")
health_data = check_backend_health()

if health_data:
    if health_data.get("status") == "healthy":
        st.sidebar.markdown(
            '<div class="status-pill status-healthy">🟢 Backend & MongoDB: Online</div>',
            unsafe_allow_html=True
        )
    else:
        st.sidebar.markdown(
            '<div class="status-pill status-degraded">🟡 Backend: Online (Dataset Mode)</div>',
            unsafe_allow_html=True
        )
    st.sidebar.caption(f"API Base: `{API_BASE_URL}` (v{health_data.get('version', '1.0.0')})")
else:
    st.sidebar.markdown(
        '<div class="status-pill status-error">🔴 Backend: Disconnected</div>',
        unsafe_allow_html=True
    )
    st.sidebar.caption(f"Target: `{API_BASE_URL}`")
    st.sidebar.info("Tip: Start the backend with: `uvicorn backend.app.main:app --reload`")

# ---------------- SESSION INITIALIZATION ----------------
if "df" not in st.session_state:
    st.session_state.df = None


# ---------------- 1. UPLOAD DATA ----------------
if menu == "📤 Upload Data":
    st.markdown("### 📂 Upload Your Dataset")
    st.info("Supported formats: CSV, XLSX. Data will be validated and imported via the Backend API.")

    col1, col2 = st.columns([3, 1])
    with col1:
        file = st.file_uploader("Upload campus energy file", type=["csv", "xlsx"])

    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⚡ Load Repository Dataset", use_container_width=True):
            with st.spinner("Importing designated campus dataset..."):
                try:
                    res = requests.post(f"{API_BASE_URL}/api/energy/import?use_default_dataset=true", timeout=10.0)
                    if res.status_code == 200:
                        import_data = res.json()
                        st.success(f"✅ {import_data.get('message', 'Import completed successfully!')}")
                        # Clear cache and refresh
                        st.cache_data.clear()
                    elif res.status_code == 503:
                        st.warning("⚠️ MongoDB is offline. Using local dataset directly.")
                    else:
                        st.error(f"Import failed: {res.text}")
                except Exception as e:
                    st.warning(f"Backend offline: {e}. Dataset is accessible in local fallback mode.")

    if file:
        try:
            with st.spinner("Processing file through Backend validation..."):
                # Forward file to backend import endpoint
                files = {"file": (file.name, file.getvalue(), file.type)}
                res = requests.post(f"{API_BASE_URL}/api/energy/import", files=files, timeout=10.0)
                
                if res.status_code == 200:
                    import_info = res.json()
                    st.success(f"✅ {import_info.get('message')}")
                    st.write(
                        f"**Processed:** {import_info.get('total_rows_processed')} rows | "
                        f"**Inserted:** {import_info.get('imported_count')} | "
                        f"**Updated:** {import_info.get('updated_count')}"
                    )
                else:
                    st.warning(f"Backend responded with: {res.text}. Previewing file locally:")

            # Parse locally for instant preview
            file.seek(0)
            if file.name.endswith(".csv"):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)
            st.session_state.df = df
            st.dataframe(df.head(10), use_container_width=True)

        except Exception as e:
            st.error(f"Error reading dataset: {e}")

    # Preview current active energy records from backend
    st.markdown("---")
    st.markdown("### 📋 Active Energy Records Preview")
    energy_data, err = fetch_api_data("/api/energy?limit=10")
    if energy_data and "records" in energy_data:
        records_df = pd.DataFrame(energy_data["records"])
        if not records_df.empty:
            st.dataframe(records_df, use_container_width=True)
            st.caption(f"Showing {len(records_df)} of {energy_data.get('total_records', len(records_df))} total records from API.")
    elif err:
        st.caption(f"Backend status: {err}")


# ---------------- 2. DASHBOARD ----------------
elif menu == "📊 Dashboard":
    summary_data, summary_err = fetch_api_data("/api/analytics/summary")
    daily_data, daily_err = fetch_api_data("/api/analytics/daily")
    fac_data, fac_err = fetch_api_data("/api/analytics/facilities")

    if summary_err or not summary_data:
        st.warning(f"⚠️ Unable to load live metrics from backend: {summary_err or 'No data'}")
        st.info("Ensure the FastAPI backend is running on `http://127.0.0.1:8000`.")
    else:
        # KPI Cards connected to real backend analytics
        col1, col2, col3, col4 = st.columns(4)
        col1.markdown(
            f'<div class="card">📊<br><b>{summary_data.get("total_records", 0)}</b><br>Daily Records</div>',
            unsafe_allow_html=True
        )
        col2.markdown(
            f'<div class="card">📂<br><b>{len(summary_data.get("facilities_breakdown", {}))}</b><br>Monitored Facilities</div>',
            unsafe_allow_html=True
        )
        col3.markdown(
            f'<div class="card">⚡<br><b>{int(summary_data.get("average_daily_consumption_kwh", 0)):,} kWh</b><br>Avg Daily Energy</div>',
            unsafe_allow_html=True
        )
        col4.markdown(
            f'<div class="card">🔥<br><b>{int(summary_data.get("max_daily_consumption_kwh", 0)):,} kWh</b><br>Peak ({summary_data.get("peak_day", "N/A")})</div>',
            unsafe_allow_html=True
        )

        st.markdown("---")

        # Energy Trends (Daily Time Series from backend)
        st.subheader("📈 Campus Daily Energy Trends")
        if daily_data and "series" in daily_data:
            time_df = pd.DataFrame(daily_data["series"])
            if not time_df.empty:
                time_df["date"] = pd.to_datetime(time_df["date"])
                fig = px.line(
                    time_df,
                    x="date",
                    y=["total", "academic_blocks", "chiller", "hostels", "staff_quarters", "stp"],
                    labels={"value": "Energy Consumption (kWh)", "date": "Date", "variable": "Sector"},
                    title="Daily Energy Consumption Across Campus Facilities",
                    template="plotly_dark",
                    color_discrete_sequence=["#38bdf8", "#818cf8", "#f43f5e", "#fbbf24", "#34d399", "#a78bfa"]
                )
                fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#ffffff")
                )
                st.plotly_chart(fig, use_container_width=True)

        # Facility Consumption Breakdown (Bar Chart from backend)
        st.subheader("📊 Facility-Wise Consumption Breakdown")
        if fac_data and "facilities" in fac_data:
            fac_df = pd.DataFrame(fac_data["facilities"])
            if not fac_df.empty:
                fig2 = px.bar(
                    fac_df,
                    x="display_name",
                    y="total_kwh",
                    text="percentage",
                    labels={"total_kwh": "Total Energy (kWh)", "display_name": "Facility", "percentage": "Share (%)"},
                    title="Total Energy Breakdown by Campus Sector",
                    template="plotly_dark",
                    color="total_kwh",
                    color_continuous_scale="Viridis"
                )
                fig2.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                fig2.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#ffffff")
                )
                st.plotly_chart(fig2, use_container_width=True)


# ---------------- 3. ANALYTICS ----------------
elif menu == "📈 Analytics":
    tab1, tab2, tab3 = st.tabs(["🔮 Forecast (3-Month)", "⚠️ Anomaly Detection", "🌱 Carbon & Cost"])

    # TAB 1: 3-MONTH ML FORECAST
    with tab1:
        st.subheader("🔮 3-Month Daily Energy Consumption Forecast")
        forecast_data, f_err = fetch_api_data("/api/forecast")

        if f_err or not forecast_data:
            st.warning(f"⚠️ Unable to retrieve forecast: {f_err or 'No data'}")
        else:
            metrics = forecast_data.get("metrics", {})
            f_points = pd.DataFrame(forecast_data.get("forecast", []))

            # Display model metrics & validation
            mcol1, mcol2, mcol3, mcol4 = st.columns(4)
            mcol1.metric("Model", "Ridge Regression")
            mcol2.metric("Validation MAE", f"{metrics.get('model_mae', 0):,.0f} kWh")
            mcol3.metric("Baseline MAE", f"{metrics.get('baseline_mae', 0):,.0f} kWh")
            mcol4.metric("Improvement", f"+{metrics.get('model_improvement_over_baseline_pct', 0):.1f}%")

            if not f_points.empty:
                f_points["date"] = pd.to_datetime(f_points["date"])
                fig_f = go.Figure()

                # Upper Bound
                fig_f.add_trace(go.Scatter(
                    x=f_points["date"],
                    y=f_points["upper_bound_kwh"],
                    mode="lines",
                    line=dict(width=0),
                    showlegend=False,
                    name="Upper Bound (95% CI)"
                ))
                # Lower Bound with fill
                fig_f.add_trace(go.Scatter(
                    x=f_points["date"],
                    y=f_points["lower_bound_kwh"],
                    mode="lines",
                    line=dict(width=0),
                    fill="tonexty",
                    fillcolor="rgba(56, 189, 248, 0.15)",
                    name="95% Confidence Interval"
                ))
                # Forecast line
                fig_f.add_trace(go.Scatter(
                    x=f_points["date"],
                    y=f_points["predicted_consumption_kwh"],
                    mode="lines+markers",
                    line=dict(color="#38bdf8", width=2),
                    name="Predicted Daily Consumption"
                ))

                fig_f.update_layout(
                    title=f"92-Day Out-of-Sample Daily Forecast ({forecast_data.get('start_date')} to {forecast_data.get('end_date')})",
                    xaxis_title="Forecast Date",
                    yaxis_title="Predicted Energy (kWh)",
                    template="plotly_dark",
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#ffffff")
                )
                st.plotly_chart(fig_f, use_container_width=True)

            # Responsible AI Disclaimer
            st.info(f"ℹ️ **Methodology & Limitations:** {forecast_data.get('disclaimer')}")

    # TAB 2: ANOMALY DETECTION
    with tab2:
        st.subheader("⚠️ Campus Anomaly Detection (Isolation Forest & 2-Sigma)")
        anom_data, anom_err = fetch_api_data("/api/anomalies")

        if anom_err or not anom_data:
            st.warning(f"⚠️ Unable to retrieve anomaly data: {anom_err or 'No data'}")
        else:
            acol1, acol2, acol3 = st.columns(3)
            acol1.metric("Evaluated Days", anom_data.get("total_observations_evaluated", 0))
            acol2.metric("Detected Anomalies", anom_data.get("anomalies_detected_count", 0))
            acol3.metric("Upper 2σ Threshold", f"{int(anom_data.get('statistical_threshold_upper', 0)):,} kWh")

            # Scatter Plot
            all_pts = pd.DataFrame(anom_data.get("all_points", []))
            if not all_pts.empty:
                all_pts["date"] = pd.to_datetime(all_pts["date"])
                fig_anom = px.scatter(
                    all_pts,
                    x="date",
                    y="observed_kwh",
                    color="is_anomaly",
                    color_discrete_map={False: "#38bdf8", True: "#f43f5e"},
                    hover_data=["z_score", "primary_driver", "detection_method"],
                    labels={"observed_kwh": "Total Consumption (kWh)", "is_anomaly": "Anomaly Detected"},
                    title="Historical Observations vs Detected Operational Variances",
                    template="plotly_dark"
                )
                # Add upper and lower threshold lines
                upper_th = anom_data.get("statistical_threshold_upper")
                lower_th = anom_data.get("statistical_threshold_lower")
                if upper_th:
                    fig_anom.add_hline(y=upper_th, line_dash="dash", line_color="#f59e0b", annotation_text="Upper 2σ Limit")
                if lower_th:
                    fig_anom.add_hline(y=lower_th, line_dash="dash", line_color="#10b981", annotation_text="Lower 2σ Limit")

                fig_anom.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#ffffff")
                )
                st.plotly_chart(fig_anom, use_container_width=True)

            # Table of Detected Anomalies with Explanations
            anom_list = anom_data.get("anomalies", [])
            if anom_list:
                st.markdown("#### 🔍 Flagged Operational Variances & Explanations")
                anom_table = pd.DataFrame(anom_list)[[
                    "date", "observed_kwh", "expected_kwh", "z_score", "primary_driver", "explanation"
                ]]
                st.dataframe(anom_table, use_container_width=True)

            st.caption(f"📌 {anom_data.get('disclaimer')}")

    # TAB 3: CARBON & COST
    with tab3:
        st.subheader("🌱 Carbon Footprint & Electrical Cost Analysis")
        summary_data, _ = fetch_api_data("/api/analytics/summary")

        if summary_data:
            total_kwh = summary_data.get("total_consumption_kwh", 0)
            carbon = summary_data.get("carbon_emissions_kg_co2", 0)
            cost = summary_data.get("estimated_cost_inr", 0)
            factor = summary_data.get("carbon_factor_kg_co2_per_kwh", 0.72)
            tariff = summary_data.get("tariff_inr_per_kwh", 8.50)

            ccol1, ccol2 = st.columns(2)
            ccol1.markdown(
                f'<div class="card card-highlight">🌱<br><h3>{carbon:,.2f} kg CO₂</h3>'
                f'Total Monthly Carbon Footprint<br><small>Factor: {factor:.2f} kg CO₂/kWh (CEA Grid Baseline)</small></div>',
                unsafe_allow_html=True
            )
            ccol2.markdown(
                f'<div class="card card-highlight">💰<br><h3>₹{cost:,.2f}</h3>'
                f'Estimated Electricity Utility Bill<br><small>Tariff: ₹{tariff:.2f}/kWh (Commercial HT Educational Tariff)</small></div>',
                unsafe_allow_html=True
            )

            # Energy source mix
            sources = summary_data.get("sources_breakdown", {})
            if sources:
                st.markdown("#### ⚡ Energy Generation & Grid Supply Mix")
                src_df = pd.DataFrame([
                    {"Source": k, "Consumption (kWh)": v["kwh"], "Share (%)": v["percentage"]}
                    for k, v in sources.items()
                ])
                st.dataframe(src_df, use_container_width=True)


# ---------------- 4. INSIGHTS ----------------
elif menu == "💡 Insights":
    st.subheader("💡 Evidence-Based Energy Conservation Recommendations")
    st.markdown("Opportunities derived from empirical facility consumption patterns and detected operational variances.")

    rec_data, rec_err = fetch_api_data("/api/recommendations")

    if rec_err or not rec_data:
        st.warning(f"⚠️ Unable to load recommendations: {rec_err or 'No data'}")
    else:
        # Summary metrics
        scol1, scol2, scol3 = st.columns(3)
        scol1.markdown(
            f'<div class="card">⚡<br><b>{int(rec_data.get("total_potential_savings_kwh", 0)):,} kWh</b><br>Potential Monthly Savings</div>',
            unsafe_allow_html=True
        )
        scol2.markdown(
            f'<div class="card">💰<br><b>₹{int(rec_data.get("total_potential_savings_inr", 0)):,}</b><br>Estimated Monthly Cost Reduction</div>',
            unsafe_allow_html=True
        )
        scol3.markdown(
            f'<div class="card">🌱<br><b>{int(rec_data.get("total_potential_co2_reduction_kg", 0)):,} kg</b><br>CO₂ Abatement Potential</div>',
            unsafe_allow_html=True
        )

        st.markdown("---")

        # Render each evidence-based recommendation item
        for rec in rec_data.get("recommendations", []):
            priority_cls = "rec-high" if rec["priority"] == "High" else "rec-medium"
            st.markdown(f"""
            <div class="rec-card {priority_cls}">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h4 style="margin: 0; color: #38bdf8;">[{rec['id']}] {rec['title']}</h4>
                    <span style="font-size: 13px; font-weight: bold; padding: 2px 8px; border-radius: 4px; background: rgba(255,255,255,0.1);">
                        Priority: {rec['priority']} | {rec['category']}
                    </span>
                </div>
                <p style="margin-top: 10px; color: #e2e8f0;"><b>Evidence:</b> {rec['evidence']}</p>
                <p style="color: #cbd5f1;"><b>Action Plan:</b> {rec['action_plan']}</p>
                <div style="background: rgba(0,0,0,0.2); padding: 8px 12px; border-radius: 6px; font-size: 14px; color: #34d399;">
                    ⚡ <b>Estimated Monthly Savings:</b> {rec['estimated_monthly_savings_kwh']:,} kWh &nbsp;|&nbsp;
                    💰 <b>₹{rec['estimated_monthly_savings_inr']:,}</b> &nbsp;|&nbsp;
                    🌱 <b>{rec['estimated_monthly_co2_reduction_kg']:,} kg CO₂</b>
                </div>
                <p style="margin-top: 6px; font-size: 12px; color: #94a3b8;"><b>Assumptions:</b> {rec['assumptions']}</p>
            </div>
            """, unsafe_allow_html=True)

        st.caption(f"📌 {rec_data.get('methodology_notes')}")


# ---------------- FOOTER ----------------
st.markdown("<hr><center style='color:white;'>🚀 AI Powered Smart Campus System</center>", unsafe_allow_html=True)