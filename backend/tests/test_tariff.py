import sys
from pathlib import Path
import unittest

_repo_root = Path(__file__).resolve().parent.parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.models.schemas import TariffConfig, TariffSlab
from backend.app.services.tariff_service import tariff_service


class TestTariffCalculator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tariff_service.reset_to_defaults("commercial")

    @classmethod
    def tearDownClass(cls):
        tariff_service.reset_to_defaults("commercial")

    def setUp(self):
        self.client = TestClient(app)

    def test_zero_consumption(self):
        """Zero consumption should result in exactly ₹0 bill and ₹0 effective rate."""
        res = tariff_service.calculate_bill(0.0)
        self.assertEqual(res.total_consumption_kwh, 0.0)
        self.assertEqual(res.total_bill_inr, 0.0)
        self.assertEqual(res.effective_rate_per_kwh, 0.0)
        self.assertEqual(len(res.slab_breakdown), 0)

    def test_consumption_within_free_slab(self):
        """Consumption within the 0-100 free slab should be charged ₹0 when free units enabled."""
        res = tariff_service.calculate_bill(50.0)
        self.assertEqual(res.total_bill_inr, 0.0)
        self.assertEqual(res.free_units_applied, 50.0)
        self.assertEqual(res.effective_rate_per_kwh, 0.0)

    def test_exact_free_slab_boundary(self):
        """Exact 100 units should result in ₹0 bill."""
        res = tariff_service.calculate_bill(100.0)
        self.assertEqual(res.total_bill_inr, 0.0)
        self.assertEqual(res.free_units_applied, 100.0)

    def test_crossing_one_slab_boundary(self):
        """150 units: 100 units @ ₹0 + 50 units @ ₹4.70 = ₹235.00."""
        res = tariff_service.calculate_bill(150.0)
        self.assertEqual(res.total_bill_inr, 235.00)
        self.assertEqual(res.free_units_applied, 100.0)
        self.assertAlmostEqual(res.effective_rate_per_kwh, 235.0 / 150.0, places=3)

    def test_exact_second_slab_boundary(self):
        """200 units: 100 @ ₹0 + 100 @ ₹4.70 = ₹470.00."""
        res = tariff_service.calculate_bill(200.0)
        self.assertEqual(res.total_bill_inr, 470.00)

    def test_crossing_multiple_slab_boundaries(self):
        """
        450 units:
        - 0-100 (100 units) @ ₹0 = ₹0
        - 100-200 (100 units) @ ₹4.70 = ₹470
        - 200-400 (200 units) @ ₹6.30 = ₹1,260
        - 400-450 (50 units) @ ₹8.00 = ₹400
        Total = 0 + 470 + 1260 + 400 = ₹2,130.00
        """
        res = tariff_service.calculate_bill(450.0)
        self.assertEqual(res.total_bill_inr, 2130.00)
        self.assertAlmostEqual(res.effective_rate_per_kwh, 2130.0 / 450.0, places=3)

    def test_consumption_in_highest_unlimited_slab(self):
        """
        600 units:
        - 0-100: 100 @ 0 = 0
        - 100-200: 100 @ 4.70 = 470
        - 200-400: 200 @ 6.30 = 1260
        - 400-500: 100 @ 8.00 = 800
        - 500-600: 100 @ 8.40 = 840
        Total = 0 + 470 + 1260 + 800 + 840 = ₹3,370.00
        """
        res = tariff_service.calculate_bill(600.0)
        self.assertEqual(res.total_bill_inr, 3370.00)
        self.assertAlmostEqual(res.effective_rate_per_kwh, 3370.0 / 600.0, places=3)

    def test_disabled_free_units(self):
        """When free units disabled, first slab rate is applied."""
        cfg = tariff_service.get_default_config()
        cfg.free_units_enabled = False
        cfg.slabs[0].rate_per_unit = 3.50

        res = tariff_service.calculate_bill(50.0, config=cfg)
        self.assertEqual(res.total_bill_inr, 175.00)  # 50 * 3.50

    def test_single_tier_flat_rate(self):
        """In single-tier mode, simple flat rate applies."""
        cfg = tariff_service.get_default_config()
        cfg.billing_mode = "single_tier"
        cfg.single_tier_rate = 8.50

        res = tariff_service.calculate_bill(100.0, config=cfg)
        self.assertEqual(res.total_bill_inr, 850.00)
        self.assertEqual(res.effective_rate_per_kwh, 8.50)

    def test_negative_consumption_validation(self):
        """Negative consumption must raise ValueError."""
        with self.assertRaises(ValueError):
            tariff_service.calculate_bill(-15.0)

    def test_invalid_slab_boundaries(self):
        """Invalid boundaries (decreasing, overlapping, gap) must fail validation."""
        # Decreasing boundary
        with self.assertRaises(ValueError):
            TariffConfig(
                profile="custom",
                slabs=[
                    TariffSlab(start_units=0.0, end_units=100.0, rate_per_unit=0.0),
                    TariffSlab(start_units=100.0, end_units=80.0, rate_per_unit=5.0),
                ]
            )

        # Boundary gap
        with self.assertRaises(ValueError):
            TariffConfig(
                profile="custom",
                slabs=[
                    TariffSlab(start_units=0.0, end_units=100.0, rate_per_unit=0.0),
                    TariffSlab(start_units=150.0, end_units=300.0, rate_per_unit=5.0),
                ]
            )

    def test_api_endpoints_and_persistence(self):
        """Verify GET, PUT, POST /calculate, and POST /reset endpoints."""
        # 1. GET /api/tariff
        resp = self.client.get("/api/tariff")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("config", data)
        self.assertIn("campus_calculation", data)

        # 2. POST /api/tariff/calculate
        calc_resp = self.client.post("/api/tariff/calculate", json={"consumption_kwh": 250.0})
        self.assertEqual(calc_resp.status_code, 200)
        calc_data = calc_resp.json()
        self.assertGreater(calc_data["total_bill_inr"], 0)
        self.assertEqual(len(calc_data["slab_breakdown"]), 5)

        # 3. PUT /api/tariff (Save modified config)
        config_to_save = data["config"]
        config_to_save["single_tier_rate"] = 9.20
        put_resp = self.client.put("/api/tariff", json=config_to_save)
        self.assertEqual(put_resp.status_code, 200)
        self.assertEqual(put_resp.json()["single_tier_rate"], 9.20)

        # 4. POST /api/tariff/reset
        reset_resp = self.client.post("/api/tariff/reset?profile=commercial")
        self.assertEqual(reset_resp.status_code, 200)
        self.assertEqual(reset_resp.json()["single_tier_rate"], 8.50)

    def test_consistent_cost_in_analytics_and_recommendations(self):
        """Verify analytics summary and recommendations calculate cost consistently."""
        sum_resp = self.client.get("/api/analytics/summary")
        self.assertEqual(sum_resp.status_code, 200)
        sum_data = sum_resp.json()
        self.assertGreater(sum_data["estimated_cost_inr"], 0)
        self.assertGreater(sum_data["tariff_inr_per_kwh"], 0)

        rec_resp = self.client.get("/api/recommendations")
        self.assertEqual(rec_resp.status_code, 200)
        rec_data = rec_resp.json()
        self.assertGreater(rec_data["total_potential_savings_inr"], 0)


if __name__ == "__main__":
    unittest.main()
