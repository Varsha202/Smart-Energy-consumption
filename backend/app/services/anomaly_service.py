import logging
from typing import List, Dict, Any
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from backend.app.services.energy_service import energy_service
from backend.app.models.schemas import (
    AnomaliesResponse,
    AnomalyPoint
)

logger = logging.getLogger("energy_backend.anomaly_service")


class AnomalyService:
    """
    Anomaly detection service combining Scikit-learn Isolation Forest with
    a statistical 2-sigma baseline, generating feature-attributed explanations.
    """

    def detect_anomalies(self) -> AnomaliesResponse:
        """Run statistical and Isolation Forest anomaly detection across historical observations."""
        df = energy_service.get_all_records_as_df()
        if df.empty or len(df) < 10:
            raise ValueError(
                f"Insufficient valid data ({len(df)} records). "
                "At least 10 observations are required to reliably perform anomaly detection."
            )

        df = df.sort_values("date").reset_index(drop=True)

        # 1. Statistical Baseline (Mean +/- 2*Std)
        mean_val = float(df["total"].mean())
        std_val = float(df["total"].std())
        if std_val == 0:
            std_val = 1.0

        upper_thresh = mean_val + 2.0 * std_val
        lower_thresh = max(0.0, mean_val - 2.0 * std_val)

        # 2. Scikit-learn Isolation Forest
        feature_cols = ["total", "academic_blocks", "chiller", "hostels", "diesel"]
        # Use existing columns
        active_features = [col for col in feature_cols if col in df.columns]
        X = df[active_features].values

        contamination_rate = 0.10
        iso_forest = IsolationForest(
            contamination=contamination_rate,
            random_state=42,
            n_estimators=100
        )
        iso_forest.fit(X)
        iso_preds = iso_forest.predict(X)  # -1 for anomaly, 1 for normal
        iso_scores = iso_forest.decision_function(X)  # lower score = more abnormal

        # Calculate facility baselines for explanation attribution
        means = df[active_features].mean().to_dict()
        stds = df[active_features].std().replace(0, 1).to_dict()

        anomaly_points: List[AnomalyPoint] = []
        all_points: List[AnomalyPoint] = []

        for idx, row in df.iterrows():
            total = float(row["total"])
            z = (total - mean_val) / std_val
            is_stat_anomaly = (total > upper_thresh) or (total < lower_thresh)
            is_iso_anomaly = (iso_preds[idx] == -1)
            is_anomaly = bool(is_stat_anomaly or is_iso_anomaly)

            date_str = row["date"].strftime("%Y-%m-%d")

            # Determine primary driver and generate evidence-based explanation
            driver = "Total Campus Load"
            max_dev = abs(z)
            for feat in ["chiller", "academic_blocks", "diesel", "hostels"]:
                if feat in row:
                    feat_val = float(row[feat])
                    feat_z = abs(feat_val - means[feat]) / stds[feat]
                    if feat_z > max_dev:
                        max_dev = feat_z
                        driver = feat.replace("_", " ").title()

            if is_anomaly:
                if total > mean_val:
                    direction = "above"
                    detail = f"Peak consumption observed ({int(total):,} kWh), driven predominantly by elevated {driver}."
                else:
                    direction = "below"
                    detail = f"Unusually low consumption observed ({int(total):,} kWh), largely due to reduced {driver}."

                explanation = (
                    f"Consumption of {int(total):,} kWh on {date_str} is {abs(z):.1f} std devs {direction} the monthly mean ({int(mean_val):,} kWh). "
                    f"{detail} "
                    f"Note: This indicates an operational variance requiring review, not a confirmed physical equipment fault."
                )
            else:
                explanation = f"Consumption on {date_str} is within standard operating variance (Z-score: {z:.2f})."

            method = "Isolation Forest + Statistical 2-Sigma" if (is_stat_anomaly and is_iso_anomaly) else (
                "Statistical 2-Sigma Threshold" if is_stat_anomaly else (
                    "Isolation Forest Multi-Feature" if is_iso_anomaly else "Normal Baseline"
                )
            )

            point = AnomalyPoint(
                date=date_str,
                observed_kwh=round(total, 2),
                expected_kwh=round(mean_val, 2),
                z_score=round(float(z), 2),
                is_anomaly=is_anomaly,
                detection_method=method,
                anomaly_score=round(float(iso_scores[idx]), 4),
                primary_driver=driver,
                explanation=explanation
            )

            all_points.append(point)
            if is_anomaly:
                anomaly_points.append(point)

        disclaimer = (
            "ANOMALY EVALUATION NOTICE: Detected anomalies reflect statistical deviations from the observed 31-day operational profile. "
            "Flagged days represent candidates for energy auditing, scheduling reviews, or load curtailment, and should not be interpreted "
            "as verified equipment defects without onsite electrical and mechanical verification."
        )

        return AnomaliesResponse(
            total_observations_evaluated=len(df),
            anomalies_detected_count=len(anomaly_points),
            anomaly_percentage=round(len(anomaly_points) / len(df) * 100, 2),
            statistical_threshold_upper=round(upper_thresh, 2),
            statistical_threshold_lower=round(lower_thresh, 2),
            anomalies=anomaly_points,
            all_points=all_points,
            disclaimer=disclaimer
        )


anomaly_service = AnomalyService()
