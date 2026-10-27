# Smart Campus Energy Consumption Analytics System — Backend API

This is the **backend branch** of the **Smart Campus Energy Consumption Analytics System**. It contains the complete FastAPI REST API, Machine Learning analytics engines, MongoDB persistence, automated test suite, and autonomous dataset fallbacks.

## ?? Repository Structure

`
.
+-- backend/
¦   +-- app/                      # FastAPI core application
¦   ¦   +-- config.py             # Pydantic Settings & environment variables
¦   ¦   +-- database.py           # PyMongo client, safe connection & fallbacks
¦   ¦   +-- main.py               # FastAPI entry point, CORS & lifespans
¦   ¦   +-- models/schemas.py     # Request/response schemas & validators
¦   ¦   +-- routes/               # API endpoints
¦   ¦   ¦   +-- health.py         # GET /, GET /health
¦   ¦   ¦   +-- energy.py         # GET/POST /api/energy, /import
¦   ¦   ¦   +-- analytics.py      # GET /api/analytics/summary, /daily, /facilities
¦   ¦   ¦   +-- forecast.py       # GET /api/forecast (92-day horizon)
¦   ¦   ¦   +-- anomalies.py      # GET /api/anomalies (Isolation Forest + 2-sigma)
¦   ¦   ¦   +-- recommendations.py# GET /api/recommendations (actionable savings)
¦   ¦   ¦   +-- tariff.py         # GET/PUT/POST /api/tariff (slabs & calculations)
¦   ¦   ¦   +-- notifications.py  # GET/POST/PATCH/DELETE /api/notifications
¦   ¦   +-- services/             # Core business & ML logic
¦   +-- api/index.py              # Serverless / Vercel entrypoint
¦   +-- scripts/import_data.py    # CLI ingestion script for MongoDB
¦   +-- tests/                    # 42 automated unit & integration tests
¦   +-- requirements.txt          # Backend Python dependencies
¦   +-- vercel.json               # Vercel deployment configuration
¦   +-- .env.example              # Sample environment template
¦   +-- README.md                 # Detailed module guide
+-- data/
¦   +-- preprocessed_energy.csv   # Local dataset fallback
¦   +-- tariff_config.json        # Tariff configuration fallback
+-- docs/                         # Architecture, methodology, problem formulation
`

## ?? Quickstart (Windows PowerShell)

### 1. Activate Existing Virtual Environment
`powershell
.\backend\.venv\Scripts\Activate.ps1
`
*(Or create a new one: python -m venv backend/.venv and install: pip install -r backend/requirements.txt)*

### 2. Configure Environment
Copy the sample environment file:
`powershell
Copy-Item backend/.env.example backend/.env
`

### 3. Run the Backend Server
`powershell
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
`
Interactive API docs:
- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc
- **Health Check**: http://127.0.0.1:8000/health

### 4. Run Unit & Integration Tests
`powershell
python -m unittest discover -s backend/tests -p "test_*.py" -v
`

> **Autonomous Fallback Mode**: If MongoDB is not running or unreachable, the backend automatically serves analytics and forecasting from data/preprocessed_energy.csv with zero server crashes.
