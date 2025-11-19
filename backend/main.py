# backend/app/main.py
from collections import deque
from datetime import datetime, timedelta
from uuid import uuid4
import io
import os
import random

import pandas as pd
import pdfplumber
import re
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
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
from ml_service import get_ml_insights, predict_pollution, forecast_trend
from pathlib import Path

ML_DIR = Path(__file__).resolve().parent.parent / "ml"
MODEL_PATH = ML_DIR / "model" / "water_model.pkl"

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
    "bod": {
        "label": "BOD",
        "unit": "mg/L",
        "max": 3.0,
        "directive": "Biological treatment required if BOD exceeds 3 mg/L.",
    },
    "cod": {
        "label": "COD",
        "unit": "mg/L",
        "max": 250.0,
        "directive": "Investigate industrial effluents; consider advanced oxidation processes.",
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
    "totaldissolved": "tds",
    "dissolvedoxygen": "do",
    "do": "do",
    "d.o.": "do",
    "oxygen": "do",
    "bod": "bod",
    "b.o.d": "bod",
    "biochemical": "bod",
    "biochemicaloxygendemand": "bod",
    "cod": "cod",
    "chemical": "cod",
    "chemicaloxygendemand": "cod",
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
    """Match parameter columns using multiple strategies like ML code."""
    # Strategy 1: Direct slug match
    for column in columns:
        slug = _slugify(str(column))
        resolved = COLUMN_ALIASES.get(slug)
        if resolved == parameter_key:
            return column
        if slug == parameter_key:
            return column
    
    # Strategy 2: Keyword matching (like ML code) - more flexible
    column_lower = {str(c).lower(): c for c in columns}
    param_keywords = {
        "bod": ["bod", "b.o.d", "biochemical"],
        "cod": ["cod", "chemical"],
        "do": ["do", "dissolved", "d.o."],
        "ph": ["ph"],
        "tds": ["tds", "total dissolved"],
        "turbidity": ["turbidity", "ntu"],
        "chlorine": ["chlorine", "freechlorine", "cl2"],
    }
    
    keywords = param_keywords.get(parameter_key, [])
    for keyword in keywords:
        for col_lower, col_original in column_lower.items():
            if keyword in col_lower:
                return col_original
    
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


def _extract_text_from_pdf(contents: bytes) -> str:
    """Extract all text from PDF for regex fallback parsing."""
    text_parts = []
    try:
        with pdfplumber.open(io.BytesIO(contents)) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
    except Exception:
        pass
    return "\n".join(text_parts)


def _parse_parameters_from_text(text: str) -> dict:
    """Extract water quality parameters from text using regex (fallback method)."""
    def find_nums(patterns):
        found = []
        for pat in patterns:
            for m in re.findall(pat, text, flags=re.IGNORECASE):
                v = m[-1] if isinstance(m, tuple) else m
                v = re.sub(r"[^\d\.\-]", "", v or "")
                try:
                    if v not in ("", ".", "-", "-."):
                        found.append(float(v))
                except ValueError:
                    pass
        return found
    
    return {
        "bod": find_nums([r"bod[^\d\-\.]{0,6}([0-9]+(?:\.[0-9]+)?)", r"biochemical oxygen demand[^\d\-\.]{0,6}([0-9]+(?:\.[0-9]+)?)"]),
        "do": find_nums([r"\bdo[^\d\-\.]{0,6}([0-9]+(?:\.[0-9]+)?)", r"dissolved oxygen[^\d\-\.]{0,6}([0-9]+(?:\.[0-9]+)?)"]),
        "cod": find_nums([r"\bcod[^\d\-\.]{0,6}([0-9]+(?:\.[0-9]+)?)", r"chemical oxygen demand[^\d\-\.]{0,6}([0-9]+(?:\.[0-9]+)?)"]),
        "ph": find_nums([r"\bph[^\d\-\.]{0,6}([0-9]+(?:\.[0-9]+)?)"]),
        "tds": find_nums([r"\btds[^\d\-\.]{0,6}([0-9]+(?:\.[0-9]+)?)", r"total dissolved solids[^\d\-\.]{0,6}([0-9]+(?:\.[0-9]+)?)"]),
    }


def _coerce_to_numeric(df: pd.DataFrame) -> pd.DataFrame:
    """Convert all columns to numeric by stripping non-numeric characters."""
    df = df.copy()
    for col in list(df.columns):
        try:
            # Convert to string, strip non-numeric chars (except decimal point and minus), convert to numeric
            s = df[col].astype(str).str.replace(r'[^0-9\.\-]', '', regex=True)
            s = pd.to_numeric(s, errors='coerce')
            df[col] = s
        except Exception:
            # Fallback: try direct numeric coercion
            try:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            except Exception:
                pass
    return df


def _dataframe_from_pdf(contents: bytes) -> pd.DataFrame:
    """Extract tables from PDF and create DataFrame with fallback to text parsing."""
    rows: list[list[str]] = []
    all_tables = []
    
    # Try to extract tables
    try:
        with pdfplumber.open(io.BytesIO(contents)) as pdf:
            print(f"[DEBUG] PDF has {len(pdf.pages)} pages")
            for page_num, page in enumerate(pdf.pages):
                try:
                    tables = page.extract_tables()
                    if tables:
                        print(f"[DEBUG] Page {page_num + 1}: Found {len(tables)} tables")
                        all_tables.extend(tables)
                except Exception as e:
                    print(f"[DEBUG] Page {page_num + 1}: Error extracting tables: {e}")
                    continue
    except Exception as e:
        print(f"[ERROR] Failed to open PDF: {e}")
        raise HTTPException(status_code=400, detail=f"Could not open PDF file: {str(e)}")
    
    # Process all tables
    dfs = []
    for table in all_tables:
        if not table or len(table) < 2:
            continue
        
        header = table[0]
        rows_data = table[1:]
        
        # Clean header row - remove newlines and normalize whitespace
        cleaned_header = []
        for col in header:
            if col is None:
                cleaned_header.append(f"col_{len(cleaned_header)}")
            else:
                cleaned = str(col).replace("\n", " ").replace("\r", " ").strip()
                cleaned = " ".join(cleaned.split())
                if not cleaned:
                    cleaned = f"col_{len(cleaned_header)}"
                cleaned_header.append(cleaned)
        
        # Clean body rows
        body = []
        for row in rows_data:
            if any(cell is not None for cell in row):
                # Pad row if needed
                while len(row) < len(cleaned_header):
                    row.append(None)
                body.append(row[:len(cleaned_header)])
        
        if body:
            df = pd.DataFrame(body, columns=cleaned_header)
            # Coerce to numeric
            df = _coerce_to_numeric(df)
            # Remove empty columns and rows
            df = df.dropna(axis=1, how='all').dropna(axis=0, how='all')
            if not df.empty:
                dfs.append(df)
    
    # Combine all dataframes
    if dfs:
        combined_df = pd.concat(dfs, ignore_index=True, sort=False)
        # Final numeric coercion
        combined_df = _coerce_to_numeric(combined_df)
        return combined_df
    
    # Fallback: extract from text if no tables found
    text = _extract_text_from_pdf(contents)
    if text:
        parsed = _parse_parameters_from_text(text)
        # Create a simple dataframe from parsed values
        max_len = max((len(v) for v in parsed.values()), default=0)
        if max_len > 0:
            data = {}
            for param, values in parsed.items():
                if values:
                    data[param] = values + [None] * (max_len - len(values))
            if data:
                return pd.DataFrame(data)
    
    raise HTTPException(status_code=400, detail="Could not extract tabular data from PDF")


def _prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # Clean column names: remove newlines, normalize whitespace
    cleaned_columns = []
    for col in df.columns:
        col_str = str(col).strip()
        # Replace newlines and carriage returns with spaces
        col_str = col_str.replace("\n", " ").replace("\r", " ")
        # Normalize multiple spaces to single space
        col_str = " ".join(col_str.split())
        # If empty, use a default name
        if not col_str:
            col_str = f"column_{len(cleaned_columns)}"
        cleaned_columns.append(col_str)
    df.columns = cleaned_columns
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
        df[time_column] = df[time_column].ffill().bfill()
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

    # Get ML insights
    ml_insights = get_ml_insights(df)
    
    # Merge ML recommendations with existing recommendations
    if ml_insights.get("recommendations"):
        for ml_rec in ml_insights["recommendations"]:
            if ml_rec not in recommendations:
                recommendations.append(ml_rec)

    return {
        "id": uuid4().hex,
        "uploaded_by": username,
        "created_at": evaluation_time,
        "source_filename": filename,
        "parameters": parameter_summaries,
        "timeseries": parameter_series,
        "alerts": alerts,
        "recommendations": recommendations,
        "ml_insights": {
            "pollution_prediction": ml_insights.get("pollution_prediction"),
            "pollution_score": ml_insights.get("pollution_score"),
            "pollution_label": ml_insights.get("pollution_label"),
            "forecasts": ml_insights.get("forecasts", {}),
            "model_available": ml_insights.get("model_available", False),
        },
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
    try:
        contents = await file.read()
        if not contents:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        
        print(f"[DEBUG] Processing file: {file.filename}, size: {len(contents)} bytes")
        df = _load_dataframe_from_upload(contents, file.filename)
        print(f"[DEBUG] DataFrame shape: {df.shape}, columns: {list(df.columns)[:10]}")
        
        if df.empty:
            raise HTTPException(status_code=400, detail="No data could be extracted from the file")
        
        report = _build_report_payload(df, current_user.username, file.filename)
        REPORT_HISTORY.appendleft(report)
        return report
    except HTTPException:
        raise
    except Exception as exc:
        print(f"[ERROR] Upload analysis failed: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to analyze file: {str(exc)}")


@app.get("/api/reports", response_model=list[schemas.UploadReport])
def list_reports(current_user: models.User = Depends(get_current_user)):
    return list(REPORT_HISTORY)


@app.get("/api/reports/latest", response_model=schemas.UploadReport | None)
def latest_report(current_user: models.User = Depends(get_current_user)):
    return REPORT_HISTORY[0] if REPORT_HISTORY else None


@app.post("/api/ml/predict", response_model=schemas.MLInsights)
async def ml_predict(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
):
    """Get ML predictions for uploaded water quality data"""
    contents = await file.read()
    df = _load_dataframe_from_upload(contents, file.filename)
    df = _prepare_dataframe(df)
    if df.empty:
        raise HTTPException(status_code=400, detail="Dataset is empty after cleaning.")
    
    insights = get_ml_insights(df)
    return schemas.MLInsights(
        pollution_prediction=insights.get("pollution_prediction"),
        pollution_score=insights.get("pollution_score"),
        pollution_label=insights.get("pollution_label"),
        forecasts=insights.get("forecasts", {}),
        model_available=insights.get("model_available", False),
    )


@app.get("/api/ml/status")
def ml_status(current_user: models.User = Depends(get_current_user)):
    """Check ML model availability"""
    from ml_service import load_model
    model, _ = load_model()
    return {
        "model_available": model is not None,
        "model_path": str(MODEL_PATH) if MODEL_PATH.exists() else None,
    }


def _generate_pdf_report(report: dict, df: pd.DataFrame) -> io.BytesIO:
    """Generate a PDF report with visualizations from the analysis report."""
    buffer = io.BytesIO()
    colors = ["#2b83ba", "#abdda4", "#fdae61", "#d7191c", "#984ea3", "#4daf4a"]
    
    with PdfPages(buffer) as pdf:
        # Title page
        fig, ax = plt.subplots(figsize=(8.27, 11.69))
        ax.axis('off')
        ax.text(0.5, 0.92, "Water Quality Analysis Report", ha='center', fontsize=20, weight='bold')
        ax.text(0.5, 0.88, f"Source: {report.get('source_filename', 'Unknown')}", ha='center', fontsize=12)
        ax.text(0.5, 0.85, f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", ha='center', fontsize=10)
        ax.text(0.5, 0.80, f"Analyzed by: {report.get('uploaded_by', 'Unknown')}", ha='center', fontsize=10)
        
        # Summary statistics
        y = 0.70
        ax.text(0.1, y, "Parameter Summary:", fontsize=14, weight='bold')
        y -= 0.05
        for param in report.get('parameters', [])[:10]:
            status_icon = "✓" if param['status'] == 'ok' else "⚠" if param['status'] == 'warning' else "✗"
            ax.text(0.1, y, f"{status_icon} {param['parameter']:<20} Avg: {param['average']:.2f} {param['unit']} "
                   f"(Range: {param['minimum']:.2f} - {param['maximum']:.2f})", fontsize=10)
            y -= 0.04
        
        # ML Insights if available
        if report.get('ml_insights', {}).get('model_available'):
            y -= 0.05
            ax.text(0.1, y, "ML Predictions:", fontsize=14, weight='bold')
            y -= 0.04
            ml = report['ml_insights']
            if ml.get('pollution_score') is not None:
                ax.text(0.1, y, f"Pollution Score: {ml['pollution_score']:.1f} ({ml.get('pollution_label', 'N/A')})", fontsize=10)
                y -= 0.04
            if ml.get('pollution_prediction') is not None:
                ax.text(0.1, y, f"Predicted Pollution Level: {ml['pollution_prediction']:.2f}", fontsize=10)
                y -= 0.04
        
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
        
        # Parameter histograms
        for i, param in enumerate(report.get('parameters', [])):
            param_key = param['parameter'].lower()
            # Try to find matching column in dataframe
            matching_col = None
            for col in df.columns:
                if param_key in str(col).lower() or any(kw in str(col).lower() for kw in [param_key[:3], param_key]):
                    matching_col = col
                    break
            
            if matching_col is None:
                continue
                
            series = pd.to_numeric(df[matching_col], errors='coerce').dropna()
            if series.size < 3:
                continue
                
            fig, ax = plt.subplots(figsize=(8.27, 5.5))
            ax.hist(series.values, bins=min(25, max(10, series.size // 5)), 
                   color=colors[i % len(colors)], edgecolor='k', alpha=0.7)
            ax.set_title(f"{param['parameter']} Distribution (n={series.size})", fontsize=14, weight='bold')
            ax.set_xlabel(f"{param['parameter']} ({param['unit']})")
            ax.set_ylabel("Frequency")
            ax.grid(True, alpha=0.3)
            stats_text = f"Mean: {series.mean():.2f}\nMedian: {series.median():.2f}\nMin: {series.min():.2f}\nMax: {series.max():.2f}"
            ax.text(0.98, 0.95, stats_text, transform=ax.transAxes, ha='right', va='top',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5), fontsize=9)
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)
        
        # Timeseries plots
        for series in report.get('timeseries', []):
            if len(series['points']) < 2:
                continue
            fig, ax = plt.subplots(figsize=(8.27, 5.5))
            points = series['points']
            timestamps = [p['timestamp'] for p in points]
            values = [p['value'] for p in points]
            ax.plot(timestamps, values, marker='o', linewidth=2, markersize=4, color=colors[0])
            ax.set_title(f"{series['parameter']} Over Time", fontsize=14, weight='bold')
            ax.set_xlabel("Time")
            ax.set_ylabel(f"{series['parameter']}")
            ax.grid(True, alpha=0.3)
            plt.xticks(rotation=45, ha='right')
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)
        
        # Recommendations page
        fig, ax = plt.subplots(figsize=(8.27, 11.69))
        ax.axis('off')
        ax.text(0.5, 0.95, "Recommendations & Treatment Guidance", ha='center', fontsize=18, weight='bold')
        y = 0.85
        for rec in report.get('recommendations', []):
            wrapped = '\n'.join([rec[i:i+80] for i in range(0, len(rec), 80)])
            ax.text(0.1, y, f"• {wrapped}", fontsize=10, va='top')
            y -= len(wrapped.split('\n')) * 0.03 + 0.02
            if y < 0.1:
                break
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
    
    buffer.seek(0)
    return buffer


@app.get("/api/reports/{report_id}/pdf")
async def download_report_pdf(
    report_id: str,
    current_user: models.User = Depends(get_current_user),
):
    """Generate and download a PDF report for a specific analysis."""
    report = next((r for r in REPORT_HISTORY if r['id'] == report_id), None)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Reconstruct dataframe from report (simplified - in production, store the dataframe)
    # For now, we'll create a minimal dataframe from the timeseries data
    df_data = {}
    for series in report.get('timeseries', []):
        param = series['parameter']
        if param not in df_data:
            df_data[param] = []
        for point in series['points']:
            df_data[param].append(point['value'])
    
    # Pad to same length
    max_len = max([len(v) for v in df_data.values()] + [1])
    for key in df_data:
        while len(df_data[key]) < max_len:
            df_data[key].append(np.nan)
    
    df = pd.DataFrame(df_data)
    
    pdf_buffer = _generate_pdf_report(report, df)
    
    filename = f"water_quality_report_{report_id[:8]}_{datetime.utcnow().strftime('%Y%m%d')}.pdf"
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@app.get("/api/reports/latest/pdf")
async def download_latest_report_pdf(
    current_user: models.User = Depends(get_current_user),
):
    """Generate and download a PDF report for the latest analysis."""
    if not REPORT_HISTORY:
        raise HTTPException(status_code=404, detail="No reports available")
    return await download_report_pdf(REPORT_HISTORY[0]['id'], current_user)
