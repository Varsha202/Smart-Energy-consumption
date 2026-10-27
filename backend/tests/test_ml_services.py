import sys
from pathlib import Path
import unittest

_repo_root = Path(__file__).resolve().parent.parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from fastapi.testclient import TestClient
from backend.app.main import app


class TestMLServices(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_forecast_endpoint(self):
        response = self.client.get("/api/forecast")
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Horizon verification (3 months = 92 days)
        self.assertEqual(data["forecast_horizon_days"], 92)
        self.assertEqual(len(data["forecast"]), 92)
        self.assertEqual(data["start_date"], "2026-08-01")
        self.assertEqual(data["end_date"], "2026-10-31")

        # Bounds and structure check
        for pt in data["forecast"][:10]:
            self.assertIn("date", pt)
            self.assertIn("predicted_consumption_kwh", pt)
            self.assertIn("lower_bound_kwh", pt)
            self.assertIn("upper_bound_kwh", pt)
            self.assertLessEqual(pt["lower_bound_kwh"], pt["predicted_consumption_kwh"])
            self.assertGreaterEqual(pt["upper_bound_kwh"], pt["predicted_consumption_kwh"])

        # Metrics check
        self.assertIn("metrics", data)
        self.assertGreater(data["metrics"]["model_mae"], 0)
        self.assertGreater(data["metrics"]["baseline_mae"], 0)

        # Clear reliability disclosure check
        self.assertIn("disclaimer", data)
        self.assertIn("31 daily records", data["disclaimer"])

    def test_anomalies_endpoint(self):
        response = self.client.get("/api/anomalies")
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["total_observations_evaluated"], 31)
        self.assertGreaterEqual(data["anomalies_detected_count"], 1)
        self.assertIn("statistical_threshold_upper", data)
        self.assertIn("statistical_threshold_lower", data)

        # Verify anomaly structure and explanation
        for anom in data["anomalies"]:
            self.assertTrue(anom["is_anomaly"])
            self.assertIn("explanation", anom)
            self.assertIn("primary_driver", anom)
            # Ensure safe non-fault phrasing
            self.assertIn("operational variance", anom["explanation"])

        self.assertIn("disclaimer", data)

    def test_recommendations_endpoint(self):
        response = self.client.get("/api/recommendations")
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertGreater(data["total_potential_savings_kwh"], 0)
        self.assertGreater(data["total_potential_savings_inr"], 0)
        self.assertGreater(data["total_potential_co2_reduction_kg"], 0)
        self.assertGreater(len(data["recommendations"]), 0)

        # Check evidence and categories
        categories = [r["category"] for r in data["recommendations"]]
        self.assertTrue(any("HVAC" in c for c in categories))
        self.assertTrue(any("Scheduling" in c for c in categories))

        for rec in data["recommendations"]:
            self.assertTrue(rec["evidence"])
            self.assertTrue(rec["action_plan"])
            self.assertTrue(rec["assumptions"])


if __name__ == "__main__":
    unittest.main()
