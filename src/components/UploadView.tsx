"use client";

import { useState, useEffect } from "react";
import { api } from "../lib/api";
import { EnergyRecord, ImportResponse } from "../types/api";
import {
  UploadCloud,
  Database,
  FileSpreadsheet,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";

interface UploadViewProps {
  onDataImported?: () => void;
}

export default function UploadView({ onDataImported }: UploadViewProps) {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState<boolean>(false);
  const [uploadResult, setUploadResult] = useState<ImportResponse | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const [activeRecords, setActiveRecords] = useState<EnergyRecord[]>([]);
  const [totalRecords, setTotalRecords] = useState<number>(0);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [page, setPage] = useState<number>(1);
  const [loadingRecords, setLoadingRecords] = useState<boolean>(true);

  const fetchRecords = async (p = 1) => {
    setLoadingRecords(true);
    const { data } = await api.getEnergyRecords({ page: p, limit: 10 });
    if (data?.records) {
      setActiveRecords(data.records);
      setTotalRecords(data.total_records || data.records.length);
      setTotalPages(data.total_pages || 1);
      setPage(data.page || p);
    }
    setLoadingRecords(false);
  };

  useEffect(() => {
    fetchRecords(1);
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleFileUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    setUploadResult(null);
    setUploadError(null);

    const { data, error } = await api.importDatasetFile(file);
    if (data) {
      setUploadResult(data);
      fetchRecords(1);
      if (onDataImported) onDataImported();
    } else {
      setUploadError(error || "Upload failed");
    }
    setUploading(false);
  };

  const handleImportDefault = async () => {
    setUploading(true);
    setUploadResult(null);
    setUploadError(null);

    const { data, error } = await api.importDefaultDataset();
    if (data) {
      setUploadResult(data);
      fetchRecords(1);
      if (onDataImported) onDataImported();
    } else {
      setUploadError(error || "Default dataset ingestion failed");
    }
    setUploading(false);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl sm:text-2xl font-bold text-slate-100 flex items-center gap-2">
          <UploadCloud size={24} className="text-sky-400" />
          Ingest & Manage Campus Energy Dataset
        </h2>
        <p className="text-xs sm:text-sm text-slate-400 mt-1">
          Upload new campus meter readings (CSV or Excel) to validate and persist into MongoDB Atlas.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Upload File Form */}
        <div className="lg:col-span-2 glass-panel p-6">
          <h3 className="text-base font-bold text-slate-100 mb-3 flex items-center gap-2">
            <FileSpreadsheet size={18} className="text-sky-400" />
            Upload Energy File
          </h3>

          <form onSubmit={handleFileUpload} className="space-y-4">
            <label
              htmlFor="energy-file-input"
              className="border-2 border-dashed border-sky-400/40 hover:border-sky-400 rounded-2xl p-8 text-center bg-sky-500/5 hover:bg-sky-500/10 cursor-pointer transition-colors block"
            >
              <UploadCloud size={44} className="text-sky-400 mx-auto mb-3" />
              <div className="text-sm font-semibold text-slate-100 mb-1">
                {file ? file.name : "Click to browse or drag & drop energy dataset"}
              </div>
              <div className="text-xs text-slate-400">
                Supports .csv, .xlsx, .xls containing campus dates and facility readings
              </div>
              <input
                id="energy-file-input"
                type="file"
                accept=".csv, .xlsx, .xls"
                onChange={handleFileChange}
                className="hidden"
              />
            </label>

            <button
              type="submit"
              disabled={!file || uploading}
              className="w-full py-2.5 px-4 rounded-xl bg-sky-500 hover:bg-sky-400 text-slate-950 font-semibold text-sm transition-colors shadow-md shadow-sky-500/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {uploading ? (
                <>
                  <RefreshCw size={16} className="animate-spin" /> Ingesting & Validating Records...
                </>
              ) : (
                <>
                  <UploadCloud size={16} /> Validate & Ingest File
                </>
              )}
            </button>
          </form>
        </div>

        {/* Quick Repository Seed Action */}
        <div className="glass-panel p-6 flex flex-col justify-between">
          <div>
            <h3 className="text-base font-bold text-slate-100 mb-2 flex items-center gap-2">
              <Database size={18} className="text-emerald-400" />
              Preprocessed Dataset Seeding
            </h3>
            <p className="text-xs text-slate-400 mb-4 leading-relaxed">
              Instantly seed MongoDB with the canonical July 2026 campus energy dataset located in{" "}
              <code className="text-slate-300 font-mono">data/preprocessed_energy.csv</code>.
            </p>
          </div>

          <button
            onClick={handleImportDefault}
            disabled={uploading}
            className="w-full py-2.5 px-4 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold text-sm transition-colors shadow-md shadow-emerald-500/20 disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {uploading ? (
              <>
                <RefreshCw size={16} className="animate-spin" /> Seeding Database...
              </>
            ) : (
              <>
                <Database size={16} /> Seed Default Dataset
              </>
            )}
          </button>
        </div>
      </div>

      {/* Ingestion Feedback Result */}
      {uploadResult && (
        <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300">
          <div className="flex items-center gap-2 font-semibold text-sm mb-1">
            <CheckCircle2 size={18} /> {uploadResult.message}
          </div>
          <div className="text-xs text-emerald-200/80 flex flex-wrap gap-4 mt-2 font-mono">
            <span>Processed: {uploadResult.total_rows_processed} rows</span>
            <span>Inserted (New): {uploadResult.imported_count}</span>
            <span>Updated (Upserted): {uploadResult.updated_count}</span>
            <span>Skipped: {uploadResult.skipped_count}</span>
          </div>
          {uploadResult.errors?.length > 0 && (
            <div className="mt-2 text-xs text-rose-300">
              Notices: {uploadResult.errors.join("; ")}
            </div>
          )}
        </div>
      )}

      {uploadError && (
        <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300 flex items-start gap-2 text-sm">
          <AlertCircle size={18} className="shrink-0 mt-0.5" />
          <div>{uploadError}</div>
        </div>
      )}

      {/* Active Records Preview */}
      <div className="glass-panel p-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-4 border-b border-white/10 gap-3 mb-4">
          <div>
            <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <Database size={16} className="text-sky-400" />
              Active Energy Records in Database (`GET /api/energy`)
            </h3>
            <p className="text-xs text-slate-400">
              Page {page} of {totalPages} ({totalRecords} total records)
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => fetchRecords(Math.max(1, page - 1))}
              disabled={page <= 1 || loadingRecords}
              className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-slate-300 disabled:opacity-30 disabled:cursor-not-allowed border border-white/10"
            >
              <ChevronLeft size={16} />
            </button>
            <span className="text-xs font-mono text-slate-300 px-2">{page}</span>
            <button
              onClick={() => fetchRecords(page + 1)}
              disabled={page >= totalPages || loadingRecords}
              className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-slate-300 disabled:opacity-30 disabled:cursor-not-allowed border border-white/10"
            >
              <ChevronRight size={16} />
            </button>
          </div>
        </div>

        {loadingRecords ? (
          <div className="py-12 flex items-center justify-center text-slate-400 text-sm">
            <RefreshCw size={20} className="animate-spin mr-2" /> Loading records from API...
          </div>
        ) : activeRecords.length === 0 ? (
          <div className="py-12 text-center text-slate-400 text-sm">
            No records found. Ingest the dataset above to seed records.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="text-[11px] uppercase tracking-wider text-slate-400 border-b border-white/10">
                <tr>
                  <th className="pb-2.5 font-semibold">Date</th>
                  <th className="pb-2.5 font-semibold text-right">Total (kWh)</th>
                  <th className="pb-2.5 font-semibold text-right">Grid TNEB</th>
                  <th className="pb-2.5 font-semibold text-right">Solar</th>
                  <th className="pb-2.5 font-semibold text-right">Diesel</th>
                  <th className="pb-2.5 font-semibold text-right">Academic</th>
                  <th className="pb-2.5 font-semibold text-right">Chiller</th>
                  <th className="pb-2.5 font-semibold text-right">Hostels</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {activeRecords.map((rec) => (
                  <tr key={rec.id || rec._id || rec.date} className="hover:bg-white/5 transition-colors">
                    <td className="py-2.5 font-semibold font-mono text-slate-200">{rec.date}</td>
                    <td className="py-2.5 text-right font-mono font-bold text-sky-400">
                      {Math.round(rec.total).toLocaleString()}
                    </td>
                    <td className="py-2.5 text-right font-mono text-slate-300">
                      {Math.round(rec.tneb_campus).toLocaleString()}
                    </td>
                    <td className="py-2.5 text-right font-mono text-emerald-400">
                      {Math.round(rec.solar).toLocaleString()}
                    </td>
                    <td className="py-2.5 text-right font-mono text-amber-400">
                      {Math.round(rec.diesel).toLocaleString()}
                    </td>
                    <td className="py-2.5 text-right font-mono text-slate-300">
                      {Math.round(rec.academic_blocks).toLocaleString()}
                    </td>
                    <td className="py-2.5 text-right font-mono text-slate-300">
                      {Math.round(rec.chiller).toLocaleString()}
                    </td>
                    <td className="py-2.5 text-right font-mono text-slate-300">
                      {Math.round(rec.hostels).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
