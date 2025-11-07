# AquaVis Dashboard - Upgrade Instructions

A modern, responsive water quality monitoring dashboard with CSV/XLSX upload, time-series analysis, and threshold alerts.

## Quick Start

### 1. Run the Upgrade Script

```bash
bash upgrade_dashboard.sh
```

This script will:
- Create/update backend files (`backend/app.py`, `backend/requirements.txt`)
- Update frontend files (`src/App.tsx`, `src/main.tsx`, `src/index.css`, `index.html`)
- Create backups of overwritten files (`.bak` extensions)
- Set up the API service (`src/services/api.ts`)

### 2. Install Frontend Dependencies

```bash
npm install
```

Required packages (already in `package.json`):
- `axios` - HTTP client
- `chart.js` - Chart library
- `react-chartjs-2` - React wrapper for Chart.js
- `chartjs-adapter-date-fns` - Date adapter for time-series charts
- `date-fns` - Date utilities
- `tailwindcss` - CSS framework
- `lucide-react` - Icons

### 3. Install Backend Dependencies

```bash
cd backend
python -m venv .venv

# Activate virtual environment:
# Windows: .venv\Scripts\activate
# Mac/Linux: source .venv/bin/activate

pip install -r requirements.txt
```

Required packages:
- `fastapi` - Web framework
- `uvicorn[standard]` - ASGI server
- `pandas` - Data analysis
- `python-multipart` - File upload support
- `numpy` - Numerical operations
- `aiofiles` - Async file operations
- `python-dotenv` - Environment variables
- `openpyxl` - Excel file support

### 4. Run the Application

**Terminal 1 - Frontend:**
```bash
npm run dev
```
Frontend will run on `http://localhost:5173` (or the next available port)

**Terminal 2 - Backend:**
```bash
cd backend
# Activate venv if not already active
uvicorn app:app --reload --port 8000
```
Backend will run on `http://localhost:8000`

### 5. Use the Dashboard

1. Open the frontend URL in your browser
2. Click "Upload Data" to select a CSV or Excel file
3. Click "Analyze" to process the file
4. View time-series charts for each parameter
5. Check for threshold alerts (red badges indicate exceeded thresholds)

## File Structure

```
wqam-dashboard/
├── backend/
│   ├── app.py              # FastAPI backend
│   └── requirements.txt    # Python dependencies
├── src/
│   ├── App.tsx             # Main React component
│   ├── main.tsx            # React entry point
│   ├── index.css           # Tailwind CSS imports
│   └── services/
│       └── api.ts          # Axios API configuration
├── index.html              # HTML template
├── upgrade_dashboard.sh    # Upgrade script
└── package.json            # Node dependencies
```

## Features

- **CSV/XLSX Upload**: Upload water quality data files
- **Time-Series Charts**: Visualize parameter trends over time
- **Threshold Alerts**: Automatic detection of threshold violations
- **Responsive Design**: Works on desktop and mobile devices
- **Dark Mode UI**: Modern dark theme with gradient accents
- **Stateless Analysis**: No database required - analysis is performed on upload

## Default Thresholds

The backend uses default thresholds (can be customized in `backend/app.py`):

- **pH**: min: 6.5, max: 8.5
- **Turbidity**: max: 5.0
- **DO** (Dissolved Oxygen): min: 5.0
- **TDS** (Total Dissolved Solids): max: 500.0
- **Iron**: max: 0.3

## Expected Data Format

CSV/Excel files should contain:
- A timestamp column (named: `timestamp`, `time`, `date`, `datetime`, or `date/time`)
- Numeric parameter columns (e.g., `pH`, `Turbidity`, `DO`, `TDS`, `Iron`)

Example:
```csv
timestamp,pH,Turbidity,DO
2024-01-01 00:00:00,7.2,2.1,6.5
2024-01-01 01:00:00,7.3,2.3,6.4
```

## Customization

### Change Thresholds

Edit `backend/app.py` and modify the `DEFAULT_THRESHOLDS` dictionary:

```python
DEFAULT_THRESHOLDS = {
    "pH": {"min": 6.5, "max": 8.5},
    "YourParameter": {"min": 0, "max": 100},
    # Add more as needed
}
```

### Change Backend URL

Edit `src/services/api.ts`:

```typescript
const api = axios.create({
  baseURL: 'http://your-backend-url:8000',
  timeout: 60000,
});
```

### Production Deployment

For production:
1. Update CORS settings in `backend/app.py` to use specific origins instead of `["*"]`
2. Set environment variables for sensitive configuration
3. Use a production ASGI server (e.g., Gunicorn with Uvicorn workers)
4. Build the frontend: `npm run build`
5. Serve the built files from `dist/` directory

## Troubleshooting

- **Backend not starting**: Ensure Python 3.8+ is installed and all dependencies are installed
- **Frontend can't connect to backend**: Check that backend is running on port 8000 and CORS is enabled
- **Charts not displaying**: Ensure `chartjs-adapter-date-fns` is installed and timestamps are in correct format
- **File upload fails**: Check that the file has a timestamp column and numeric parameter columns

## License

MIT License

