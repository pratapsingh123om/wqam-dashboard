# backend/app/schemas.py
from typing import Literal
from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    password: str
    role: str | None = "user"

class UserOut(BaseModel):
    id: int
    username: str
    role: str

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class KpiBlock(BaseModel):
    ph: float
    do: float
    temp: float
    turbidity: float


class TimeseriesPoint(BaseModel):
    date: str
    value: float


class MapSite(BaseModel):
    id: str
    name: str
    latitude: float
    longitude: float
    county: str
    status: Literal["good", "warning", "poor"]


class Alert(BaseModel):
    id: str
    title: str
    severity: Literal["info", "warning", "critical"]
    message: str
    timestamp: str


class Operations(BaseModel):
    filtrationHours: float
    cleaningMinutes: float
    disinfectionHours: float


class MobileStatus(BaseModel):
    nickname: str
    owner: str
    waterTemp: float
    airTemp: float
    automation: bool


class MobileTimeline(BaseModel):
    day: str
    filtrationHours: float
    cleaningMinutes: float
    disinfectionHours: float


class MobileAnalysis(BaseModel):
    label: str
    value: float
    unit: str
    tone: Literal["rose", "amber", "emerald", "sky", "violet"]


class MobilePayload(BaseModel):
    status: MobileStatus
    timeline: MobileTimeline
    analysis: list[MobileAnalysis]


class DashboardResponse(BaseModel):
    kpis: KpiBlock
    timeseries: list[TimeseriesPoint]
    alerts: list[Alert]
    sites: list[MapSite]
    operations: Operations
    mobile: MobilePayload


class ParameterPoint(BaseModel):
    timestamp: str
    value: float


class ParameterSeries(BaseModel):
    parameter: str
    points: list[ParameterPoint]


class ParameterSummary(BaseModel):
    parameter: str
    unit: str
    average: float
    minimum: float
    maximum: float
    status: Literal["ok", "warning", "critical"]
    directive: str | None = None


class MLInsights(BaseModel):
    pollution_prediction: float | None = None
    pollution_score: float | None = None
    pollution_label: str | None = None
    forecasts: dict[str, list[float]] = {}
    model_available: bool = False


class LocationInfo(BaseModel):
    state: str | None = None
    location: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class UploadReport(BaseModel):
    id: str
    uploaded_by: str
    created_at: str
    source_filename: str | None = None
    parameters: list[ParameterSummary]
    timeseries: list[ParameterSeries]
    alerts: list[Alert]
    recommendations: list[str]
    location: LocationInfo | None = None
    map_status: Literal["good", "warning", "poor"] = "good"
    ml_insights: MLInsights | None = None
