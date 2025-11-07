# Modern Dashboard Upgrade Script (PowerShell)
Write-Host "==== Modern Dashboard Upgrade Script ====" -ForegroundColor Cyan
$ROOT = Get-Location
Write-Host "Project root: $ROOT" -ForegroundColor Green

function Backup-File {
    param($FilePath)
    if (Test-Path $FilePath) {
        $BackupPath = "$FilePath.bak"
        Copy-Item $FilePath $BackupPath
        Write-Host "Backed up $FilePath -> $BackupPath" -ForegroundColor Yellow
    }
}

# 1) Create backend folder and files
Write-Host "`nCreating backend files..." -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path "backend" | Out-Null

# Create requirements.txt
@"
fastapi
uvicorn[standard]
pandas
python-multipart
numpy
aiofiles
python-dotenv
openpyxl
"@ | Out-File -FilePath "backend\requirements.txt" -Encoding UTF8

# Create app.py
@"
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
import numpy as np
from typing import List, Dict
from pydantic import BaseModel
import datetime

app = FastAPI(title="WQ Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Default thresholds (can be expanded or loaded from config)
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
    Accepts CSV file (or TSV) with at least a timestamp column and parameter columns.
    Expected columns:
      - timestamp (name: timestamp, time, date, DateTime or similar)
      - parameter columns (pH, Turbidity, DO, etc.)
    Returns JSON with time-series per parameter and simple alerts.
    """
    contents = await file.read()
    try:
        # try to infer CSV
        df = pd.read_csv(io.BytesIO(contents))
    except Exception:
        try:
            df = pd.read_excel(io.BytesIO(contents))
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Could not parse uploaded file: {exc}")

    # find timestamp column
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
        # leave as-is; if conversion fails, create synthetic sequential times
        df[tcol] = pd.date_range(end=pd.Timestamp.now(), periods=len(df))

    df = df.sort_values(by=tcol).reset_index(drop=True)

    # choose numeric columns as parameters excluding timestamp
    numeric_cols = [c for c in df.columns if c!=tcol and pd.api.types.is_numeric_dtype(df[c])]

    results = []
    alerts = []

    for param in numeric_cols:
        vals = df[param].fillna(method='ffill').fillna(0).astype(float).tolist()
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
    return {"status":"ok","time": datetime.datetime.utcnow().isoformat()}
"@ | Out-File -FilePath "backend\app.py" -Encoding UTF8

Write-Host "Backend created at backend\ (requirements.txt + app.py)" -ForegroundColor Green

# 2) Update frontend files
Write-Host "`nUpdating frontend files..." -ForegroundColor Cyan

# Backup files
Backup-File "src\App.tsx"
Backup-File "src\main.tsx"
Backup-File "src\index.css"
Backup-File "index.html"
Backup-File "package.json"
Backup-File "src\App.css"

# Create new App.tsx
$AppTsx = @'
import React, { useState, useRef } from "react";
import axios from 'axios';
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

      const res = await axios.post('http://localhost:8000/analyze', form, {
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
                ...(s.threshold && s.threshold.max ? [{
                  label: `${s.parameter} - max threshold`,
                  data: s.timestamps.map(() => ({ x: s.timestamps[0], y: s.threshold.max })),
                  borderDash: [6,6],
                  borderColor: 'rgba(239, 68, 68, 0.7)',
                  backgroundColor: 'transparent',
                  pointRadius: 0,
                  fill: false,
                }] : []),
                ...(s.threshold && s.threshold.min ? [{
                  label: `${s.parameter} - min threshold`,
                  data: s.timestamps.map(() => ({ x: s.timestamps[0], y: s.threshold.min })),
                  borderDash: [6,6],
                  borderColor: 'rgba(34, 197, 94, 0.7)',
                  backgroundColor: 'transparent',
                  pointRadius: 0,
                  fill: false,
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
'@
$AppTsx | Out-File -FilePath "src\App.tsx" -Encoding UTF8

# Create new index.css
@"
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
"@ | Out-File -FilePath "src\index.css" -Encoding UTF8

# Create new main.tsx
@"
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
"@ | Out-File -FilePath "src\main.tsx" -Encoding UTF8

# Create api.ts service
New-Item -ItemType Directory -Force -Path "src\services" | Out-Null
@"
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 60000,
});

export default api;
"@ | Out-File -FilePath "src\services\api.ts" -Encoding UTF8

# Update index.html
@"
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <link rel="icon" href="/vite.svg" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>WQAM Dashboard</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
"@ | Out-File -FilePath "index.html" -Encoding UTF8

Write-Host "index.html updated." -ForegroundColor Green

# Print final instructions
Write-Host "`n==== DONE. Files created/updated. Backups: *.bak in case of problems. ====" -ForegroundColor Green
Write-Host "`nNext steps (run these in separate terminals):" -ForegroundColor Cyan
Write-Host "`n1) Frontend:" -ForegroundColor Yellow
Write-Host "   cd $ROOT" -ForegroundColor White
Write-Host "   npm install axios chart.js react-chartjs-2 chartjs-adapter-date-fns date-fns" -ForegroundColor White
Write-Host "   npm run dev" -ForegroundColor White
Write-Host "`n2) Backend:" -ForegroundColor Yellow
Write-Host "   # First, install Python if not installed:" -ForegroundColor White
Write-Host "   # Download from: https://www.python.org/downloads/" -ForegroundColor White
Write-Host "   # OR use: winget install Python.Python.3.11" -ForegroundColor White
Write-Host "   cd $ROOT\backend" -ForegroundColor White
Write-Host "   python -m venv .venv" -ForegroundColor White
Write-Host "   .venv\Scripts\activate" -ForegroundColor White
Write-Host "   pip install -r requirements.txt" -ForegroundColor White
Write-Host "   uvicorn app:app --reload --port 8000" -ForegroundColor White
Write-Host "`nOpen your Vite dev server (frontend) and backend on port 8000." -ForegroundColor Cyan
Write-Host "The frontend posts to http://localhost:8000/analyze" -ForegroundColor Cyan
Write-Host "`n==== Upgrade script finished ====" -ForegroundColor Green
