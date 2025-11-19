export type SiteStatus = "good" | "warning" | "poor";
export type AlertSeverity = "info" | "warning" | "critical";
export type AnalysisTone = "rose" | "amber" | "emerald" | "sky" | "violet";

export interface DashboardKpis {
  ph: number;
  do: number;
  temp: number;
  turbidity: number;
}

export interface DashboardTimeseriesPoint {
  date: string;
  value: number;
}

export interface DashboardSite {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  county: string;
  status: SiteStatus;
}

export interface DashboardAlert {
  id: string;
  title: string;
  severity: AlertSeverity;
  message: string;
  timestamp: string;
}

export interface DashboardOperations {
  filtrationHours: number;
  cleaningMinutes: number;
  disinfectionHours: number;
}

export interface DashboardMobileStatus {
  nickname: string;
  owner: string;
  waterTemp: number;
  airTemp: number;
  automation: boolean;
}

export interface DashboardMobileTimeline {
  day: string;
  filtrationHours: number;
  cleaningMinutes: number;
  disinfectionHours: number;
}

export interface DashboardMobileAnalysis {
  label: string;
  value: number;
  unit: string;
  tone: AnalysisTone;
}

export interface DashboardMobilePayload {
  status: DashboardMobileStatus;
  timeline: DashboardMobileTimeline;
  analysis: DashboardMobileAnalysis[];
}

export interface DashboardData {
  kpis: DashboardKpis;
  timeseries: DashboardTimeseriesPoint[];
  alerts: DashboardAlert[];
  sites: DashboardSite[];
  operations: DashboardOperations;
  mobile: DashboardMobilePayload;
}

export type ParameterStatus = "ok" | "warning" | "critical";

export interface ParameterSummary {
  parameter: string;
  unit: string;
  average: number;
  minimum: number;
  maximum: number;
  status: ParameterStatus;
  directive?: string | null;
}

export interface ParameterPoint {
  timestamp: string;
  value: number;
}

export interface ParameterSeries {
  parameter: string;
  points: ParameterPoint[];
}

export interface MLInsights {
  pollution_prediction?: number | null;
  pollution_score?: number | null;
  pollution_label?: string | null;
  forecasts?: Record<string, number[]>;
  model_available: boolean;
}

export interface UploadReport {
  id: string;
  uploaded_by: string;
  created_at: string;
  source_filename?: string | null;
  parameters: ParameterSummary[];
  timeseries: ParameterSeries[];
  alerts: DashboardAlert[];
  recommendations: string[];
  ml_insights?: MLInsights | null;
}

