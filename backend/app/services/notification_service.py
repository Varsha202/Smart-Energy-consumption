import uuid
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from pymongo import DESCENDING
from pymongo.errors import PyMongoError
from bson import ObjectId

from ..config import settings
from ..database import db_manager, DatabaseUnavailableException
from .energy_service import energy_service
from .anomaly_service import anomaly_service
from ..models.schemas import (
    NotificationItem,
    NotificationListResponse,
    NotificationCheckResponse,
    NotificationMarkReadResponse,
    NotificationSeverity,
    NotificationType
)

logger = logging.getLogger("energy_backend.notification_service")

FACILITY_DISPLAY_NAMES = {
    "academic_blocks": "Academic Blocks",
    "hostels": "Hostels",
    "chiller": "Chiller Plant",
    "staff_quarters": "Staff Quarters",
    "stp": "Sewage Treatment Plant (STP)"
}


class NotificationService:
    """
    Manages campus energy alerts and notifications.
    Supports anomaly-driven alerts, campus peak-consumer tracking,
    and facility-specific baseline surge alerts with robust deduplication.
    Persists in MongoDB Atlas with resilient in-memory fallback.
    """

    def __init__(self):
        # Resilient in-memory fallback store: keyed by dedup_key
        self._memory_store: Dict[str, Dict[str, Any]] = {}
        self._has_run_initial_check: bool = False

    def _get_collection(self):
        """Retrieve MongoDB notification collection if available."""
        return db_manager.get_notification_collection()

    def _doc_to_item(self, doc: Dict[str, Any]) -> NotificationItem:
        """Convert MongoDB document or in-memory dict to NotificationItem schema."""
        doc_id = str(doc.get("_id") or doc.get("id") or uuid.uuid4().hex[:12])
        created_val = doc.get("created_at")
        if isinstance(created_val, datetime):
            created_str = created_val.isoformat()
        elif isinstance(created_val, str):
            created_str = created_val
        else:
            created_str = datetime.utcnow().isoformat()

        return NotificationItem(
            id=doc_id,
            title=doc.get("title", "Energy Alert"),
            message=doc.get("message", ""),
            severity=doc.get("severity", NotificationSeverity.INFO.value),
            notification_type=doc.get("notification_type", NotificationType.ANOMALY.value),
            building=doc.get("building", "Campus Wide"),
            detection_date=doc.get("detection_date"),
            observed_kwh=doc.get("observed_kwh"),
            baseline_kwh=doc.get("baseline_kwh"),
            metric_deviation_pct=doc.get("metric_deviation_pct"),
            dedup_key=doc.get("dedup_key", ""),
            is_read=bool(doc.get("is_read", False)),
            created_at=created_str,
            metadata=doc.get("metadata", {})
        )

    def run_detection_check(
        self,
        peak_threshold_pct: float = 30.0,
        surge_std_dev: float = 2.0
    ) -> NotificationCheckResponse:
        """
        Executes unified detection check:
        1. Anomaly alerts via existing Isolation Forest + 2-Sigma AnomalyService.
        2. High-energy-consumption campus peak alerts.
        3. Facility baseline surge alerts (abnormal consumption relative to own historical baseline).
        Deduplicates every alert by unique dedup_key to prevent redundant notifications.
        """
        candidates: List[Dict[str, Any]] = []

        # ---------------- 1. ANOMALY DETECTION ALERTS ----------------
        try:
            anomaly_result = anomaly_service.detect_anomalies()
            for point in anomaly_result.anomalies:
                driver = point.primary_driver or "Total Campus Load"
                driver_clean = driver.lower().replace(" ", "_")
                dedup_key = f"anomaly:{point.date}:{driver_clean}"

                # Severity attribution based on statistical Z-score and isolation score
                if abs(point.z_score) >= 2.5 or point.anomaly_score < -0.15:
                    severity = NotificationSeverity.CRITICAL.value
                elif abs(point.z_score) >= 2.0:
                    severity = NotificationSeverity.WARNING.value
                else:
                    severity = NotificationSeverity.INFO.value

                building = "Campus Wide" if driver.lower() == "total campus load" else driver

                pct_diff = 0.0
                if point.expected_kwh and point.expected_kwh > 0:
                    pct_diff = round(((point.observed_kwh - point.expected_kwh) / point.expected_kwh) * 100, 2)

                candidates.append({
                    "title": f"Anomaly Detected: {building}",
                    "message": point.explanation,
                    "severity": severity,
                    "notification_type": NotificationType.ANOMALY.value,
                    "building": building,
                    "detection_date": point.date,
                    "observed_kwh": point.observed_kwh,
                    "baseline_kwh": point.expected_kwh,
                    "metric_deviation_pct": pct_diff,
                    "dedup_key": dedup_key,
                    "is_read": False,
                    "created_at": datetime.utcnow(),
                    "metadata": {
                        "z_score": point.z_score,
                        "anomaly_score": point.anomaly_score,
                        "detection_method": point.detection_method,
                        "disclaimer": anomaly_result.disclaimer
                    }
                })
        except Exception as e:
            logger.warning("Anomaly detection check encountered an error: %s", str(e))

        # ---------------- 2. HIGH CONSUMPTION & BASELINE SURGES ----------------
        try:
            df = energy_service.get_all_records_as_df()
            if not df.empty and len(df) >= 5:
                facility_keys = [k for k in FACILITY_DISPLAY_NAMES.keys() if k in df.columns]
                
                if facility_keys:
                    # 2A. Campus Peak Consumer (highest consuming building across period)
                    facility_sums = {k: float(df[k].sum()) for k in facility_keys}
                    total_campus_facility = sum(facility_sums.values())

                    if total_campus_facility > 0:
                        highest_key = max(facility_sums, key=facility_sums.get)
                        highest_kwh = facility_sums[highest_key]
                        highest_share = (highest_kwh / total_campus_facility) * 100
                        highest_name = FACILITY_DISPLAY_NAMES.get(highest_key, highest_key.title())

                        start_str = df["date"].min().strftime("%Y-%m-%d")
                        end_str = df["date"].max().strftime("%Y-%m-%d")
                        peak_dedup = f"high_consumption:campus_peak:{highest_key}:{start_str}_{end_str}"

                        if highest_share >= peak_threshold_pct:
                            candidates.append({
                                "title": f"Campus Peak Consumer: {highest_name}",
                                "message": (
                                    f"{highest_name} is currently the highest energy consumer on campus, "
                                    f"demanding {highest_kwh:,.1f} kWh ({highest_share:.1f}% of total campus facility load). "
                                    f"This exceeds the target peak threshold of {peak_threshold_pct:.0f}%. "
                                    "Prioritize building-level schedule audits, chiller setpoint tuning, and HVAC duty cycling."
                                ),
                                "severity": NotificationSeverity.CRITICAL.value if highest_share >= 45.0 else NotificationSeverity.WARNING.value,
                                "notification_type": NotificationType.HIGH_CONSUMPTION.value,
                                "building": highest_name,
                                "detection_date": end_str,
                                "observed_kwh": round(highest_kwh, 2),
                                "baseline_kwh": round(total_campus_facility / len(facility_keys), 2),
                                "metric_deviation_pct": round(highest_share, 2),
                                "dedup_key": peak_dedup,
                                "is_read": False,
                                "created_at": datetime.utcnow(),
                                "metadata": {
                                    "share_pct": round(highest_share, 2),
                                    "threshold_pct": peak_threshold_pct,
                                    "reporting_period": f"{start_str} to {end_str}",
                                    "facility_total_kwh": round(total_campus_facility, 2)
                                }
                            })

                    # 2B. Historical Baseline Surge per Building (Distinguishing from highest consumer)
                    for f in facility_keys:
                        series = df[f].astype(float)
                        f_mean = float(series.mean())
                        f_std = float(series.std())
                        if f_std <= 0:
                            f_std = 1.0

                        f_name = FACILITY_DISPLAY_NAMES.get(f, f.title())
                        surge_threshold = f_mean + (surge_std_dev * f_std)

                        # Filter days exceeding historical baseline threshold
                        surge_df = df[df[f] > surge_threshold]
                        for _, row in surge_df.iterrows():
                            val = float(row[f])
                            date_str = row["date"].strftime("%Y-%m-%d")
                            z = (val - f_mean) / f_std
                            surge_pct = ((val - f_mean) / f_mean) * 100 if f_mean > 0 else 0.0

                            candidates.append({
                                "title": f"Facility Baseline Surge: {f_name}",
                                "message": (
                                    f"{f_name} consumed {val:,.1f} kWh on {date_str}, an abnormal surge of +{surge_pct:.1f}% "
                                    f"above its own historical baseline average ({f_mean:,.1f} kWh, Z={z:.2f}). "
                                    f"This spike is specific to {f_name}'s baseline and requires operational inspection."
                                ),
                                "severity": NotificationSeverity.CRITICAL.value if z >= 2.5 else NotificationSeverity.WARNING.value,
                                "notification_type": NotificationType.BASELINE_SURGE.value,
                                "building": f_name,
                                "detection_date": date_str,
                                "observed_kwh": round(val, 2),
                                "baseline_kwh": round(f_mean, 2),
                                "metric_deviation_pct": round(surge_pct, 2),
                                "dedup_key": f"baseline_surge:{f}:{date_str}",
                                "is_read": False,
                                "created_at": datetime.utcnow(),
                                "metadata": {
                                    "z_score": round(z, 2),
                                    "baseline_mean_kwh": round(f_mean, 2),
                                    "standard_deviation": round(f_std, 2)
                                }
                            })
        except Exception as e:
            logger.warning("High consumption baseline check encountered an error: %s", str(e))

        # ---------------- 3. PERSISTENCE & DEDUPLICATION ----------------
        new_count = self._persist_candidates(candidates)
        self._has_run_initial_check = True

        total_count, unread_count = self._get_counts()
        return NotificationCheckResponse(
            message=f"Detection check completed. {new_count} new alerts generated.",
            new_notifications_count=new_count,
            total_notifications=total_count,
            unread_count=unread_count
        )

    def _persist_candidates(self, candidates: List[Dict[str, Any]]) -> int:
        """
        Inserts new candidates using dedup_key.
        Avoids creating duplicate notifications for existing alerts.
        """
        new_count = 0
        try:
            collection = self._get_collection()
            for item in candidates:
                key = item["dedup_key"]
                # Upsert using $setOnInsert so existing alerts are NEVER overwritten or duplicated
                res = collection.update_one(
                    {"dedup_key": key},
                    {"$setOnInsert": item},
                    upsert=True
                )
                if res.upserted_id is not None:
                    new_count += 1
                # Sync to in-memory fallback
                if key not in self._memory_store:
                    item_copy = dict(item)
                    item_copy["_id"] = str(res.upserted_id or uuid.uuid4().hex[:12])
                    self._memory_store[key] = item_copy
            return new_count
        except (DatabaseUnavailableException, PyMongoError) as e:
            logger.info("MongoDB unavailable for notifications (%s), using in-memory store.", str(e))
            for item in candidates:
                key = item["dedup_key"]
                if key not in self._memory_store:
                    item_copy = dict(item)
                    item_copy["_id"] = uuid.uuid4().hex[:12]
                    self._memory_store[key] = item_copy
                    new_count += 1
            return new_count

    def _get_counts(self) -> Tuple[int, int]:
        """Returns (total_notifications, unread_count)."""
        try:
            collection = self._get_collection()
            total = collection.count_documents({})
            unread = collection.count_documents({"is_read": False})
            return total, unread
        except (DatabaseUnavailableException, PyMongoError):
            total = len(self._memory_store)
            unread = sum(1 for item in self._memory_store.values() if not item.get("is_read", False))
            return total, unread

    def list_notifications(
        self,
        unread_only: bool = False,
        severity: Optional[str] = None,
        building: Optional[str] = None,
        limit: int = 50,
        skip: int = 0
    ) -> NotificationListResponse:
        """Retrieve paginated and filtered notification list."""
        # Auto-run initial detection if store is empty
        total_count, _ = self._get_counts()
        if total_count == 0 and not self._has_run_initial_check:
            self.run_detection_check()

        try:
            collection = self._get_collection()
            query: Dict[str, Any] = {}
            if unread_only:
                query["is_read"] = False
            if severity:
                query["severity"] = severity.lower()
            if building:
                query["building"] = building

            cursor = (
                collection.find(query)
                .sort("created_at", DESCENDING)
                .skip(skip)
                .limit(limit)
            )
            items = [self._doc_to_item(doc) for doc in cursor]
            total, unread = self._get_counts()
            return NotificationListResponse(
                total=total,
                unread_count=unread,
                items=items
            )
        except (DatabaseUnavailableException, PyMongoError):
            logger.info("Using in-memory store for list_notifications.")
            filtered = list(self._memory_store.values())
            if unread_only:
                filtered = [i for i in filtered if not i.get("is_read", False)]
            if severity:
                filtered = [i for i in filtered if i.get("severity", "").lower() == severity.lower()]
            if building:
                filtered = [i for i in filtered if i.get("building") == building]

            # Sort descending by date/created
            def sort_key(x):
                return str(x.get("created_at", ""))

            filtered.sort(key=sort_key, reverse=True)
            page_slice = filtered[skip : skip + limit]
            items = [self._doc_to_item(doc) for doc in page_slice]
            total, unread = self._get_counts()
            return NotificationListResponse(
                total=total,
                unread_count=unread,
                items=items
            )

    def get_unread_count(self) -> int:
        """Returns the number of unread notifications."""
        _, unread = self._get_counts()
        return unread

    def mark_as_read(self, notification_id: str) -> NotificationMarkReadResponse:
        """Marks a single notification as read."""
        marked = 0
        try:
            collection = self._get_collection()
            filter_query: Dict[str, Any] = {}
            if ObjectId.is_valid(notification_id):
                filter_query = {"$or": [{"_id": ObjectId(notification_id)}, {"_id": notification_id}, {"id": notification_id}]}
            else:
                filter_query = {"$or": [{"_id": notification_id}, {"id": notification_id}]}

            res = collection.update_one(filter_query, {"$set": {"is_read": True}})
            marked = res.modified_count
        except (DatabaseUnavailableException, PyMongoError):
            pass

        # Update in-memory fallback
        for key, item in self._memory_store.items():
            if str(item.get("_id")) == notification_id or str(item.get("id")) == notification_id:
                if not item.get("is_read", False):
                    item["is_read"] = True
                    marked = max(marked, 1)

        _, unread = self._get_counts()
        return NotificationMarkReadResponse(
            success=True,
            marked_count=marked,
            unread_count=unread
        )

    def mark_all_as_read(self) -> NotificationMarkReadResponse:
        """Marks all unread notifications as read."""
        marked = 0
        try:
            collection = self._get_collection()
            res = collection.update_many({"is_read": False}, {"$set": {"is_read": True}})
            marked = res.modified_count
        except (DatabaseUnavailableException, PyMongoError):
            pass

        for item in self._memory_store.values():
            if not item.get("is_read", False):
                item["is_read"] = True
                marked += 1

        _, unread = self._get_counts()
        return NotificationMarkReadResponse(
            success=True,
            marked_count=marked,
            unread_count=unread
        )

    def delete_notification(self, notification_id: str) -> bool:
        """Deletes a notification by id."""
        deleted = False
        try:
            collection = self._get_collection()
            filter_query: Dict[str, Any] = {}
            if ObjectId.is_valid(notification_id):
                filter_query = {"$or": [{"_id": ObjectId(notification_id)}, {"_id": notification_id}, {"id": notification_id}]}
            else:
                filter_query = {"$or": [{"_id": notification_id}, {"id": notification_id}]}

            res = collection.delete_one(filter_query)
            deleted = res.deleted_count > 0
        except (DatabaseUnavailableException, PyMongoError):
            pass

        target_keys = [
            k for k, v in self._memory_store.items()
            if str(v.get("_id")) == notification_id or str(v.get("id")) == notification_id
        ]
        for k in target_keys:
            del self._memory_store[k]
            deleted = True

        return deleted

    def clear_all(self) -> None:
        """Clears all notifications from database and in-memory store."""
        try:
            collection = self._get_collection()
            collection.delete_many({})
        except (DatabaseUnavailableException, PyMongoError):
            pass
        self._memory_store.clear()
        self._has_run_initial_check = False


notification_service = NotificationService()
