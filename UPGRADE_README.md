# WQAM Dashboard Upgrade Guide

This guide will help you upgrade your WQAM dashboard with a FastAPI backend and Chart.js frontend.

## Prerequisites

- Node.js and npm installed
- Python 3.8+ installed
- Git Bash (for Windows) or WSL (Windows Subsystem for Linux) OR use the PowerShell script

## Quick Start

### Option 1: Using Bash Script (Git Bash / WSL / Mac / Linux)

1. Open terminal in the project root (`wqam-dashboard`)

2. Make the script executable:
   ```bash
   chmod +x upgrade_dashboard.sh
   ```

3. Run the script:
   ```bash
   bash upgrade_dashboard.sh
   ```

### Option 2: Using PowerShell (Windows)

1. Open PowerShell in the project root

2. Run:
   ```powershell
   .\upgrade_dashboard.ps1
   ```

## What the Script Does

1. **Backs up original files** (creates `.bak` copies)
2. **Creates backend folder** with:
   - `app.py` - FastAPI backend for CSV analysis
   - `requirements.txt` - Python dependencies
3. **Updates frontend files**:
   - `src/App.tsx` - Modern React component with Chart.js
   - `src/main.tsx` - Entry point
   - `src/index.css` - Tailwind styles
   - `index.html` - HTML template
4. **Creates service files**:
   - `src/services/api.ts` - Axios helper

## After Running the Script

### 1. Install Frontend Dependencies

```bash
cd wqam-dashboard
npm install axios chart.js react-chartjs-2 chartjs-adapter-date-fns date-fns
```

### 2. Set Up Backend

#### Create Virtual Environment (Recommended)

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

#### Run Backend Server

```bash
uvicorn app:app --reload --port 8000
```

### 3. Run Frontend

In a separate terminal:

```bash
cd wqam-dashboard
npm run dev
```

## Usage

1. **Start both servers** (backend on port 8000, frontend on port 5173)
2. **Open frontend** in browser: `http://localhost:5173`
3. **Upload a CSV file** with columns:
   - `timestamp` (or `time`, `date`, `datetime`)
   - Parameter columns: `pH`, `Turbidity`, `DO`, `TDS`, `Iron`, etc.
4. **Click "Analyze"** to see time-series charts with threshold lines

## Example CSV Format

```csv
timestamp,pH,Turbidity,DO,TDS,Iron
2024-01-01 00:00:00,7.2,1.5,8.5,320,0.2
2024-01-01 01:00:00,7.3,1.6,8.4,325,0.21
2024-01-01 02:00:00,7.1,1.4,8.6,318,0.19
```

## Default Thresholds

The backend checks these thresholds (configurable in `backend/app.py`):

- **pH**: min: 6.5, max: 8.5
- **Turbidity**: max: 5.0
- **DO**: min: 5.0
- **TDS**: max: 500.0
- **Iron**: max: 0.3

## Troubleshooting

### Backend won't start
- Check Python version: `python --version` (should be 3.8+)
- Ensure virtual environment is activated
- Check if port 8000 is available

### Frontend can't connect to backend
- Ensure backend is running on `http://localhost:8000`
- Check CORS settings in `backend/app.py`
- Verify axios baseURL in `src/services/api.ts`

### Charts not displaying
- Check browser console for errors
- Verify Chart.js dependencies are installed
- Check that data is being returned from backend

## Restoring Backups

If something goes wrong, restore from backups:

```bash
# Restore App.tsx
cp src/App.tsx.bak src/App.tsx

# Restore other files similarly
```

## Next Steps

- Add authentication
- Connect to database for persistent storage
- Add more chart types (bar, pie, etc.)
- Implement real-time data updates
- Add export functionality (PDF, Excel)

## Support

For issues or questions, check:
- FastAPI docs: https://fastapi.tiangolo.com/
- Chart.js docs: https://www.chartjs.org/
- React docs: https://react.dev/
