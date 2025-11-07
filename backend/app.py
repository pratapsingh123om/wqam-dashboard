from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
import numpy as np
from typing import List, Dict
from pydantic import BaseModel
import datetime

app = FastAPI(title="WQ Dashboard API")

# CORS middleware - permissive for dev (use specific origins in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Default thresholds (can be expanded or loaded from config/env)
# To customize thresholds, modify this dict or load from a config file
DEFAULT_THRESHOLDS = {
    "pH": {"min": 6.5, "max": 8.5},
    "Turbidity": {"max": 5.0},
    "DO": {"min": 5.0},
    "TDS": {"max": 500.0},
    "Iron": {"max": 0.3},
    # add more as needed
}

class AnalysisResult(BaseModel):
    parameter: str
    timestamps: List[str]
    values: List[float]
    exceeded: bool
    threshold: Dict

@app.post("/analyze")
async def analyze_csv(file: UploadFile = File(...)):
    """
    Accepts CSV/XLSX file with at least a timestamp column and parameter columns.
    Expected columns:
      - timestamp (name: timestamp, time, date, DateTime or similar)
      - parameter columns (pH, Turbidity, DO, etc.)
    Returns JSON with time-series per parameter and simple alerts.
    Stateless - no data is persisted to database.
    """
    contents = await file.read()
    try:
        # try to infer CSV first
        df = pd.read_csv(io.BytesIO(contents))
    except Exception:
        try:
            # fallback to Excel
            df = pd.read_excel(io.BytesIO(contents))
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Could not parse uploaded file: {exc}")

    # find timestamp column (case-insensitive search)
    time_cols = [c for c in df.columns if c.lower() in ("timestamp","time","date","datetime","date/time")]
    if time_cols:
        tcol = time_cols[0]
    else:
        # try first column if it looks like dates
        tcol = df.columns[0]

    # coerce to datetime
    try:
        df[tcol] = pd.to_datetime(df[tcol])
    except Exception:
        # if conversion fails, create synthetic sequential times
        df[tcol] = pd.date_range(end=pd.Timestamp.now(), periods=len(df))

    # sort by time
    df = df.sort_values(by=tcol).reset_index(drop=True)

    # choose numeric columns as parameters (excluding timestamp)
    numeric_cols = [c for c in df.columns if c!=tcol and pd.api.types.is_numeric_dtype(df[c])]

    results = []
    alerts = []

    for param in numeric_cols:
        # Forward fill missing values, then fill remaining NaN with 0
        # Note: fillna(method='ffill') is deprecated in newer pandas, use ffill() instead
        vals = df[param].ffill().fillna(0).astype(float).tolist()
        times = df[tcol].dt.strftime("%Y-%m-%d %H:%M:%S").tolist()
        thr = DEFAULT_THRESHOLDS.get(param, {})
        exceeded = False

        # simple threshold checks
        if 'max' in thr and any(v > thr['max'] for v in vals):
            exceeded = True
        if 'min' in thr and any(v < thr['min'] for v in vals):
            exceeded = True

        if exceeded:
            alerts.append({"parameter": param, "threshold": thr})

        results.append({
            "parameter": param,
            "timestamps": times,
            "values": vals,
            "exceeded": exceeded,
            "threshold": thr
        })

    summary = {
        "parameters": results,
        "alerts": alerts,
        "n_rows": len(df),
        "time_column": tcol
    }
    return summary

@app.get("/health")
def health():
    """Health check endpoint"""
    return {"status":"ok","time": datetime.datetime.utcnow().isoformat()}
