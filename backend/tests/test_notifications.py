import sys
from pathlib import Path
import unittest

_repo_root = Path(__file__).resolve().parent.parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.notification_service import notification_service


class TestNotificationsAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        notification_service.clear_all()

    def tearDown(self):
        notification_service.clear_all()

    def test_run_detection_check_and_deduplication(self):
        """Verify unified detection generates anomaly, peak, and baseline surge alerts without duplicates."""
        # 1. First run generates alerts
        response = self.client.post("/api/notifications/check?peak_threshold_pct=25.0&surge_std_dev=1.8")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(data["new_notifications_count"], 0)
        self.assertGreater(data["total_notifications"], 0)
        self.assertEqual(data["unread_count"], data["total_notifications"])

        first_count = data["total_notifications"]

        # 2. Second run must deduplicate and return 0 new alerts
        response_dup = self.client.post("/api/notifications/check?peak_threshold_pct=25.0&surge_std_dev=1.8")
        self.assertEqual(response_dup.status_code, 200)
        data_dup = response_dup.json()
        self.assertEqual(data_dup["new_notifications_count"], 0)
        self.assertEqual(data_dup["total_notifications"], first_count)

    def test_alert_types_and_fields(self):
        """Verify notifications contain proper structure, severity, facility, dates, and baseline comparisons."""
        self.client.post("/api/notifications/check?peak_threshold_pct=25.0&surge_std_dev=1.8")
        response = self.client.get("/api/notifications?limit=100")
        self.assertEqual(response.status_code, 200)
        data = response.json()

        items = data["items"]
        self.assertGreater(len(items), 0)

        types_found = set(item["notification_type"] for item in items)
        # Should include anomaly alerts
        self.assertIn("anomaly", types_found)
        # Should include high_consumption (campus peak) or baseline_surge
        self.assertTrue(
            "high_consumption" in types_found or "baseline_surge" in types_found,
            "Expected high_consumption or baseline_surge alerts in notifications"
        )

        for item in items:
            self.assertIn("id", item)
            self.assertIn("title", item)
            self.assertIn("message", item)
            self.assertIn("severity", item)
            self.assertIn(item["severity"], ["critical", "warning", "info"])
            self.assertIn("building", item)
            self.assertIsNotNone(item["building"])
            self.assertIn("dedup_key", item)
            self.assertIn("is_read", item)
            self.assertFalse(item["is_read"])
            self.assertIn("created_at", item)

    def test_distinction_highest_consumer_vs_baseline_surge(self):
        """Verify distinction between highest consumer and building-specific baseline surge."""
        self.client.post("/api/notifications/check?peak_threshold_pct=20.0&surge_std_dev=1.5")
        response = self.client.get("/api/notifications?limit=100")
        items = response.json()["items"]

        peak_alerts = [i for i in items if i["notification_type"] == "high_consumption"]
        surge_alerts = [i for i in items if i["notification_type"] == "baseline_surge"]

        if peak_alerts:
            peak = peak_alerts[0]
            self.assertIn("Campus Peak Consumer", peak["title"])
            self.assertIn("metric_deviation_pct", peak)
            self.assertGreater(peak["metric_deviation_pct"], 0)

        if surge_alerts:
            surge = surge_alerts[0]
            self.assertIn("Facility Baseline Surge", surge["title"])
            self.assertIn("Z=", surge["message"])
            self.assertIn("observed_kwh", surge)
            self.assertIn("baseline_kwh", surge)

    def test_unread_count_endpoint(self):
        """Verify unread-count endpoint returns accurate counts."""
        self.client.post("/api/notifications/check?peak_threshold_pct=30.0&surge_std_dev=2.0")
        response = self.client.get("/api/notifications/unread-count")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("unread_count", data)
        self.assertGreater(data["unread_count"], 0)

    def test_mark_individual_and_all_read(self):
        """Verify marking a single notification as read and marking all as read."""
        self.client.post("/api/notifications/check?peak_threshold_pct=30.0&surge_std_dev=2.0")
        list_res = self.client.get("/api/notifications?limit=10")
        items = list_res.json()["items"]
        self.assertGreater(len(items), 1)

        first_id = items[0]["id"]
        initial_unread = list_res.json()["unread_count"]

        # Mark single item as read
        patch_res = self.client.patch(f"/api/notifications/{first_id}/read")
        self.assertEqual(patch_res.status_code, 200)
        patch_data = patch_res.json()
        self.assertTrue(patch_data["success"])
        self.assertEqual(patch_data["marked_count"], 1)
        self.assertEqual(patch_data["unread_count"], initial_unread - 1)

        # Mark all as read
        all_res = self.client.post("/api/notifications/mark-all-read")
        self.assertEqual(all_res.status_code, 200)
        all_data = all_res.json()
        self.assertTrue(all_data["success"])
        self.assertEqual(all_data["unread_count"], 0)

        # Confirm unread_count is 0
        count_res = self.client.get("/api/notifications/unread-count")
        self.assertEqual(count_res.json()["unread_count"], 0)

    def test_filters_and_validation(self):
        """Verify filtering by severity, read status, and invalid query handling."""
        self.client.post("/api/notifications/check?peak_threshold_pct=30.0&surge_std_dev=2.0")

        # Invalid severity should return 400
        bad_res = self.client.get("/api/notifications?severity=invalid_tier")
        self.assertEqual(bad_res.status_code, 400)

        # Filter by critical
        crit_res = self.client.get("/api/notifications?severity=critical")
        self.assertEqual(crit_res.status_code, 200)
        crit_items = crit_res.json()["items"]
        for it in crit_items:
            self.assertEqual(it["severity"], "critical")


if __name__ == "__main__":
    unittest.main()
