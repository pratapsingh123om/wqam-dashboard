import type { DashboardData, UploadReport, MLInsights } from "../types/dashboard";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

let authToken: string | null = null;

export function setAuthToken(token: string | null) {
  authToken = token;
}

async function apiFetch<T = unknown>(path: string, options: RequestInit = {}): Promise<T> {
  const isFormData = typeof FormData !== "undefined" && options.body instanceof FormData;
  const headers = new Headers(options.headers ?? {});

  if (!isFormData && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  if (authToken) {
    headers.set("Authorization", `Bearer ${authToken}`);
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  const text = await res.text();
  const payload = text ? (() => { try { return JSON.parse(text); } catch { return text; } })() : null;

  if (!res.ok) {
    const detail = typeof payload === "string" ? payload : payload?.detail;
    throw new Error(detail || `API error: ${res.status}`);
  }

  return payload as T;
}

export async function fetchDemo(): Promise<DashboardData> {
  return apiFetch<DashboardData>("/api/demo");
}

export async function uploadWaterData(formData: FormData): Promise<UploadReport> {
  return apiFetch<UploadReport>("/api/uploads/analyze", {
    method: "POST",
    body: formData,
  });
}

export async function fetchReports(): Promise<UploadReport[]> {
  return apiFetch<UploadReport[]>("/api/reports");
}

export async function getMLPredictions(formData: FormData): Promise<MLInsights> {
  return apiFetch<MLInsights>("/api/ml/predict", {
    method: "POST",
    body: formData,
  });
}

export async function getMLStatus(): Promise<{ model_available: boolean; model_path: string | null }> {
  return apiFetch<{ model_available: boolean; model_path: string | null }>("/api/ml/status");
}

export async function downloadReportPdf(reportId: string): Promise<Blob> {
  const headers = new Headers();
  if (authToken) {
    headers.set("Authorization", `Bearer ${authToken}`);
  }
  
  const res = await fetch(`${API_BASE}/api/reports/${reportId}/pdf`, {
    headers,
  });
  
  if (!res.ok) {
    throw new Error(`Failed to download PDF: ${res.status}`);
  }
  
  return res.blob();
}

export async function downloadLatestReportPdf(): Promise<Blob> {
  const headers = new Headers();
  if (authToken) {
    headers.set("Authorization", `Bearer ${authToken}`);
  }
  
  const res = await fetch(`${API_BASE}/api/reports/latest/pdf`, {
    headers,
  });
  
  if (!res.ok) {
    throw new Error(`Failed to download PDF: ${res.status}`);
  }
  
  return res.blob();
}

export default apiFetch;
