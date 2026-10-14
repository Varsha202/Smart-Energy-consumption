"""
Centralized API Client for Smart Campus Energy Analytics Frontend.
Connects Streamlit interface to FastAPI backend with configurable API_BASE_URL,
robust error handling, timeouts, and fallback resilience.
"""
import os
import logging
from typing import Optional, Dict, Any, Tuple
import requests

logger = logging.getLogger("energy_frontend.api_client")


class APIClient:
    """Centralized client for interacting with the Smart Campus Energy Backend API."""

    def __init__(self, base_url: Optional[str] = None, timeout: float = 8.0):
        self.base_url = (base_url or os.getenv("API_BASE_URL", "http://127.0.0.1:8000")).rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

    def _url(self, path: str) -> str:
        if not path.startswith("/"):
            path = "/" + path
        return f"{self.base_url}{path}"

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Execute an HTTP request with error trapping and friendly messages.
        Returns: (response_data_dict, error_string)
        """
        t = timeout or self.timeout
        try:
            res = self.session.request(
                method=method,
                url=self._url(path),
                params=params,
                json=json_data,
                files=files,
                timeout=t
            )
            if res.status_code in (200, 201):
                try:
                    return res.json(), None
                except ValueError:
                    return None, "Backend returned invalid non-JSON data."
            elif res.status_code == 503:
                # Service Unavailable / DB disconnected
                detail = "Database or backend service is temporarily degraded/unavailable."
                try:
                    err_json = res.json()
                    detail = err_json.get("detail") or err_json.get("message") or detail
                except Exception:
                    pass
                return None, f"Service Notice (503): {detail}"
            else:
                err_msg = f"HTTP {res.status_code}"
                try:
                    err_json = res.json()
                    err_msg = err_json.get("detail") or err_json.get("message") or err_msg
                except Exception:
                    if res.text:
                        err_msg = f"{err_msg}: {res.text[:120]}"
                return None, err_msg

        except requests.exceptions.Timeout:
            return None, f"Request timed out after {t}s connecting to {self.base_url}."
        except requests.exceptions.ConnectionError:
            return None, f"Cannot connect to backend at {self.base_url}. Ensure the FastAPI server is running."
        except requests.exceptions.RequestException as e:
            return None, f"Request failed: {str(e)}"

    # ---------------- HEALTH & SYSTEM ----------------
    def check_health(self) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Verify API health status and database connectivity."""
        return self._request("GET", "/health", timeout=3.0)

    # ---------------- ENERGY DATA ----------------
    def get_energy_records(
        self,
        page: int = 1,
        limit: int = 50,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Fetch paginated energy records with optional date range filters."""
        params: Dict[str, Any] = {"page": page, "limit": limit}
        if start_date:
            params["start_date"] = str(start_date)
        if end_date:
            params["end_date"] = str(end_date)
        return self._request("GET", "/api/energy", params=params)

    def create_energy_record(self, record_data: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Submit a single daily energy consumption record."""
        return self._request("POST", "/api/energy", json_data=record_data)

    def import_dataset_file(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str = "text/csv"
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Upload a CSV or Excel file for ingestion and database upsert."""
        files = {"file": (filename, file_bytes, content_type)}
        return self._request("POST", "/api/energy/import", files=files, timeout=20.0)

    def import_default_dataset(self) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Trigger ingestion of the repository standard dataset into MongoDB."""
        return self._request("POST", "/api/energy/import?use_default_dataset=true", timeout=20.0)

    # ---------------- ANALYTICS ----------------
    def get_analytics_summary(self) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Fetch overall campus consumption KPIs, source breakdown, and facility totals."""
        return self._request("GET", "/api/analytics/summary")

    def get_daily_series(self) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Fetch historical daily consumption time series segmented by facility."""
        return self._request("GET", "/api/analytics/daily")

    def get_facility_breakdown(self) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Fetch total consumption and percentage share per facility."""
        return self._request("GET", "/api/analytics/facilities")

    # ---------------- MACHINE LEARNING ----------------
    def get_forecast(self) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Fetch 92-day daily out-of-sample forecast with confidence bounds and metrics."""
        return self._request("GET", "/api/forecast")

    def get_anomalies(self) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Fetch detected energy consumption anomalies with feature explanations."""
        return self._request("GET", "/api/anomalies")

    # ---------------- RECOMMENDATIONS ----------------
    def get_recommendations(self) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Fetch evidence-based energy conservation actions and estimated impact."""
        return self._request("GET", "/api/recommendations")


# Default client instance
api_client = APIClient()
