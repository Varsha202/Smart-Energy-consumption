from .health import router as health_router
from .energy import router as energy_router
from .analytics import router as analytics_router
from .forecast import router as forecast_router
from .anomalies import router as anomalies_router
from .recommendations import router as recommendations_router
from .tariff import router as tariff_router
from .notifications import router as notifications_router

__all__ = [
    "health_router",
    "energy_router",
    "analytics_router",
    "forecast_router",
    "anomalies_router",
    "recommendations_router",
    "tariff_router",
    "notifications_router"
]

