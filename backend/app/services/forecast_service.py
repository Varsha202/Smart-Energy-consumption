import logging
from datetime import timedelta
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from .energy_service import energy_service
from ..models.schemas import (
    ForecastResponse,
    ForecastMetrics,
    ForecastPoint
)

logger = logging.getLogger("energy_backend.forecast_service")


class ForecastService:
    """
    Forecasting service providing a 3-month daily energy consumption projection.
    Uses Scikit-learn Linear Regression with calendar feature engineering,
    rigorously validated against a day-of-week moving average baseline.
    """

    def _engineer_features(self, dates: pd.Series, base_date: pd.Timestamp) -> pd.DataFrame:
        """Engineer temporal and calendar features without look-ahead data leakage."""
        trend = (dates - base_date).dt.days.values
        day_of_week = dates.dt.dayofweek.values
        is_weekend = (day_of_week >= 5).astype(int)

        # One-hot encode day of week (7 categories, dropping first to avoid collinearity)
        features = pd.DataFrame({
            "trend": trend,
            "is_weekend": is_weekend
        })
        for d in range(1, 7):
            features[f"dow_{d}"] = (day_of_week == d).astype(int)

        return features

    def _time_aware_validation(
        self,
        df: pd.DataFrame,
        base_date: pd.Timestamp
    ) -> Tuple[ForecastMetrics, float]:
        """
        Perform chronological train/test split (first ~70% train, last ~30% test).
        Compares Linear Regression against a Day-of-Week historical mean baseline.
        """
        n = len(df)
        train_size = int(n * 0.70)
        train_df = df.iloc[:train_size].copy()
        test_df = df.iloc[train_size:].copy()

        # Baseline: average consumption per day-of-week observed in training data
        dow_means = train_df.groupby(train_df["date"].dt.dayofweek)["total"].mean().to_dict()
        overall_train_mean = train_df["total"].mean()

        baseline_preds = test_df["date"].dt.dayofweek.map(
            lambda d: dow_means.get(d, overall_train_mean)
        ).values

        # ML Model: Linear Regression
        X_train = self._engineer_features(train_df["date"], base_date)
        y_train = train_df["total"].values

        X_test = self._engineer_features(test_df["date"], base_date)
        y_test = test_df["total"].values

        val_model = Ridge(alpha=1.0)
        val_model.fit(X_train, y_train)
        model_preds = val_model.predict(X_test)

        # Calculate metrics
        b_mae = float(mean_absolute_error(y_test, baseline_preds))
        b_rmse = float(np.sqrt(mean_squared_error(y_test, baseline_preds)))

        m_mae = float(mean_absolute_error(y_test, model_preds))
        m_rmse = float(np.sqrt(mean_squared_error(y_test, model_preds)))
        m_r2 = float(r2_score(y_test, model_preds))

        improvement = ((b_mae - m_mae) / b_mae * 100) if b_mae > 0 else 0.0

        # Calculate residual standard error on train set
        train_preds = val_model.predict(X_train)
        residual_std = float(np.std(y_train - train_preds, ddof=X_train.shape[1]))

        metrics = ForecastMetrics(
            validation_method="Chronological Train/Validation Split (70% train, 30% test)",
            train_records_count=len(train_df),
            test_records_count=len(test_df),
            model_mae=round(m_mae, 2),
            model_rmse=round(m_rmse, 2),
            model_r2=round(m_r2, 4),
            baseline_mae=round(b_mae, 2),
            baseline_rmse=round(b_rmse, 2),
            model_improvement_over_baseline_pct=round(improvement, 2)
        )

        return metrics, residual_std

    def generate_three_month_forecast(self) -> ForecastResponse:
        """
        Generate 3-month daily forecast (92 days: Aug, Sep, Oct 2026).
        Returns model metrics, uncertainty intervals, and explicit reliability disclosures.
        """
        df = energy_service.get_all_records_as_df()
        if df.empty or len(df) < 14:
            raise ValueError(
                f"Insufficient historical data ({len(df)} records). "
                "At least 14 daily records are required to perform baseline modeling and validation."
            )

        df = df.sort_values("date").reset_index(drop=True)
        base_date = df["date"].min()
        last_date = df["date"].max()

        # Perform time-aware validation
        metrics, residual_std = self._time_aware_validation(df, base_date)

        # Train final model on full historical dataset
        X_full = self._engineer_features(df["date"], base_date)
        y_full = df["total"].values

        final_model = Ridge(alpha=1.0)
        final_model.fit(X_full, y_full)

        # Full in-sample residuals for uncertainty bound estimation
        in_sample_preds = final_model.predict(X_full)
        full_residual_std = float(np.std(y_full - in_sample_preds, ddof=X_full.shape[1]))
        if full_residual_std == 0:
            full_residual_std = residual_std or 1000.0

        # Define 3-month horizon (92 days: Aug (31) + Sep (30) + Oct (31) = 92 days)
        forecast_horizon_days = 92
        future_dates = [
            last_date + timedelta(days=i)
            for i in range(1, forecast_horizon_days + 1)
        ]
        future_dates_series = pd.Series(future_dates)
        X_future = self._engineer_features(future_dates_series, base_date)

        future_predictions = final_model.predict(X_future)

        # Build forecast points with 95% confidence bounds (1.96 * residual standard error)
        # Note: uncertainty widens slightly with time step
        forecast_points: List[ForecastPoint] = []
        for i, f_date in enumerate(future_dates):
            pred_kwh = float(future_predictions[i])
            # Expansion factor for out-of-sample uncertainty
            uncertainty_scale = 1.96 * full_residual_std * np.sqrt(1 + (i / forecast_horizon_days) * 0.5)
            lower = max(9000.0, pred_kwh - uncertainty_scale)  # Campus base load clamp
            upper = pred_kwh + uncertainty_scale
            is_wknd = f_date.dayofweek >= 5

            forecast_points.append(ForecastPoint(
                date=f_date.strftime("%Y-%m-%d"),
                predicted_consumption_kwh=round(pred_kwh, 2),
                lower_bound_kwh=round(lower, 2),
                upper_bound_kwh=round(upper, 2),
                is_weekend=bool(is_wknd)
            ))

        disclaimer = (
            "MODEL RELIABILITY DISCLOSURE: This forecast was trained on a single month (31 daily records in July 2026). "
            "While calendar day-of-week patterns and weekend load reductions are statistically captured, a 31-day sample "
            "CANNOT identify annual seasonality, monsoon/weather transitions, semester examination schedules, or academic term breaks. "
            "These projections should be interpreted as trend indicators with widening confidence intervals, not guaranteed commitments."
        )

        data_limitations = (
            f"Historical training window: {len(df)} days ({base_date.strftime('%Y-%m-%d')} to {last_date.strftime('%Y-%m-%d')}). "
            "Feature space includes trend progression and day-of-week indicators. Out-of-sample horizon: 92 days."
        )

        return ForecastResponse(
            model_name="Ridge Regularized Linear Regression (with Day-of-Week & Trend Features)",
            baseline_name="Historical Day-of-Week Mean Baseline",
            forecast_horizon_days=forecast_horizon_days,
            start_date=future_dates[0].strftime("%Y-%m-%d"),
            end_date=future_dates[-1].strftime("%Y-%m-%d"),
            metrics=metrics,
            forecast=forecast_points,
            historical_summary={
                "training_days": len(df),
                "historical_mean_kwh": round(float(df["total"].mean()), 2),
                "historical_min_kwh": round(float(df["total"].min()), 2),
                "historical_max_kwh": round(float(df["total"].max()), 2),
                "forecast_mean_kwh": round(float(np.mean(future_predictions)), 2)
            },
            disclaimer=disclaimer,
            data_limitations=data_limitations
        )


forecast_service = ForecastService()
