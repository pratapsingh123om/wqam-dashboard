# Quick Start Guide - WQAM Dashboard

## Step 1: Run the Upgrade Script

### Windows (PowerShell)
```powershell
# If you have Git Bash installed:
bash upgrade_dashboard.sh

# OR if you have WSL:
wsl bash upgrade_dashboard.sh
```

### Mac/Linux
```bash
chmod +x upgrade_dashboard.sh
bash upgrade_dashboard.sh
```

## Step 2: Install Frontend Dependencies

```bash
cd wqam-dashboard
npm install axios chart.js react-chartjs-2 chartjs-adapter-date-fns date-fns
```

## Step 3: Set Up Backend

### Create Virtual Environment

**Windows:**
```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**Mac/Linux:**
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Run Backend Server

```bash
uvicorn app:app --reload --port 8000
```

Keep this terminal open - the backend should be running on `http://localhost:8000`

## Step 4: Run Frontend

Open a **new terminal** and run:

```bash
cd wqam-dashboard
npm run dev
```

The frontend should be running on `http://localhost:5173`

## Step 5: Test the Dashboard

1. Open `http://localhost:5173` in your browser
2. Click "Upload Data" and select a CSV file
3. Click "Analyze"
4. View the time-series charts with threshold lines

## Example CSV Format

Create a file `test_data.csv`:

```csv
timestamp,pH,Turbidity,DO,TDS,Iron
2024-01-01 00:00:00,7.2,1.5,8.5,320,0.2
2024-01-01 01:00:00,7.3,1.6,8.4,325,0.21
2024-01-01 02:00:00,7.1,1.4,8.6,318,0.19
2024-01-01 03:00:00,7.4,1.7,8.3,330,0.22
2024-01-01 04:00:00,7.0,1.3,8.7,315,0.18
```

## Troubleshooting

### Backend not starting?
- Check Python version: `python --version` (needs 3.8+)
- Make sure virtual environment is activated
- Check if port 8000 is available: `netstat -an | findstr :8000` (Windows) or `lsof -i :8000` (Mac/Linux)

### Frontend can't connect?
- Make sure backend is running on port 8000
- Check browser console for CORS errors
- Verify `src/services/api.ts` has correct baseURL

### Charts not showing?
- Check browser console for errors
- Verify all Chart.js packages are installed
- Make sure CSV file has proper format

## What Changed?

- ✅ Backend: FastAPI server for CSV analysis
- ✅ Frontend: Chart.js with threshold lines
- ✅ UI: Modern dark theme with gradient backgrounds
- ✅ Alerts: Visual indicators for threshold violations
- ✅ Logo: Replaced "WQAM Pro" with logo area

## Next Steps

- Add database for persistent storage
- Implement user authentication
- Add more chart types
- Export reports (PDF/Excel)
- Real-time data updates
