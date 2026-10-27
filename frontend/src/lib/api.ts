import {
  HealthResponse,
  EnergyListResponse,
  ImportResponse,
  AnalyticsSummaryResponse,
  DailyAnalyticsResponse,
  FacilitiesResponse,
  ForecastResponse,
  AnomaliesResponse,
  RecommendationsResponse,
  TariffConfig,
  TariffCalculationResult,
  TariffGetResponse,
  ApiResponse,
} from "../types/api";

export const getApiBaseUrl = (): string => {
  if (typeof window !== "undefined") {
    const custom = window.localStorage.getItem("SMART_ENERGY_API_BASE_URL");
    if (custom && custom.trim() !== "") {
      return custom.trim().replace(/\/$/, "");
    }
  }
  return (process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
};

export const setApiBaseUrl = (url: string): void => {
  if (typeof window !== "undefined") {
    if (url && url.trim() !== "") {
      window.localStorage.setItem("SMART_ENERGY_API_BASE_URL", url.trim().replace(/\/$/, ""));
    } else {
      window.localStorage.removeItem("SMART_ENERGY_API_BASE_URL");
    }
  }
};

interface RequestOptions extends RequestInit {
  timeout?: number;
}

const request = async <T>(path: string, options: RequestOptions = {}): Promise<ApiResponse<T>> => {
  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl}${path.startsWith("/") ? path : `/${path}`}`;

  const headers: HeadersInit = {
    Accept: "application/json",
    ...(options.headers || {}),
  };

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), options.timeout || 12000);

    const res = await fetch(url, {
      ...options,
      headers,
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (res.ok) {
      const data: T = await res.json();
      return { data, error: null };
    }

    if (res.status === 503) {
      let detail = "Database or backend services are degraded/unavailable.";
      try {
        const errJson = await res.json();
        detail = errJson.detail || errJson.message || detail;
      } catch (_) {}
      return { data: null, error: `Service Unavailable (503): ${detail}` };
    }

    let errorMsg = `HTTP ${res.status}`;
    try {
      const errJson = await res.json();
      errorMsg = errJson.detail || errJson.message || errorMsg;
    } catch (_) {
      const txt = await res.text();
      if (txt) errorMsg = `${errorMsg}: ${txt.slice(0, 100)}`;
    }
    return { data: null, error: errorMsg };
  } catch (err: any) {
    if (err?.name === "AbortError") {
      return { data: null, error: `Request timed out connecting to ${baseUrl}` };
    }
    return {
      data: null,
      error: `Cannot reach backend at ${baseUrl}. Ensure the FastAPI server is running.`,
    };
  }
};

export const api = {
  checkHealth: async (): Promise<ApiResponse<HealthResponse>> =>
    request<HealthResponse>("/health", { timeout: 4000 }),

  getEnergyRecords: async ({
    page = 1,
    limit = 50,
    start_date = null,
    end_date = null,
  }: {
    page?: number;
    limit?: number;
    start_date?: string | null;
    end_date?: string | null;
  } = {}): Promise<ApiResponse<EnergyListResponse>> => {
    const params = new URLSearchParams({ page: String(page), limit: String(limit) });
    if (start_date) params.append("start_date", start_date);
    if (end_date) params.append("end_date", end_date);
    return request<EnergyListResponse>(`/api/energy?${params.toString()}`);
  },

  importDatasetFile: async (file: File): Promise<ApiResponse<ImportResponse>> => {
    const baseUrl = getApiBaseUrl();
    const url = `${baseUrl}/api/energy/import`;
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(url, {
        method: "POST",
        body: formData,
      });
      if (res.ok) {
        const data: ImportResponse = await res.json();
        return { data, error: null };
      }
      let err = `HTTP ${res.status}`;
      try {
        const j = await res.json();
        err = j.detail || j.message || err;
      } catch (_) {}
      return { data: null, error: err };
    } catch (e: any) {
      return { data: null, error: e?.message || "File upload failed" };
    }
  },

  importDefaultDataset: async (): Promise<ApiResponse<ImportResponse>> => {
    return request<ImportResponse>("/api/energy/import?use_default_dataset=true", {
      method: "POST",
      timeout: 25000,
    });
  },

  getAnalyticsSummary: async (): Promise<ApiResponse<AnalyticsSummaryResponse>> =>
    request<AnalyticsSummaryResponse>("/api/analytics/summary"),

  getDailySeries: async (): Promise<ApiResponse<DailyAnalyticsResponse>> =>
    request<DailyAnalyticsResponse>("/api/analytics/daily"),

  getFacilityBreakdown: async (): Promise<ApiResponse<FacilitiesResponse>> =>
    request<FacilitiesResponse>("/api/analytics/facilities"),

  getForecast: async (): Promise<ApiResponse<ForecastResponse>> =>
    request<ForecastResponse>("/api/forecast"),

  getAnomalies: async (): Promise<ApiResponse<AnomaliesResponse>> =>
    request<AnomaliesResponse>("/api/anomalies"),

  getRecommendations: async (): Promise<ApiResponse<RecommendationsResponse>> =>
    request<RecommendationsResponse>("/api/recommendations"),

  getTariffConfig: async (): Promise<ApiResponse<TariffGetResponse>> =>
    request<TariffGetResponse>("/api/tariff"),

  updateTariffConfig: async (config: TariffConfig): Promise<ApiResponse<TariffConfig>> =>
    request<TariffConfig>("/api/tariff", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(config),
    }),

  calculateTariff: async ({
    consumption_kwh,
    config,
  }: {
    consumption_kwh: number;
    config?: TariffConfig;
  }): Promise<ApiResponse<TariffCalculationResult>> =>
    request<TariffCalculationResult>("/api/tariff/calculate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ consumption_kwh, config }),
    }),

  resetTariffConfig: async (profile: string = "commercial"): Promise<ApiResponse<TariffConfig>> =>
    request<TariffConfig>(`/api/tariff/reset?profile=${encodeURIComponent(profile)}`, {
      method: "POST",
    }),
};
