import pandas as pd
from pathlib import Path
import re

IN_FILE = Path("output/combined.csv")
OUT_FILE = Path("output/cleaned.csv")


def is_numeric(val):
    try:
        float(val)
        return True
    except:
        return False


def clean_data():
    df = pd.read_csv(IN_FILE, header=None)

    # 1. use first row as header if it looks like text headers
    if df.iloc[0].astype(str).str.contains("[A-Za-z]").any():
        df.columns = df.iloc[0]
        df = df[1:]

    # Normalize column names
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(r"[^a-z0-9]+", "_", regex=True)
    )

    # Keep only numeric-like columns
    numeric_cols = []
    for col in df.columns:
        sample_vals = df[col].astype(str).head(20)
        numeric_count = sum(sample_vals.apply(is_numeric))
        if numeric_count >= 5:  # 5 numeric samples → numeric column
            numeric_cols.append(col)

    if not numeric_cols:
        raise ValueError("❗ No numeric columns detected in cleaned dataset!")

    clean_df = df[numeric_cols].apply(pd.to_numeric, errors="coerce")
    clean_df = clean_df.dropna(how="all")

    clean_df.to_csv(OUT_FILE, index=False)
    print(f"✅ Cleaned dataset saved to: {OUT_FILE}")


if __name__ == "__main__":
    clean_data()
