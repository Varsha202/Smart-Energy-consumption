"use client";

import { useState, useEffect } from "react";
import { api } from "../lib/api";
import {
  TariffConfig,
  TariffSlab,
  TariffCalculationResult,
} from "../types/api";
import {
  Receipt,
  Calculator,
  Save,
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
  Info,
  Plus,
  Trash2,
  DollarSign,
  TrendingDown,
  TrendingUp,
  Zap,
  Building,
  Sliders,
  Check,
} from "lucide-react";

interface TariffViewProps {
  onTariffUpdated?: () => void;
}

export default function TariffView({ onTariffUpdated }: TariffViewProps) {
  const [config, setConfig] = useState<TariffConfig | null>(null);
  const [activeProfile, setActiveProfile] = useState<string>("commercial");
  const [billingMode, setBillingMode] = useState<"progressive" | "single_tier">("progressive");
  const [freeUnitsEnabled, setFreeUnitsEnabled] = useState<boolean>(true);
  const [singleTierRate, setSingleTierRate] = useState<number>(8.50);
  const [slabs, setSlabs] = useState<TariffSlab[]>([]);

  // Simulation & Campus consumption
  const [campusConsumption, setCampusConsumption] = useState<number>(0);
  const [simConsumption, setSimConsumption] = useState<number>(0);
  const [calcResult, setCalcResult] = useState<TariffCalculationResult | null>(null);

  // Status & feedback
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [message, setMessage] = useState<{ type: "success" | "error" | "info"; text: string } | null>(null);

  const loadTariffData = async () => {
    setLoading(true);
    const { data, error } = await api.getTariffConfig();
    if (data) {
      const cfg = data.config;
      setConfig(cfg);
      setActiveProfile(cfg.profile || "commercial");
      setBillingMode(cfg.billing_mode || "progressive");
      setFreeUnitsEnabled(cfg.free_units_enabled ?? true);
      setSingleTierRate(cfg.single_tier_rate ?? 8.50);
      setSlabs(cfg.slabs || []);
      setCampusConsumption(data.campus_consumption_kwh || 0);
      setSimConsumption(data.campus_consumption_kwh || 1000);
      setCalcResult(data.campus_calculation);
    } else if (error) {
      setMessage({ type: "error", text: error });
    }
    setLoading(false);
  };

  useEffect(() => {
    loadTariffData();
  }, []);

  // Compute live calculation
  const runCalculation = async (testConfig?: TariffConfig, units?: number) => {
    const targetUnits = units !== undefined ? units : simConsumption;
    const targetConfig: TariffConfig = testConfig || {
      profile: activeProfile,
      billing_mode: billingMode,
      free_units_enabled: freeUnitsEnabled,
      free_units_limit: 100.0,
      single_tier_rate: Number(singleTierRate),
      slabs: slabs,
      notes: config?.notes,
    };

    const { data, error } = await api.calculateTariff({
      consumption_kwh: Number(targetUnits),
      config: targetConfig,
    });

    if (data) {
      setCalcResult(data);
    } else if (error) {
      setMessage({ type: "error", text: error });
    }
  };

  // Slab table editing handlers
  const handleRateChange = (index: number, val: number) => {
    const updated = [...slabs];
    updated[index].rate_per_unit = Math.max(0, val);
    setSlabs(updated);
  };

  const handleEndUnitsChange = (index: number, val: string) => {
    const updated = [...slabs];
    const num = val === "" ? null : Math.max(0, parseFloat(val));
    updated[index].end_units = num;
    // update contiguous next slab start if present
    if (index < updated.length - 1 && num !== null) {
      updated[index + 1].start_units = num;
    }
    setSlabs(updated);
  };

  const handleAddSlab = () => {
    const lastSlab = slabs[slabs.length - 1];
    const newStart = lastSlab?.end_units ?? (lastSlab?.start_units ?? 0) + 100;

    // Convert last slab end from None to newStart
    const updated = slabs.map((s, idx) => {
      if (idx === slabs.length - 1 && s.end_units === null) {
        return { ...s, end_units: newStart };
      }
      return s;
    });

    updated.push({
      start_units: newStart,
      end_units: null,
      rate_per_unit: 8.50,
      label: `Above ${newStart} units`,
    });
    setSlabs(updated);
  };

  const handleRemoveSlab = (index: number) => {
    if (slabs.length <= 1) {
      setMessage({ type: "error", text: "At least one slab must remain." });
      return;
    }
    const filtered = slabs.filter((_, idx) => idx !== index);
    // Fix boundaries to remain contiguous
    filtered[0].start_units = 0;
    for (let i = 1; i < filtered.length; i++) {
      filtered[i].start_units = filtered[i - 1].end_units ?? filtered[i].start_units;
    }
    // Ensure last slab has null end if removed was the end
    if (index === slabs.length - 1) {
      filtered[filtered.length - 1].end_units = null;
    }
    setSlabs(filtered);
  };

  // Profile switch
  const handleProfileChange = async (newProfile: string) => {
    setActiveProfile(newProfile);
    const { data } = await api.resetTariffConfig(newProfile);
    if (data) {
      setConfig(data);
      setBillingMode(data.billing_mode);
      setFreeUnitsEnabled(data.free_units_enabled);
      setSingleTierRate(data.single_tier_rate);
      setSlabs(data.slabs);
      runCalculation(data);
      setMessage({ type: "info", text: `Switched to ${newProfile.toUpperCase()} profile template.` });
    }
  };

  // Reset to defaults
  const handleResetDefaults = async () => {
    setLoading(true);
    const { data, error } = await api.resetTariffConfig(activeProfile);
    if (data) {
      setConfig(data);
      setBillingMode(data.billing_mode);
      setFreeUnitsEnabled(data.free_units_enabled);
      setSingleTierRate(data.single_tier_rate);
      setSlabs(data.slabs);
      runCalculation(data);
      setMessage({ type: "success", text: "Reset to initial configurable default parameters." });
      if (onTariffUpdated) onTariffUpdated();
    } else if (error) {
      setMessage({ type: "error", text: error });
    }
    setLoading(false);
  };

  // Save configuration permanently to backend
  const handleSaveConfig = async () => {
    setSaving(true);
    setMessage(null);

    const configToSave: TariffConfig = {
      profile: activeProfile,
      billing_mode: billingMode,
      free_units_enabled: freeUnitsEnabled,
      free_units_limit: 100.0,
      single_tier_rate: Number(singleTierRate),
      slabs: slabs,
      notes: config?.notes || "Initial configuration values. Not officially verified regulatory tariffs.",
    };

    const { data, error } = await api.updateTariffConfig(configToSave);
    if (data) {
      setConfig(data);
      runCalculation(data);
      setMessage({ type: "success", text: "Tariff configuration safely saved and persisted!" });
      if (onTariffUpdated) onTariffUpdated();
    } else if (error) {
      setMessage({ type: "error", text: error });
    }
    setSaving(false);
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-slate-100 flex items-center gap-2">
            <Calculator size={24} className="text-sky-400" />
            Configurable Progressive Electricity Tariff Calculator
          </h2>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Progressive slab modeling, multi-tier utility simulations, and campus expenditure forecasting.
          </p>
        </div>

        {/* Profile Pill Selector */}
        <div className="flex items-center gap-1.5 p-1 rounded-xl bg-white/5 border border-white/10 self-start sm:self-auto">
          <button
            onClick={() => handleProfileChange("commercial")}
            className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
              activeProfile === "commercial"
                ? "bg-sky-500 text-slate-950 shadow-md shadow-sky-500/20"
                : "text-slate-300 hover:text-white"
            }`}
          >
            Commercial / Institutional
          </button>
          <button
            onClick={() => handleProfileChange("domestic")}
            className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
              activeProfile === "domestic"
                ? "bg-sky-500 text-slate-950 shadow-md shadow-sky-500/20"
                : "text-slate-300 hover:text-white"
            }`}
          >
            Domestic
          </button>
          <button
            onClick={() => handleProfileChange("custom")}
            className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
              activeProfile === "custom"
                ? "bg-sky-500 text-slate-950 shadow-md shadow-sky-500/20"
                : "text-slate-300 hover:text-white"
            }`}
          >
            Custom
          </button>
        </div>
      </div>

      {/* Prominent Disclaimer Notice */}
      <div className="p-4 rounded-xl bg-sky-500/10 border border-sky-500/20 text-sky-200 text-xs flex items-start gap-3">
        <Info size={17} className="shrink-0 mt-0.5 text-sky-400" />
        <div className="leading-relaxed">
          <strong className="text-sky-300">Tariff Notice & Modeling Scope: </strong>
          The exact official utility tariff slabs, state regulatory rates, and fixed charges have not been verified.
          All values below are editable configuration baselines for analytics, optimization, and scenario testing.
          Verify with your regional electricity board (e.g. TANGEDCO/TNEB) tariff schedules for official billing.
        </div>
      </div>

      {/* Alert Notification Message */}
      {message && (
        <div
          className={`p-4 rounded-xl text-xs flex items-center justify-between border ${
            message.type === "success"
              ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300"
              : message.type === "error"
              ? "bg-rose-500/10 border-rose-500/30 text-rose-300"
              : "bg-sky-500/10 border-sky-500/30 text-sky-300"
          }`}
        >
          <div className="flex items-center gap-2">
            {message.type === "success" ? (
              <CheckCircle2 size={16} />
            ) : (
              <AlertTriangle size={16} />
            )}
            <span>{message.text}</span>
          </div>
          <button
            onClick={() => setMessage(null)}
            className="text-slate-400 hover:text-white text-xs font-bold"
          >
            ✕
          </button>
        </div>
      )}

      {/* Top Simulation Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1: Total Consumption */}
        <div className="glass-panel p-5">
          <div className="text-xs text-slate-400 font-semibold uppercase tracking-wider mb-2 flex items-center justify-between">
            <span>Evaluated Volume</span>
            <Zap size={16} className="text-sky-400" />
          </div>
          <div className="text-2xl sm:text-3xl font-extrabold text-sky-400 tracking-tight">
            {calcResult ? `${Math.round(calcResult.total_consumption_kwh).toLocaleString()} kWh` : "—"}
          </div>
          <div className="text-xs text-slate-400 mt-2">
            Campus Record Base: <span className="text-slate-200 font-mono">{Math.round(campusConsumption).toLocaleString()} kWh</span>
          </div>
        </div>

        {/* Metric 2: Estimated Bill */}
        <div className="glass-panel p-5">
          <div className="text-xs text-slate-400 font-semibold uppercase tracking-wider mb-2 flex items-center justify-between">
            <span>Estimated Electricity Bill</span>
            <DollarSign size={16} className="text-amber-400" />
          </div>
          <div className="text-2xl sm:text-3xl font-extrabold text-amber-400 tracking-tight">
            {calcResult ? `₹${Math.round(calcResult.total_bill_inr).toLocaleString()}` : "—"}
          </div>
          <div className="text-xs text-slate-400 mt-2">
            Billing Engine:{" "}
            <span className="font-semibold text-slate-200 uppercase text-[11px]">
              {billingMode === "progressive" ? "Progressive Slabs" : "Single Flat Rate"}
            </span>
          </div>
        </div>

        {/* Metric 3: Average Effective Rate */}
        <div className="glass-panel p-5">
          <div className="text-xs text-slate-400 font-semibold uppercase tracking-wider mb-2 flex items-center justify-between">
            <span>Effective Cost Per Unit</span>
            <Receipt size={16} className="text-emerald-400" />
          </div>
          <div className="text-2xl sm:text-3xl font-extrabold text-emerald-400 tracking-tight">
            {calcResult ? `₹${calcResult.effective_rate_per_kwh.toFixed(2)}` : "—"}
            <span className="text-xs font-normal text-slate-400 ml-1">/ kWh</span>
          </div>
          <div className="text-xs text-slate-400 mt-2">
            Free Units Applied: <span className="text-slate-200 font-semibold">{calcResult?.free_units_applied || 0} kWh</span>
          </div>
        </div>

        {/* Metric 4: Before and After Comparison */}
        <div className="glass-panel p-5">
          <div className="text-xs text-slate-400 font-semibold uppercase tracking-wider mb-2 flex items-center justify-between">
            <span>vs Baseline (₹8.50 Flat)</span>
            {calcResult && calcResult.cost_difference_inr <= 0 ? (
              <TrendingDown size={16} className="text-emerald-400" />
            ) : (
              <TrendingUp size={16} className="text-rose-400" />
            )}
          </div>
          <div
            className={`text-2xl sm:text-3xl font-extrabold tracking-tight ${
              calcResult && calcResult.cost_difference_inr <= 0
                ? "text-emerald-400"
                : "text-rose-400"
            }`}
          >
            {calcResult
              ? `${calcResult.cost_difference_inr <= 0 ? "-" : "+"}₹${Math.round(
                  Math.abs(calcResult.cost_difference_inr)
                ).toLocaleString()}`
              : "—"}
          </div>
          <div className="text-xs text-slate-400 mt-2">
            Variance:{" "}
            <span className="font-semibold text-slate-200">
              {calcResult
                ? `${calcResult.percentage_difference >= 0 ? "+" : ""}${calcResult.percentage_difference.toFixed(1)}%`
                : "—"}
            </span>{" "}
            vs ₹{calcResult ? Math.round(calcResult.baseline_flat_cost_inr).toLocaleString() : 0}
          </div>
        </div>
      </div>

      {/* Main Settings Panel */}
      <div className="glass-panel p-6 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-4 border-b border-white/10 gap-3">
          <div>
            <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <Sliders size={18} className="text-sky-400" />
              Billing Model & Structure Configuration
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Customize consumption thresholds, per-unit tariffs, and utility billing modes.
            </p>
          </div>

          {/* Mode Switch */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400 font-medium">Mode:</span>
            <div className="p-1 rounded-xl bg-slate-900 border border-white/10 flex items-center">
              <button
                type="button"
                onClick={() => setBillingMode("progressive")}
                className={`px-3 py-1 text-xs font-semibold rounded-lg transition-colors ${
                  billingMode === "progressive"
                    ? "bg-sky-500 text-slate-950"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                Progressive Slabs
              </button>
              <button
                type="button"
                onClick={() => setBillingMode("single_tier")}
                className={`px-3 py-1 text-xs font-semibold rounded-lg transition-colors ${
                  billingMode === "single_tier"
                    ? "bg-sky-500 text-slate-950"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                Single-Tier Flat
              </button>
            </div>
          </div>
        </div>

        {/* Mode Specific Controls */}
        {billingMode === "single_tier" ? (
          <div className="p-5 rounded-xl bg-slate-900/60 border border-white/10 max-w-md">
            <label className="block text-xs font-semibold text-slate-300 mb-2">
              Flat Electricity Tariff Rate (₹ per kWh)
            </label>
            <div className="flex items-center gap-3">
              <input
                type="number"
                step="0.05"
                min="0"
                value={singleTierRate}
                onChange={(e) => setSingleTierRate(parseFloat(e.target.value) || 0)}
                className="w-40 px-3 py-2 rounded-xl bg-slate-950 border border-white/15 text-slate-100 font-mono font-semibold text-sm focus:outline-none focus:border-sky-500"
              />
              <span className="text-xs text-slate-400">Standard HT educational/commercial rate</span>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Free Tier Toggle */}
            <div className="flex items-center justify-between p-4 rounded-xl bg-slate-900/60 border border-white/10">
              <div>
                <div className="text-sm font-semibold text-slate-200">
                  Subsidized Free Tier (0–100 Units @ ₹0/kWh)
                </div>
                <div className="text-xs text-slate-400 mt-0.5">
                  When enabled, the first 100 units are exempt from energy charges.
                </div>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={freeUnitsEnabled}
                  onChange={(e) => setFreeUnitsEnabled(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-slate-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-sky-500"></div>
              </label>
            </div>

            {/* Editable Slab Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="text-[11px] uppercase tracking-wider text-slate-400 border-b border-white/10">
                  <tr>
                    <th className="pb-3 font-semibold">Slab #</th>
                    <th className="pb-3 font-semibold">Range (Start kWh)</th>
                    <th className="pb-3 font-semibold">Range (End kWh)</th>
                    <th className="pb-3 font-semibold">Tariff Rate (₹/kWh)</th>
                    <th className="pb-3 font-semibold">Label / Tier</th>
                    <th className="pb-3 font-semibold text-center">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {slabs.map((slab, index) => {
                    const isFirstFree = index === 0 && freeUnitsEnabled;
                    return (
                      <tr key={index} className="hover:bg-white/5 transition-colors">
                        <td className="py-3 font-mono font-bold text-sky-400">
                          Slab {index + 1}
                        </td>
                        <td className="py-3 font-mono text-slate-300">
                          {slab.start_units.toLocaleString()} kWh
                        </td>
                        <td className="py-3">
                          {index === slabs.length - 1 ? (
                            <span className="px-2.5 py-1 rounded-lg bg-white/5 text-slate-400 font-mono">
                              ∞ (Unlimited)
                            </span>
                          ) : (
                            <input
                              type="number"
                              min={slab.start_units + 1}
                              value={slab.end_units ?? ""}
                              onChange={(e) => handleEndUnitsChange(index, e.target.value)}
                              className="w-28 px-2.5 py-1.5 rounded-lg bg-slate-950 border border-white/15 text-slate-100 font-mono text-xs focus:outline-none focus:border-sky-500"
                            />
                          )}
                        </td>
                        <td className="py-3">
                          {isFirstFree ? (
                            <span className="px-2.5 py-1 rounded-lg bg-emerald-500/15 text-emerald-300 font-mono font-semibold">
                              ₹0.00 (Free)
                            </span>
                          ) : (
                            <div className="flex items-center gap-1.5">
                              <span className="text-slate-400">₹</span>
                              <input
                                type="number"
                                step="0.10"
                                min="0"
                                value={slab.rate_per_unit}
                                onChange={(e) => handleRateChange(index, parseFloat(e.target.value) || 0)}
                                className="w-24 px-2.5 py-1.5 rounded-lg bg-slate-950 border border-white/15 text-slate-100 font-mono font-semibold text-xs focus:outline-none focus:border-sky-500"
                              />
                            </div>
                          )}
                        </td>
                        <td className="py-3 text-slate-400">
                          {slab.label || (slab.end_units ? `${slab.start_units}-${slab.end_units} kWh` : `Above ${slab.start_units} kWh`)}
                        </td>
                        <td className="py-3 text-center">
                          {slabs.length > 1 && (
                            <button
                              type="button"
                              onClick={() => handleRemoveSlab(index)}
                              className="p-1.5 rounded-lg text-rose-400 hover:text-white hover:bg-rose-500/20 transition-colors"
                              title="Remove slab"
                            >
                              <Trash2 size={15} />
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            <button
              type="button"
              onClick={handleAddSlab}
              className="flex items-center gap-2 px-3.5 py-2 text-xs font-semibold rounded-xl bg-white/5 hover:bg-white/10 text-sky-400 border border-white/10 transition-colors"
            >
              <Plus size={15} /> Add Progressive Slab
            </button>
          </div>
        )}

        {/* Consumption Simulation Slider */}
        <div className="p-4 rounded-xl bg-slate-900/60 border border-white/10 space-y-2">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-300">
            <span>Interactive Consumption Simulation:</span>
            <span className="text-sky-400 font-mono font-bold text-sm">
              {Math.round(simConsumption).toLocaleString()} kWh
            </span>
          </div>
          <input
            type="range"
            min="0"
            max={Math.max(campusConsumption * 1.5, 50000)}
            step="50"
            value={simConsumption}
            onChange={(e) => {
              const val = parseFloat(e.target.value);
              setSimConsumption(val);
              runCalculation(undefined, val);
            }}
            className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-sky-500"
          />
          <div className="flex justify-between text-[10px] text-slate-500">
            <span>0 kWh</span>
            <span
              onClick={() => {
                setSimConsumption(campusConsumption);
                runCalculation(undefined, campusConsumption);
              }}
              className="cursor-pointer text-sky-400 hover:underline"
            >
              Set to Campus Total ({Math.round(campusConsumption).toLocaleString()} kWh)
            </span>
            <span>{Math.round(Math.max(campusConsumption * 1.5, 50000)).toLocaleString()} kWh</span>
          </div>
        </div>

        {/* Slab Cost Distribution Breakdown Table */}
        {calcResult?.slab_breakdown && calcResult.slab_breakdown.length > 0 && (
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">
              Cost Contribution by Consumption Slab
            </h4>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="text-[11px] uppercase tracking-wider text-slate-400 border-b border-white/10">
                  <tr>
                    <th className="pb-2 font-semibold">Tier</th>
                    <th className="pb-2 font-semibold">Range</th>
                    <th className="pb-2 font-semibold text-right">Units Apportioned</th>
                    <th className="pb-2 font-semibold text-right">Tariff Rate</th>
                    <th className="pb-2 font-semibold text-right">Subtotal Cost (₹)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5 font-mono">
                  {calcResult.slab_breakdown.map((s) => (
                    <tr key={s.slab_index} className="hover:bg-white/5 transition-colors">
                      <td className="py-2 text-slate-300 font-sans">{s.label || `Slab ${s.slab_index}`}</td>
                      <td className="py-2 text-slate-400">
                        {s.start_units.toLocaleString()} - {s.end_units ? s.end_units.toLocaleString() : "∞"}
                      </td>
                      <td className="py-2 text-right text-sky-300 font-semibold">
                        {s.units_in_slab.toLocaleString()} kWh
                      </td>
                      <td className="py-2 text-right text-slate-300">
                        ₹{s.rate_per_unit.toFixed(2)}
                      </td>
                      <td className="py-2 text-right text-amber-400 font-bold">
                        ₹{s.slab_cost.toLocaleString()}
                      </td>
                    </tr>
                  ))}
                  <tr className="border-t border-white/20 font-bold text-slate-100">
                    <td colSpan={2} className="py-2.5 font-sans">
                      Calculated Total
                    </td>
                    <td className="py-2.5 text-right text-sky-400 font-mono">
                      {Math.round(calcResult.total_consumption_kwh).toLocaleString()} kWh
                    </td>
                    <td className="py-2.5 text-right text-emerald-400 font-mono">
                      ₹{calcResult.effective_rate_per_kwh.toFixed(2)} / kWh (Avg)
                    </td>
                    <td className="py-2.5 text-right text-amber-400 font-mono text-sm">
                      ₹{Math.round(calcResult.total_bill_inr).toLocaleString()}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Action Controls */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-4 border-t border-white/10">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => runCalculation()}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-sky-500 hover:bg-sky-400 text-slate-950 font-semibold text-xs sm:text-sm transition-colors shadow-md shadow-sky-500/20"
            >
              <Calculator size={15} /> Apply Changes
            </button>
            <button
              type="button"
              onClick={handleResetDefaults}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-slate-300 font-medium text-xs sm:text-sm border border-white/10 transition-colors"
            >
              <RotateCcw size={15} /> Reset Defaults
            </button>
          </div>

          <button
            type="button"
            onClick={handleSaveConfig}
            disabled={saving}
            className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs sm:text-sm transition-colors shadow-md shadow-emerald-500/20 disabled:opacity-50"
          >
            <Save size={16} /> {saving ? "Saving Configuration..." : "Save Configuration"}
          </button>
        </div>
      </div>
    </div>
  );
}
