# pdf_to_csv_and_combine.py
# Place this file in ml/ and run: python pdf_to_csv_and_combine.py
import os
from pathlib import Path
import pandas as pd
import tabula
import traceback

# optional import for fallback; install camelot if you want
try:
    import camelot
    _have_camelot = True
except Exception:
    _have_camelot = False

RAW_DIR = Path("data/raw")
PARSED_DIR = Path("data/parsed")
OUT_DIR = Path("data")
PARSED_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR.mkdir(parents=True, exist_ok=True)

def try_tabula(pdf_path):
    # try lattice then stream
    for mode in ("lattice", "stream"):
        try:
            dfs = tabula.read_pdf(str(pdf_path), pages="all", multiple_tables=True, lattice=(mode=="lattice"))
            if dfs and len(dfs) > 0:
                return dfs
        except Exception as e:
            print(f"tabula {mode} failed for {pdf_path.name} -> {e}")
    return []

def try_camelot(pdf_path):
    if not _have_camelot:
        return []
    try:
        tables = camelot.read_pdf(str(pdf_path), pages="all", flavor="stream")  # try stream first
        if tables and len(tables) > 0:
            return [t.df for t in tables]
        # try lattice
        tables = camelot.read_pdf(str(pdf_path), pages="all", flavor="lattice")
        return [t.df for t in tables] if tables else []
    except Exception as e:
        print(f"camelot failed for {pdf_path.name} -> {e}")
        return []

def sanitize_df(df):
    # trim whitespace column names
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    # drop fully empty columns
    df = df.loc[:, ~(df.isna().all())]
    return df

def parse_pdf(pdf_path):
    try:
        dfs = try_tabula(pdf_path)
        if not dfs:
            dfs = try_camelot(pdf_path)
        parsed = []
        for i, df in enumerate(dfs):
            try:
                df = sanitize_df(df)
                if df.shape[0] >= 1 and df.shape[1] >= 2:
                    parsed.append(df)
            except Exception as e:
                print("skip table", pdf_path.name, i, e)
        return parsed
    except Exception as e:
        print("parse error:", pdf_path, e)
        traceback.print_exc()
        return []

def normalize_columns_and_keep(df):
    # quick mapping for wastewater STP tables (common params)
    mapping = {}
    for c in df.columns:
        lc = c.lower()
        if "bod" in lc:
            mapping[c] = "bod"
        elif "cod" in lc:
            mapping[c] = "cod"
        elif "tss" in lc or "suspended" in lc:
            mapping[c] = "tss"
        elif "ph" == lc or "ph " in lc or " ph" in lc:
            mapping[c] = "ph"
        elif "do" in lc and "d.o" not in lc:  # careful
            mapping[c] = "do"
        elif "tds" in lc:
            mapping[c] = "tds"
        elif "temp" in lc or "temperature" in lc:
            mapping[c] = "temp"
        elif "flow" in lc:
            mapping[c] = "flow"
        elif "site" in lc or "station" in lc or "location" in lc or "plant" in lc or "stp" in lc:
            mapping[c] = "site"
    if mapping:
        df = df.rename(columns=mapping)
    # Keep mapped columns + numeric-looking columns + site columns
    keep = [c for c in df.columns if c in mapping.values() or 'site' in c.lower() or pd.api.types.is_numeric_dtype(df[c])]
    if not keep:
        # fallback: keep all
        keep = list(df.columns)
    return df[keep]

def coerce_numeric_cols(df):
    for c in df.columns:
        # leave site column if non-numeric
        if 'site' in c.lower() or 'station' in c.lower():
            continue
        # remove commas, non-numeric characters, percent signs etc
        s = df[c].astype(str).str.replace(r'[^0-9\.\-]', '', regex=True)
        df[c] = pd.to_numeric(s, errors='coerce')
    return df

def main():
    pdfs = sorted(RAW_DIR.glob("*.pdf"))
    if not pdfs:
        print("No PDFs found in", RAW_DIR)
        return
    frames = []
    for pdf in pdfs:
        print("Parsing", pdf.name)
        tables = parse_pdf(pdf)
        if not tables:
            print("  no tables parsed from", pdf.name)
            continue
        for i, t in enumerate(tables):
            t = normalize_columns_and_keep(t)
            t['source_pdf'] = pdf.name
            # try to save parsed csv for manual inspection
            out_csv = PARSED_DIR / f"{pdf.stem}_table_{i+1}.csv"
            try:
                t.to_csv(out_csv, index=False)
            except Exception as e:
                print("  can't write parsed csv", out_csv, e)
            # coerce numeric where possible
            t = coerce_numeric_cols(t)
            frames.append(t)
    if not frames:
        print("No tables successfully parsed. Inspect data/parsed for raw outputs.")
        return
    combined = pd.concat(frames, ignore_index=True, sort=False)
    # final cleanup: drop duplicates and empty rows
    combined = combined.drop_duplicates().dropna(how='all')
    combined.to_csv(OUT_DIR / "combined.csv", index=False)
    print("WROTE:", OUT_DIR / "combined.csv", "shape:", combined.shape)
    print("Parsed CSVs are in", PARSED_DIR)

if __name__ == "__main__":
    main()
