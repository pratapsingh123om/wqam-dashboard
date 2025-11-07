# Water Quality Monitoring and Analysis Dashboard (WQAM)

A modern, comprehensive dashboard for monitoring, analyzing, and predicting water quality in real-time.

## Features

### 🌟 Key Features

1. **Real-Time Water Monitoring**
   - Live readings from water sensors
   - Track pH, TDS, Turbidity, and Iron content
   - Dynamic charts and gauges

2. **Smart Data Analysis & AI Insights**
   - Upload data in CSV or Excel formats
   - AI-powered pattern detection and anomaly identification
   - Health ratings, safety alerts, and recommendations

3. **Interactive Visualization**
   - Multiple chart types (Line, Bar, Area)
   - Color-coded alerts (Safe, Moderate, At Risk)
   - Location-based reports

4. **Multi-Language Interface**
   - Support for English, Hindi, and Bengali
   - Automatic language switching

5. **Data Import, Export, and Sharing**
   - Import existing data files
   - Export reports in PDF and Word formats
   - Share insights and charts

6. **Alerts & Safety Notifications**
   - Automatic flagging of unsafe readings
   - Visual alerts on dashboard
   - Recommendations for corrective action

7. **Secure User Access**
   - Secure login system
   - Personalized dashboards
   - Multi-source data management

## Getting Started

### Prerequisites

- Node.js (v18 or higher)
- npm or yarn

### Installation

1. Navigate to the project directory:
```bash
cd wqam-dashboard
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

4. Open your browser and navigate to:
```
http://localhost:5173
```

### Building for Production

```bash
npm run build
```

The production build will be in the `dist` directory.

## Usage

### Dashboard Overview

- **Sidebar**: Navigation menu with Dashboard, Reports, Settings, etc.
- **Top Bar**: Search, language selector, notifications, and user profile
- **Stat Cards**: Quick overview of key metrics (Total Samples, Readings, Alerts, Locations)
- **Charts**: Multiple visualizations showing trends and comparisons
- **Analysis Section**: Click "Analyze" button to view:
  - Analysis techniques
  - Recommendations
  - Trend analysis charts
  - Export options (PDF/Word)

### Exporting Reports

1. Click the "Analyze" button to open the analysis section
2. Click "Export as PDF" or "Export as Word" to download reports
3. Reports include:
   - Summary statistics
   - Analysis techniques used
   - Recommendations
   - Generated date

### Language Switching

Use the language selector in the top bar to switch between:
- English (EN)
- Hindi (हिं)
- Bengali (BN)

## Technology Stack

- **React 19** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Recharts** - Chart library
- **Lucide React** - Icons
- **jsPDF** - PDF generation
- **docx** - Word document generation
- **file-saver** - File download

## Project Structure

```
wqam-dashboard/
├── src/
│   ├── App.tsx          # Main dashboard component
│   ├── App.css          # App-specific styles
│   ├── index.css        # Global styles
│   └── main.tsx         # Entry point
├── public/              # Static assets
├── index.html           # HTML template
└── package.json         # Dependencies
```

## Features in Detail

### Analyze Function

The analyze function provides:
- **Graphs and Charts**: Visual representation of water quality trends
- **Techniques**: Statistical analysis, trend detection, anomaly detection
- **Suggestions**: Actionable recommendations based on data analysis

### Export Functionality

- **PDF Export**: Generate PDF reports with summary data
- **Word Export**: Create Word documents with detailed analysis
- Both formats include timestamps and comprehensive data

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.
