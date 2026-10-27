import logging
from typing import Dict, Any, List
import pandas as pd
from ..config import settings
from .energy_service import energy_service
from .tariff_service import tariff_service
from ..models.schemas import (
    AnalyticsSummaryResponse,
    MetricWithPercent,
    DailyAnalyticsResponse,
    DailySeriesItem,
    FacilitiesResponse,
    FacilityMetric
)

logger = logging.getLogger("energy_backend.analytics_service")


FACILITY_DISPLAY_NAMES = {
    "staff_quarters": "Staff Quarters",
    "academic_blocks": "Academic Blocks",
    "hostels": "Hostels",
    "chiller": "Chiller Plant",
    "stp": "Sewage Treatment Plant (STP)"
}

SOURCE_DISPLAY_NAMES = {
    "tneb_campus": "TNEB Campus Grid",
    "tneb_new_stp": "TNEB New STP Grid",
    "solar": "Solar Generation",
    "diesel": "Diesel Backup",
    "biogas": "Biogas Generation"
}


class AnalyticsService:
    """Computes campus-wide KPIs, source/facility breakdowns, and daily time-series."""

    def get_summary(self) -> AnalyticsSummaryResponse:
        """Compute aggregate campus metrics and breakdowns."""
        df = energy_service.get_all_records_as_df()
        if df.empty:
            raise ValueError("No energy records available to calculate analytics.")

        total_kwh = float(df["total"].sum())
        avg_daily = float(df["total"].mean())
        min_daily = float(df["total"].min())
        max_daily = float(df["total"].max())

        peak_row = df.loc[df["total"].idxmax()]
        lowest_row = df.loc[df["total"].idxmin()]
        peak_day = peak_row["date"].strftime("%Y-%m-%d")
        lowest_day = lowest_row["date"].strftime("%Y-%m-%d")

        start_date = df["date"].min().strftime("%Y-%m-%d")
        end_date = df["date"].max().strftime("%Y-%m-%d")

        # Sources Breakdown
        sources = ["tneb_campus", "tneb_new_stp", "solar", "diesel", "biogas"]
        sources_breakdown = {}
        for s in sources:
            if s in df.columns:
                s_sum = float(df[s].sum())
                pct = round((s_sum / total_kwh * 100), 2) if total_kwh > 0 else 0.0
                sources_breakdown[SOURCE_DISPLAY_NAMES.get(s, s)] = MetricWithPercent(
                    kwh=round(s_sum, 2),
                    percentage=pct
                )

        # Facilities Breakdown
        facilities = ["staff_quarters", "academic_blocks", "hostels", "chiller", "stp"]
        facilities_breakdown = {}
        for f in facilities:
            if f in df.columns:
                f_sum = float(df[f].sum())
                pct = round((f_sum / total_kwh * 100), 2) if total_kwh > 0 else 0.0
                facilities_breakdown[FACILITY_DISPLAY_NAMES.get(f, f)] = MetricWithPercent(
                    kwh=round(f_sum, 2),
                    percentage=pct
                )

        # Standard emissions & progressive/configured cost calculation
        carbon_emissions = round(total_kwh * settings.GRID_EMISSION_FACTOR_KG_CO2_PER_KWH, 2)
        tariff_result = tariff_service.calculate_bill(total_kwh)
        estimated_cost = tariff_result.total_bill_inr
        effective_tariff = tariff_result.effective_rate_per_kwh

        return AnalyticsSummaryResponse(
            total_consumption_kwh=round(total_kwh, 2),
            average_daily_consumption_kwh=round(avg_daily, 2),
            min_daily_consumption_kwh=round(min_daily, 2),
            max_daily_consumption_kwh=round(max_daily, 2),
            peak_day=peak_day,
            lowest_day=lowest_day,
            total_records=len(df),
            date_range={"start": start_date, "end": end_date},
            sources_breakdown=sources_breakdown,
            facilities_breakdown=facilities_breakdown,
            carbon_emissions_kg_co2=carbon_emissions,
            estimated_cost_inr=estimated_cost,
            carbon_factor_kg_co2_per_kwh=settings.GRID_EMISSION_FACTOR_KG_CO2_PER_KWH,
            tariff_inr_per_kwh=effective_tariff,
            tariff_mode=tariff_result.billing_mode,
            tariff_profile=tariff_result.profile
        )

    def get_daily_series(self) -> DailyAnalyticsResponse:
        """Returns ordered chronological daily series for visualization."""
        df = energy_service.get_all_records_as_df()
        if df.empty:
            return DailyAnalyticsResponse(total_days=0, series=[])

        series: List[DailySeriesItem] = []
        for _, row in df.iterrows():
            series.append(DailySeriesItem(
                date=row["date"].strftime("%Y-%m-%d"),
                total=round(float(row["total"]), 2),
                tneb_campus=round(float(row.get("tneb_campus", 0)), 2),
                tneb_new_stp=round(float(row.get("tneb_new_stp", 0)), 2),
                solar=round(float(row.get("solar", 0)), 2),
                diesel=round(float(row.get("diesel", 0)), 2),
                biogas=round(float(row.get("biogas", 0)), 2),
                staff_quarters=round(float(row.get("staff_quarters", 0)), 2),
                academic_blocks=round(float(row.get("academic_blocks", 0)), 2),
                hostels=round(float(row.get("hostels", 0)), 2),
                chiller=round(float(row.get("chiller", 0)), 2),
                stp=round(float(row.get("stp", 0)), 2)
            ))

        return DailyAnalyticsResponse(
            total_days=len(series),
            series=series
        )

    def get_facilities_breakdown(self) -> FacilitiesResponse:
        """Returns deep breakdown of each facility's consumption, daily average, and peak day."""
        df = energy_service.get_all_records_as_df()
        if df.empty:
            return FacilitiesResponse(total_campus_kwh=0.0, facilities=[])

        total_campus_kwh = float(df["total"].sum())
        facilities_metrics: List[FacilityMetric] = []
        facilities = ["academic_blocks", "hostels", "chiller", "staff_quarters", "stp"]

        for f in facilities:
            if f in df.columns:
                f_total = float(df[f].sum())
                f_avg = float(df[f].mean())
                pct = (f_total / total_campus_kwh * 100) if total_campus_kwh > 0 else 0.0
                peak_idx = df[f].idxmax()
                peak_row = df.loc[peak_idx]
                peak_kwh = float(peak_row[f])
                peak_date = peak_row["date"].strftime("%Y-%m-%d")

                facilities_metrics.append(FacilityMetric(
                    facility_name=f,
                    display_name=FACILITY_DISPLAY_NAMES.get(f, f.replace("_", " ").title()),
                    total_kwh=round(f_total, 2),
                    daily_avg_kwh=round(f_avg, 2),
                    percentage=round(pct, 2),
                    peak_kwh=round(peak_kwh, 2),
                    peak_date=peak_date
                ))

        # Sort by total consumption descending
        facilities_metrics.sort(key=lambda m: m.total_kwh, reverse=True)

        return FacilitiesResponse(
            total_campus_kwh=round(total_campus_kwh, 2),
            facilities=facilities_metrics
        )


analytics_service = AnalyticsService()
