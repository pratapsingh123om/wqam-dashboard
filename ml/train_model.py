import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.impute import SimpleImputer
import joblib

def train():

    df = pd.read_csv("output/cleaned.csv")

    # ---- CHOOSE TARGET COLUMN ----
    TARGET = "13"   # using column 13 as pollution metric

    if TARGET not in df.columns:
        raise ValueError(f"Target column {TARGET} not found in dataset")

    # Drop rows where target missing
    df = df.dropna(subset=[TARGET])

    # Separate features & target
    y = df[TARGET]
    X = df.drop(columns=[TARGET])

    # Keep only numeric columns
    X = X.select_dtypes(include=[np.number])

    if X.shape[1] < 3:
        raise ValueError("Not enough numeric feature columns to train.")

    # Impute missing values
    imp = SimpleImputer(strategy="median")
    X = imp.fit_transform(X)

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Model
    model = RandomForestRegressor(
        n_estimators=200,
        random_state=42
    )

    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)

    print(f"Training complete. MAE = {mae:.4f}")

    joblib.dump(model, "model/water_model.pkl")
    print("Model saved at: model/water_model.pkl")

if __name__ == "__main__":
    train()
