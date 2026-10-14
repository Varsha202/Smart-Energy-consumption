# AI-Driven Smart Campus Energy Backend API & Analytics Engine

Welcome to the backend service of the **Smart Campus Energy Consumption Analytics System**. This production-ready, modular backend is built using **FastAPI**, **MongoDB (PyMongo)**, **Scikit-learn**, and **Pandas**, and integrates seamlessly with the existing **Streamlit** dashboard.

---

## 🏗️ Architecture & Features

```
backend/
├── app/
│   ├── config.py                 # Pydantic Settings & environment variables
│   ├── database.py               # PyMongo client, safe connection, timeouts & indices
│   ├── main.py                   # FastAPI application entry point, CORS, and lifespans
│   ├── models/
│   │   ├── schemas.py            # Pydantic request/response schemas & validators
│   │   └── __init__.py
│   ├── routes/
│   │   ├── health.py             # GET /, GET /health
│   │   ├── energy.py             # GET/POST /api/energy, POST /api/energy/import
│   │   ├── analytics.py          # GET /api/analytics/summary, /daily, /facilities
│   │   ├── forecast.py           # GET /api/forecast (3-month daily horizon)
│   │   ├── anomalies.py          # GET /api/anomalies (Isolation Forest + 2-sigma)
│   │   ├── recommendations.py    # GET /api/recommendations (evidence-based)
│   │   └── __init__.py
│   └── services/
│       ├── energy_service.py     # Data ingestion, deduplication & fallback
│       ├── analytics_service.py  # Campus KPIs and facility breakdowns
│       ├── forecast_service.py   # Machine learning 92-day forecast & validation
│       ├── anomaly_service.py    # Multi-feature anomaly detection & explanations
│       └── recommendation_service.py # Evidence-based energy conservation actions
├── scripts/
│   └── import_data.py            # CLI script to populate MongoDB from CSV
├── tests/                        # Comprehensive unit tests (100% pass)
├── requirements.txt              # Backend dependencies
├── .env.example                  # Environment configuration template
└── README.md                     # This documentation
```

### Key Capabilities
1. **Robust Ingestion & Deduplication**:
   - Parses dates flexibly (`YYYY-MM-DD`, `DD.MM.YYYY`, `DD-MM-YYYY`) and validates non-negative consumption numbers.
   - Prevents duplicate entries using MongoDB unique index on `date` and atomic upsert operations.
   - Gracefully falls back to the local repository dataset (`data/preprocessed_energy.csv`) if MongoDB is offline, ensuring uninterrupted demonstrations.
2. **Defensible 3-Month ML Forecasting**:
   - Out-of-sample 92-day daily forecast (August 1 to October 31, 2026).
   - Regularized Ridge model with calendar features evaluated against a historical day-of-week moving average baseline.
   - 95% confidence intervals derived from residual standard error.
   - Explicit scientific disclosure: clearly notes that a single month of training data (31 days in July 2026) cannot capture annual seasonality or multi-month weather transitions.
3. **Statistical & Machine Learning Anomaly Detection**:
   - Combines a 2-sigma statistical threshold with multi-feature **Isolation Forest**.
   - Identifies specific driver facilities (e.g. Chiller surges, Academic Block peaks, Diesel backup runs) with explanatory messages noting operational variance rather than confirmed equipment defects.
4. **Evidence-Based Recommendations**:
   - Grounded in empirical facility patterns: Chilled water temperature resets (+1°C), weekend academic baseload curtailment, diesel generator coordination, and solar-STP load shifting.
   - Financial savings calculated using standard educational HT commercial tariff (₹8.50/kWh).
   - Carbon savings calculated using official Indian Central Electricity Authority (CEA) grid factor (0.72 kg CO₂/kWh).

---

## 🚀 Setup & Execution Guide (Windows PowerShell)

Open **Windows PowerShell** in the project root directory:
```powershell
cd c:\Users\VARSHA\OneDrive\Desktop\Smart-Energy-consumption
```

### 1. Create a Python Virtual Environment
```powershell
python -m venv .venv
```

### 2. Activate the Virtual Environment
```powershell
.\.venv\Scripts\Activate.ps1
```
*(If script execution is disabled on your machine, run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` once).*

### 3. Install Dependencies
```powershell
pip install --upgrade pip
pip install -r backend/requirements.txt
```

### 4. Configure Environment Variables
Copy the sample environment file:
```powershell
Copy-Item backend/.env.example backend/.env
```
Default values inside `backend/.env`:
```ini
MONGODB_URI=mongodb://localhost:27017
DATABASE_NAME=smart_energy_db
ENERGY_COLLECTION=energy_records
HOST=127.0.0.1
PORT=8000
GRID_EMISSION_FACTOR_KG_CO2_PER_KWH=0.72
DEFAULT_TARIFF_INR_PER_KWH=8.50
```

---

## 🗄️ MongoDB Configuration & Data Import

### Starting MongoDB Service
- **If running local MongoDB Service (Windows Service)**:
  ```powershell
  Start-Service -Name MongoDB
  ```
- **If running MongoDB as a standalone executable**:
  ```powershell
  mongod --dbpath "C:\data\db"
  ```
- **If using MongoDB Atlas (Cloud)**:
  Set `MONGODB_URI="mongodb+srv://<username>:<password>@cluster0.mongodb.net/?retryWrites=true&w=majority"` in `backend/.env`.

> **Note on Fallback**: If MongoDB is not running, the backend automatically operates in **Local Dataset Fallback Mode**, serving data directly from `data/preprocessed_energy.csv` without throwing unhandled crashes!

### Importing the CSV Dataset into MongoDB
Run the CLI ingestion script:
```powershell
python backend/scripts/import_data.py
```
To import an alternative CSV file:
```powershell
python backend/scripts/import_data.py --file "path\to\custom_energy_data.csv"
```

---

## ⚡ Starting the FastAPI Backend

Run the Uvicorn development server:
```powershell
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Initializing MongoDB connection...
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

### Interactive API Documentation (Swagger & ReDoc)
Open your browser to test endpoints interactively:
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## 🖥️ Starting the Streamlit Frontend

Open a new PowerShell window, activate the virtual environment, and launch Streamlit:
```powershell
cd c:\Users\VARSHA\OneDrive\Desktop\Smart-Energy-consumption
.\.venv\Scripts\Activate.ps1
streamlit run app.py
```
The dashboard will open automatically in your browser at:
`http://localhost:8501`

### Verifying Frontend-to-Backend Connectivity
- Look at the sidebar:
  - **🟢 Backend & MongoDB: Online**: Backend connected to live database.
  - **🟡 Backend: Online (Dataset Mode)**: Backend serving preprocessed dataset while MongoDB is idle.
- Check the **📊 Dashboard**: KPI cards and Plotly charts will populate with live backend data.
- Check the **📈 Analytics** tabs:
  - **🔮 Forecast**: Inspect the 92-day forecast curve with 95% confidence intervals and validation metrics.
  - **⚠️ Anomaly**: View detected operational outliers and driver explanations.
  - **🌱 Carbon & Cost**: Inspect verifiable emissions and tariff calculations.
- Check the **💡 Insights** tab: View actionable recommendations with savings in kWh, ₹, and CO₂.

---

## 🧪 Running Unit Tests

Run the full automated test suite covering endpoints, schema validations, forecasting, anomalies, recommendations, and database disconnection handling:
```powershell
python -m unittest discover -s backend/tests -p "test_*.py" -v
```
All 23 tests should pass:
```
Ran 23 tests in 51s
OK
```

---

## 🛠️ Common Troubleshooting

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| `Status: Degraded (MongoDB disconnected)` | MongoDB service is not started on `localhost:27017` | Backend continues to serve requests via local CSV fallback. To connect live DB, start MongoDB service or update `MONGODB_URI` in `.env`. |
| `ModuleNotFoundError: No module named 'backend'` | Running script from inside a subfolder | Always execute commands from project root or ensure `PYTHONPATH=.` |
| `Import error / file format rejected` | Uploaded file is not CSV/XLSX or is missing required columns | Ensure dataset has columns: `Date`, `TNEB_Campus`, `TNEB_New_STP`, `Solar`, `Diesel`, `Biogas`, `Staff_Quarters`, `Academic_Blocks`, `Hostels`, `Chiller`, `STP`, `Total`. |
| `CORS Error in Browser` | Cross-origin request blocked | Add the frontend origin to `CORS_ORIGINS` in `backend/app/config.py` or `.env`. |
