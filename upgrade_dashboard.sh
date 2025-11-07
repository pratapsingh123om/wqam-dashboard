#!/usr/bin/env bash

set -euo pipefail

echo "==== Modern Dashboard Upgrade Script ===="
ROOT="$(pwd)"
echo "Project root: $ROOT"

backup_file() {
  f="$1"
  if [ -f "$f" ]; then
    cp "$f" "${f}.bak"
    echo "Backed up $f -> ${f}.bak"
  fi
}

# 1) Create backend folder and files
mkdir -p backend
echo "Creating backend files..."

cat > backend/requirements.txt <<'PYREQ'
fastapi
uvicorn[standard]
pandas
python-multipart
numpy
aiofiles
python-dotenv
openpyxl
PYREQ

cat > backend/app.py <<'PYAPP'
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
PYAPP

echo "Backend created at backend/ (requirements.txt + app.py)"

# 2) Update frontend files (React + Tailwind)
echo "Updating frontend files..."

# Backup files
backup_file src/App.tsx
backup_file src/main.tsx
backup_file src/index.css
backup_file index.html
backup_file package.json
backup_file src/App.css

# Overwrite App.tsx
cat > src/App.tsx <<'REACT'
import React, { useState, useRef } from "react";
import api from './services/api';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  LineElement,
  CategoryScale,
  LinearScale,
  PointElement,
  Tooltip,
  Legend,
  TimeScale
} from 'chart.js';
import 'chartjs-adapter-date-fns';
import { Droplet, Upload, AlertTriangle, CheckCircle } from 'lucide-react';

ChartJS.register(
  LineElement,
  CategoryScale,
  LinearScale,
  PointElement,
  Tooltip,
  Legend,
  TimeScale
);

type ParamSeries = {
  parameter: string;
  timestamps: string[];
  values: number[];
  exceeded: boolean;
  threshold: any;
}

function Logo() {
  return (
    <div className="flex items-center space-x-3 px-6 py-4">
      <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white font-bold text-xl shadow-lg">
        <Droplet size={28} />
      </div>
      <div>
        <div className="text-white text-xl font-bold">WQAM</div>
        <div className="text-white/80 text-xs">Water Quality Monitor</div>
      </div>
    </div>
  )
}

function App() {
  const [uploading, setUploading] = useState(false);
  const [series, setSeries] = useState<ParamSeries[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const fileRef = useRef<HTMLInputElement | null>(null);

  async function handleUpload(e: React.FormEvent) {
    e.preventDefault();
    const f = fileRef.current?.files?.[0];
    if (!f) return alert("Pick a CSV/XLSX file first");

    setUploading(true);
    try {
      const form = new FormData();
      form.append('file', f);

      const res = await api.post('/analyze', form, {
        headers: {"Content-Type": "multipart/form-data"}
      });

      setSeries(res.data.parameters || []);
      setAlerts(res.data.alerts || []);
    } catch (err: any) {
      console.error(err);
      alert(`Upload failed: ${err.message || 'See console'}`);
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 text-slate-100">
      <nav className="flex items-center justify-between px-6 py-4 border-b border-slate-800/50 bg-slate-900/50 backdrop-blur-sm">
        <Logo />
        <div className="flex items-center space-x-3">
          <label className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 px-4 py-2 rounded-lg cursor-pointer transition-all shadow-lg hover:shadow-xl flex items-center gap-2">
            <Upload size={18} />
            <input ref={fileRef} type="file" accept=".csv, .xlsx, .xls" className="hidden" onChange={() => {}} />
            Upload Data
          </label>
          <button 
            onClick={handleUpload} 
            disabled={uploading} 
            className="bg-gradient-to-r from-indigo-500 to-purple-500 hover:from-indigo-600 hover:to-purple-600 px-6 py-2 rounded-lg font-semibold transition-all shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {uploading ? "Analyzing..." : "Analyze"}
          </button>
        </div>
      </nav>

      <main className="p-6">
        {alerts.length > 0 && (
          <div className="mb-6">
            <div className="bg-gradient-to-r from-red-600 to-red-700 text-white px-6 py-4 rounded-xl shadow-xl border-l-4 border-red-400">
              <div className="flex items-center gap-3">
                <AlertTriangle size={24} />
                <div>
                  <strong className="text-lg">Alerts:</strong> {alerts.map(a => a.parameter).join(", ")} - thresholds exceeded.
                </div>
              </div>
            </div>
          </div>
        )}

        {series.length === 0 && (
          <div className="flex flex-col items-center justify-center h-96 text-center">
            <Droplet size={64} className="text-purple-400 mb-4" />
            <h2 className="text-2xl font-bold mb-2">Welcome to WQAM Dashboard</h2>
            <p className="text-slate-400 mb-6">Upload a CSV or Excel file to analyze water quality data</p>
            <p className="text-sm text-slate-500">Expected columns: timestamp, pH, Turbidity, DO, TDS, Iron, etc.</p>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {series.map((s, idx) => {
            const data = {
              labels: s.timestamps,
              datasets: [
                {
                  label: s.parameter,
                  data: s.values.map((v, i) => ({ x: s.timestamps[i], y: v })),
                  borderColor: s.exceeded ? 'rgb(239, 68, 68)' : 'rgb(99, 102, 241)',
                  backgroundColor: s.exceeded ? 'rgba(239, 68, 68, 0.1)' : 'rgba(99, 102, 241, 0.1)',
                  tension: 0.3,
                  fill: true,
                  pointRadius: 2,
                  pointHoverRadius: 5
                },
                // threshold flat line if provided (max threshold)
                ...(s.threshold && s.threshold.max ? [{
                  label: `${s.parameter} - max threshold`,
                  data: s.timestamps.map((ts) => ({ x: ts, y: s.threshold.max })),
                  borderDash: [6, 6],
                  borderColor: 'rgba(239, 68, 68, 0.7)',
                  backgroundColor: 'transparent',
                  pointRadius: 0,
                  fill: false,
                  tension: 0,
                }] : []),
                // threshold flat line if provided (min threshold)
                ...(s.threshold && s.threshold.min ? [{
                  label: `${s.parameter} - min threshold`,
                  data: s.timestamps.map((ts) => ({ x: ts, y: s.threshold.min })),
                  borderDash: [6, 6],
                  borderColor: 'rgba(34, 197, 94, 0.7)',
                  backgroundColor: 'transparent',
                  pointRadius: 0,
                  fill: false,
                  tension: 0,
                }] : [])
              ]
            };

            const options:any = {
              responsive: true,
              maintainAspectRatio: false,
              plugins: { 
                legend: { display: true, position: 'top' as const },
                tooltip: {
                  mode: 'index' as const,
                  intersect: false,
                }
              },
              scales: {
                x: { 
                  type: 'time' as const,
                  time: { 
                    unit: 'day' as const,
                    displayFormats: {
                      day: 'MMM dd'
                    }
                  }
                },
                y: {
                  beginAtZero: false
                }
              }
            };

            return (
              <div key={idx} className="bg-slate-800/80 backdrop-blur-sm p-6 rounded-xl shadow-xl border border-slate-700/50">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-xl font-bold text-white">{s.parameter}</h3>
                    <p className="text-sm text-slate-400">{s.exceeded ? "Threshold exceeded" : "Within normal range"}</p>
                  </div>
                  <div className={`px-4 py-2 rounded-full text-sm font-semibold flex items-center gap-2 ${
                    s.exceeded ? 'bg-red-600 text-white' : 'bg-green-600 text-white'
                  }`}>
                    {s.exceeded ? <AlertTriangle size={16} /> : <CheckCircle size={16} />}
                    {s.exceeded ? 'Alert' : 'OK'}
                  </div>
                </div>
                <div style={{height: 280}} className="mt-3">
                  <Line data={data} options={options} />
                </div>
              </div>
            )
          })}
        </div>
      </main>

      <footer className="p-4 text-center text-slate-500 text-sm border-t border-slate-800/50 mt-8">
        WQAM — Water Quality Monitoring Dashboard
      </footer>
    </div>
  );
}

export default App;
REACT

# Overwrite src/index.css to ensure Tailwind basics present
cat > src/index.css <<'CSS'
@tailwind base;
@tailwind components;
@tailwind utilities;

html, body, #root {
  height: 100%;
  margin: 0;
  padding: 0;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
CSS

# Ensure main.tsx imports index.css (backup was taken)
cat > src/main.tsx <<'MAIN'
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
MAIN

# Provide a small helper service for axios (optional)
mkdir -p src/services
cat > src/services/api.ts <<'API'
import axios from 'axios';

// Centralized API configuration
// Change baseURL for production deployment
const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 60000,
});

export default api;
API

# 3) Modify index.html to show favicon/logo place
backup_file index.html
cat > index.html <<'HTML'
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <link rel="icon" href="/logo192.png" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>AquaVis Dashboard</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
HTML

echo "index.html updated."

# 4) Print final instructions
echo ""
echo "==== DONE. Files created/updated. Backups: *.bak in case of problems. ===="
echo ""
echo "Next steps (run these in separate terminals):"
echo ""
echo "1) Frontend:"
echo "   cd $ROOT"
echo "   npm install"
echo "   npm run dev"
echo ""
echo "2) Backend:"
echo "   cd $ROOT/backend"
echo "   # Create venv (recommended):"
echo "   python -m venv .venv"
echo "   # Activate venv:"
echo "   # Windows: .venv\\Scripts\\activate"
echo "   # Mac/Linux: source .venv/bin/activate"
echo "   pip install -r requirements.txt"
echo "   uvicorn app:app --reload --port 8000"
echo ""
echo "Open your Vite dev server (frontend) and backend on port 8000."
echo "The frontend posts to http://localhost:8000/analyze"
echo ""
echo "==== Upgrade script finished ===="
