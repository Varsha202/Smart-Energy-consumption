import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Smart Energy AI",
    page_icon="⚡",
    layout="wide"
)

# ---------------- PREMIUM CSS ----------------
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
}

/* -------- FILE UPLOADER FIX -------- */

/* Label */
[data-testid="stFileUploader"] label {
    color: #ffffff !important;
    font-size: 16px !important;
    font-weight: 600 !important;
}

/* Upload box */
[data-testid="stFileUploader"] section {
    border: 2px dashed #38bdf8 !important;
    border-radius: 12px !important;
    background: rgba(255,255,255,0.05) !important;
    padding: 20px !important;
}

/* Drag text */
[data-testid="stFileUploader"] section div {
    color: #e2e8f0 !important;
}

/* Button */
[data-testid="stFileUploader"] button {
    background-color: #38bdf8 !important;
    color: black !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
}

/* Hover */
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

# ---------------- SESSION ----------------
if "df" not in st.session_state:
    st.session_state.df = None

# ---------------- UPLOAD ----------------
if menu == "📤 Upload Data":

    st.markdown("### 📂 Upload Your Dataset")
    st.info("Supported formats: CSV, XLSX")

    file = st.file_uploader("", type=["csv", "xlsx"])

    if file:
        try:
            if file.name.endswith(".csv"):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)

            st.session_state.df = df

            st.success("✅ Dataset uploaded successfully!")
            st.dataframe(df.head())

        except Exception as e:
            st.error(f"Error: {e}")

# ---------------- DASHBOARD ----------------
elif menu == "📊 Dashboard":

    df = st.session_state.df

    if df is None:
        st.warning("⚠️ Upload data first")
    else:
        numeric_df = df.select_dtypes(include='number')

        col1, col2, col3, col4 = st.columns(4)

        col1.markdown(f'<div class="card">📊<br>{len(df)}<br>Records</div>', unsafe_allow_html=True)
        col2.markdown(f'<div class="card">📂<br>{len(df.columns)}<br>Columns</div>', unsafe_allow_html=True)
        col3.markdown(f'<div class="card">⚡<br>{int(numeric_df.mean().mean())}<br>Avg Energy</div>', unsafe_allow_html=True)
        col4.markdown(f'<div class="card">🔥<br>{int(numeric_df.max().max())}<br>Peak</div>', unsafe_allow_html=True)

        st.markdown("---")

        st.subheader("📈 Energy Trends")
        fig = px.line(numeric_df)
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("📊 Average Consumption")
        fig2 = px.bar(numeric_df.mean())
        st.plotly_chart(fig2, use_container_width=True)

# ---------------- ANALYTICS ----------------
elif menu == "📈 Analytics":

    df = st.session_state.df

    if df is None:
        st.warning("⚠️ Upload data first")
    else:
        numeric_df = df.select_dtypes(include='number')

        tab1, tab2, tab3 = st.tabs(["🔮 Forecast", "⚠️ Anomaly", "🌱 Carbon"])

        with tab1:
            st.subheader("Forecasting")
            fig = px.line(numeric_df)
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            st.subheader("Anomaly Detection")
            threshold = numeric_df.mean() + 2 * numeric_df.std()
            anomalies = numeric_df[numeric_df > threshold]

            fig = px.scatter(numeric_df)
            st.plotly_chart(fig, use_container_width=True)

            st.dataframe(anomalies.dropna(how="all"))

        with tab3:
            st.subheader("Carbon Analysis")
            total = numeric_df.sum().sum()
            carbon = total * 0.0005

            st.markdown(f'<div class="card">🌱 {carbon:.2f} kg CO₂ Emission</div>', unsafe_allow_html=True)

# ---------------- INSIGHTS ----------------
elif menu == "💡 Insights":

    st.subheader("💡 Smart Recommendations")

    st.markdown("""
    <div class="card">
    ✔ Reduce peak usage<br>
    ✔ Optimize HVAC systems<br>
    ✔ Switch to renewable energy<br>
    ✔ Smart scheduling
    </div>
    """, unsafe_allow_html=True)

# ---------------- FOOTER ----------------
st.markdown("<hr><center style='color:white;'>🚀 AI Powered Smart Campus System</center>", unsafe_allow_html=True)