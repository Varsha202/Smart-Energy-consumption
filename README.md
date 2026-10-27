# Smart Campus Energy Consumption Analytics System

An AI-driven platform for smart campus energy monitoring, predictive load forecasting, statistical & machine learning anomaly detection, multi-tier tariff estimation, and energy conservation recommendations.

---

## ?? Repository Structure & Branch Architecture

This repository separates the frontend user interface and the backend analytics service across dedicated branches to maintain clean modularity and independent deployment lifecycles:

| Branch | Role | Tech Stack | Quickstart |
| :--- | :--- | :--- | :--- |
| [rontend](https://github.com/Varsha202/Smart-Energy-consumption/tree/frontend) | Complete Web UI Dashboard | Next.js 14 (App Router), React 18, Tailwind CSS, Recharts, TypeScript | 
pm install && npm run dev (Port 3000) |
| [ackend](https://github.com/Varsha202/Smart-Energy-consumption/tree/backend) | REST API & ML Analytics Engine | FastAPI, Python 3.11, MongoDB, Scikit-learn, Uvicorn | uvicorn backend.app.main:app --reload (Port 8000) |
| [main](https://github.com/Varsha202/Smart-Energy-consumption/tree/main) | Repository Overview & Documentation | Markdown | Landing page & branch guide |

---

## ?? Quick Navigation

### 1. Working on the Frontend
Switch to the rontend branch to work on the Next.js user interface:
`ash
git checkout frontend
npm install
npm run dev
`
* **Dashboard URL**: [http://localhost:3000](http://localhost:3000)
* **Configuration**: Set NEXT_PUBLIC_API_BASE_URL in .env.local to point to the FastAPI backend (http://127.0.0.1:8000).

### 2. Working on the Backend
Switch to the ackend branch to work on the FastAPI services, ML models, and database:
`ash
git checkout backend
# Windows PowerShell:
.\backend\.venv\Scripts\Activate.ps1
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
`
* **API Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* **Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
* **Automated Tests**: python -m unittest discover -s backend/tests -p "test_*.py" -v

---

## ??? System Architecture

`
                    +----------------------------------------------+
                    ¦               Next.js Frontend               ¦
                    ¦               (Branch: frontend)             ¦
                    ¦  Executive KPIs | Forecast | Anomaly Alerts  ¦
                    ¦   Tariff Calculator | Realtime Notifications ¦
                    +----------------------------------------------+
                                           ¦ HTTP / JSON
                                           ?
                    +----------------------------------------------+
                    ¦               FastAPI Backend                ¦
                    ¦               (Branch: backend)              ¦
                    ¦  Energy Ingestion | Isolation Forest ML      ¦
                    ¦  Ridge Forecast Engine | Notification Store  ¦
                    +----------------------------------------------+
                                   ¦
                    +-----------------------------+
                    ?                             ?
       +------------------------+    +------------------------+
       ¦   MongoDB Database     ¦    ¦  Local Dataset Fallback¦
       ¦   (Primary Store)      ¦    ¦  (Autonomous Mode)     ¦
       +------------------------+    +------------------------+
`

---

## ?? Development Guidelines

1. **Frontend Development**: All UI components, styles, Next.js routing, and client API services belong exclusively in the rontend branch.
2. **Backend Development**: All API endpoints, ML algorithms, database logic, unit tests, and backend deployment configuration belong exclusively in the ackend branch.
3. **Main Branch Policy**: The main branch serves as the repository entry point and does not contain application code directly.