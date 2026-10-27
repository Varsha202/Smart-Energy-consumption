"use client";

import { useState, useEffect } from "react";
import { api } from "../lib/api";
import { RecommendationsResponse } from "../types/api";
import { Zap, DollarSign, Leaf, RefreshCw, AlertTriangle, Lightbulb } from "lucide-react";

interface InsightsViewProps {
  refreshTrigger?: number;
}

export default function InsightsView({ refreshTrigger = 0 }: InsightsViewProps) {
  const [recData, setRecData] = useState<RecommendationsResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    const { data, error: err } = await api.getRecommendations();
    if (err && !data) {
      setError(err);
    } else {
      setRecData(data);
    }
    setLoading(false);
  };

  useEffect(() => {
    loadData();
  }, [refreshTrigger]);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl sm:text-2xl font-bold text-slate-100 flex items-center gap-2">
          <Lightbulb size={22} className="text-sky-400" />
          Evidence-Based Energy Conservation Recommendations
        </h2>
        <p className="text-xs sm:text-sm text-slate-400 mt-1">
          Targeted engineering interventions derived from empirical campus load profiles and detected operational variances.
        </p>
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

      {/* Summary Impact KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Card 1: Monthly Energy Savings */}
        <div className="glass-panel p-5">
          <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider mb-2">
            <span>Potential Monthly Savings</span>
            <div className="p-2 rounded-lg bg-sky-500/10 text-sky-400">
              <Zap size={18} />
            </div>
          </div>
          <div className="text-2xl sm:text-3xl font-extrabold text-sky-400 tracking-tight">
            {loading
              ? "..."
              : recData
              ? `${Math.round(recData.total_potential_savings_kwh).toLocaleString()} kWh`
              : "0 kWh"}
          </div>
          <div className="text-xs text-slate-500 mt-1">Estimated campus-wide efficiency gain</div>
        </div>

        {/* Card 2: Cost Reduction */}
        <div className="glass-panel p-5">
          <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider mb-2">
            <span>Monthly Cost Reduction</span>
            <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400">
              <DollarSign size={18} />
            </div>
          </div>
          <div className="text-2xl sm:text-3xl font-extrabold text-amber-400 tracking-tight">
            {loading
              ? "..."
              : recData
              ? `₹${Math.round(recData.total_potential_savings_inr).toLocaleString()}`
              : "₹0"}
          </div>
          <div className="text-xs text-slate-500 mt-1">Commercial electricity bill savings</div>
        </div>

        {/* Card 3: CO2 Abatement */}
        <div className="glass-panel p-5">
          <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider mb-2">
            <span>CO₂ Abatement Potential</span>
            <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
              <Leaf size={18} />
            </div>
          </div>
          <div className="text-2xl sm:text-3xl font-extrabold text-emerald-400 tracking-tight">
            {loading
              ? "..."
              : recData
              ? `${Math.round(recData.total_potential_co2_reduction_kg).toLocaleString()} kg`
              : "0 kg"}
          </div>
          <div className="text-xs text-slate-500 mt-1">Direct environmental emission reduction</div>
        </div>
      </div>

      {/* Actionable Recommendations List */}
      <div>
        <h3 className="text-base font-bold text-slate-100 mb-3">
          Prioritized Action Items ({recData?.recommendations?.length || 0})
        </h3>

        {loading ? (
          <div className="glass-panel p-10 flex flex-col items-center justify-center text-slate-400 text-sm">
            <RefreshCw size={24} className="animate-spin text-sky-400 mb-2" />
            <span>Evaluating facility load profiles and calculating savings potential...</span>
          </div>
        ) : !recData?.recommendations?.length ? (
          <div className="glass-panel p-10 text-center text-slate-400 text-sm">
            No recommendations available at this time.
          </div>
        ) : (
          <div className="space-y-4">
            {recData.recommendations.map((rec) => {
              const isHigh = rec.priority === "High";
              const borderCls = isHigh ? "border-l-rose-500" : "border-l-amber-500";
              const badgeCls = isHigh
                ? "bg-rose-500/15 text-rose-300 border-rose-500/30"
                : "bg-amber-500/15 text-amber-300 border-amber-500/30";

              return (
                <div
                  key={rec.id}
                  className={`glass-panel p-5 border-l-4 ${borderCls} glass-panel-hover`}
                >
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-3">
                    <h4 className="text-base font-bold text-sky-400">
                      [{rec.id}] {rec.title}
                    </h4>
                    <span
                      className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border ${badgeCls} self-start sm:self-auto`}
                    >
                      Priority: {rec.priority} • {rec.category}
                    </span>
                  </div>

                  <div className="space-y-2 text-xs sm:text-sm">
                    <div>
                      <strong className="text-slate-100 font-semibold">Operational Evidence: </strong>
                      <span className="text-slate-300">{rec.evidence}</span>
                    </div>

                    <div>
                      <strong className="text-slate-100 font-semibold">Action Plan: </strong>
                      <span className="text-slate-200">{rec.action_plan}</span>
                    </div>
                  </div>

                  {/* Quantified Savings Banner */}
                  <div className="mt-3.5 p-3 rounded-xl bg-slate-900/80 border border-white/5 flex flex-wrap items-center gap-4 text-xs font-semibold text-emerald-400">
                    <div className="flex items-center gap-1.5">
                      <Zap size={14} />
                      <span>Monthly: {Math.round(rec.estimated_monthly_savings_kwh).toLocaleString()} kWh</span>
                    </div>
                    <div className="flex items-center gap-1.5 text-amber-400">
                      <DollarSign size={14} />
                      <span>Cost: ₹{Math.round(rec.estimated_monthly_savings_inr).toLocaleString()}</span>
                    </div>
                    <div className="flex items-center gap-1.5 text-emerald-300">
                      <Leaf size={14} />
                      <span>CO₂: {Math.round(rec.estimated_monthly_co2_reduction_kg).toLocaleString()} kg</span>
                    </div>
                  </div>

                  <div className="mt-2.5 text-[11px] text-slate-400 italic">
                    Engineering Assumptions: {rec.assumptions}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {recData?.methodology_notes && (
          <div className="mt-4 text-center text-xs text-slate-400">
            📌 {recData.methodology_notes}
          </div>
        )}
      </div>
    </div>
  );
}
