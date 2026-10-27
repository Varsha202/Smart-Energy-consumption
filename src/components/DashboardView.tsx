"use client";

import { useState, useEffect } from "react";
import { api } from "../lib/api";
import {
  AnalyticsSummaryResponse,
  DailySeriesItem,
  FacilityMetric,
} from "../types/api";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from "recharts";
import {
  Calendar,
  Filter,
  AlertTriangle,
  Zap,
  DollarSign,
  Leaf,
  Flame,
  Building,
  RefreshCw,
  Layers,
} from "lucide-react";

interface DashboardViewProps {
  refreshTrigger?: number;
}

const FACILITY_COLORS: Record<string, string> = {
  total: "#38bdf8",
  academic_blocks: "#818cf8",
  chiller: "#f43f5e",
  hostels: "#fbbf24",
  staff_quarters: "#34d399",
  stp: "#a78bfa",
};

const FACILITY_LABELS: Record<string, string> = {
  total: "Campus Total",
  academic_blocks: "Academic Blocks",
  chiller: "Chiller Plant (HVAC)",
  hostels: "Hostels",
  staff_quarters: "Staff Quarters",
  stp: "Sewage Treatment (STP)",
};

export default function DashboardView({ refreshTrigger = 0 }: DashboardViewProps) {
  const [summary, setSummary] = useState<AnalyticsSummaryResponse | null>(null);
  const [dailySeries, setDailySeries] = useState<DailySeriesItem[]>([]);
  const [facilities, setFacilities] = useState<FacilityMetric[]>([]);
  const [startDate, setStartDate] = useState<string>("2026-07-01");
  const [endDate, setEndDate] = useState<string>("2026-07-31");
  const [selectedFacility, setSelectedFacility] = useState<string>("all");
  const [loading, setLoading] = useState<boolean>(true);
  const [filterLoading, setFilterLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);

    const [sumRes, dailyRes, facRes] = await Promise.all([
      api.getAnalyticsSummary(),
      api.getDailySeries(),
      api.getFacilityBreakdown(),
    ]);

    if (sumRes.error && !sumRes.data) {
      setError(sumRes.error);
    } else {
      setSummary(sumRes.data);
      setDailySeries(dailyRes.data?.series || []);
      setFacilities(facRes.data?.facilities || []);
      if (sumRes.data?.date_range) {
        if (sumRes.data.date_range.start) setStartDate(sumRes.data.date_range.start);
        if (sumRes.data.date_range.end) setEndDate(sumRes.data.date_range.end);
      }
    }
    setLoading(false);
  };

  const handleFilter = async (e: React.FormEvent) => {
    e.preventDefault();
    setFilterLoading(true);
    setError(null);

    const { data, error: filterErr } = await api.getEnergyRecords({
      page: 1,
      limit: 100,
      start_date: startDate,
      end_date: endDate,
    });

    if (data?.records) {
      // Map records to series format
      const formattedSeries: DailySeriesItem[] = data.records.map((r) => ({
        date: r.date,
        total: r.total,
        tneb_campus: r.tneb_campus,
        tneb_new_stp: r.tneb_new_stp,
        solar: r.solar,
        diesel: r.diesel,
        biogas: r.biogas,
        staff_quarters: r.staff_quarters,
        academic_blocks: r.academic_blocks,
        hostels: r.hostels,
        chiller: r.chiller,
        stp: r.stp,
      }));
      setDailySeries(formattedSeries);
    } else if (filterErr) {
      setError(filterErr);
    }
    setFilterLoading(false);
  };

  const handleResetFilter = () => {
    setSelectedFacility("all");
    loadData();
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

  // Filter daily series if specific facility is chosen
  const displayedSeries = dailySeries.map((item) => {
    if (selectedFacility === "all") return item;
    return item;
  });

  return (
    <div className="space-y-6">
      {/* Date & Facility Filter Bar */}
      <div className="glass-panel p-5">
        <form
          onSubmit={handleFilter}
          className="flex flex-col lg:flex-row lg:items-end justify-between gap-4"
        >
          <div className="flex flex-wrap items-center gap-4 flex-1">
            <div className="flex items-center gap-2 text-sky-400 font-semibold text-sm">
              <Calendar size={18} />
              <span>Filters:</span>
            </div>

            <div className="flex-1 min-w-[140px]">
              <label className="block text-xs text-slate-400 font-medium mb-1">
                Start Date
              </label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                min="2026-01-01"
                max="2026-12-31"
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-white/10 text-slate-100 text-sm focus:outline-none focus:border-sky-500"
              />
            </div>

            <div className="flex-1 min-w-[140px]">
              <label className="block text-xs text-slate-400 font-medium mb-1">
                End Date
              </label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                min="2026-01-01"
                max="2026-12-31"
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-white/10 text-slate-100 text-sm focus:outline-none focus:border-sky-500"
              />
            </div>

            <div className="flex-1 min-w-[180px]">
              <label className="block text-xs text-slate-400 font-medium mb-1 flex items-center gap-1">
                <Building size={12} /> Monitored Sector Focus
              </label>
              <select
                value={selectedFacility}
                onChange={(e) => setSelectedFacility(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-white/10 text-slate-100 text-sm focus:outline-none focus:border-sky-500"
              >
                <option value="all">All Sectors (Campus Total)</option>
                <option value="academic_blocks">Academic Blocks</option>
                <option value="chiller">Chiller Plant (HVAC)</option>
                <option value="hostels">Hostels</option>
                <option value="staff_quarters">Staff Quarters</option>
                <option value="stp">STP</option>
              </select>
            </div>
          </div>

          <div className="flex items-center gap-3 self-end">
            <button
              type="submit"
              disabled={filterLoading}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-sky-500 hover:bg-sky-400 text-slate-950 font-semibold text-sm transition-colors shadow-md shadow-sky-500/20 disabled:opacity-50"
            >
              {filterLoading ? (
                <>
                  <RefreshCw size={15} className="animate-spin" /> Applying...
                </>
              ) : (
                <>
                  <Filter size={15} /> Apply Filter
                </>
              )}
            </button>
            <button
              type="button"
              onClick={handleResetFilter}
              className="px-4 py-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-slate-300 text-sm font-medium border border-white/10 transition-colors"
            >
              Reset
            </button>
          </div>
        </form>
      </div>

      {/* Error banner */}
      {error && (
        <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 flex items-start gap-3 text-sm">
          <AlertTriangle size={18} className="shrink-0 mt-0.5" />
          <div>
            <div className="font-semibold">Backend Notice</div>
            <div className="text-amber-200/80">{error}</div>
          </div>
        </div>
      )}

      {/* Primary KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Total Energy */}
        <div className="glass-panel glass-panel-hover p-5 relative overflow-hidden">
          <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider mb-2">
            <span>Total Consumption</span>
            <div className="p-2 rounded-lg bg-sky-500/10 text-sky-400">
              <Zap size={18} />
            </div>
          </div>
          <div className="text-2xl sm:text-3xl font-extrabold text-sky-400 tracking-tight">
            {loading
              ? "..."
              : summary
              ? `${Math.round(summary.total_consumption_kwh).toLocaleString()} kWh`
              : "0 kWh"}
          </div>
          <div className="text-xs text-slate-400 mt-2 flex items-center justify-between">
            <span>Daily Avg:</span>
            <span className="font-semibold text-slate-200">
              {summary ? `${Math.round(summary.average_daily_consumption_kwh).toLocaleString()} kWh` : "—"}
            </span>
          </div>
          <div className="absolute -bottom-6 -right-6 w-24 h-24 bg-sky-500/10 rounded-full blur-xl pointer-events-none" />
        </div>

        {/* Card 2: Electricity Cost */}
        <div className="glass-panel glass-panel-hover p-5 relative overflow-hidden">
          <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider mb-2">
            <span>Estimated Utility Cost</span>
            <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400">
              <DollarSign size={18} />
            </div>
          </div>
          <div className="text-2xl sm:text-3xl font-extrabold text-amber-400 tracking-tight">
            {loading
              ? "..."
              : summary
              ? `₹${Math.round(summary.estimated_cost_inr).toLocaleString()}`
              : "₹0"}
          </div>
          <div className="text-xs text-slate-400 mt-2 flex items-center justify-between">
            <span>Tariff Rate:</span>
            <span className="font-semibold text-slate-200">
              ₹{summary?.tariff_inr_per_kwh?.toFixed(2) || "8.50"} / kWh
            </span>
          </div>
          <div className="absolute -bottom-6 -right-6 w-24 h-24 bg-amber-500/10 rounded-full blur-xl pointer-events-none" />
        </div>

        {/* Card 3: Carbon Emissions */}
        <div className="glass-panel glass-panel-hover p-5 relative overflow-hidden">
          <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider mb-2">
            <span>Carbon Footprint</span>
            <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
              <Leaf size={18} />
            </div>
          </div>
          <div className="text-2xl sm:text-3xl font-extrabold text-emerald-400 tracking-tight">
            {loading
              ? "..."
              : summary
              ? `${Math.round(summary.carbon_emissions_kg_co2).toLocaleString()} kg`
              : "0 kg"}
          </div>
          <div className="text-xs text-slate-400 mt-2 flex items-center justify-between">
            <span>Grid Baseline:</span>
            <span className="font-semibold text-slate-200">
              {summary?.carbon_factor_kg_co2_per_kwh?.toFixed(2) || "0.72"} kg CO₂/kWh
            </span>
          </div>
          <div className="absolute -bottom-6 -right-6 w-24 h-24 bg-emerald-500/10 rounded-full blur-xl pointer-events-none" />
        </div>

        {/* Card 4: Peak Consumption */}
        <div className="glass-panel glass-panel-hover p-5 relative overflow-hidden">
          <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider mb-2">
            <span>Peak Demand</span>
            <div className="p-2 rounded-lg bg-rose-500/10 text-rose-400">
              <Flame size={18} />
            </div>
          </div>
          <div className="text-2xl sm:text-3xl font-extrabold text-rose-400 tracking-tight">
            {loading
              ? "..."
              : summary
              ? `${Math.round(summary.max_daily_consumption_kwh).toLocaleString()} kWh`
              : "0 kWh"}
          </div>
          <div className="text-xs text-slate-400 mt-2 flex items-center justify-between">
            <span>Recorded Date:</span>
            <span className="font-semibold text-rose-300">
              {summary?.peak_day || "N/A"}
            </span>
          </div>
          <div className="absolute -bottom-6 -right-6 w-24 h-24 bg-rose-500/10 rounded-full blur-xl pointer-events-none" />
        </div>
      </div>

      {/* Historical Energy Trends Chart */}
      <div className="glass-panel p-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-4 border-b border-white/10 gap-3">
          <div>
            <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <Layers size={18} className="text-sky-400" />
              Campus Daily Energy Trends
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Historical daily observations across campus facilities ({dailySeries.length} recorded days)
            </p>
          </div>
          {selectedFacility !== "all" && (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-sky-500/15 text-sky-300 border border-sky-500/30">
              Filtered to: {FACILITY_LABELS[selectedFacility] || selectedFacility}
            </span>
          )}
        </div>

        <div className="h-[360px] w-full pt-6">
          {loading ? (
            <div className="h-full flex items-center justify-center text-slate-400 text-sm">
              <RefreshCw size={20} className="animate-spin mr-2" /> Loading energy trend series...
            </div>
          ) : displayedSeries.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-slate-400 text-sm">
              <AlertTriangle size={32} className="text-amber-400 mb-2" />
              <span>No energy records found for the selected date range.</span>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={displayedSeries} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.08)" vertical={false} />
                <XAxis
                  dataKey="date"
                  stroke="#64748b"
                  fontSize={12}
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
                  fontSize={12}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
                />
                <Tooltip
                  contentStyle={customTooltipStyle}
                  formatter={(value: any, name: any) => [
                    `${Number(value).toLocaleString()} kWh`,
                    FACILITY_LABELS[String(name)] || name,
                  ]}
                  labelFormatter={(lbl) => `Date: ${lbl}`}
                />
                <Legend
                  wrapperStyle={{ paddingTop: "14px", fontSize: "12px" }}
                  formatter={(val) => FACILITY_LABELS[String(val)] || val}
                />

                {selectedFacility === "all" ? (
                  <>
                    <Line
                      type="monotone"
                      dataKey="total"
                      name="total"
                      stroke={FACILITY_COLORS.total}
                      strokeWidth={3}
                      dot={false}
                      activeDot={{ r: 6 }}
                    />
                    <Line
                      type="monotone"
                      dataKey="academic_blocks"
                      name="academic_blocks"
                      stroke={FACILITY_COLORS.academic_blocks}
                      strokeWidth={1.8}
                      dot={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="chiller"
                      name="chiller"
                      stroke={FACILITY_COLORS.chiller}
                      strokeWidth={1.8}
                      dot={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="hostels"
                      name="hostels"
                      stroke={FACILITY_COLORS.hostels}
                      strokeWidth={1.8}
                      dot={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="staff_quarters"
                      name="staff_quarters"
                      stroke={FACILITY_COLORS.staff_quarters}
                      strokeWidth={1.8}
                      dot={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="stp"
                      name="stp"
                      stroke={FACILITY_COLORS.stp}
                      strokeWidth={1.8}
                      dot={false}
                    />
                  </>
                ) : (
                  <Line
                    type="monotone"
                    dataKey={selectedFacility}
                    name={selectedFacility}
                    stroke={FACILITY_COLORS[selectedFacility] || "#38bdf8"}
                    strokeWidth={3}
                    dot={{ r: 4, fill: FACILITY_COLORS[selectedFacility] || "#38bdf8" }}
                    activeDot={{ r: 7 }}
                  />
                )}
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Facility Breakdown & Comparisons */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Bar Chart */}
        <div className="glass-panel p-6">
          <div className="flex items-center justify-between pb-4 border-b border-white/10 mb-4">
            <div>
              <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
                <Building size={16} className="text-sky-400" />
                Facility-Wise Energy Distribution
              </h2>
              <p className="text-xs text-slate-400">Total consumption share across campus infrastructure</p>
            </div>
          </div>

          <div className="h-[280px] w-full">
            {loading ? (
              <div className="h-full flex items-center justify-center text-slate-400 text-sm">
                <RefreshCw size={18} className="animate-spin mr-2" /> Loading breakdown...
              </div>
            ) : facilities.length === 0 ? (
              <div className="h-full flex items-center justify-center text-slate-400 text-sm">
                No facility data available
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={facilities} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.08)" horizontal={false} />
                  <XAxis
                    type="number"
                    stroke="#64748b"
                    fontSize={11}
                    tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
                  />
                  <YAxis
                    dataKey="display_name"
                    type="category"
                    stroke="#94a3b8"
                    fontSize={12}
                    tickLine={false}
                    width={110}
                  />
                  <Tooltip
                    contentStyle={customTooltipStyle}
                    formatter={(val: any) => [`${Number(val).toLocaleString()} kWh`, "Total Energy"]}
                  />
                  <Bar dataKey="total_kwh" radius={[0, 8, 8, 0]}>
                    {facilities.map((entry, index) => {
                      const colors = ["#38bdf8", "#818cf8", "#f43f5e", "#fbbf24", "#34d399"];
                      return <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />;
                    })}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Facility Comparative Table */}
        <div className="glass-panel p-6">
          <div className="flex items-center justify-between pb-4 border-b border-white/10 mb-4">
            <div>
              <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
                <Layers size={16} className="text-sky-400" />
                Department / Sector Metrics
              </h2>
              <p className="text-xs text-slate-400">Granular comparative breakdown</p>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="text-[11px] uppercase tracking-wider text-slate-400 border-b border-white/10">
                <tr>
                  <th className="pb-2.5 font-semibold">Sector</th>
                  <th className="pb-2.5 font-semibold text-right">Total (kWh)</th>
                  <th className="pb-2.5 font-semibold text-right">Daily Avg</th>
                  <th className="pb-2.5 font-semibold text-right">Share (%)</th>
                  <th className="pb-2.5 font-semibold text-right">Peak (kWh)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {facilities.map((fac) => (
                  <tr key={fac.facility_name} className="hover:bg-white/5 transition-colors">
                    <td className="py-2.5 font-medium text-slate-200">{fac.display_name}</td>
                    <td className="py-2.5 text-right text-sky-400 font-semibold font-mono">
                      {Math.round(fac.total_kwh).toLocaleString()}
                    </td>
                    <td className="py-2.5 text-right text-slate-300 font-mono">
                      {Math.round(fac.daily_avg_kwh).toLocaleString()}
                    </td>
                    <td className="py-2.5 text-right font-semibold">
                      <span className="px-2 py-0.5 rounded-full bg-sky-500/10 text-sky-300 text-[11px]">
                        {fac.percentage.toFixed(1)}%
                      </span>
                    </td>
                    <td className="py-2.5 text-right text-slate-400 font-mono">
                      {Math.round(fac.peak_kwh).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
