# Smart Campus Energy Consumption Analytics — Next.js 14 Frontend

Modern, high-performance, responsive AI Dashboard built with **Next.js 14 (App Router)**, **TypeScript**, **Tailwind CSS**, **Recharts**, and **Lucide React**.

## ?? Quickstart

### 1. Install Dependencies
`ash
npm install
`

### 2. Configure Environment Variables
Copy the template and set the backend API URL:
`ash
cp .env.example .env.local
`
Inside .env.local:
`ini
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
`

### 3. Run Development Server
`ash
npm run dev
`
Open [http://localhost:3000](http://localhost:3000) in your browser.

### 4. Build for Production
`ash
npm run build
npm run start
`

---

## ?? Key Features

1. **Executive Overview Dashboard**: Real-time campus total consumption, renewable generation (solar/biogas), grid reliance, carbon emissions, and electricity costs.
2. **Defensible ML Forecasting**: Visualizes the 92-day out-of-sample daily energy demand prediction with 95% confidence intervals and validation metrics.
3. **Multi-Feature Anomaly Detection**: Highlights facility-level operational outliers detected by Isolation Forest & 2-sigma thresholds with causal explanations.
4. **Actionable Insights & Recommendations**: Energy conservation measures calculated with standard Indian CEA grid factors and commercial HT tariffs.
5. **Interactive Tariff Calculator**: Visualizes multi-tier progressive billing slabs, free allowances, fixed charges, and dynamic cost breakdowns.
6. **Live Notification Bell**: Real-time alerts with severity badges, audio chime, threshold checks, and read/unread state tracking.
7. **CSV Dataset Ingestion**: Flexible drag-and-drop CSV uploader directly to FastAPI backend with client-side format validation.

---

## ?? Backend Connection

This frontend connects to the FastAPI backend running on the ackend branch.
Ensure the FastAPI server is running on http://127.0.0.1:8000. You can test connection status anytime using the live health indicator in the dashboard header.