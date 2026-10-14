from backend.app.routes.health import router as health_router
from backend.app.routes.energy import router as energy_router
from backend.app.routes.analytics import router as analytics_router
from backend.app.routes.forecast import router as forecast_router
from backend.app.routes.anomalies import router as anomalies_router
from backend.app.routes.recommendations import router as recommendations_router

__all__ = [
    "health_router",
    "energy_router",
    "analytics_router",
    "forecast_router",
    "anomalies_router",
    "recommendations_router"
]
