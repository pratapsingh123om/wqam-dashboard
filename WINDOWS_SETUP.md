# Windows Setup Guide - WQAM Dashboard

## Step 1: Install Python (if not installed)

### Option A: Using Winget (Windows Package Manager)
```powershell
winget install Python.Python.3.11
```

### Option B: Download from Python.org
1. Go to: https://www.python.org/downloads/
2. Download Python 3.11 or later
3. **IMPORTANT**: Check "Add Python to PATH" during installation
4. Run the installer

### Option C: Using Microsoft Store
```powershell
# Open Microsoft Store and search for "Python 3.11"
# OR run:
python
# This will prompt to install from Microsoft Store
```

### Verify Python Installation
```powershell
python --version
# Should show: Python 3.11.x or later

pip --version
# Should show: pip version
```

## Step 2: Run the Upgrade Script

```powershell
cd C:\Users\gsr33\WQAM\wqam-dashboard
.\upgrade_dashboard.ps1
```

If you get an execution policy error, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\upgrade_dashboard.ps1
```

## Step 3: Install Frontend Dependencies

```powershell
cd C:\Users\gsr33\WQAM\wqam-dashboard
npm install axios chart.js react-chartjs-2 chartjs-adapter-date-fns date-fns
```

## Step 4: Set Up Backend

### Create Virtual Environment
```powershell
cd C:\Users\gsr33\WQAM\wqam-dashboard\backend
python -m venv .venv
```

### Activate Virtual Environment
```powershell
.venv\Scripts\activate
```

You should see `(.venv)` in your prompt.

### Install Backend Dependencies
```powershell
pip install -r requirements.txt
```

### Run Backend Server
```powershell
uvicorn app:app --reload --port 8000
```

Keep this terminal open - backend should be running on `http://localhost:8000`

## Step 5: Run Frontend

Open a **NEW PowerShell terminal** and run:

```powershell
cd C:\Users\gsr33\WQAM\wqam-dashboard
npm run dev
```

Frontend should be running on `http://localhost:5173`

## Troubleshooting

### Python not found?
- Make sure Python is installed: `python --version`
- Check if Python is in PATH: `$env:Path -split ';' | Select-String python`
- Reinstall Python and check "Add to PATH"

### Virtual environment not activating?
- Make sure you're in the `backend` folder
- Try: `.\.venv\Scripts\Activate.ps1`
- If blocked, run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

### Port 8000 already in use?
- Find what's using it: `netstat -ano | findstr :8000`
- Kill the process or use a different port: `uvicorn app:app --reload --port 8001`

### Frontend can't connect to backend?
- Make sure backend is running on port 8000
- Check CORS settings in `backend\app.py`
- Verify `src\services\api.ts` has correct baseURL

## Quick Commands Reference

```powershell
# Install Python (if needed)
winget install Python.Python.3.11

# Run upgrade script
.\upgrade_dashboard.ps1

# Frontend setup
npm install axios chart.js react-chartjs-2 chartjs-adapter-date-fns date-fns
npm run dev

# Backend setup
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
```

## Next Steps

1. Open `http://localhost:5173` in your browser
2. Upload a CSV file with water quality data
3. Click "Analyze" to see charts with threshold lines
