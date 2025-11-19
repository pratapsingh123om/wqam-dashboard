"""
ML Service Module
Integrates ML models for water quality prediction and analysis
"""
import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import joblib
from sklearn.impute import SimpleImputer
import warnings
warnings.filterwarnings("ignore")

# Add ML directory to path to import model
# Check for Docker-mounted path first, then fallback to relative path
import os
ML_DIR_DOCKER = Path("/ml")  # Docker mount point
ML_DIR_LOCAL = Path(__file__).resolve().parent.parent / "ml"

if ML_DIR_DOCKER.exists() and (ML_DIR_DOCKER / "model" / "water_model.pkl").exists():
    ML_DIR = ML_DIR_DOCKER
else:
    ML_DIR = ML_DIR_LOCAL

MODEL_PATH = ML_DIR / "model" / "water_model.pkl"

# Global model cache
_model = None
_imputer = None


def load_model():
    """Load the trained ML model and imputer"""
    global _model, _imputer
    
    if _model is not None:
        return _model, _imputer
    
    if not MODEL_PATH.exists():
        print(f"Warning: Model not found at {MODEL_PATH}. ML predictions will be disabled.")
        return None, None
    
    try:
        _model = joblib.load(MODEL_PATH)
        # Create imputer (using median strategy as in training)
        _imputer = SimpleImputer(strategy="median")
        print(f"ML model loaded successfully from {MODEL_PATH}")
        return _model, _imputer
    except Exception as e:
        print(f"Error loading ML model: {e}")
        return None, None


def prepare_features(df: pd.DataFrame) -> Optional[np.ndarray]:
    """
    Prepare features from dataframe for ML model prediction.
    Returns numpy array of features ready for model input.
    """
    model, imputer = load_model()
    if model is None:
        return None
    
    # Make a copy to avoid modifying original
    df = df.copy()
    
    # Keep only numeric columns
    numeric_df = df.select_dtypes(include=[np.number])
    
    if numeric_df.shape[1] < 3:
        return None
    
    # Impute missing values
    try:
        # Fit imputer if not fitted yet (using training data statistics if available)
        if not hasattr(imputer, 'statistics_') or imputer.statistics_ is None:
            # Use median of current data
            imputed_data = imputer.fit_transform(numeric_df)
        else:
            imputed_data = imputer.transform(numeric_df)
        
        return imputed_data
    except Exception as e:
        print(f"Error preparing features: {e}")
        return None


def predict_pollution(df: pd.DataFrame) -> Optional[float]:
    """
    Predict pollution level using the trained ML model.
    Returns predicted value or None if model unavailable.
    """
    model, _ = load_model()
    if model is None:
        return None
    
    features = prepare_features(df)
    if features is None:
        return None
    
    try:
        prediction = model.predict(features)
        # Return mean prediction if multiple rows
        return float(np.mean(prediction))
    except Exception as e:
        print(f"Error making prediction: {e}")
        return None


def forecast_trend(series: pd.Series, steps: int = 3) -> Optional[List[float]]:
    """
    Simple linear forecast for time series data.
    Returns list of forecasted values.
    """
    from sklearn.linear_model import LinearRegression
    
    s = series.dropna().reset_index(drop=True)
    if s.size < 3:
        return None
    
    try:
        X = np.arange(len(s)).reshape(-1, 1)
        y = s.values.reshape(-1, 1)
        model = LinearRegression().fit(X, y)
        xf = np.arange(len(s), len(s) + steps).reshape(-1, 1)
        yf = model.predict(xf).ravel()
        return [float(v) for v in yf]
    except Exception as e:
        print(f"Error forecasting trend: {e}")
        return None


def compute_pollution_score(values: Dict[str, List[float]]) -> Tuple[float, str]:
    """
    Compute pollution score from parameter values.
    Returns (score, label) tuple.
    """
    score = 0.0
    bod = values.get("bod", [])
    do = values.get("do", [])
    cod = values.get("cod", [])
    ph = values.get("ph", [])
    tds = values.get("tds", [])
    
    if bod:
        if max(bod) > 6:
            score += 2
        elif max(bod) > 3:
            score += 1
    
    if do:
        if min(do) < 3:
            score += 2
        elif min(do) < 5:
            score += 1
    
    if cod and max(cod) > 250:
        score += 1
    
    if ph:
        p = np.mean(ph)
        if p < 6.5 or p > 8.5:
            score += 0.5
    
    if tds and max(tds) > 2000:
        score += 0.5
    
    # Map score to label
    if score >= 3:
        label = "POLLUTED"
    elif score >= 1.5:
        label = "MODERATE"
    else:
        label = "GOOD"
    
    return float(score), label


def extract_parameters_from_df(df: pd.DataFrame) -> Dict[str, List[float]]:
    """
    Extract water quality parameters from dataframe.
    Returns dict with parameter names as keys and lists of values.
    """
    # Column name mappings (case-insensitive)
    param_mappings = {
        "bod": ["bod", "biochemical", "b.o.d"],
        "cod": ["cod", "chemical"],
        "do": ["do", "dissolved oxygen", "d.o."],
        "ph": ["ph", "ph "],
        "tds": ["tds", "total dissolved"],
        "turbidity": ["turbidity", "ntu"],
        "chlorine": ["chlorine", "freechlorine", "cl2"],
    }
    
    extracted = {}
    # Create a normalized copy for matching
    df_normalized = df.copy()
    # Normalize column names: lowercase, strip, replace newlines/spaces
    normalized_cols = {}
    for col in df.columns:
        normalized = str(col).lower().strip().replace("\n", " ").replace("\r", " ")
        normalized = " ".join(normalized.split())  # Remove extra spaces
        normalized_cols[normalized] = col
    
    for param, keywords in param_mappings.items():
        values = []
        for normalized_col, original_col in normalized_cols.items():
            # Check if any keyword matches
            if any(kw in normalized_col for kw in keywords):
                try:
                    # Use original column name to access data
                    numeric_vals = pd.to_numeric(df[original_col], errors="coerce").dropna().tolist()
                    values.extend([float(v) for v in numeric_vals if not np.isnan(v)])
                except (KeyError, TypeError) as e:
                    # Skip if column access fails
                    continue
        if values:
            extracted[param] = values
    
    return extracted


def get_ml_insights(df: pd.DataFrame) -> Dict:
    """
    Get comprehensive ML-based insights from dataframe.
    Returns dict with predictions, forecasts, and recommendations.
    """
    insights = {
        "pollution_prediction": None,
        "pollution_score": None,
        "pollution_label": None,
        "forecasts": {},
        "recommendations": [],
        "model_available": False,
    }
    
    # Load model
    model, _ = load_model()
    insights["model_available"] = model is not None
    
    # Get pollution prediction
    if model is not None:
        prediction = predict_pollution(df)
        insights["pollution_prediction"] = prediction
    
    # Extract parameters and compute score
    params = extract_parameters_from_df(df)
    if params:
        score, label = compute_pollution_score(params)
        insights["pollution_score"] = score
        insights["pollution_label"] = label
    
    # Generate forecasts for key parameters
    for param in ["ph", "do", "turbidity", "tds"]:
        if param in params and len(params[param]) >= 3:
            series = pd.Series(params[param])
            forecast = forecast_trend(series, steps=3)
            if forecast:
                insights["forecasts"][param] = forecast
    
    # Generate recommendations based on insights
    recommendations = []
    if insights["pollution_label"] == "POLLUTED":
        recommendations.append("Immediate action required: Water quality is below acceptable standards.")
    elif insights["pollution_label"] == "MODERATE":
        recommendations.append("Monitor closely: Water quality is approaching threshold limits.")
    
    if params.get("do") and min(params["do"]) < 5:
        recommendations.append("Low dissolved oxygen detected. Increase aeration and reduce organic load.")
    
    if params.get("bod") and max(params["bod"]) > 6:
        recommendations.append("High BOD detected. Prioritize biological treatment upgrades.")
    
    if params.get("ph"):
        ph_mean = np.mean(params["ph"])
        if ph_mean < 6.5 or ph_mean > 8.5:
            recommendations.append("pH out of optimal range. Adjust with acid/alkali dosing.")
    
    if not recommendations:
        recommendations.append("All monitored parameters are within acceptable ranges.")
    
    insights["recommendations"] = recommendations
    
    return insights

