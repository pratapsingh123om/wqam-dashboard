import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { api, apiFetch } from '../services/api'; // Assuming apiFetch is imported
import type { DashboardData, UploadReport } from '../types/dashboard';
import type { User } from '../types';
import { Chart as ReactChart } from 'react-chartjs-2'; // For React Chart.js component

// Utility components to simplify JSX
const PanelHeader: React.FC<{ title: string; subtitle: string }> = ({ title, subtitle }) => (
  <header>
    <h1>{title}</h1>
    <div className="muted">{subtitle}</div>
  </header>
);

const Button: React.FC<{ children: React.ReactNode; onClick?: () => void; className?: string; type?: "button" | "submit" | "reset" }> = ({ children, onClick, className, type = "button" }) => (
  <button type={type} onClick={onClick} className={`${className || ''}`}>{children}</button>
);

const Input: React.FC<React.InputHTMLAttributes<HTMLInputElement>> = (props) => (
  <input {...props} className="flex-1 px-2 py-1 rounded-md border border-gray-700 bg-gray-900 text-white placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-blue-500" />
);

const Select: React.FC<React.SelectHTMLAttributes<HTMLSelectElement>> = (props) => (
  <select {...props} className="px-2 py-1 rounded-md border border-gray-700 bg-gray-900 text-white focus:outline-none focus:ring-1 focus:ring-blue-500" />
);


interface DashboardProps {
  role: string | null;
  onLogout: () => void;
}

const Dashboard: React.FC<DashboardProps> = ({ role, onLogout }) => {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [reports, setReports] = useState<UploadReport[]>([]);
  const [pendingUsers, setPendingUsers] = useState<User[]>([]);
  const [newUserName, setNewUserName] = useState('');
  const [newUserRole, setNewUserRole] = useState('user');
  const [logMessages, setLogMessages] = useState<string[]>([]);
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [apiBase, setApiBase] = useState('http://localhost:8000/api'); // Default to backend service
  const [lastReport, setLastReport] = useState<UploadReport | null>(null); // To store the last generated report

  const log = useCallback((message: string) => {
    setLogMessages(prev => [`[${new Date().toLocaleTimeString()}] ${message}`, ...prev.slice(0, 49)]);
  }, []);

  // Fetch Dashboard Data and Reports
  const fetchData = useCallback(async () => {
    try {
      const demoData = await apiFetch<DashboardData>('/demo');
      setDashboardData(demoData);
      const fetchedReports = await apiFetch<UploadReport[]>('/reports');
      setReports(fetchedReports);
    } catch (error) {
      log(`Error fetching dashboard data or reports: ${error}`);
    }
  }, [log]);

  // Fetch Pending Users for Admin Panel
  const fetchPendingUsers = useCallback(async () => {
    if (role === 'admin') {
      try {
        const users = await apiFetch<User[]>('/admin/pending-users');
        setPendingUsers(users);
      } catch (error) {
        log(`Error fetching pending users: ${error}`);
      }
    }
  }, [role, log]);

  useEffect(() => {
    fetchData();
    fetchPendingUsers();
  }, [fetchData, fetchPendingUsers]);

  // Admin Actions
  const handleCreateUser = async () => {
    if (!newUserName) {
      alert('Enter username');
      return;
    }
    try {
      await api.post('/auth/register', { username: newUserName, password: 'password', role: newUserRole });
      log(`Created pending user ${newUserName} (${newUserRole})`);
      setNewUserName('');
      fetchPendingUsers(); // Refresh pending user list
    } catch (error) {
      log(`Error creating user: ${error}`);
    }
  };

  const handleApproveUser = async (userId: number) => {
    try {
      await api.post(`/admin/approve-user/${userId}`);
      log(`Approved user ${userId}`);
      fetchPendingUsers(); // Refresh pending user list
    } catch (error) {
      log(`Error approving user ${userId}: ${error}`);
    }
  };

  // Uploads & Model Actions
  const handlePdfUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files) {
      const filesArray = Array.from(event.target.files);
      setUploadedFiles(filesArray);
      log(`Selected ${filesArray.length} file(s)`);
    }
  };

  const handleAnalyze = async () => {
    if (!uploadedFiles.length) {
      alert('Please choose PDFs first (Upload PDFs).');
      return;
    }
    log('Starting analysis...');
    try {
      const formData = new FormData();
      uploadedFiles.forEach(f => formData.append('file', f, f.name));
      const response = await api.post('/uploads/analyze', formData);
      setLastReport(response.data);
      setReports(prev => [response.data, ...prev]); // Add to reports list
      log('Analysis completed.');
      alert('Analysis completed (report saved in Reports panel).');
    } catch (error) {
      log(`Error during analysis: ${error}`);
      alert(`Error: ${error}`);
    }
  };

  const handleGenerateReport = () => {
    if (!lastReport) {
      alert('Run analysis first');
      return;
    }
    // This action would typically trigger a backend process to generate a human-readable report (e.g., PDF/DOCX)
    // For this demo, we'll just acknowledge it.
    log('Report summary generated (mock).');
    alert('Report summary generated and saved to Reports list.');
  };

  const handleDownloadReport = async (reportId: string) => { // Updated to accept reportId
    try {
      const pdfBlob = await apiFetch<Blob>(`/reports/${reportId}/pdf`, { responseType: 'blob' } as RequestInit);
      const url = window.URL.createObjectURL(pdfBlob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `wqam-report-${reportId.substring(0,8)}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      log(`Downloaded report (PDF) for ID: ${reportId}.`);
    } catch (error) {
      log(`Error downloading report ${reportId}: ${error}`);
      alert(`Error: ${error}`);
    }
  };


  // Placeholder for modelPath from gui.html (static for this demo)
  const modelPath = 'file:///C:/Users/gsr33/wqam-dashboard/data/row/model.pkl';

  // Chart data for Industry/Plant Dashboard
  const chartData = useMemo(() => {
    if (!dashboardData?.timeseries || dashboardData.timeseries.length === 0) {
      return { labels: [], datasets: [] };
    }
    const labels = dashboardData.timeseries.map(item => new Date(item.date).toLocaleDateString());
    const dataPoints = dashboardData.timeseries.map(item => item.value);

    return {
      labels,
      datasets: [
        {
          label: 'Water Quality Index',
          data: dataPoints,
          borderColor: 'var(--accent)',
          backgroundColor: 'rgba(124, 58, 237, 0.2)',
          tension: 0.4,
          fill: true,
          pointRadius: 3,
          pointBackgroundColor: 'var(--accent)',
        },
      ],
    };
  }, [dashboardData]);

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: {
          color: 'var(--muted)',
        },
      },
    },
    scales: {
      x: {
        ticks: {
          color: 'var(--muted)',
        },
        grid: {
          color: 'rgba(255, 255, 255, 0.05)',
        },
      },
      y: {
        ticks: {
          color: 'var(--muted)',
        },
        grid: {
          color: 'rgba(255, 255, 255, 0.05)',
        },
      },
    },
  };

  // Validator actions (mock for now)
  const handleApproveReport = () => {
    alert('Report approved (mock).');
    log('Validator approved report (mock).');
  };

  const handleRejectReport = () => {
    alert('Report rejected (mock).');
    log('Validator rejected report (mock).');
  };


  return (
    <div className="app">
      {/* Admin column */}
      <div className="col">
        {['admin'].includes(role || '') && (
          <div className="panel admin">
            <PanelHeader title="Admin Control Panel" subtitle="Approve users, manage validators" />

            <div className="controls">
              <Button className="btn-primary">Scan Repo (mock)</Button>
              <Button onClick={fetchPendingUsers}>Refresh Users</Button> {/* Added onClick for Refresh Users */}
              <Button onClick={onLogout}>Logout</Button> {/* Added Logout button */}
            </div>

            <h3 className="mt-3 text-lg font-semibold">Pending approvals</h3>
            <div className="user-list">
              {pendingUsers.length === 0 ? (
                <div className="small muted">No users pending approval.</div>
              ) : (
                pendingUsers.map(user => (
                  <div key={user.id} className="user-card">
                    <div>
                      <div className="font-bold">{user.username}</div>
                      <div className="small muted">{user.role}</div>
                    </div>
                    <div className="flex-row">
                      <Button className="btn-primary small" onClick={() => handleApproveUser(user.id)}>Approve</Button>
                    </div>
                  </div>
                ))
              )}
            </div>

            <h3 className="mt-3 text-lg font-semibold">Create user</h3>
            <div className="flex-row">
              <Input
                id="newUserName"
                placeholder="Name"
                value={newUserName}
                onChange={(e) => setNewUserName(e.target.value)}
              />
              <Select id="newUserRole" value={newUserRole} onChange={(e) => setNewUserRole(e.target.value)}>
                <option value="user">User</option>
                <option value="validator">Validator</option>
                <option value="business">Business</option>
                <option value="admin">Admin</option>
              </Select>
              <Button onClick={handleCreateUser}>Create</Button>
            </div>
          </div>
        )}

        {/* Uploads & Model Panel */}
        <div className="panel">
          <PanelHeader title="Uploads & Model" subtitle="Upload PDFs, analyze, download reports" />

          <div className="file-row">
            <label htmlFor="pdfUpload" className="btn-primary" style={{ cursor: 'pointer' }}>Upload PDFs</label>
            <Input id="pdfUpload" type="file" accept="application/pdf" multiple onChange={handlePdfUpload} />
            <div className="muted small">{uploadedFiles.length ? uploadedFiles.map(f => f.name).join(', ') : 'No files chosen'}</div>
          </div>

          <div className="mt-3 controls">
            <Button className="btn-success" onClick={handleAnalyze}>Analyze (run model)</Button>
            <Button className="btn-primary" onClick={handleGenerateReport}>Generate Report</Button>
            <Button className="btn-primary" onClick={() => lastReport && handleDownloadReport(lastReport.id)}>Download Report (PDF)</Button> {/* Use lastReport.id for download */}
          </div>
          <div className="mt-3 small muted">
            Model file (placeholder): <span style={{ fontFamily: 'monospace', color: '#cfe8ff' }}>{modelPath}</span>
          </div>
        </div>

        {/* Activity Panel */}
        <div className="panel">
          <PanelHeader title="Activity" subtitle="Logs & short messages" />
          <pre className="log" style={{ whiteSpace: 'pre-wrap' }}>
            {logMessages.map((msg, i) => <div key={i}>{msg}</div>)}
          </pre>
        </div>
      </div>

      {/* Middle column: Industry / Plant */}
      <div className="col">
        {['business', 'user', 'validator', 'admin', 'plant'].includes(role || '') && (
          <div className="panel industry">
            <PanelHeader title="Industry / Plant Dashboard" subtitle="STP/WTP plant metrics & suggestions" />

            <div className="kpis">
              <div className="kpi">
                <div className="muted">pH</div>
                <div className="text-xl font-extrabold">{dashboardData?.kpis.ph.toFixed(1) || 'N/A'}</div>
                <div className="small muted">Target 6.8 – 7.2</div>
              </div>
              <div className="kpi">
                <div className="muted">Turbidity (NTU)</div>
                <div className="text-xl font-extrabold">{dashboardData?.kpis.turbidity.toFixed(1) || 'N/A'}</div>
                <div className="small muted">Acceptable &lt; 5</div>
              </div>
              <div className="kpi">
                <div className="muted">DO (mg/L)</div>
                <div className="text-xl font-extrabold">{dashboardData?.kpis.do.toFixed(1) || 'N/A'}</div>
                <div className="small muted">Target &gt; 5</div>
              </div>
              <div className="kpi">
                <div className="muted">Temp (°C)</div>
                <div className="text-xl font-extrabold">{dashboardData?.kpis.temp.toFixed(1) || 'N/A'}</div>
                <div className="small muted">Range 20 – 30</div>
              </div>
            </div>

            <div className="mt-4">
              <h3 className="my-2 text-lg font-semibold">Parameter trends</h3>
              <div className="chart-wrap panel" style={{ padding: '8px' }}>
                <ReactChart type="line" data={chartData} options={chartOptions} />
              </div>
            </div>

            <div className="mt-3">
              <h3 className="my-2 text-lg font-semibold">AI Suggestion</h3>
              <div className="p-3 rounded-md bg-gray-900">
                <strong id="aiSuggestion">
                  {lastReport?.ml_insights?.pollution_label || 'No analysis run yet.'}
                </strong>
                <ul id="treatmentSteps" className="mt-2">
                  {lastReport?.recommendations?.map((rec: string, i: number) => (
                    <li key={i} className="small muted">{rec}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Reports Panel */}
        {['business', 'user', 'validator', 'admin', 'plant'].includes(role || '') && (
          <div className="panel">
            <PanelHeader title="Reports" subtitle="Saved reports & download" />
            <div className="user-list">
              {reports.length === 0 ? (
                <div className="small muted">No reports available.</div>
              ) : (
                reports.map(report => (
                  <div key={report.id} className="user-card">
                    <div>
                      <div className="font-bold">{report.source_filename || `Report ${report.id.substring(0, 8)}`}</div>
                      <div className="small muted">{new Date(report.created_at).toLocaleString()}</div>
                    </div>
                    <div className="flex-row">
                      <Button className="btn-primary small" onClick={() => handleDownloadReport(report.id)}>Download</Button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>

      {/* Right column: Validators / quick controls */}
      <div className="col">
        {['validator', 'admin'].includes(role || '') && (
          <div className="panel validator">
            <PanelHeader title="Validator Panel" subtitle="Verify model outputs & approve treatments" />

            <div className="user-list">
              {reports.filter(r => r.ml_insights?.pollution_label).length === 0 ? (
                <div className="small muted">No reports for validation.</div>
              ) : (
                reports.filter(r => r.ml_insights?.pollution_label).map(report => (
                  <div key={report.id} className="user-card">
                    <div>
                      <div className="font-bold">{report.source_filename || `Report ${report.id.substring(0, 8)}`}</div>
                      <div className="small muted">{report.ml_insights?.pollution_label}</div>
                    </div>
                    <div className="flex-row">
                      <Button className="btn-primary small">Inspect</Button>
                    </div>
                  </div>
                ))
              )}
            </div>

            <div className="mt-3">
              <h3 className="text-lg font-semibold">Quick Validate</h3>
              <div className="flex-row">
                <Select>
                  <option>Select Report</option>
                  {reports.filter(r => r.ml_insights?.pollution_label).map(report => (
                    <option key={report.id} value={report.id}>
                      {report.source_filename || `Report ${report.id.substring(0, 8)}`}
                    </option>
                  ))}
                </Select>
                <Button className="btn-primary" onClick={handleApproveReport}>Approve</Button>
                <Button className="btn-danger" onClick={handleRejectReport}>Reject</Button>
              </div>
            </div>
          </div>
        )}

        {/* Settings Panel */}
        {['admin'].includes(role || '') && ( // Only admin can see settings
          <div className="panel">
            <PanelHeader title="Settings" subtitle="Base URL & integration" />
            <div className="flex flex-col gap-2">
              <label className="small muted">Backend API base URL</label>
              <Input
                id="apiBase"
                placeholder="e.g. http://localhost:8000"
                value={apiBase}
                onChange={(e) => setApiBase(e.target.value)}
              />
              <label className="small muted">Model file URL (optional for direct model call)</label>
              <Input id="modelUrlInput" placeholder="file:///... or https://..." />
              <div className="small muted">Tip: Set the Model file path to your local model path if you serve it locally. Otherwise configure API endpoints on your backend.</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;