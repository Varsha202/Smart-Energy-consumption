import sys
from pathlib import Path
import unittest

_repo_root = Path(__file__).resolve().parent.parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from fastapi.testclient import TestClient
from backend.app.main import app


class TestAnalyticsAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_analytics_summary(self):
        response = self.client.get("/api/analytics/summary")
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertGreater(data["total_consumption_kwh"], 0)
        self.assertGreater(data["average_daily_consumption_kwh"], 0)
        self.assertEqual(data["total_records"], 31)
        self.assertIsNotNone(data["peak_day"])
        self.assertIsNotNone(data["lowest_day"])

        # Check source breakdown exists
        self.assertIn("sources_breakdown", data)
        self.assertIn("TNEB Campus Grid", data["sources_breakdown"])

        # Check facility breakdown exists
        self.assertIn("facilities_breakdown", data)
        self.assertIn("Academic Blocks", data["facilities_breakdown"])

        # Check emissions & cost
        self.assertGreater(data["carbon_emissions_kg_co2"], 0)
        self.assertGreater(data["estimated_cost_inr"], 0)

    def test_daily_series(self):
        response = self.client.get("/api/analytics/daily")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total_days"], 31)
        self.assertEqual(len(data["series"]), 31)
        first_item = data["series"][0]
        self.assertIn("date", first_item)
        self.assertIn("total", first_item)
        self.assertIn("academic_blocks", first_item)

    def test_facilities_breakdown(self):
        response = self.client.get("/api/analytics/facilities")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(data["total_campus_kwh"], 0)
        facilities = data["facilities"]
        self.assertEqual(len(facilities), 5)

        facility_names = [f["facility_name"] for f in facilities]
        self.assertIn("academic_blocks", facility_names)
        self.assertIn("chiller", facility_names)
        self.assertIn("hostels", facility_names)
        self.assertIn("staff_quarters", facility_names)
        self.assertIn("stp", facility_names)

        # Ensure percentages sum close to 100%
        total_pct = sum(f["percentage"] for f in facilities)
        self.assertAlmostEqual(total_pct, 100.0, delta=1.0)


if __name__ == "__main__":
    unittest.main()
