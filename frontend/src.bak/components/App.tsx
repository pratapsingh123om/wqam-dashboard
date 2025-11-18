import ActiveUsersWidget from './components/ActiveUsersWidget';
import AlertsPanel from './components/AlertsPanel';
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
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
  <ActiveUsersWidget />
  <AlertsPanel orgId={1} />
  {/* your existing KPI card or another widget */}
</div>

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
