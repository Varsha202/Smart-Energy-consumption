import unittest
from fastapi.testclient import TestClient
from backend.app.main import app


class TestEnergyAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_list_energy_records(self):
        response = self.client.get("/api/energy?limit=10")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("records", data)
        self.assertIn("total_records", data)
        self.assertIn("page", data)
        self.assertIn("total_pages", data)
        self.assertGreaterEqual(data["total_records"], 31)
        self.assertLessEqual(len(data["records"]), 10)

    def test_pagination(self):
        res1 = self.client.get("/api/energy?page=1&limit=5")
        res2 = self.client.get("/api/energy?page=2&limit=5")
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(res2.status_code, 200)
        page1_dates = [r["date"] for r in res1.json()["records"]]
        page2_dates = [r["date"] for r in res2.json()["records"]]
        # Ensure pages do not overlap
        self.assertFalse(set(page1_dates).intersection(set(page2_dates)))

    def test_date_range_filtering(self):
        response = self.client.get("/api/energy?start_date=2026-07-10&end_date=2026-07-15")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        for r in data["records"]:
            self.assertTrue("2026-07-10" <= r["date"] <= "2026-07-15")

    def test_import_default_dataset(self):
        response = self.client.post("/api/energy/import?use_default_dataset=true")
        # May be 200 or 503 depending on whether MongoDB is locally running
        self.assertIn(response.status_code, [200, 503])
        if response.status_code == 200:
            data = response.json()
            self.assertEqual(data["total_rows_processed"], 31)


if __name__ == "__main__":
    unittest.main()
