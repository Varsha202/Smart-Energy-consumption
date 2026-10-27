import sys
from pathlib import Path
import unittest
from unittest.mock import patch

_repo_root = Path(__file__).resolve().parent.parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import db_manager, DatabaseUnavailableException


class TestDatabaseFailureHandling(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    @patch.object(db_manager, "ping", return_value=False)
    def test_health_reports_degraded_when_mongodb_down(self, mock_ping):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "degraded")
        self.assertEqual(data["database"], "disconnected")
        self.assertIn("MongoDB is unreachable", data["details"])

    @patch.object(db_manager, "get_database", side_effect=DatabaseUnavailableException("Connection timeout"))
    def test_post_energy_record_returns_503_when_db_down(self, mock_get_db):
        payload = {
            "date": "2026-07-31",
            "tneb_campus": 16960.0,
            "tneb_new_stp": 532.0,
            "solar": 4532.0,
            "diesel": 2800.0,
            "biogas": 364.0,
            "staff_quarters": 1898.0,
            "academic_blocks": 11533.0,
            "hostels": 6858.0,
            "chiller": 4003.0,
            "stp": 896.0
        }
        response = self.client.post("/api/energy", json=payload)
        self.assertEqual(response.status_code, 503)
        data = response.json()
        self.assertIn("detail", data)
        self.assertIn("Database is unavailable", data["detail"])

    @patch.object(db_manager, "ping", return_value=False)
    def test_read_fallback_when_db_down(self, mock_ping):
        # Reads should gracefully fall back to local dataset without crashing
        response = self.client.get("/api/analytics/summary")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total_records"], 31)


if __name__ == "__main__":
    unittest.main()
