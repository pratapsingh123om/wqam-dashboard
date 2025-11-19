# backend/app/main.py
from collections import deque
from datetime import datetime, timedelta
from uuid import uuid4
import io
import os
import random

import pandas as pd
import pdfplumber
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from dotenv import load_dotenv

load_dotenv()

import models
import schemas
from db import SessionLocal, engine, Base
from auth import (
    hash_password,
    verify_password,
    create_access_token,
    decode_token,
)

# create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="WQAM Backend")

# CORS
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
origins = [FRONTEND_URL, "http://localhost:5173", "http://127.0.0.1:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

# --- Analytics configuration -------------------------------------------------
TIME_COLUMN_CANDIDATES = {"timestamp", "time", "date", "datetime", "sampletime"}

PARAMETERS = {
    "ph": {
        "label": "pH",
        "unit": "",
        "min": 6.5,
        "max": 8.5,
        "directive": "Dose lime or acid to keep pH within 6.5-8.5.",
    },
    "turbidity": {
        "label": "Turbidity",
        "unit": "NTU",
        "max": 5.0,
        "directive": "Check filters/backwash to reduce particulate load.",
    },
    "tds": {
        "label": "TDS",
        "unit": "mg/L",
        "max": 500.0,
        "directive": "Investigate source water or ion exchange before distribution.",
    },
    "do": {
        "label": "Dissolved Oxygen",
        "unit": "mg/L",
        "min": 5.0,
        "directive": "Increase aeration/recirculation for better oxygen transfer.",
    },
    "chlorine": {
        "label": "Free Chlorine",
        "unit": "ppm",
        "min": 0.2,
        "max": 0.5,
        "directive": "Tweak dosing pump to maintain disinfectant residual.",
    },
}

COLUMN_ALIASES = {
    "ph": "ph",
    "potentialofhydrogen": "ph",
    "turbidity": "turbidity",
    "ntu": "turbidity",
    "tds": "tds",
    "totaldissolvedsolids": "tds",
    "dissolvedoxygen": "do",
    "do": "do",
    "oxygen": "do",
    "freechlorine": "chlorine",
    "chlorine": "chlorine",
    "cl2": "chlorine",
}

REPORT_HISTORY: deque[dict] = deque(maxlen=25)

# -----------------------------------------------------------------------------
# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    username = payload.get("sub")
    if username is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def _slugify(value: str) -> str:
    return "".join(ch for ch in value.lower() if ch.isalnum())


def _match_parameter_column(columns: list[str], parameter_key: str) -> str | None:
    for column in columns:
        slug = _slugify(str(column))
        resolved = COLUMN_ALIASES.get(slug)
        if resolved == parameter_key:
            return column
        if slug == parameter_key:
            return column
    return None


def _load_dataframe_from_upload(contents: bytes, filename: str | None) -> pd.DataFrame:
    name = (filename or "").lower()
    try:
        if name.endswith(".pdf"):
            return _dataframe_from_pdf(contents)
        if name.endswith(".xlsx") or name.endswith(".xls"):
            return pd.read_excel(io.BytesIO(contents))
        # default to CSV
        return pd.read_csv(io.BytesIO(contents))
    except Exception as exc:  # pragma: no cover - surface friendly message
        raise HTTPException(status_code=400, detail=f"Unable to parse file: {exc}") from exc


def _dataframe_from_pdf(contents: bytes) -> pd.DataFrame:
    rows: list[list[str]] = []
    with pdfplumber.open(io.BytesIO(contents)) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if table:
                rows.extend(table)
    if not rows:
        raise HTTPException(status_code=400, detail="Could not extract tabular data from PDF")
    header = rows[0]
    body = [row for row in rows[1:] if any(cell is not None for cell in row)]
    return pd.DataFrame(body, columns=header)


def _prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(col).strip() for col in df.columns]
    df = df.dropna(how="all")
    return df


def _build_report_payload(df: pd.DataFrame, username: str, filename: str | None) -> dict:
    df = _prepare_dataframe(df)
    if df.empty:
        raise HTTPException(status_code=400, detail="Dataset is empty after cleaning.")

    time_column = next((col for col in df.columns if str(col).strip().lower() in TIME_COLUMN_CANDIDATES), None)
    if time_column:
        df[time_column] = pd.to_datetime(df[time_column], errors="coerce")
        if df[time_column].isna().all():
            time_column = None

    if not time_column:
        time_column = "generated_timestamp"
        df[time_column] = pd.date_range(end=datetime.utcnow(), periods=len(df))
    else:
        df[time_column] = df[time_column].fillna(method="ffill").fillna(method="bfill")
        df[time_column] = df[time_column].fillna(pd.Timestamp.utcnow())

    timestamps = df[time_column].dt.strftime("%Y-%m-%d %H:%M:%S").tolist()

    parameter_summaries: list[dict] = []
    parameter_series: list[dict] = []
    alerts: list[dict] = []
    recommendations: list[str] = []
    evaluation_time = datetime.utcnow().isoformat()

    for key, config in PARAMETERS.items():
        column = _match_parameter_column(df.columns.tolist(), key)
        if column is None:
            continue
        values = pd.to_numeric(df[column], errors="coerce")
        filled_values = values.ffill().bfill()
        if filled_values.dropna().empty:
            continue
        series_points = [
            {"timestamp": timestamps[idx], "value": round(float(val), 3)}
            for idx, val in enumerate(filled_values)
        ]

        avg = float(filled_values.mean())
        min_val = float(filled_values.min())
        max_val = float(filled_values.max())

        status = "ok"
        directive = config.get("directive")
        min_threshold = config.get("min")
        max_threshold = config.get("max")

        if min_threshold is not None and min_val < min_threshold:
            status = "warning"
        if max_threshold is not None and max_val > max_threshold:
            status = "warning"
        if (
            (min_threshold is not None and min_val < min_threshold * 0.8)
            or (max_threshold is not None and max_val > max_threshold * 1.2)
        ):
            status = "critical"

        if status != "ok":
            alerts.append(
                {
                    "id": f"{key}-{uuid4().hex[:6]}",
                    "title": f"{config['label']} out of range",
                    "severity": "critical" if status == "critical" else "warning",
                    "message": f"{config['label']} recorded {round(max_val if status!='ok' else avg, 2)} {config['unit']}",
                    "timestamp": evaluation_time,
                }
            )
            if directive and directive not in recommendations:
                recommendations.append(directive)

        parameter_summaries.append(
            {
                "parameter": config["label"],
                "unit": config["unit"],
                "average": round(avg, 3),
                "minimum": round(min_val, 3),
                "maximum": round(max_val, 3),
                "status": status,
                "directive": directive if status != "ok" else None,
            }
        )
        parameter_series.append({"parameter": config["label"], "points": series_points})

    if not parameter_summaries:
        raise HTTPException(status_code=400, detail="No recognized water-quality parameters in file.")

    if not recommendations:
        recommendations.append("All monitored parameters fall within the configured guardrails.")

    return {
        "id": uuid4().hex,
        "uploaded_by": username,
        "created_at": evaluation_time,
        "source_filename": filename,
        "parameters": parameter_summaries,
        "timeseries": parameter_series,
        "alerts": alerts,
        "recommendations": recommendations,
    }
@app.post("/api/auth/register", response_model=schemas.UserOut)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    exists = db.query(models.User).filter(models.User.username == user_in.username).first()
    if exists:
        raise HTTPException(status_code=400, detail="Username already exists")
    # if role is admin, allow creation always for now (can be restricted in prod)
    user = models.User(
        username=user_in.username,
        hashed_password=hash_password(user_in.password),
        role=user_in.role or "user"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@app.post("/api/auth/login", response_model=schemas.Token)
def login(form: schemas.UserCreate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token({"sub": user.username, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer", "role": user.role}

@app.get("/api/auth/me", response_model=schemas.UserOut)
def me(current_user: models.User = Depends(get_current_user)):
    return current_user

# simple health
@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/demo", response_model=schemas.DashboardResponse)
def demo_snapshot(current_user: models.User = Depends(get_current_user)):
    """Return a curated snapshot used by the dashboard UI."""
    now = datetime.utcnow()
    timeseries = [
        {
            "date": (now - timedelta(days=29 - idx)).strftime("%Y-%m-%d"),
            "value": round(58 + 6 * random.random() + idx * 0.3, 2),
        }
        for idx in range(30)
    ]

    sites = [
        {
            "id": "s1",
            "name": "Godavari Intake",
            "latitude": 17.6597,
            "longitude": 75.9064,
            "county": "District HQ",
            "status": "good",
        },
        {
            "id": "s2",
            "name": "WTP Valve House",
            "latitude": 18.506,
            "longitude": 73.8567,
            "county": "Urban",
            "status": "warning",
        },
        {
            "id": "s3",
            "name": "Storage Reservoir",
            "latitude": 19.9975,
            "longitude": 73.7898,
            "county": "Rural",
            "status": "poor",
        },
        {
            "id": "s4",
            "name": "Canal Outlet",
            "latitude": 20.5937,
            "longitude": 78.9629,
            "county": "Outreach",
            "status": "good",
        },
    ]

    alerts = [
        {
            "id": "a1",
            "title": "Turbidity rising",
            "severity": "warning",
            "message": "NTU crossed 4.5 at Storage Reservoir",
            "timestamp": now.isoformat(),
        },
        {
            "id": "a2",
            "title": "Disinfection overdue",
            "severity": "critical",
            "message": "Chlorine dosing pending for Canal Outlet",
            "timestamp": (now - timedelta(hours=2)).isoformat(),
        },
        {
            "id": "a3",
            "title": "Pump maintenance",
            "severity": "info",
            "message": "Scheduled backwash cycle at WTP Valve House",
            "timestamp": (now - timedelta(hours=5)).isoformat(),
        },
    ]

    operations = {
        "filtrationHours": 18,
        "cleaningMinutes": 35,
        "disinfectionHours": 8,
    }

    mobile_payload = {
        "status": {
            "nickname": "Effortless Pool",
            "owner": current_user.username,
            "waterTemp": 25,
            "airTemp": 18,
            "automation": True,
        },
        "timeline": {
            "day": now.strftime("%a %d"),
            "filtrationHours": 17,
            "cleaningMinutes": operations["cleaningMinutes"],
            "disinfectionHours": operations["disinfectionHours"],
        },
        "analysis": [
            {"label": "Free chlorine", "value": 0.27, "unit": "ppm", "tone": "rose"},
            {"label": "Combined chlorine", "value": 0.02, "unit": "ppm", "tone": "emerald"},
            {"label": "pH", "value": 7.5, "unit": "", "tone": "amber"},
            {"label": "Total chlorine", "value": 2.1, "unit": "ppm", "tone": "violet"},
        ],
    }

    return {
        "kpis": {"ph": 7.2, "do": 6.8, "temp": 23.5, "turbidity": 2.4},
        "timeseries": timeseries,
        "alerts": alerts,
        "sites": sites,
        "operations": operations,
        "mobile": mobile_payload,
    }


@app.post("/api/uploads/analyze", response_model=schemas.UploadReport)
async def analyze_upload(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
):
    contents = await file.read()
    df = _load_dataframe_from_upload(contents, file.filename)
    report = _build_report_payload(df, current_user.username, file.filename)
    REPORT_HISTORY.appendleft(report)
    return report


@app.get("/api/reports", response_model=list[schemas.UploadReport])
def list_reports(current_user: models.User = Depends(get_current_user)):
    return list(REPORT_HISTORY)


@app.get("/api/reports/latest", response_model=schemas.UploadReport | None)
def latest_report(current_user: models.User = Depends(get_current_user)):
    return REPORT_HISTORY[0] if REPORT_HISTORY else None
