import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date

# ---------------- CENTRALIZED API CLIENT IMPORT ----------------
from src.api_client import APIClient, api_client
from src.analytics import calculate_summary_kpis

# ---------------- PAGE CONFIGURATION ----------------
st.set_page_config(
    page_title="Smart Energy AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- PREMIUM CSS (Preserved UI Design) ----------------
st.markdown("""
<style>

/* Main Background */
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
    font-size: 15px;
}

/* Titles */
.title {
    text-align: center;
    font-size: 40px;
    font-weight: 800;
    color: #38bdf8;
    margin-bottom: 0px;
    letter-spacing: -0.5px;
}
.subtitle {
    text-align: center;
    color: #cbd5f1;
    font-size: 17px;
    margin-bottom: 25px;
    font-weight: 400;
}

/* KPI Cards */
.card {
    background: rgba(255, 255, 255, 0.07);
    padding: 18px;
    border-radius: 14px;
    backdrop-filter: blur(12px);
    text-align: center;
    font-size: 16px;
    font-weight: 500;
    border: 1px solid rgba(255, 255, 255, 0.1);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    margin-bottom: 12px;
}
.card-val {
    font-size: 26px;
    font-weight: 700;
    color: #38bdf8;
    margin: 6px 0;
}
.card-highlight {
    border-color: rgba(56, 189, 248, 0.5);
    background: rgba(56, 189, 248, 0.08);
}

/* Recommendation Cards */
.rec-card {
    background: rgba(255, 255, 255, 0.06);
    border-left: 5px solid #38bdf8;
    padding: 18px 22px;
    border-radius: 10px;
    margin-bottom: 18px;
    text-align: left;
    border-top: 1px solid rgba(255, 255, 255, 0.05);
    border-right: 1px solid rgba(255, 255, 255, 0.05);
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}
.rec-high {
    border-left-color: #f43f5e;
}
.rec-medium {
    border-left-color: #f59e0b;
}

/* Connectivity Status Badges */
.status-pill {
    display: inline-block;
    padding: 5px 14px;
    border-radius: 9999px;
    font-size: 13px;
    font-weight: 600;
    margin-top: 8px;
    margin-bottom: 8px;
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

/* File Uploader Custom Styling */
[data-testid="stFileUploader"] label {
    color: #ffffff !important;
    font-size: 15px !important;
    font-weight: 600 !important;
}
[data-testid="stFileUploader"] section {
    border: 2px dashed #38bdf8 !important;
    border-radius: 12px !important;
    background: rgba(255, 255, 255, 0.04) !important;
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

</style>
""", unsafe_allow_html=True)

# ---------------- HEADER TITLE ----------------
st.markdown('<div class="title">⚡ Smart Campus Energy AI Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Predict • Analyze • Optimize Energy Usage</div>', unsafe_allow_html=True)

# ---------------- SIDEBAR CONFIGURATION & STATUS ----------------
st.sidebar.markdown("### 📌 Navigation")
menu = st.sidebar.radio("", [
    "📤 Upload Data",
    "📊 Dashboard",
    "📈 Analytics",
    "💡 Insights"
])

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔌 API Connection")

# Configurable API Base URL
configured_url = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
if "api_url" not in st.session_state:
    st.session_state.api_url = configured_url

with st.sidebar.expander("⚙️ Backend Endpoint Settings"):
    custom_url = st.text_input("API Base URL:", value=st.session_state.api_url)
    if custom_url != st.session_state.api_url:
        st.session_state.api_url = custom_url.rstrip("/")
        st.cache_data.clear()
        st.rerun()

client = APIClient(base_url=st.session_state.api_url)

# Health & Connectivity Check
health_data, health_err = client.check_health()

if health_data:
    if health_data.get("status") == "healthy" and health_data.get("database") == "connected":
        st.sidebar.markdown(
            '<div class="status-pill status-healthy">🟢 Connected (MongoDB Active)</div>',
            unsafe_allow_html=True
        )
    else:
        st.sidebar.markdown(
            '<div class="status-pill status-degraded">🟡 Online (Dataset Fallback)</div>',
            unsafe_allow_html=True
        )
    st.sidebar.caption(f"Host: `{st.session_state.api_url}` | v{health_data.get('version', '1.0.0')}")
else:
    st.sidebar.markdown(
        '<div class="status-pill status-error">🔴 Backend Offline</div>',
        unsafe_allow_html=True
    )
    st.sidebar.caption(f"Target: `{st.session_state.api_url}`")
    st.sidebar.info("Tip: Start the FastAPI backend with: `python -m uvicorn app.main:app --reload` inside the `backend` folder.")

if st.sidebar.button("🔄 Refresh Cached Data", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# ---------------- SESSION INITIALIZATION ----------------
if "df" not in st.session_state:
    st.session_state.df = None


# ==============================================================================
# 1. 📤 UPLOAD DATA
# ==============================================================================
if menu == "📤 Upload Data":
    st.markdown("### 📂 Upload Your Dataset")
    st.info("Supported formats: **CSV**, **XLSX**. Uploaded records are validated by FastAPI and ingested into the analytics pipeline.")

    col1, col2 = st.columns([3, 1])
    with col1:
        uploaded_file = st.file_uploader("Select energy consumption file", type=["csv", "xlsx"])

    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("⚡ Ingest Campus Dataset", use_container_width=True, help="Load preprocessed repository dataset into MongoDB via FastAPI"):
            with st.spinner("Calling POST /api/energy/import..."):
                import_res, import_err = client.import_default_dataset()
                if import_res:
                    st.success(f"✅ {import_res.get('message', 'Import completed successfully!')}")
                    st.write(
                        f"**Processed:** {import_res.get('total_rows_processed')} rows | "
                        f"**Inserted:** {import_res.get('imported_count')} | "
                        f"**Updated:** {import_res.get('updated_count')}"
                    )
                    st.cache_data.clear()
                elif import_err:
                    st.warning(f"Backend notice: {import_err}")

    if uploaded_file:
        try:
            with st.spinner("Sending file to FastAPI backend for ingestion..."):
                file_bytes = uploaded_file.getvalue()
                res_data, res_err = client.import_dataset_file(
                    file_bytes=file_bytes,
                    filename=uploaded_file.name,
                    content_type=uploaded_file.type or "text/csv"
                )

                if res_data:
                    st.success(f"✅ {res_data.get('message', 'File successfully processed and imported!')}")
                    st.write(
                        f"**Total Processed:** {res_data.get('total_rows_processed')} rows | "
                        f"**Imported (New):** {res_data.get('imported_count')} | "
                        f"**Updated (Upserted):** {res_data.get('updated_count')}"
                    )
                    st.cache_data.clear()
                elif res_err:
                    st.warning(f"API notice: {res_err}")

            # Local preview
            uploaded_file.seek(0)
            if uploaded_file.name.endswith(".csv"):
                df_local = pd.read_csv(uploaded_file)
            else:
                df_local = pd.read_excel(uploaded_file)
            st.session_state.df = df_local

            st.markdown("#### 📄 Uploaded File Preview")
            st.dataframe(df_local.head(10), use_container_width=True)

        except Exception as e:
            st.error(f"Error reading file: {e}")

    # Active Database Records Table from GET /api/energy
    st.markdown("---")
    st.markdown("### 📋 Active Energy Records from Backend API (`GET /api/energy`)")
    
    with st.spinner("Fetching active records..."):
        records_data, records_err = client.get_energy_records(page=1, limit=15)

    if records_data and "records" in records_data:
        records_df = pd.DataFrame(records_data["records"])
        if not records_df.empty:
            # Reorder columns for clean presentation
            first_cols = ["date", "total", "tneb_campus", "solar", "diesel", "academic_blocks", "chiller", "hostels"]
            display_cols = [c for c in first_cols if c in records_df.columns] + [c for c in records_df.columns if c not in first_cols and c != "id"]
            st.dataframe(records_df[display_cols], use_container_width=True)
            st.caption(f"Showing page {records_data.get('page', 1)} of {records_data.get('total_pages', 1)} ({records_data.get('total_records', len(records_df))} total records in database).")
        else:
            st.info("No records currently loaded in the database. Use the 'Ingest Campus Dataset' button above to seed data.")
    elif records_err:
        st.warning(f"Backend records preview unavailable: {records_err}")


# ==============================================================================
# 2. 📊 DASHBOARD
# ==============================================================================
elif menu == "📊 Dashboard":
    # Interactive Date Filtering Controls
    with st.expander("📅 Filter by Date Range", expanded=True):
        col_f1, col_f2, col_f3 = st.columns([2, 2, 1])
        with col_f1:
            start_date_input = st.date_input("Start Date", value=date(2026, 7, 1), min_value=date(2026, 1, 1), max_value=date(2026, 12, 31))
        with col_f2:
            end_date_input = st.date_input("End Date", value=date(2026, 7, 31), min_value=date(2026, 1, 1), max_value=date(2026, 12, 31))
        with col_f3:
            st.markdown("<br>", unsafe_allow_html=True)
            apply_filter = st.button("Apply Filter", use_container_width=True)

    start_iso = start_date_input.strftime("%Y-%m-%d") if start_date_input else None
    end_iso = end_date_input.strftime("%Y-%m-%d") if end_date_input else None

    # Fetch live analytics endpoints
    with st.spinner("Loading metrics from FastAPI backend..."):
        summary_data, summary_err = client.get_analytics_summary()
        daily_data, daily_err = client.get_daily_series()
        fac_data, fac_err = client.get_facility_breakdown()
        filtered_records, _ = client.get_energy_records(page=1, limit=100, start_date=start_iso, end_date=end_iso)

    if summary_err and not summary_data:
        st.warning(f"⚠️ Live metrics unavailable: {summary_err}")
        st.info("Check that the FastAPI server is running (`python -m uvicorn app.main:app --reload`).")

        # Graceful local fallback if preprocessed CSV is on disk
        if os.path.exists("data/preprocessed_energy.csv"):
            st.markdown("#### ⚡ Showing Offline Local Dataset Fallback")
            local_df = pd.read_csv("data/preprocessed_energy.csv")
            kpis = calculate_summary_kpis(local_df)
            col1, col2, col3, col4 = st.columns(4)
            col1.markdown(f'<div class="card">📊<br><div class="card-val">{kpis["records_count"]}</div>Records</div>', unsafe_allow_html=True)
            col2.markdown(f'<div class="card">📂<br><div class="card-val">{len(local_df.columns)}</div>Columns</div>', unsafe_allow_html=True)
            col3.markdown(f'<div class="card">⚡<br><div class="card-val">{int(kpis["average_daily_kwh"]):,} kWh</div>Avg Energy</div>', unsafe_allow_html=True)
            col4.markdown(f'<div class="card">🔥<br><div class="card-val">{int(kpis["peak_kwh"]):,} kWh</div>Peak ({kpis["peak_date"]})</div>', unsafe_allow_html=True)
    else:
        # Display Actual API Response in KPI Cards
        col1, col2, col3, col4 = st.columns(4)
        total_rec = summary_data.get("total_records", 0)
        fac_count = len(summary_data.get("facilities_breakdown", {}))
        avg_kwh = summary_data.get("average_daily_consumption_kwh", 0)
        peak_kwh = summary_data.get("max_daily_consumption_kwh", 0)
        peak_day = summary_data.get("peak_day", "N/A")

        col1.markdown(
            f'<div class="card">📊<br><div class="card-val">{total_rec}</div>Daily Records</div>',
            unsafe_allow_html=True
        )
        col2.markdown(
            f'<div class="card">📂<br><div class="card-val">{fac_count}</div>Monitored Facilities</div>',
            unsafe_allow_html=True
        )
        col3.markdown(
            f'<div class="card">⚡<br><div class="card-val">{int(avg_kwh):,} kWh</div>Avg Daily Energy</div>',
            unsafe_allow_html=True
        )
        col4.markdown(
            f'<div class="card">🔥<br><div class="card-val">{int(peak_kwh):,} kWh</div>Peak ({peak_day})</div>',
            unsafe_allow_html=True
        )

        st.markdown("---")

        # 📈 Energy Trends (Daily Time Series from GET /api/analytics/daily)
        st.subheader("📈 Campus Daily Energy Trends")
        
        # If user applied date filtering, use the filtered energy records from API
        time_series_data = None
        if filtered_records and filtered_records.get("records"):
            time_series_data = filtered_records["records"]
        elif daily_data and "series" in daily_data:
            time_series_data = daily_data["series"]

        if time_series_data:
            time_df = pd.DataFrame(time_series_data)
            if not time_df.empty:
                time_df["date"] = pd.to_datetime(time_df["date"])
                time_df = time_df.sort_values("date")

                available_breakdowns = [c for c in ["total", "academic_blocks", "chiller", "hostels", "staff_quarters", "stp"] if c in time_df.columns]
                fig = px.line(
                    time_df,
                    x="date",
                    y=available_breakdowns,
                    labels={"value": "Energy (kWh)", "date": "Observation Date", "variable": "Sector / Total"},
                    title=f"Daily Consumption Trends ({time_df['date'].dt.strftime('%b %d').iloc[0]} - {time_df['date'].dt.strftime('%b %d, %Y').iloc[-1]})",
                    template="plotly_dark",
                    color_discrete_sequence=["#38bdf8", "#818cf8", "#f43f5e", "#fbbf24", "#34d399", "#a78bfa"]
                )
                fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#ffffff"),
                    hovermode="x unified",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig, use_container_width=True)

        # 📊 Facility-Wise Consumption Breakdown (Bar Chart from GET /api/analytics/facilities)
        st.subheader("📊 Facility-Wise Consumption Breakdown")
        if fac_data and "facilities" in fac_data:
            fac_df = pd.DataFrame(fac_data["facilities"])
            if not fac_df.empty:
                fig2 = px.bar(
                    fac_df,
                    x="display_name",
                    y="total_kwh",
                    text="percentage",
                    labels={"total_kwh": "Total Energy (kWh)", "display_name": "Campus Sector", "percentage": "Share (%)"},
                    title="Energy Consumption Distribution by Campus Facility",
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


# ==============================================================================
# 3. 📈 ANALYTICS
# ==============================================================================
elif menu == "📈 Analytics":
    tab1, tab2, tab3 = st.tabs(["🔮 Forecast", "⚠️ Anomaly", "🌱 Carbon"])

    # ---------------- TAB 1: FORECASTING ----------------
    with tab1:
        st.subheader("🔮 3-Month Daily Out-of-Sample Forecast")
        st.caption("Machine Learning Ridge Regression Model with Confidence Intervals (Aug 1 - Oct 31, 2026)")

        with st.spinner("Generating 3-month forecast from GET /api/forecast..."):
            forecast_data, f_err = client.get_forecast()

        if f_err or not forecast_data:
            st.warning(f"⚠️ Unable to retrieve forecast: {f_err or 'No data returned'}")
        else:
            metrics = forecast_data.get("metrics", {})
            f_points = pd.DataFrame(forecast_data.get("forecast", []))

            # Metric KPIs
            mcol1, mcol2, mcol3, mcol4 = st.columns(4)
            mcol1.metric("Model Architecture", "Ridge Regression")
            mcol2.metric("Validation MAE", f"{metrics.get('model_mae', 0):,.0f} kWh")
            mcol3.metric("Baseline MAE", f"{metrics.get('baseline_mae', 0):,.0f} kWh")
            improvement = metrics.get('model_improvement_over_baseline_pct', 0)
            mcol4.metric("Improvement vs Baseline", f"+{improvement:.1f}%")

            if not f_points.empty:
                f_points["date"] = pd.to_datetime(f_points["date"])
                fig_f = go.Figure()

                # Upper Bound Line
                fig_f.add_trace(go.Scatter(
                    x=f_points["date"],
                    y=f_points["upper_bound_kwh"],
                    mode="lines",
                    line=dict(width=0),
                    showlegend=False,
                    name="Upper Bound (95% CI)"
                ))
                # Lower Bound Line with shaded fill
                fig_f.add_trace(go.Scatter(
                    x=f_points["date"],
                    y=f_points["lower_bound_kwh"],
                    mode="lines",
                    line=dict(width=0),
                    fill="tonexty",
                    fillcolor="rgba(56, 189, 248, 0.16)",
                    name="95% Confidence Interval"
                ))
                # Predicted Mean Line
                fig_f.add_trace(go.Scatter(
                    x=f_points["date"],
                    y=f_points["predicted_consumption_kwh"],
                    mode="lines+markers",
                    line=dict(color="#38bdf8", width=2.5),
                    marker=dict(size=4),
                    name="Predicted Daily Consumption"
                ))

                fig_f.update_layout(
                    title=f"92-Day Out-of-Sample Forecast ({forecast_data.get('start_date')} to {forecast_data.get('end_date')})",
                    xaxis_title="Forecast Date",
                    yaxis_title="Predicted Consumption (kWh)",
                    template="plotly_dark",
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#ffffff"),
                    hovermode="x unified"
                )
                st.plotly_chart(fig_f, use_container_width=True)

            # Scientific Disclaimer Box
            if forecast_data.get("disclaimer"):
                st.info(f"ℹ️ **Methodology & Limitations:** {forecast_data.get('disclaimer')}")

    # ---------------- TAB 2: ANOMALY DETECTION ----------------
    with tab2:
        st.subheader("⚠️ Campus Anomaly Detection")
        st.caption("Ensemble: Multi-Feature Isolation Forest combined with a 2-Sigma Statistical Threshold")

        with st.spinner("Analyzing operational variances from GET /api/anomalies..."):
            anom_data, anom_err = client.get_anomalies()

        if anom_err or not anom_data:
            st.warning(f"⚠️ Unable to retrieve anomaly data: {anom_err or 'No data returned'}")
        else:
            acol1, acol2, acol3 = st.columns(3)
            acol1.metric("Evaluated Days", anom_data.get("total_observations_evaluated", 0))
            acol2.metric("Detected Anomalies", anom_data.get("anomalies_detected_count", 0))
            upper_th = anom_data.get("statistical_threshold_upper", 0)
            acol3.metric("Upper 2σ Threshold", f"{int(upper_th):,} kWh")

            # Plotly Scatter Chart
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
                    labels={"observed_kwh": "Total Energy (kWh)", "is_anomaly": "Flagged Anomaly"},
                    title="Campus Daily Observations vs Detected Anomalies",
                    template="plotly_dark"
                )
                if upper_th:
                    fig_anom.add_hline(y=upper_th, line_dash="dash", line_color="#f59e0b", annotation_text="Upper 2σ Bound")
                lower_th = anom_data.get("statistical_threshold_lower")
                if lower_th:
                    fig_anom.add_hline(y=lower_th, line_dash="dash", line_color="#10b981", annotation_text="Lower 2σ Bound")

                fig_anom.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#ffffff")
                )
                st.plotly_chart(fig_anom, use_container_width=True)

            # Detailed Flagged Anomalies Table
            anomalies_list = anom_data.get("anomalies", [])
            if anomalies_list:
                st.markdown("#### 🔍 Flagged Operational Variances & Root-Cause Explanations")
                anom_table = pd.DataFrame(anomalies_list)[[
                    "date", "observed_kwh", "expected_kwh", "z_score", "primary_driver", "explanation"
                ]]
                st.dataframe(anom_table, use_container_width=True)

            if anom_data.get("disclaimer"):
                st.caption(f"📌 {anom_data.get('disclaimer')}")

    # ---------------- TAB 3: CARBON & COST ----------------
    with tab3:
        st.subheader("🌱 Carbon Footprint & Electrical Utility Cost")

        with st.spinner("Fetching carbon and cost analytics..."):
            summary_data, _ = client.get_analytics_summary()

        if summary_data:
            carbon = summary_data.get("carbon_emissions_kg_co2", 0)
            cost = summary_data.get("estimated_cost_inr", 0)
            factor = summary_data.get("carbon_factor_kg_co2_per_kwh", 0.72)
            tariff = summary_data.get("tariff_inr_per_kwh", 8.50)

            ccol1, ccol2 = st.columns(2)
            ccol1.markdown(
                f'<div class="card card-highlight">🌱<br><div class="card-val">{carbon:,.2f} kg CO₂</div>'
                f'Total Campus Carbon Footprint<br><small style="color:#94a3b8;">Grid Baseline Factor: {factor:.2f} kg CO₂/kWh (CEA India Database)</small></div>',
                unsafe_allow_html=True
            )
            ccol2.markdown(
                f'<div class="card card-highlight">💰<br><div class="card-val">₹{cost:,.2f}</div>'
                f'Estimated Electricity Utility Bill<br><small style="color:#94a3b8;">Commercial HT Educational Tariff: ₹{tariff:.2f}/kWh</small></div>',
                unsafe_allow_html=True
            )

            # Energy Sources Mix Breakdown
            sources = summary_data.get("sources_breakdown", {})
            if sources:
                st.markdown("#### ⚡ Campus Energy Generation & Grid Supply Mix")
                src_df = pd.DataFrame([
                    {"Supply Source": k, "Total Energy (kWh)": v["kwh"], "Percentage Share (%)": f"{v['percentage']:.1f}%"}
                    for k, v in sources.items()
                ])
                st.dataframe(src_df, use_container_width=True)


# ==============================================================================
# 4. 💡 INSIGHTS
# ==============================================================================
elif menu == "💡 Insights":
    st.subheader("💡 Smart Recommendations")
    st.markdown("Data-driven conservation initiatives derived from real facility usage patterns and operational variances.")

    with st.spinner("Fetching recommendations from GET /api/recommendations..."):
        rec_data, rec_err = client.get_recommendations()

    if rec_err or not rec_data:
        st.warning(f"⚠️ Recommendations unavailable: {rec_err or 'No data returned'}")
    else:
        # Top KPI Summary Cards
        scol1, scol2, scol3 = st.columns(3)
        tot_kwh = rec_data.get("total_potential_savings_kwh", 0)
        tot_inr = rec_data.get("total_potential_savings_inr", 0)
        tot_co2 = rec_data.get("total_potential_co2_reduction_kg", 0)

        scol1.markdown(
            f'<div class="card">⚡<br><div class="card-val">{int(tot_kwh):,} kWh</div>Potential Monthly Energy Savings</div>',
            unsafe_allow_html=True
        )
        scol2.markdown(
            f'<div class="card">💰<br><div class="card-val">₹{int(tot_inr):,}</div>Estimated Monthly Cost Reduction</div>',
            unsafe_allow_html=True
        )
        scol3.markdown(
            f'<div class="card">🌱<br><div class="card-val">{int(tot_co2):,} kg</div>CO₂ Abatement Potential</div>',
            unsafe_allow_html=True
        )

        st.markdown("---")

        # Actionable Recommendation Cards
        recs = rec_data.get("recommendations", [])
        for rec in recs:
            priority = rec.get("priority", "Medium")
            priority_cls = "rec-high" if priority == "High" else "rec-medium"
            badge_color = "#f43f5e" if priority == "High" else "#f59e0b"

            st.markdown(f"""
            <div class="rec-card {priority_cls}">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h4 style="margin: 0; color: #38bdf8;">[{rec.get('id', 'REC')}] {rec.get('title', '')}</h4>
                    <span style="font-size: 12px; font-weight: 700; padding: 3px 10px; border-radius: 6px; background: rgba(0,0,0,0.3); color: {badge_color};">
                        Priority: {priority} | {rec.get('category', 'Efficiency')}
                    </span>
                </div>
                <p style="margin-top: 10px; color: #e2e8f0; font-size: 14px;"><b>Operational Evidence:</b> {rec.get('evidence', '')}</p>
                <p style="color: #cbd5f1; font-size: 14px;"><b>Action Plan:</b> {rec.get('action_plan', '')}</p>
                <div style="background: rgba(0,0,0,0.25); padding: 10px 14px; border-radius: 8px; font-size: 14px; color: #34d399; margin: 8px 0;">
                    ⚡ <b>Monthly Savings:</b> {rec.get('estimated_monthly_savings_kwh', 0):,} kWh &nbsp;|&nbsp;
                    💰 <b>₹{rec.get('estimated_monthly_savings_inr', 0):,}</b> &nbsp;|&nbsp;
                    🌱 <b>{rec.get('estimated_monthly_co2_reduction_kg', 0):,} kg CO₂</b>
                </div>
                <p style="margin-top: 6px; font-size: 12px; color: #94a3b8;"><b>Engineering Assumptions:</b> {rec.get('assumptions', '')}</p>
            </div>
            """, unsafe_allow_html=True)

        if rec_data.get("methodology_notes"):
            st.caption(f"📌 {rec_data.get('methodology_notes')}")


# ---------------- FOOTER ----------------
st.markdown("<hr><center style='color:#94a3b8; font-size:13px;'>🚀 AI Powered Smart Campus System &nbsp;|&nbsp; FastAPI Backend Integrated</center>", unsafe_allow_html=True)