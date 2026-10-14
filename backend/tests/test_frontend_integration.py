import unittest
from fastapi.testclient import TestClient
from backend.app.main import app


class TestFrontendAPIIntegration(unittest.TestCase):
    """Verifies that the backend APIs fulfill all data contracts required by the frontend."""

    def setUp(self):
        self.client = TestClient(app)

    def test_frontend_health_and_connection(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("status", data)

    def test_frontend_dashboard_data_contract(self):
        # 1. Summary KPIs for cards
        summary_resp = self.client.get("/api/analytics/summary")
        self.assertEqual(summary_resp.status_code, 200)
        summary = summary_resp.json()
        self.assertIn("total_records", summary)
        self.assertIn("average_daily_consumption_kwh", summary)
        self.assertIn("max_daily_consumption_kwh", summary)
        self.assertIn("carbon_emissions_kg_co2", summary)

        # 2. Daily time series for Plotly line chart
        daily_resp = self.client.get("/api/analytics/daily")
        self.assertEqual(daily_resp.status_code, 200)
        daily = daily_resp.json()
        self.assertTrue(len(daily["series"]) > 0)
        self.assertIn("date", daily["series"][0])
        self.assertIn("total", daily["series"][0])

        # 3. Facility breakdown for Plotly bar chart
        fac_resp = self.client.get("/api/analytics/facilities")
        self.assertEqual(fac_resp.status_code, 200)
        facilities = fac_resp.json()["facilities"]
        self.assertTrue(len(facilities) > 0)
        self.assertIn("facility_name", facilities[0])
        self.assertIn("total_kwh", facilities[0])

    def test_frontend_analytics_tabs_contract(self):
        # Tab 1: Forecast
        forecast_resp = self.client.get("/api/forecast")
        self.assertEqual(forecast_resp.status_code, 200)
        forecast_data = forecast_resp.json()
        self.assertIn("forecast", forecast_data)
        self.assertEqual(len(forecast_data["forecast"]), 92)

        # Tab 2: Anomalies
        anom_resp = self.client.get("/api/anomalies")
        self.assertEqual(anom_resp.status_code, 200)
        anom_data = anom_resp.json()
        self.assertIn("anomalies", anom_data)
        self.assertIn("statistical_threshold_upper", anom_data)

        # Tab 3: Recommendations
        rec_resp = self.client.get("/api/recommendations")
        self.assertEqual(rec_resp.status_code, 200)
        rec_data = rec_resp.json()
        self.assertIn("recommendations", rec_data)
        self.assertGreater(len(rec_data["recommendations"]), 0)


if __name__ == "__main__":
    unittest.main()
