"use client";

import { useState, useEffect } from "react";
import { api } from "../lib/api";
import {
  ForecastResponse,
  AnomaliesResponse,
  AnalyticsSummaryResponse,
} from "../types/api";
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import {
  TrendingUp,
  AlertTriangle,
  Leaf,
  DollarSign,
  Info,
  RefreshCw,
  Cpu,
  ShieldAlert,
  Zap,
} from "lucide-react";

interface AnalyticsViewProps {
  refreshTrigger?: number;
}

export default function AnalyticsView({ refreshTrigger = 0 }: AnalyticsViewProps) {
  const [activeSubTab, setActiveSubTab] = useState<"forecast" | "anomaly" | "carbon">("forecast");
  const [forecastData, setForecastData] = useState<ForecastResponse | null>(null);
  const [anomalyData, setAnomalyData] = useState<AnomaliesResponse | null>(null);
  const [summaryData, setSummaryData] = useState<AnalyticsSummaryResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);

    const [fRes, aRes, sRes] = await Promise.all([
      api.getForecast(),
      api.getAnomalies(),
      api.getAnalyticsSummary(),
    ]);

    setForecastData(fRes.data);
    setAnomalyData(aRes.data);
    setSummaryData(sRes.data);

    if (fRes.error && aRes.error && sRes.error) {
      setError(fRes.error || aRes.error || sRes.error);
    }
    setLoading(false);
  };

  useEffect(() => {
    loadData();
  }, [refreshTrigger]);

  const customTooltipStyle = {
    backgroundColor: "#0f172a",
    border: "1px solid rgba(255, 255, 255, 0.15)",
    borderRadius: "12px",
    color: "#ffffff",
    fontSize: "13px",
    padding: "10px 14px",
    boxShadow: "0 10px 25px -5px rgba(0, 0, 0, 0.5)",
  };

  return (
    <div className="space-y-6">
      {/* Sub-tabs Header */}
      <div className="flex items-center gap-2 p-1.5 rounded-2xl bg-white/5 border border-white/10 w-fit">
        <button
          onClick={() => setActiveSubTab("forecast")}
          className={`flex items-center gap-2 px-5 py-2 rounded-xl text-sm font-semibold transition-all duration-200 ${
            activeSubTab === "forecast"
              ? "bg-sky-500 text-slate-950 shadow-md shadow-sky-500/20"
              : "text-slate-300 hover:text-white hover:bg-white/5"
          }`}
        >
          <TrendingUp size={16} /> 🔮 ML Forecast (92-Day)
        </button>
        <button
          onClick={() => setActiveSubTab("anomaly")}
          className={`flex items-center gap-2 px-5 py-2 rounded-xl text-sm font-semibold transition-all duration-200 ${
            activeSubTab === "anomaly"
              ? "bg-rose-500 text-white shadow-md shadow-rose-500/20"
              : "text-slate-300 hover:text-white hover:bg-white/5"
          }`}
        >
          <AlertTriangle size={16} /> ⚠️ Anomaly Detection
        </button>
        <button
          onClick={() => setActiveSubTab("carbon")}
          className={`flex items-center gap-2 px-5 py-2 rounded-xl text-sm font-semibold transition-all duration-200 ${
            activeSubTab === "carbon"
              ? "bg-emerald-500 text-slate-950 shadow-md shadow-emerald-500/20"
              : "text-slate-300 hover:text-white hover:bg-white/5"
          }`}
        >
          <Leaf size={16} /> 🌱 Carbon & Cost
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 flex items-start gap-3 text-sm">
          <AlertTriangle size={18} className="shrink-0 mt-0.5" />
          <div>
            <div className="font-semibold">Notice</div>
            <div className="text-amber-200/80">{error}</div>
          </div>
        </div>
      )}

      {/* ==================== TAB 1: FORECAST ==================== */}
      {activeSubTab === "forecast" && (
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
            <div>
              <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
                <Cpu size={20} className="text-sky-400" />
                3-Month Daily Out-of-Sample Forecast
              </h2>
              <p className="text-xs text-slate-400 mt-1">
                Machine Learning Ridge Regression Model with 95% Confidence Intervals (Aug 1 - Oct 31, 2026)
              </p>
            </div>
          </div>

          {/* Forecast Metric Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="glass-panel p-5">
              <div className="text-xs text-slate-400 font-semibold uppercase tracking-wider mb-1">
                Architecture
              </div>
              <div className="text-xl font-bold text-sky-400">
                {forecastData?.model_name || "Ridge Regression"}
              </div>
              <div className="text-xs text-slate-500 mt-1">L2 Regularized Linear Model</div>
            </div>

            <div className="glass-panel p-5">
              <div className="text-xs text-slate-400 font-semibold uppercase tracking-wider mb-1">
                Validation MAE
              </div>
              <div className="text-xl font-bold text-slate-100">
                {forecastData?.metrics
                  ? `${Math.round(forecastData.metrics.model_mae).toLocaleString()} kWh`
                  : "—"}
              </div>
              <div className="text-xs text-slate-500 mt-1">Mean Absolute Error</div>
            </div>

            <div className="glass-panel p-5">
              <div className="text-xs text-slate-400 font-semibold uppercase tracking-wider mb-1">
                Baseline MAE
              </div>
              <div className="text-xl font-bold text-slate-100">
                {forecastData?.metrics
                  ? `${Math.round(forecastData.metrics.baseline_mae).toLocaleString()} kWh`
                  : "—"}
              </div>
              <div className="text-xs text-slate-500 mt-1">Day-of-Week Naive Baseline</div>
            </div>

            <div className="glass-panel p-5">
              <div className="text-xs text-slate-400 font-semibold uppercase tracking-wider mb-1">
                Improvement
              </div>
              <div className="text-xl font-bold text-emerald-400">
                {forecastData?.metrics
                  ? `+${forecastData.metrics.model_improvement_over_baseline_pct.toFixed(1)}%`
                  : "—"}
              </div>
              <div className="text-xs text-slate-500 mt-1">Outperformance vs Baseline</div>
            </div>
          </div>

          {/* Forecast Area Chart */}
          <div className="glass-panel p-6">
            <h3 className="text-base font-bold text-slate-100 mb-1">
              92-Day Predictive Horizon ({forecastData?.start_date} to {forecastData?.end_date})
            </h3>
            <p className="text-xs text-slate-400 mb-4">
              Solid line depicts predicted daily mean; shaded band indicates 95% confidence interval
            </p>

            <div className="h-[360px] w-full">
              {loading ? (
                <div className="h-full flex items-center justify-center text-slate-400 text-sm">
                  <RefreshCw size={20} className="animate-spin mr-2" /> Generating ML forecast...
                </div>
              ) : !forecastData?.forecast?.length ? (
                <div className="h-full flex items-center justify-center text-slate-400 text-sm">
                  No forecast points returned
                </div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart
                    data={forecastData.forecast}
                    margin={{ top: 10, right: 20, left: 10, bottom: 0 }}
                  >
                    <defs>
                      <linearGradient id="forecastFill" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.25} />
                        <stop offset="95%" stopColor="#38bdf8" stopOpacity={0.0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.08)" vertical={false} />
                    <XAxis
                      dataKey="date"
                      stroke="#64748b"
                      fontSize={11}
                      tickLine={false}
                      tickFormatter={(val) => {
                        try {
                          const d = new Date(val);
                          return `${d.getDate()} ${d.toLocaleString("en-US", { month: "short" })}`;
                        } catch (_) {
                          return val;
                        }
                      }}
                    />
                    <YAxis
                      stroke="#64748b"
                      fontSize={11}
                      tickLine={false}
                      axisLine={false}
                      tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
                    />
                    <Tooltip
                      contentStyle={customTooltipStyle}
                      formatter={(v: any, name: any) => [
                        `${Number(v).toLocaleString()} kWh`,
                        name === "predicted_consumption_kwh"
                          ? "Predicted Daily Consumption"
                          : name === "upper_bound_kwh"
                          ? "Upper 95% Bound"
                          : "Lower 95% Bound",
                      ]}
                      labelFormatter={(lbl) => `Forecast Date: ${lbl}`}
                    />
                    <Legend wrapperStyle={{ paddingTop: "12px", fontSize: "12px" }} />
                    <Area
                      type="monotone"
                      dataKey="upper_bound_kwh"
                      name="Upper 95% Bound"
                      stroke="transparent"
                      fill="#38bdf8"
                      fillOpacity={0.12}
                    />
                    <Area
                      type="monotone"
                      dataKey="lower_bound_kwh"
                      name="Lower 95% Bound"
                      stroke="transparent"
                      fill="#38bdf8"
                      fillOpacity={0.12}
                    />
                    <Line
                      type="monotone"
                      dataKey="predicted_consumption_kwh"
                      name="Predicted Daily Consumption"
                      stroke="#38bdf8"
                      strokeWidth={2.5}
                      dot={false}
                      activeDot={{ r: 6 }}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          {/* Scientific Disclaimer */}
          {forecastData?.disclaimer && (
            <div className="p-4 rounded-xl bg-sky-500/10 border border-sky-500/20 text-sky-200 text-xs flex items-start gap-3">
              <Info size={16} className="shrink-0 mt-0.5 text-sky-400" />
              <div>
                <strong className="text-sky-300">Methodology & Empirical Constraints: </strong>
                {forecastData.disclaimer}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ==================== TAB 2: ANOMALY DETECTION ==================== */}
      {activeSubTab === "anomaly" && (
        <div className="space-y-6">
          <div>
            <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
              <ShieldAlert size={20} className="text-rose-400" />
              Campus Anomaly & Variance Detection
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Ensemble: Multi-Feature Isolation Forest combined with a 2-Sigma Statistical Threshold
            </p>
          </div>

          {/* Anomaly Metrics */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="glass-panel p-5">
              <div className="text-xs text-slate-400 font-semibold uppercase tracking-wider mb-1">
                Evaluated Days
              </div>
              <div className="text-2xl font-bold text-slate-100">
                {anomalyData?.total_observations_evaluated || 0}
              </div>
              <div className="text-xs text-slate-500 mt-1">Total time-series observations</div>
            </div>

            <div className="glass-panel p-5">
              <div className="text-xs text-slate-400 font-semibold uppercase tracking-wider mb-1">
                Detected Anomalies
              </div>
              <div className="text-2xl font-bold text-rose-400">
                {anomalyData?.anomalies_detected_count || 0}
              </div>
              <div className="text-xs text-slate-500 mt-1">
                {anomalyData?.anomaly_percentage?.toFixed(1) || "0.0"}% of observations flagged
              </div>
            </div>

            <div className="glass-panel p-5">
              <div className="text-xs text-slate-400 font-semibold uppercase tracking-wider mb-1">
                Statistical 2σ Threshold
              </div>
              <div className="text-2xl font-bold text-amber-400">
                {anomalyData?.statistical_threshold_upper
                  ? `${Math.round(anomalyData.statistical_threshold_upper).toLocaleString()} kWh`
                  : "—"}
              </div>
              <div className="text-xs text-slate-500 mt-1">Upper operational variance threshold</div>
            </div>
          </div>

          {/* Anomaly Scatter Chart */}
          <div className="glass-panel p-6">
            <h3 className="text-base font-bold text-slate-100 mb-1">
              Campus Daily Observations vs Flagged Anomalies
            </h3>
            <p className="text-xs text-slate-400 mb-4">
              Cyan nodes represent standard baseline operations; Rose nodes represent operational anomalies
            </p>

            <div className="h-[340px] w-full">
              {loading ? (
                <div className="h-full flex items-center justify-center text-slate-400 text-sm">
                  <RefreshCw size={20} className="animate-spin mr-2" /> Evaluating anomalies...
                </div>
              ) : !anomalyData?.all_points?.length ? (
                <div className="h-full flex items-center justify-center text-slate-400 text-sm">
                  No anomaly points evaluated
                </div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart
                    data={anomalyData.all_points}
                    margin={{ top: 10, right: 20, left: 10, bottom: 0 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.08)" vertical={false} />
                    <XAxis
                      dataKey="date"
                      stroke="#64748b"
                      fontSize={11}
                      tickLine={false}
                      tickFormatter={(val) => {
                        try {
                          const d = new Date(val);
                          return `${d.getDate()} ${d.toLocaleString("en-US", { month: "short" })}`;
                        } catch (_) {
                          return val;
                        }
                      }}
                    />
                    <YAxis
                      stroke="#64748b"
                      fontSize={11}
                      tickLine={false}
                      axisLine={false}
                      tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
                    />
                    <Tooltip
                      contentStyle={customTooltipStyle}
                      formatter={(v: any, name: any, item: any) => [
                        `${Number(v).toLocaleString()} kWh (${item.payload.is_anomaly ? "ANOMALY" : "Normal"})`,
                        item.payload.primary_driver ? `Driver: ${item.payload.primary_driver}` : "Energy",
                      ]}
                      labelFormatter={(lbl) => `Observation Date: ${lbl}`}
                    />
                    {anomalyData.statistical_threshold_upper > 0 && (
                      <ReferenceLine
                        y={anomalyData.statistical_threshold_upper}
                        stroke="#f59e0b"
                        strokeDasharray="4 4"
                        label={{ value: "Upper 2σ Bound", fill: "#f59e0b", fontSize: 11, position: "top" }}
                      />
                    )}
                    {anomalyData.statistical_threshold_lower > 0 && (
                      <ReferenceLine
                        y={anomalyData.statistical_threshold_lower}
                        stroke="#10b981"
                        strokeDasharray="4 4"
                        label={{ value: "Lower 2σ Bound", fill: "#10b981", fontSize: 11, position: "bottom" }}
                      />
                    )}
                    <Line
                      type="monotone"
                      dataKey="observed_kwh"
                      name="Observed Daily Energy"
                      stroke="#38bdf8"
                      strokeWidth={2}
                      dot={(props: any) => {
                        const { cx, cy, payload } = props;
                        if (!cx || !cy) return <g key={props.key} />;
                        const isAnom = payload.is_anomaly;
                        return (
                          <circle
                            key={props.key}
                            cx={cx}
                            cy={cy}
                            r={isAnom ? 6 : 3.5}
                            fill={isAnom ? "#f43f5e" : "#38bdf8"}
                            stroke={isAnom ? "#ffffff" : "transparent"}
                            strokeWidth={isAnom ? 2 : 0}
                          />
                        );
                      }}
                      activeDot={{ r: 7 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          {/* Anomaly Incidents Table */}
          {anomalyData?.anomalies && anomalyData.anomalies.length > 0 && (
            <div className="glass-panel p-6">
              <h3 className="text-base font-bold text-slate-100 mb-3 flex items-center gap-2">
                <AlertTriangle size={16} className="text-rose-400" />
                Flagged Operational Variances & Root-Cause Explanations
              </h3>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="text-[11px] uppercase tracking-wider text-slate-400 border-b border-white/10">
                    <tr>
                      <th className="pb-2.5 font-semibold">Date</th>
                      <th className="pb-2.5 font-semibold">Observed</th>
                      <th className="pb-2.5 font-semibold">Expected</th>
                      <th className="pb-2.5 font-semibold">Z-Score</th>
                      <th className="pb-2.5 font-semibold">Primary Driver</th>
                      <th className="pb-2.5 font-semibold">Root Cause Explanation</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {anomalyData.anomalies.map((anom) => (
                      <tr key={anom.date} className="hover:bg-white/5 transition-colors">
                        <td className="py-2.5 font-semibold text-rose-300 font-mono">{anom.date}</td>
                        <td className="py-2.5 text-slate-100 font-mono font-semibold">
                          {Math.round(anom.observed_kwh).toLocaleString()} kWh
                        </td>
                        <td className="py-2.5 text-slate-400 font-mono">
                          {Math.round(anom.expected_kwh).toLocaleString()} kWh
                        </td>
                        <td className="py-2.5 font-mono text-amber-300 font-semibold">
                          +{anom.z_score.toFixed(2)}σ
                        </td>
                        <td className="py-2.5 font-medium text-sky-400">{anom.primary_driver}</td>
                        <td className="py-2.5 text-slate-300 max-w-md">{anom.explanation}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ==================== TAB 3: CARBON & COST ==================== */}
      {activeSubTab === "carbon" && (
        <div className="space-y-6">
          <div>
            <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
              <Leaf size={20} className="text-emerald-400" />
              Carbon Footprint & Utility Cost Breakdown
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Empirical environmental impact and commercial electrical utility accounting
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Carbon Footprint Card */}
            <div className="glass-panel p-6 border-l-4 border-l-emerald-400">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs uppercase font-semibold text-slate-400 tracking-wider">
                  Campus Carbon Footprint
                </span>
                <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-400">
                  <Leaf size={22} />
                </div>
              </div>
              <div className="text-3xl font-extrabold text-emerald-400 tracking-tight">
                {summaryData
                  ? `${Math.round(summaryData.carbon_emissions_kg_co2).toLocaleString()} kg CO₂`
                  : "0 kg"}
              </div>
              <p className="text-xs text-slate-400 mt-2">
                Grid Baseline Factor:{" "}
                <span className="text-slate-200 font-semibold">
                  {summaryData?.carbon_factor_kg_co2_per_kwh?.toFixed(2) || "0.72"} kg CO₂/kWh
                </span>{" "}
                (Central Electricity Authority CEA India Database)
              </p>
            </div>

            {/* Utility Cost Card */}
            <div className="glass-panel p-6 border-l-4 border-l-amber-400">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs uppercase font-semibold text-slate-400 tracking-wider">
                  Electricity Utility Expenditure
                </span>
                <div className="p-2.5 rounded-xl bg-amber-500/10 text-amber-400">
                  <DollarSign size={22} />
                </div>
              </div>
              <div className="text-3xl font-extrabold text-amber-400 tracking-tight">
                {summaryData
                  ? `₹${Math.round(summaryData.estimated_cost_inr).toLocaleString()}`
                  : "₹0"}
              </div>
              <p className="text-xs text-slate-400 mt-2">
                Commercial High Tension (HT) Educational Tariff:{" "}
                <span className="text-slate-200 font-semibold">
                  ₹{summaryData?.tariff_inr_per_kwh?.toFixed(2) || "8.50"} / kWh
                </span>
              </p>
            </div>
          </div>

          {/* Energy Sources Mix Table */}
          {summaryData?.sources_breakdown && (
            <div className="glass-panel p-6">
              <h3 className="text-base font-bold text-slate-100 mb-2 flex items-center gap-2">
                <Zap size={16} className="text-sky-400" />
                Campus Energy Generation & Grid Supply Mix
              </h3>
              <p className="text-xs text-slate-400 mb-4">
                Total energy generation and grid utility supply shares
              </p>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="text-[11px] uppercase tracking-wider text-slate-400 border-b border-white/10">
                    <tr>
                      <th className="pb-2.5 font-semibold">Supply Source</th>
                      <th className="pb-2.5 font-semibold text-right">Total Energy (kWh)</th>
                      <th className="pb-2.5 font-semibold text-right">Percentage Share (%)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {Object.entries(summaryData.sources_breakdown).map(([source, metric]) => (
                      <tr key={source} className="hover:bg-white/5 transition-colors">
                        <td className="py-2.5 font-medium text-slate-200">{source}</td>
                        <td className="py-2.5 text-right font-mono font-semibold text-sky-400">
                          {Math.round(metric.kwh).toLocaleString()}
                        </td>
                        <td className="py-2.5 text-right font-semibold">
                          <span className="px-2 py-0.5 rounded-full bg-sky-500/10 text-sky-300 text-[11px]">
                            {metric.percentage.toFixed(1)}%
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
