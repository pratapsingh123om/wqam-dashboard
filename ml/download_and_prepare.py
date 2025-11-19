# train_model.py
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix
import joblib

DATA = Path("data/combined.csv")
MODEL_DIR = Path("models")
MODEL_DIR.mkdir(parents=True, exist_ok=True)

def create_target(df):
    # Simple, pragmatic target:
    # Mark sample as polluted (1) if BOD > 3 mg/L OR DO < 5 mg/L (adjust thresholds as you like)
    # If both columns missing, drop the row for training.
    cond_bod = df.get("bod")
    cond_do = df.get("do")
    target = pd.Series(index=df.index, dtype="Int64")
    # default 0
    target[:] = 0
    if cond_bod is not None:
        target.loc[cond_bod > 3] = 1
    if cond_do is not None:
        target.loc[cond_do < 5] = 1
    # drop where both are NaN and no features
    mask_nodata = (cond_bod.isna() if cond_bod is not None else pd.Series(True, index=df.index)) & (cond_do.isna() if cond_do is not None else pd.Series(True, index=df.index))
    target = target[~mask_nodata]
    return target

def main():
    df = pd.read_csv(DATA)
    print("Loaded", df.shape)
    # keep a handful of numeric features common in NWMP datasets
    features = ["bod", "do", "ph", "cod", "tds", "temp"]
    X = df[features].copy()
    y = create_target(df)

    # align X and y (drop rows missing target)
    X = X.loc[y.index]
    # drop columns where all NaNs
    X = X.dropna(axis=1, how='all')
    # If too few rows, bail
    if X.shape[0] < 30:
        print("Not enough labeled rows to train (need ~30+). Check data/combined.csv")
        return

    # pipeline
    pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("clf", RandomForestClassifier(n_estimators=200, random_state=42))
    ])

    X_train, X_test, y_train, y_test = train_test_split(X, y, stratify=y, test_size=0.2, random_state=42)
    pipe.fit(X_train, y_train)
    preds = pipe.predict(X_test)
    print("Classification report:")
    print(classification_report(y_test, preds))
    print("Confusion matrix:")
    print(confusion_matrix(y_test, preds))

    joblib.dump(pipe, MODEL_DIR / "rf_model.joblib")
    print("Saved model to", MODEL_DIR / "rf_model.joblib")

if __name__ == "__main__":
    main()
