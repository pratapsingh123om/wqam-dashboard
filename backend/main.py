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
from sklearn.linear_model import LinearRegression

ML_DIR = Path(__file__).resolve().parent.parent / "ml"
MODEL_PATH = ML_DIR / "model" / "water_model.pkl"

# Color palette for reports (from generate_report.py)
REPORT_PALETTE = ["#2b83ba", "#abdda4", "#fdae61", "#d7191c", "#984ea3", "#4daf4a"]

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


def _extract_location_from_text(text: str) -> dict:
    """Extract location information from PDF text."""
    location_info = {
        "state": None,
        "location": None,
        "latitude": None,
        "longitude": None,
    }
    
    # Common Indian states
    indian_states = [
        "andhra pradesh", "arunachal pradesh", "assam", "bihar", "chhattisgarh",
        "goa", "gujarat", "haryana", "himachal pradesh", "jharkhand", "karnataka",
        "kerala", "madhya pradesh", "maharashtra", "manipur", "meghalaya", "mizoram",
        "nagaland", "odisha", "punjab", "rajasthan", "sikkim", "tamil nadu",
        "telangana", "tripura", "uttar pradesh", "uttarakhand", "west bengal"
    ]
    
    text_lower = text.lower()
    
    # Try to find state
    for state in indian_states:
        if state in text_lower:
            location_info["state"] = state.title()
            break
    
    # Try to find location names (common patterns)
    location_patterns = [
        r"(?:location|site|station|monitoring point)[\s:]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:drain|canal|river|lake|pond|stp|wtp)",
    ]
    
    for pattern in location_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            location_info["location"] = matches[0] if isinstance(matches[0], str) else matches[0][0]
            break
    
    # Try to find coordinates (lat/long)
    coord_patterns = [
        r"(\d+\.\d+)[°\s]*[NS]?[\s,]+(\d+\.\d+)[°\s]*[EW]?",
        r"lat[itude]*[\s:]+(\d+\.\d+)[\s,]+long[itude]*[\s:]+(\d+\.\d+)",
    ]
    
    for pattern in coord_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            if isinstance(matches[0], tuple) and len(matches[0]) >= 2:
                try:
                    location_info["latitude"] = float(matches[0][0])
                    location_info["longitude"] = float(matches[0][1])
                    break
                except (ValueError, IndexError):
                    continue
    
    # If no coordinates found but we have state, use approximate center
    if location_info["state"] and not location_info["latitude"]:
        # Approximate coordinates for Indian states (simplified)
        state_coords = {
            "Maharashtra": (19.7515, 75.7139),
            "Gujarat": (23.0225, 72.5714),
            "Karnataka": (15.3173, 75.7139),
            "Tamil Nadu": (11.1271, 78.6569),
            "Uttar Pradesh": (26.8467, 80.9462),
            "West Bengal": (22.9868, 87.8550),
        }
        if location_info["state"] in state_coords:
            location_info["latitude"], location_info["longitude"] = state_coords[location_info["state"]]
    
    return location_info


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
            # Map columns to parameters BEFORE coercion (while we still have meaningful names)
            df = _map_columns_to_parameters(df)
            # Coerce to numeric
            df = _coerce_to_numeric(df)
            # Remove empty columns and rows
            df = df.dropna(axis=1, how='all').dropna(axis=0, how='all')
            if not df.empty:
                dfs.append(df)
    
    # Combine all dataframes
    if dfs:
        combined_df = pd.concat(dfs, ignore_index=True, sort=False)
        # Map columns again after combining (in case some were missed)
        combined_df = _map_columns_to_parameters(combined_df)
        # Final numeric coercion
        combined_df = _coerce_to_numeric(combined_df)
        print(f"[DEBUG] Combined DataFrame after mapping: {list(combined_df.columns)}")
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


def _normalize_colname(c: str) -> str:
    """Normalize column name for matching."""
    return re.sub(r'[^0-9a-zA-Z]+', '_', str(c)).strip().lower()

def _map_columns_to_parameters(df: pd.DataFrame) -> pd.DataFrame:
    """Map generic column names to parameter names using ML-style heuristics."""
    df = df.copy()
    mapping = {}
    
    # Parameter keywords (from ML code)
    param_keywords = {
        'bod': ['bod', 'biochemical', 'b.o.d', 'b o d'],
        'cod': ['cod', 'chemical'],
        'do': ['dissolved oxygen', 'd.o.', ' do ', 'do '],
        'ph': ['ph', 'ph '],
        'tds': ['tds', 'total dissolved'],
        'turbidity': ['turbidity', 'ntu'],
        'chlorine': ['chlorine', 'freechlorine', 'cl2', 'free chlorine'],
        'temp': ['temp', 'temperature'],
    }
    
    for col in df.columns:
        col_str = str(col).strip()
        col_lower = col_str.lower()
        col_normalized = _normalize_colname(col_str)
        
        # Try to match to a parameter
        for param, keywords in param_keywords.items():
            for keyword in keywords:
                if keyword in col_lower or keyword in col_normalized:
                    mapping[col] = param
                    print(f"[DEBUG] Mapped column '{col}' -> parameter '{param}'")
                    break
            if col in mapping:
                break
    
    if mapping:
        df = df.rename(columns=mapping)
        print(f"[DEBUG] Mapped {len(mapping)} columns to parameters")
    
    return df

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
    
    # Map columns to parameters BEFORE returning
    df = _map_columns_to_parameters(df)
    
    return df


def _build_report_payload(df: pd.DataFrame, username: str, filename: str | None, pdf_text: str | None = None) -> dict:
    df = _prepare_dataframe(df)
    if df.empty:
        raise HTTPException(status_code=400, detail="Dataset is empty after cleaning.")
    
    print(f"[DEBUG] After column mapping, DataFrame has columns: {list(df.columns)}")

    # Extract location from PDF text if available
    location_info = {}
    if pdf_text:
        location_info = _extract_location_from_text(pdf_text)

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
        print(f"[DEBUG] Added timeseries for {config['label']} with {len(series_points)} points")

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

    # Determine map status based on alerts
    map_status = "good"
    if any(a["severity"] == "critical" for a in alerts):
        map_status = "poor"
    elif any(a["severity"] == "warning" for a in alerts):
        map_status = "warning"
    
    return {
        "id": uuid4().hex,
        "uploaded_by": username,
        "created_at": evaluation_time,
        "source_filename": filename,
        "parameters": parameter_summaries,
        "timeseries": parameter_series,
        "alerts": alerts,
        "recommendations": recommendations,
        "location": location_info if location_info.get("latitude") else None,
        "map_status": map_status,
        "ml_insights": {
            "pollution_prediction": ml_insights.get("pollution_prediction"),
            "pollution_score": ml_insights.get("pollution_score"),
            "pollution_label": ml_insights.get("pollution_label"),
            "forecasts": ml_insights.get("forecasts", {}),
            "model_available": ml_insights.get("model_available", False),
        },
    }
@app.post("/api/auth/register", response_model=schemas.UserOut, status_code=201)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    exists = db.query(models.User).filter(models.User.username == user_in.username).first()
    if exists:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Enforce valid roles for self-registration
    valid_roles = ["validator", "user", "business", "plant"]
    if user_in.role and user_in.role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role '{user_in.role}'. Allowed roles: {', '.join(valid_roles)}")
    
    user = models.User(
        username=user_in.username,
        hashed_password=hash_password(user_in.password),
        role=user_in.role or "user" # Role from input or default to "user"
        # is_active will default to False from models.py
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
    if not user.is_active: # New check
        raise HTTPException(status_code=403, detail="Account is not active. Please contact administrator for approval.")
    access_token = create_access_token({"sub": user.username, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer", "role": user.role}

@app.get("/api/auth/me", response_model=schemas.UserOut)
def me(current_user: models.User = Depends(get_current_user)):
    return current_user


# Admin-specific dependency
def get_admin_user(current_user: models.User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can access this resource")
    return current_user

@app.get("/api/admin/pending-users", response_model=list[schemas.UserOut])
def get_pending_users(db: Session = Depends(get_db), admin_user: models.User = Depends(get_admin_user)):
    pending_users = db.query(models.User).filter(models.User.is_active == False).all()
    return pending_users

@app.post("/api/admin/approve-user/{user_id}", response_model=schemas.UserOut)
def approve_user(user_id: int, db: Session = Depends(get_db), admin_user: models.User = Depends(get_admin_user)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_active:
        raise HTTPException(status_code=400, detail="User is already active")
    
    user.is_active = True
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


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
        
        # Extract text from PDF for location extraction
        pdf_text = None
        if file.filename and file.filename.lower().endswith('.pdf'):
            pdf_text = _extract_text_from_pdf(contents)
        
        report = _build_report_payload(df, current_user.username, file.filename, pdf_text)
        REPORT_HISTORY.appendleft(report)
        print(f"[DEBUG] Report created with ID: {report['id']}")
        print(f"[DEBUG] Report has {len(report.get('timeseries', []))} timeseries entries")
        print(f"[DEBUG] Report has {len(report.get('parameters', []))} parameters")
        print(f"[DEBUG] REPORT_HISTORY now has {len(REPORT_HISTORY)} reports")
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


def _simple_forecast(series: pd.Series, steps: int = 3) -> np.ndarray | None:
    """Linear forecast using sklearn LinearRegression on index -> value (from generate_report.py)."""
    s = series.dropna().reset_index(drop=True)
    if s.size < 3:
        return None
    X = np.arange(len(s)).reshape(-1, 1)
    y = s.values.reshape(-1, 1)
    model = LinearRegression().fit(X, y)
    xf = np.arange(len(s), len(s) + steps).reshape(-1, 1)
    yf = model.predict(xf).ravel()
    return yf

def _map_parameter_label_to_key(label: str) -> str:
    """Map parameter label (e.g., 'Dissolved Oxygen') to key (e.g., 'do')."""
    label_lower = label.lower()
    mapping = {
        'ph': 'ph',
        'dissolved oxygen': 'do',
        'bod': 'bod',
        'b.o.d': 'bod',
        'biochemical oxygen demand': 'bod',
        'cod': 'cod',
        'chemical oxygen demand': 'cod',
        'tds': 'tds',
        'total dissolved solids': 'tds',
        'turbidity': 'turbidity',
        'free chlorine': 'chlorine',
        'chlorine': 'chlorine',
        'temperature': 'temp',
        'temp': 'temp',
    }
    for key, value in mapping.items():
        if key in label_lower:
            return value
    # Fallback: try to extract from label
    if 'dissolved' in label_lower and 'oxygen' in label_lower:
        return 'do'
    if 'bod' in label_lower or 'biochemical' in label_lower:
        return 'bod'
    if 'cod' in label_lower or 'chemical' in label_lower:
        return 'cod'
    if 'ph' in label_lower:
        return 'ph'
    if 'tds' in label_lower or 'total dissolved' in label_lower:
        return 'tds'
    return label_lower.replace(' ', '_')[:10]  # Fallback

def _generate_pdf_report(report: dict, df: pd.DataFrame) -> io.BytesIO:
    """Generate a comprehensive PDF report using generate_report.py style (enhanced version)."""
    buffer = io.BytesIO()
    colors = REPORT_PALETTE
    
    # Build parameter data from timeseries (primary source) and DataFrame (fallback)
    param_data = {}  # key -> list of values
    param_info = {}  # key -> {label, unit, stats}
    
    # Extract from timeseries (most reliable)
    for series in report.get('timeseries', []):
        param_label = series.get('parameter', '')
        param_key = _map_parameter_label_to_key(param_label)
        values = [p.get('value', 0) for p in series.get('points', []) if p.get('value') is not None]
        if values:
            param_data[param_key] = values
            param_info[param_key] = {
                'label': param_label,
                'unit': next((p.get('unit', '') for p in report.get('parameters', []) if p.get('parameter') == param_label), ''),
            }
    
    # Fallback: extract from DataFrame columns
    for col in df.columns:
        col_str = str(col).lower()
        param_key = _map_parameter_label_to_key(col_str)
        if param_key not in param_data:
            series = pd.to_numeric(df[col], errors='coerce').dropna()
            if series.size > 0:
                param_data[param_key] = series.tolist()
                param_info[param_key] = {'label': str(col), 'unit': ''}
    
    # Also get from parameter summaries for metadata
    for param_summary in report.get('parameters', []):
        param_label = param_summary.get('parameter', '')
        param_key = _map_parameter_label_to_key(param_label)
        if param_key not in param_info:
            param_info[param_key] = {
                'label': param_label,
                'unit': param_summary.get('unit', ''),
            }
        elif not param_info[param_key].get('unit'):
            param_info[param_key]['unit'] = param_summary.get('unit', '')
    
    print(f"[DEBUG] PDF generation: Found {len(param_data)} parameters with data: {list(param_data.keys())}")
    
    with PdfPages(buffer) as pdf:
        # Title page (NWMP style from generate_report.py)
        fig, ax = plt.subplots(figsize=(8.27, 11.69))
        ax.axis('off')
        ax.text(0.5, 0.92, "NWMP — Auto-generated Visual Report", ha='center', fontsize=20, weight='bold')
        ax.text(0.5, 0.88, f"Source: {report.get('source_filename', 'Unknown')}", ha='center', fontsize=10)
        ax.text(0.5, 0.85, f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", ha='center', fontsize=9)
        ax.text(0.5, 0.82, f"Analyzed by: {report.get('uploaded_by', 'Unknown')}", ha='center', fontsize=9)
        
        # Parameter summary statistics (generate_report.py style)
        y = 0.75
        for param_key in ['bod', 'cod', 'do', 'ph', 'tds', 'turbidity', 'chlorine', 'temp']:
            if param_key in param_data:
                values = param_data[param_key]
                s = pd.Series(values)
                s = pd.to_numeric(s, errors='coerce').dropna()
                if s.size > 0:
                    param_label = param_info.get(param_key, {}).get('label', param_key.upper())
                    unit = param_info.get(param_key, {}).get('unit', '')
                    ax.text(0.02, y, f"{param_key.upper():<12} n={s.size:<5} mean={s.mean():.2f}  median={s.median():.2f}  min={s.min():.2f}  max={s.max():.2f} {unit}", fontsize=10)
                else:
                    ax.text(0.02, y, f"{param_key.upper():<12} no data", fontsize=10)
            else:
                ax.text(0.02, y, f"{param_key.upper():<12} not found", fontsize=10)
            y -= 0.035
        
        # ML Insights if available
        if report.get('ml_insights', {}).get('model_available'):
            y -= 0.05
            ax.text(0.02, y, "ML Predictions:", fontsize=12, weight='bold')
            y -= 0.035
            ml = report['ml_insights']
            if ml.get('pollution_score') is not None:
                ax.text(0.02, y, f"Pollution Score: {ml['pollution_score']:.1f} ({ml.get('pollution_label', 'N/A')})", fontsize=10)
                y -= 0.035
            if ml.get('pollution_prediction') is not None:
                ax.text(0.02, y, f"Predicted Pollution Level: {ml['pollution_prediction']:.2f}", fontsize=10)
                y -= 0.035
        
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
        
        # Per-parameter histograms (generate_report.py style)
        for i, param_key in enumerate(['bod', 'cod', 'do', 'ph', 'tds', 'turbidity', 'chlorine', 'temp']):
            if param_key not in param_data:
                continue
            
            values = param_data[param_key]
            s = pd.Series(values)
            s = pd.to_numeric(s, errors='coerce').dropna()
            if s.size == 0:
                continue
            
            param_label = param_info.get(param_key, {}).get('label', param_key.upper())
            fig, ax = plt.subplots(figsize=(8.27, 5.5))
            ax.hist(s.values, bins=min(25, max(10, s.size // 5)), color=colors[i % len(colors)], edgecolor='k', alpha=0.9)
            ax.set_title(f"{param_label} distribution — n={s.size}", fontsize=14)
            ax.set_xlabel(f"{param_label} ({param_info.get(param_key, {}).get('unit', '')})")
            ax.set_ylabel("count")
            ax.grid(True, alpha=0.25)
            ax.text(0.98, 0.95, f"mean={s.mean():.2f}\nmedian={s.median():.2f}\nmin={s.min():.2f}\nmax={s.max():.2f}", 
                   transform=ax.transAxes, ha='right', va='top', bbox=dict(alpha=0.1))
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)
        
        # Pairwise scatter plots (generate_report.py style)
        numeric_params = [p for p in ['bod', 'cod', 'do', 'ph', 'tds', 'turbidity', 'chlorine', 'temp'] 
                          if p in param_data and len(param_data[p]) >= 10]
        
        for i in range(len(numeric_params)):
            for j in range(i+1, len(numeric_params)):
                a = numeric_params[i]
                b = numeric_params[j]
                values_a = param_data[a]
                values_b = param_data[b]
                # Align lengths
                min_len = min(len(values_a), len(values_b))
                if min_len < 8:
                    continue
                values_a = values_a[:min_len]
                values_b = values_b[:min_len]
                # Create DataFrame for scatter
                scatter_df = pd.DataFrame({a: values_a, b: values_b})
                scatter_df = scatter_df.apply(pd.to_numeric, errors='coerce').dropna()
                if scatter_df.shape[0] < 8:
                    continue
                fig, ax = plt.subplots(figsize=(8.27, 5.5))
                ax.scatter(scatter_df[a], scatter_df[b], c=colors[(i+j) % len(colors)], alpha=0.8)
                ax.set_xlabel(a.upper())
                ax.set_ylabel(b.upper())
                ax.set_title(f"{a.upper()} vs {b.upper()} (n={scatter_df.shape[0]})")
                ax.grid(True, alpha=0.25)
                pdf.savefig(fig, bbox_inches='tight')
                plt.close(fig)
        
        # Timeseries plots with forecasts (generate_report.py style)
        for series in report.get('timeseries', []):
            if len(series['points']) < 3:
                continue
            
            points = series['points']
            timestamps = [p['timestamp'] for p in points]
            values = [p['value'] for p in points]
            
            # Convert timestamps to datetime if needed
            try:
                timestamps_dt = [pd.to_datetime(ts) for ts in timestamps]
            except:
                timestamps_dt = list(range(len(timestamps)))
            
            fig, ax = plt.subplots(figsize=(8.27, 5.5))
            ax.plot(timestamps_dt, values, marker='o', linewidth=2, label='observed')
            ax.set_title(f"Timeseries: {series['parameter']}", fontsize=14)
            ax.set_xlabel("Time")
            ax.set_ylabel(series['parameter'])
            ax.grid(True, alpha=0.25)
            
            # Add forecast if enough data
            if len(values) >= 3:
                try:
                    s = pd.Series(values)
                    yf = _simple_forecast(s, steps=3)
                    if yf is not None:
                        forecast_times = list(range(len(values), len(values) + len(yf)))
                        ax.plot(forecast_times, yf, linestyle='--', marker='x', label='forecast', color='red')
                        ax.legend()
                except:
                    pass
            
            plt.xticks(rotation=45, ha='right')
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)
        
        # Conclusions & prioritized actions (generate_report.py style)
        summary_text = []
        if 'bod' in param_data:
            bod_values = param_data['bod']
            bod_series = pd.Series(bod_values)
            bod_series = pd.to_numeric(bod_series, errors='coerce').dropna()
            if bod_series.size > 0 and bod_series.mean() > 3:
                summary_text.append("Elevated BOD (organic load) — prioritize biological treatment upgrades and aeration.")
        
        if 'do' in param_data:
            do_values = param_data['do']
            do_series = pd.Series(do_values)
            do_series = pd.to_numeric(do_series, errors='coerce').dropna()
            if do_series.size > 0 and do_series.mean() < 5:
                summary_text.append("Low DO — increase aeration and reduce upstream organic discharges.")
        
        if 'cod' in param_data:
            cod_values = param_data['cod']
            cod_series = pd.Series(cod_values)
            cod_series = pd.to_numeric(cod_series, errors='coerce').dropna()
            if cod_series.size > 0 and cod_series.mean() > 50:
                summary_text.append("High COD — investigate industrial effluents; consider AOP for hard-to-destroy organics.")
        
        # Add recommendations from report
        for rec in report.get('recommendations', []):
            if rec not in summary_text:
                summary_text.append(rec)
        
        if not summary_text:
            summary_text.append("No immediate red flags detected by automated heuristics; inspect raw tables or provide Excel/CSV for best results.")
        
        fig, ax = plt.subplots(figsize=(8.27, 5.5))
        ax.axis('off')
        ax.text(0.02, 0.92, "Conclusions & Prioritized Actions", fontsize=16, weight='bold')
        for i, line in enumerate(summary_text):
            ax.text(0.02, 0.85 - i*0.07, f"- {line}", fontsize=11)
        ax.text(0.02, 0.35, "Next steps:", fontsize=12, weight='bold')
        nexts = [
            "1) Provide native Excel/CSV exports if possible (best data quality).",
            "2) Upload all year PDFs for trend analysis & forecasting.",
            "3) For identified hotspots, run grab sample chemical analysis and upstream sampling."
        ]
        for i, n in enumerate(nexts):
            ax.text(0.02, 0.30 - i*0.05, n, fontsize=10)
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
    print(f"[DEBUG] PDF request - REPORT_HISTORY length: {len(REPORT_HISTORY)}")
    print(f"[DEBUG] REPORT_HISTORY contents: {[r.get('id', 'no-id') for r in list(REPORT_HISTORY)]}")
    
    if not REPORT_HISTORY or len(REPORT_HISTORY) == 0:
        print("[ERROR] REPORT_HISTORY is empty")
        raise HTTPException(status_code=404, detail="No reports available")
    
    report = REPORT_HISTORY[0]
    if not report:
        print("[ERROR] First report in HISTORY is None")
        raise HTTPException(status_code=404, detail="No reports available")
    
    print(f"[DEBUG] Generating PDF for report ID: {report.get('id', 'unknown')}")
    print(f"[DEBUG] Report has {len(report.get('timeseries', []))} timeseries")
    print(f"[DEBUG] Report timeseries: {[s.get('parameter', 'unknown') for s in report.get('timeseries', [])]}")
    
    # Reconstruct dataframe from report - use parameters if timeseries is empty
    df_data = {}
    
    # First try timeseries
    for series in report.get('timeseries', []):
        param = series.get('parameter', 'unknown')
        if param not in df_data:
            df_data[param] = []
        for point in series.get('points', []):
            val = point.get('value', 0)
            if val is not None and not (isinstance(val, float) and np.isnan(val)):
                df_data[param].append(val)
    
    # Fallback: use parameter summaries if timeseries is empty
    if not df_data:
        print("[DEBUG] No timeseries data, using parameter summaries")
        for param_summary in report.get('parameters', []):
            param_name = param_summary.get('parameter', '').lower()
            # Map common parameter names
            param_map = {
                'ph': 'ph',
                'dissolved oxygen': 'do',
                'bod': 'bod',
                'cod': 'cod',
                'tds': 'tds',
                'turbidity': 'turbidity',
                'free chlorine': 'chlorine',
            }
            mapped_param = param_map.get(param_name, param_name)
            if mapped_param not in df_data:
                # Create synthetic data from average
                avg = param_summary.get('average', 0)
                df_data[mapped_param] = [avg] * 10  # Create 10 data points
    
    # Pad to same length
    if df_data:
        max_len = max([len(v) for v in df_data.values()] + [1])
        for key in df_data:
            while len(df_data[key]) < max_len:
                df_data[key].append(df_data[key][-1] if df_data[key] else 0)  # Repeat last value instead of NaN
        df = pd.DataFrame(df_data)
        print(f"[DEBUG] Reconstructed DataFrame with shape: {df.shape}, columns: {list(df.columns)}")
    else:
        # Create minimal dataframe if no data
        print("[WARN] No data available for PDF generation, creating empty DataFrame")
        df = pd.DataFrame({'ph': [7.0], 'do': [6.0]})  # Dummy data
    
    try:
        pdf_buffer = _generate_pdf_report(report, df)
        filename = f"water_quality_report_{report.get('id', 'unknown')[:8]}_{datetime.utcnow().strftime('%Y%m%d')}.pdf"
        print(f"[DEBUG] PDF generated successfully")
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        print(f"[ERROR] Failed to generate PDF: {e}", exc_info=True)
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")
