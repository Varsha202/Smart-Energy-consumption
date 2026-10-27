export interface HealthResponse {
  status: "healthy" | "degraded" | "unhealthy";
  timestamp: string;
  version: string;
  database: "connected" | "disconnected";
  database_name: string;
  collection_name: string;
  details?: string;
}

export interface EnergyRecord {
  id?: string;
  _id?: string;
  date: string;
  tneb_campus: number;
  tneb_new_stp: number;
  solar: number;
  diesel: number;
  biogas: number;
  staff_quarters: number;
  academic_blocks: number;
  hostels: number;
  chiller: number;
  stp: number;
  total: number;
}

export interface EnergyListResponse {
  total_records: number;
  page: number;
  limit: number;
  total_pages: number;
  start_date?: string | null;
  end_date?: string | null;
  records: EnergyRecord[];
}

export interface ImportResponse {
  message: string;
  total_rows_processed: number;
  imported_count: number;
  updated_count: number;
  skipped_count: number;
  errors: string[];
}

export interface MetricWithPercent {
  kwh: number;
  percentage: number;
}

export interface AnalyticsSummaryResponse {
  total_consumption_kwh: number;
  average_daily_consumption_kwh: number;
  min_daily_consumption_kwh: number;
  max_daily_consumption_kwh: number;
  peak_day?: string | null;
  lowest_day?: string | null;
  total_records: number;
  date_range: {
    start: string;
    end: string;
  };
  sources_breakdown: Record<string, MetricWithPercent>;
  facilities_breakdown: Record<string, MetricWithPercent>;
  carbon_emissions_kg_co2: number;
  estimated_cost_inr: number;
  carbon_factor_kg_co2_per_kwh: number;
  tariff_inr_per_kwh: number;
  tariff_mode?: "progressive" | "single_tier";
  tariff_profile?: string;
}

export interface DailySeriesItem {
  date: string;
  total: number;
  tneb_campus: number;
  tneb_new_stp: number;
  solar: number;
  diesel: number;
  biogas: number;
  staff_quarters: number;
  academic_blocks: number;
  hostels: number;
  chiller: number;
  stp: number;
}

export interface DailyAnalyticsResponse {
  total_days: number;
  series: DailySeriesItem[];
}

export interface FacilityMetric {
  facility_name: string;
  display_name: string;
  total_kwh: number;
  daily_avg_kwh: number;
  percentage: number;
  peak_kwh: number;
  peak_date?: string | null;
}

export interface FacilitiesResponse {
  total_campus_kwh: number;
  facilities: FacilityMetric[];
}

export interface ForecastPoint {
  date: string;
  predicted_consumption_kwh: number;
  lower_bound_kwh: number;
  upper_bound_kwh: number;
  is_weekend: boolean;
}

export interface ForecastMetrics {
  validation_method: string;
  train_records_count: number;
  test_records_count: number;
  model_mae: number;
  model_rmse: number;
  model_r2: number;
  baseline_mae: number;
  baseline_rmse: number;
  model_improvement_over_baseline_pct: number;
}

export interface ForecastResponse {
  model_name: string;
  baseline_name: string;
  forecast_horizon_days: number;
  start_date: string;
  end_date: string;
  metrics: ForecastMetrics;
  forecast: ForecastPoint[];
  historical_summary: Record<string, any>;
  disclaimer: string;
  data_limitations: string;
}

export interface AnomalyPoint {
  date: string;
  observed_kwh: number;
  expected_kwh: number;
  z_score: number;
  is_anomaly: boolean;
  detection_method: string;
  anomaly_score: number;
  primary_driver: string;
  explanation: string;
}

export interface AnomaliesResponse {
  total_observations_evaluated: number;
  anomalies_detected_count: number;
  anomaly_percentage: number;
  statistical_threshold_upper: number;
  statistical_threshold_lower: number;
  anomalies: AnomalyPoint[];
  all_points: AnomalyPoint[];
  disclaimer: string;
}

export interface RecommendationItem {
  id: string;
  title: string;
  category: string;
  priority: "High" | "Medium" | "Low";
  evidence: string;
  action_plan: string;
  estimated_monthly_savings_kwh: number;
  estimated_monthly_savings_inr: number;
  estimated_monthly_co2_reduction_kg: number;
  assumptions: string;
}

export interface RecommendationsResponse {
  generated_at: string;
  campus_monthly_consumption_kwh: number;
  total_potential_savings_kwh: number;
  total_potential_savings_inr: number;
  total_potential_co2_reduction_kg: number;
  tariff_inr_per_kwh: number;
  grid_emission_factor_kg_co2_per_kwh: number;
  recommendations: RecommendationItem[];
  methodology_notes: string;
}

export interface ApiResponse<T> {
  data: T | null;
  error: string | null;
}

export interface TariffSlab {
  start_units: number;
  end_units?: number | null;
  rate_per_unit: number;
  label?: string | null;
}

export interface TariffConfig {
  profile: "commercial" | "domestic" | "custom" | string;
  billing_mode: "progressive" | "single_tier";
  free_units_enabled: boolean;
  free_units_limit: number;
  single_tier_rate: number;
  slabs: TariffSlab[];
  notes?: string;
}

export interface SlabCalculationDetail {
  slab_index: number;
  start_units: number;
  end_units?: number | null;
  rate_per_unit: number;
  units_in_slab: number;
  slab_cost: number;
  label?: string | null;
}

export interface TariffCalculationResult {
  total_consumption_kwh: number;
  total_bill_inr: number;
  effective_rate_per_kwh: number;
  billing_mode: "progressive" | "single_tier";
  profile: string;
  free_units_applied: number;
  slab_breakdown: SlabCalculationDetail[];
  baseline_flat_cost_inr: number;
  cost_difference_inr: number;
  percentage_difference: number;
  notes: string;
}

export interface TariffGetResponse {
  config: TariffConfig;
  campus_consumption_kwh: number;
  campus_calculation: TariffCalculationResult;
}

