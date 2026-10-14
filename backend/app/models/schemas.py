import re
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------- HEALTH & STATUS ----------------

class ServiceStatusResponse(BaseModel):
    message: str = "Smart Campus Energy Backend API"
    status: str = "running"
    version: str = "1.0.0"


class HealthResponse(BaseModel):
    status: str  # healthy, degraded, unhealthy
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str
    database: str  # connected, disconnected
    database_name: str
    collection_name: str
    details: Optional[str] = None


# ---------------- ENERGY DATA SCHEMAS ----------------

def parse_and_normalize_date(v: Any) -> str:
    """Normalize incoming date to standard ISO format (YYYY-MM-DD)."""
    if isinstance(v, datetime):
        return v.strftime("%Y-%m-%d")
    if not isinstance(v, str):
        raise ValueError("Date must be a string or datetime object")
    
    clean_date = v.strip()
    # Check for DD.MM.YYYY
    if re.match(r"^\d{2}\.\d{2}\.\d{4}$", clean_date):
        parts = clean_date.split(".")
        return f"{parts[2]}-{parts[1]}-{parts[0]}"
    # Check for DD-MM-YYYY
    elif re.match(r"^\d{2}-\d{2}-\d{4}$", clean_date):
        parts = clean_date.split("-")
        return f"{parts[2]}-{parts[1]}-{parts[0]}"
    # Check for YYYY-MM-DD
    elif re.match(r"^\d{4}-\d{2}-\d{2}$", clean_date):
        return clean_date
    # Try generic parsing
    for fmt in ("%d.%m.%Y", "%d-%m-%Y", "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
        try:
            dt = datetime.strptime(clean_date, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    raise ValueError(f"Unrecognized date format: '{v}'. Supported formats: YYYY-MM-DD, DD.MM.YYYY, DD-MM-YYYY")


class EnergyRecordBase(BaseModel):
    date: str = Field(..., description="Date in YYYY-MM-DD format (or DD.MM.YYYY which will be normalized)")
    tneb_campus: float = Field(..., ge=0, description="TNEB Campus Grid Electricity (kWh)")
    tneb_new_stp: float = Field(..., ge=0, description="TNEB New STP Grid Electricity (kWh)")
    solar: float = Field(..., ge=0, description="Solar Generation (kWh)")
    diesel: float = Field(0.0, ge=0, description="Diesel Backup Generator (kWh)")
    biogas: float = Field(0.0, ge=0, description="Biogas Generation (kWh)")
    staff_quarters: float = Field(..., ge=0, description="Staff Quarters Consumption (kWh)")
    academic_blocks: float = Field(..., ge=0, description="Academic Blocks Consumption (kWh)")
    hostels: float = Field(..., ge=0, description="Hostels Consumption (kWh)")
    chiller: float = Field(..., ge=0, description="Chiller Plant Consumption (kWh)")
    stp: float = Field(..., ge=0, description="STP Consumption (kWh)")
    total: Optional[float] = Field(None, ge=0, description="Total Campus Consumption (kWh)")

    @field_validator("date", mode="before")
    def validate_date(cls, v):
        return parse_and_normalize_date(v)

    @model_validator(mode="after")
    def validate_or_compute_total(self):
        facility_sum = (
            self.staff_quarters +
            self.academic_blocks +
            self.hostels +
            self.chiller +
            self.stp
        )
        if self.total is None or self.total <= 0:
            self.total = facility_sum
        return self


class EnergyRecordCreate(EnergyRecordBase):
    pass


class EnergyRecordResponse(EnergyRecordBase):
    id: Optional[str] = Field(None, alias="_id")

    class Config:
        populate_by_name = True


class EnergyListResponse(BaseModel):
    total_records: int
    page: int
    limit: int
    total_pages: int
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    records: List[EnergyRecordResponse]


class ImportResponse(BaseModel):
    message: str
    total_rows_processed: int
    imported_count: int
    updated_count: int
    skipped_count: int
    errors: List[str] = []


# ---------------- ANALYTICS SCHEMAS ----------------

class MetricWithPercent(BaseModel):
    kwh: float
    percentage: float


class AnalyticsSummaryResponse(BaseModel):
    total_consumption_kwh: float
    average_daily_consumption_kwh: float
    min_daily_consumption_kwh: float
    max_daily_consumption_kwh: float
    peak_day: Optional[str] = None
    lowest_day: Optional[str] = None
    total_records: int
    date_range: Dict[str, str]
    sources_breakdown: Dict[str, MetricWithPercent]
    facilities_breakdown: Dict[str, MetricWithPercent]
    carbon_emissions_kg_co2: float
    estimated_cost_inr: float
    carbon_factor_kg_co2_per_kwh: float
    tariff_inr_per_kwh: float


class DailySeriesItem(BaseModel):
    date: str
    total: float
    tneb_campus: float
    tneb_new_stp: float
    solar: float
    diesel: float
    biogas: float
    staff_quarters: float
    academic_blocks: float
    hostels: float
    chiller: float
    stp: float


class DailyAnalyticsResponse(BaseModel):
    total_days: int
    series: List[DailySeriesItem]


class FacilityMetric(BaseModel):
    facility_name: str
    display_name: str
    total_kwh: float
    daily_avg_kwh: float
    percentage: float
    peak_kwh: float
    peak_date: Optional[str] = None


class FacilitiesResponse(BaseModel):
    total_campus_kwh: float
    facilities: List[FacilityMetric]


# ---------------- FORECAST SCHEMAS ----------------

class ForecastPoint(BaseModel):
    date: str
    predicted_consumption_kwh: float
    lower_bound_kwh: float
    upper_bound_kwh: float
    is_weekend: bool


class ForecastMetrics(BaseModel):
    validation_method: str
    train_records_count: int
    test_records_count: int
    model_mae: float
    model_rmse: float
    model_r2: float
    baseline_mae: float
    baseline_rmse: float
    model_improvement_over_baseline_pct: float


class ForecastResponse(BaseModel):
    model_name: str
    baseline_name: str
    forecast_horizon_days: int
    start_date: str
    end_date: str
    metrics: ForecastMetrics
    forecast: List[ForecastPoint]
    historical_summary: Dict[str, Any]
    disclaimer: str
    data_limitations: str


# ---------------- ANOMALY DETECTION SCHEMAS ----------------

class AnomalyPoint(BaseModel):
    date: str
    observed_kwh: float
    expected_kwh: float
    z_score: float
    is_anomaly: bool
    detection_method: str
    anomaly_score: float
    primary_driver: str
    explanation: str


class AnomaliesResponse(BaseModel):
    total_observations_evaluated: int
    anomalies_detected_count: int
    anomaly_percentage: float
    statistical_threshold_upper: float
    statistical_threshold_lower: float
    anomalies: List[AnomalyPoint]
    all_points: List[AnomalyPoint]
    disclaimer: str


# ---------------- RECOMMENDATION SCHEMAS ----------------

class RecommendationItem(BaseModel):
    id: str
    title: str
    category: str  # Chiller, Solar, Diesel, Baseload, Grid
    priority: str  # High, Medium, Low
    evidence: str
    action_plan: str
    estimated_monthly_savings_kwh: float
    estimated_monthly_savings_inr: float
    estimated_monthly_co2_reduction_kg: float
    assumptions: str


class RecommendationsResponse(BaseModel):
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    campus_monthly_consumption_kwh: float
    total_potential_savings_kwh: float
    total_potential_savings_inr: float
    total_potential_co2_reduction_kg: float
    tariff_inr_per_kwh: float
    grid_emission_factor_kg_co2_per_kwh: float
    recommendations: List[RecommendationItem]
    methodology_notes: str
