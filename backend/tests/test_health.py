import sys
from pathlib import Path
import unittest

_repo_root = Path(__file__).resolve().parent.parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from fastapi.testclient import TestClient
from backend.app.config import settings
from backend.app.main import app


class TestHealthEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_root_status(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["message"], "Smart Campus Energy Backend API")
        self.assertEqual(data["status"], "running")
        self.assertTrue("version" in data)

    def test_health_check(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn(data["status"], ["healthy", "degraded"])
        self.assertIn(data["database"], ["connected", "disconnected"])
        self.assertTrue("timestamp" in data)
        self.assertTrue("version" in data)
        self.assertEqual(data["database_name"], settings.DATABASE_NAME)
        self.assertEqual(data["collection_name"], "energy_records")


if __name__ == "__main__":
    unittest.main()
