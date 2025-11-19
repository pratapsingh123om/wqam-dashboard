# ML Model Integration Summary

## Overview
This document describes the integration of the ML model with the frontend and backend of the WQAM Dashboard.

## Integration Components

### 1. Backend ML Service (`backend/ml_service.py`)
A comprehensive ML service module that provides:
- **Model Loading**: Loads the trained RandomForestRegressor model from `ml/model/water_model.pkl`
- **Pollution Prediction**: Uses the ML model to predict pollution levels from water quality data
- **Trend Forecasting**: Provides linear regression-based forecasts for time series data
- **Pollution Scoring**: Computes heuristic pollution scores and labels (GOOD/MODERATE/POLLUTED)
- **Parameter Extraction**: Automatically extracts water quality parameters from dataframes
- **Comprehensive Insights**: Combines all ML capabilities into a single insights object

### 2. Backend API Integration (`backend/main.py`)
- **Enhanced Upload Analysis**: The `/api/uploads/analyze` endpoint now includes ML insights in the response
- **New ML Endpoints**:
  - `POST /api/ml/predict`: Get ML predictions for uploaded data
  - `GET /api/ml/status`: Check ML model availability

### 3. Backend Schema Updates (`backend/schemas.py`)
- Added `MLInsights` schema to structure ML prediction data
- Updated `UploadReport` schema to include optional `ml_insights` field

### 4. Frontend Type Definitions (`frontend/src/types/dashboard.ts`)
- Added `MLInsights` interface matching backend schema
- Updated `UploadReport` interface to include ML insights

### 5. Frontend UI Updates

#### Uploads Page (`frontend/src/pages/Uploads.tsx`)
- Displays ML predictions and pollution scores
- Shows parameter forecasts (next 3 steps)
- Visual indicators for ML-enabled analysis
- Color-coded ML insights panel

#### Reports Page (`frontend/src/pages/Reports.tsx`)
- Added ML status column in reports table
- Shows pollution labels from ML analysis
- Indicates which reports have ML insights

#### API Service (`frontend/src/services/api.ts`)
- Added `getMLPredictions()` function
- Added `getMLStatus()` function

## Features Enabled

### 1. Automatic ML Predictions
When users upload water quality data (CSV/PDF/Excel), the system automatically:
- Runs ML model predictions
- Computes pollution scores
- Generates forecasts for key parameters
- Provides ML-enhanced recommendations

### 2. Pollution Assessment
- **Prediction**: ML model predicts pollution levels based on learned patterns
- **Score**: Heuristic score (0-5+) based on parameter thresholds
- **Label**: Categorical assessment (GOOD/MODERATE/POLLUTED)

### 3. Forecasting
- Linear regression-based forecasts for:
  - pH levels
  - Dissolved Oxygen (DO)
  - Turbidity
  - Total Dissolved Solids (TDS)
- Provides next 3 forecasted values for each parameter

### 4. Enhanced Recommendations
ML insights are merged with traditional threshold-based recommendations to provide:
- Data-driven predictions
- Trend-based forecasts
- Heuristic pollution assessments
- Actionable treatment guidance

## Model Requirements

The ML model expects:
- **Location**: `ml/model/water_model.pkl`
- **Type**: RandomForestRegressor (scikit-learn)
- **Input**: Numeric features from water quality data
- **Output**: Pollution prediction value

## Dependencies Added

### Backend (`backend/requirements.txt`)
- `scikit-learn`: ML model library
- `joblib`: Model serialization
- `numpy`: Numerical operations (already used, now explicit)

## Usage

### Automatic Integration
ML predictions are automatically included when:
1. User uploads a file via `/api/uploads/analyze`
2. Backend processes the data
3. ML service analyzes the data
4. Results are included in the response

### Manual ML Prediction
To get ML predictions separately:
```typescript
const formData = new FormData();
formData.append("file", file);
const insights = await getMLPredictions(formData);
```

### Check ML Status
```typescript
const status = await getMLStatus();
// Returns: { model_available: boolean, model_path: string | null }
```

## Error Handling

- If ML model is not available, the system gracefully degrades:
  - `model_available: false` in responses
  - Traditional analysis still works
  - No ML insights included
- If model fails to load, warnings are logged but the system continues

## Future Enhancements

Potential improvements:
1. Model retraining endpoint
2. Batch prediction support
3. Advanced forecasting models (ARIMA, LSTM)
4. Anomaly detection using ML
5. Model versioning and A/B testing
6. Real-time streaming predictions

## Testing

To verify the integration:
1. Ensure ML model exists at `ml/model/water_model.pkl`
2. Upload a water quality data file
3. Check that `ml_insights` appears in the response
4. Verify ML predictions are displayed in the frontend
5. Test ML status endpoint: `GET /api/ml/status`

## Notes

- The ML model uses column 13 as the target (as configured in `ml/train_model.py`)
- Feature preparation matches the training pipeline (numeric columns, median imputation)
- Forecasts use simple linear regression; more sophisticated models can be added later
- ML insights are optional - the system works without them if the model is unavailable

