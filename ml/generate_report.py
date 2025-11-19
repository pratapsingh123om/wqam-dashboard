#!/usr/bin/env python3
"""
generate_report.py
Usage:
  python generate_report.py         # reads all PDFs under data/pdfs and writes reports/report_<ts>.pdf
  python generate_report.py --input data/pdfs --out reports/report.pdf
"""

import argparse
from pathlib import Path
import re
import pdfplumber
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime, timezone
from sklearn.linear_model import LinearRegression
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

# -------------------------
# Config
# -------------------------
DEFAULT_INPUT = Path("data/pdfs")
DEFAULT_OUTPUT_DIR = Path("reports")
# color palette (user requested colourful)
PALETTE = ["#2b83ba", "#abdda4", "#fdae61", "#d7191c", "#984ea3", "#4daf4a"]

# -------------------------
# Utilities
# -------------------------
def extract_tables_pdfplumber(pdf_path):
    """Return list of dataframes extracted via pdfplumber tables."""
    dfs = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                try:
                    tables = page.extract_tables()
                except Exception:
                    tables = []
                for t in tables:
                    if t and len(t) > 1:
                        # header row then data
                        try:
                            df = pd.DataFrame(t[1:], columns=t[0])
                        except Exception:
                            df = pd.DataFrame(t)
                        dfs.append(df)
    except Exception as e:
        print(f"[WARN] pdfplumber failed for {pdf_path}: {e}")
    return dfs

def extract_text(pdf_path):
    """Concatenate all page text via pdfplumber."""
    all_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            all_text.append(page.extract_text() or "")
    return "\n".join(all_text)

def normalize_colname(c):
    return re.sub(r'[^0-9a-zA-Z]+', '_', str(c)).strip().lower()

# heuristics to map table columns to parameter names
PARAM_KEYS = {
    'bod': ['bod', 'biochemical', 'b.o.d'],
    'cod': ['cod', 'chemical'],
    'do': ['dissolved oxygen', 'd.o.', ' do ', r'\bdo\b'],
    'ph': ['ph'],
    'tds': ['tds', 'total dissolved'],
    'temp': ['temp', 'temperature'],
    'conductivity': ['conductivity', 'ec', 'umhos', 'µmhos']
}

def map_columns(df):
    """Rename likely parameter columns (best-effort)."""
    mapping = {}
    for c in df.columns:
        cc = str(c).lower()
        cc2 = normalize_colname(cc)
        for param, keys in PARAM_KEYS.items():
            for k in keys:
                if (isinstance(k, str) and k in cc) or (isinstance(k, str) and k in cc2):
                    mapping[c] = param
                    break
            if c in mapping:
                break
    return df.rename(columns=mapping)

def coerce_params(df: pd.DataFrame) -> pd.DataFrame:
    """
    Robust numeric coercion:
    - Convert every column to numeric after stripping non-numeric characters.
    - Collapse duplicate-named columns (same label) by taking first non-null value.
    """
    if df is None:
        return pd.DataFrame()
    df = df.copy()
    if df.empty:
        return df

    # 1) Coerce each column: convert to string, strip non-numeric chars, convert to numeric
    for col in list(df.columns):
        try:
            # convert to str first (handles mixed types), strip currency/units/letters
            s = df[col].astype(str).str.replace(r'[^0-9\.\-]', '', regex=True)
            s = pd.to_numeric(s, errors='coerce')
            df[col] = s
        except Exception:
            # fallback: try direct numeric coercion
            try:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            except Exception:
                # leave as-is (non-numeric)
                pass

    # 2) Collapse duplicate column labels (logical duplicates produced by map_columns)
    cols = list(df.columns)
    # Build dict name -> list of columns with that name (preserve original order)
    name_to_cols = {}
    for c in cols:
        name_to_cols.setdefault(c, []).append(c)
    # For names with multiple column occurrences (rare), collapse horizontally
    for name, col_list in list(name_to_cols.items()):
        # but ensure col_list actually references distinct positions (some tables may yield same labels)
        positions = [i for i, c in enumerate(cols) if c == name]
        if len(positions) > 1:
            # sub-DataFrame of the duplicate columns (by position)
            sub = df.iloc[:, positions]
            # first non-null across row (bfill then take first column)
            try:
                collapsed = sub.bfill(axis=1).iloc[:, 0]
            except Exception:
                collapsed = sub.iloc[:, 0]
            # assign collapsed to the (first) name
            df[name] = collapsed
            # drop all duplicate occurrences except the first positional column
            to_drop_positions = positions[1:]
            to_drop_labels = [cols[p] for p in to_drop_positions]
            # drop by positional columns (they share same label), use iloc index trick:
            df = df.drop(df.columns[to_drop_positions], axis=1, errors='ignore')
            # rebuild cols list
            cols = list(df.columns)

    return df

def fallback_regex_parse(text):
    """Extract numbers from the text using loose regex for parameters."""
    finds = {'bod':[], 'cod':[], 'do':[], 'ph':[], 'tds':[], 'temp':[], 'conductivity':[]}
    for m in re.finditer(r'BOD[^\d\-\.]{0,10}([0-9]{1,5}(?:\.[0-9]+)?)', text, re.I):
        finds['bod'].append(float(m.group(1)))
    for m in re.finditer(r'COD[^\d\-\.]{0,10}([0-9]{1,6}(?:\.[0-9]+)?)', text, re.I):
        finds['cod'].append(float(m.group(1)))
    for m in re.finditer(r'\bDO[^\d\-\.]{0,10}([0-9]{1,2}(?:\.[0-9]+)?)', text, re.I):
        finds['do'].append(float(m.group(1)))
    for m in re.finditer(r'\bPH[^\d\-\.]{0,10}([0-9]{1,2}(?:\.[0-9]+)?)', text, re.I):
        finds['ph'].append(float(m.group(1)))
    for m in re.finditer(r'Temp(?:erature)?[^\d\-\.]{0,10}([0-9]{1,3}(?:\.[0-9]+)?)', text, re.I):
        finds['temp'].append(float(m.group(1)))
    return finds

# -------------------------
# Report generator
# -------------------------
def build_combined_dataframe(pdf_files):
    """Return dataframe combining extracted tables and regex fallback for list of PDFs."""
    frames = []
    for p in pdf_files:
        tables = extract_tables_pdfplumber(p)
        if tables:
            for t in tables:
                t = map_columns(t)
                t = coerce_params(t)
                # ensure source column is present as string
                t['source_pdf'] = p.name
                frames.append(t)
        else:
            # fallback: parse by regex and create small dataframe
            text = extract_text(p)
            parsed = fallback_regex_parse(text)
            maxlen = max((len(v) for v in parsed.values()), default=0)
            rows = []
            for i in range(maxlen):
                row = {k: (parsed[k][i] if i < len(parsed[k]) else np.nan) for k in parsed}
                row['source_pdf'] = p.name
                rows.append(row)
            if rows:
                df = pd.DataFrame(rows)
                df = coerce_params(df)
                frames.append(df)
    if frames:
        big = pd.concat(frames, ignore_index=True, sort=False)
    else:
        big = pd.DataFrame()
    if not big.empty:
        big = coerce_params(big)  # final pass
    return big

def simple_forecast(series, steps=3):
    """Linear forecast using sklearn LinearRegression on index -> value"""
    s = series.dropna().reset_index(drop=True)
    if s.size < 3:
        return None
    X = np.arange(len(s)).reshape(-1,1)
    y = s.values.reshape(-1,1)
    model = LinearRegression().fit(X, y)
    xf = np.arange(len(s), len(s)+steps).reshape(-1,1)
    yf = model.predict(xf).ravel()
    return yf

def create_pdf_report(df, pdf_paths, out_pdf_path):
    out_pdf_path.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
    with PdfPages(out_pdf_path) as pdf:
        # Title page
        fig, ax = plt.subplots(figsize=(8.27, 11.69))
        ax.axis('off')
        ax.text(0.5, 0.92, "NWMP — Auto-generated Visual Report", ha='center', fontsize=20, weight='bold')
        ax.text(0.5, 0.88, f"Files analyzed: {len(pdf_paths)}", ha='center', fontsize=10)
        ax.text(0.5, 0.85, f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", ha='center', fontsize=9)
        y = 0.75
        for param in ['bod','cod','do','ph','tds','temp','conductivity']:
            if param in df.columns:
                s = pd.to_numeric(df[param], errors='coerce').dropna()
                if s.size>0:
                    ax.text(0.02, y, f"{param.upper():<12} n={s.size:<5} mean={s.mean():.2f}  median={s.median():.2f}  min={s.min():.2f}  max={s.max():.2f}", fontsize=10)
                else:
                    ax.text(0.02, y, f"{param.upper():<12} no data", fontsize=10)
            else:
                ax.text(0.02, y, f"{param.upper():<12} not found", fontsize=10)
            y -= 0.035
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)

        # Per-parameter histograms
        colors = PALETTE
        for i, param in enumerate(['bod','cod','do','ph','tds','temp','conductivity']):
            if param in df.columns:
                s = pd.to_numeric(df[param], errors='coerce').dropna()
                if s.size == 0:
                    continue
                fig, ax = plt.subplots(figsize=(8.27,5.5))
                ax.hist(s.values, bins=25, color=colors[i % len(colors)], edgecolor='k', alpha=0.9)
                ax.set_title(f"{param.upper()} distribution — n={s.size}", fontsize=14)
                ax.set_xlabel(param.upper())
                ax.set_ylabel("count")
                ax.grid(True, alpha=0.25)
                ax.text(0.98, 0.95, f"mean={s.mean():.2f}\nmedian={s.median():.2f}\nmin={s.min():.2f}\nmax={s.max():.2f}", transform=ax.transAxes, ha='right', va='top', bbox=dict(alpha=0.1))
                pdf.savefig(fig, bbox_inches='tight')
                plt.close(fig)

        # Pairwise scatter for parameters (if enough data)
        numeric_params = [p for p in ['bod','cod','do','ph','tds','temp','conductivity'] if p in df.columns and pd.to_numeric(df[p], errors='coerce').dropna().size >= 10]
        for i in range(len(numeric_params)):
            for j in range(i+1, len(numeric_params)):
                a = numeric_params[i]; b = numeric_params[j]
                sub = df[[a,b]].apply(pd.to_numeric, errors='coerce').dropna()
                if sub.shape[0] < 8:
                    continue
                fig, ax = plt.subplots(figsize=(8.27,5.5))
                ax.scatter(sub[a], sub[b], c=colors[(i+j) % len(colors)], alpha=0.8)
                ax.set_xlabel(a.upper()); ax.set_ylabel(b.upper())
                ax.set_title(f"{a.upper()} vs {b.upper()} (n={sub.shape[0]})")
                ax.grid(True, alpha=0.25)
                pdf.savefig(fig, bbox_inches='tight')
                plt.close(fig)

        # Timeseries by year if source_pdf contains year
        if 'source_pdf' in df.columns:
            # ensure string type (avoids .str accessor error)
            df['source_pdf'] = df['source_pdf'].astype(str)
            # extract year
            try:
                df['year'] = df['source_pdf'].str.extract(r'(\b19\d{2}\b|\b20\d{2}\b)')[0]
                df['year'] = pd.to_numeric(df['year'], errors='coerce')
            except Exception:
                df['year'] = np.nan

            if df['year'].notna().sum() > 0:
                for param in numeric_params:
                    ts_df = df.groupby('year')[param].mean().dropna()
                    if ts_df.shape[0] >= 2:
                        fig, ax = plt.subplots(figsize=(8.27,5.5))
                        ax.plot(ts_df.index.astype(int), ts_df.values, marker='o', linewidth=2)
                        ax.set_title(f"Yearly mean: {param.upper()}", fontsize=14)
                        ax.set_xlabel("Year")
                        ax.set_ylabel(param.upper())
                        ax.grid(True, alpha=0.25)
                        if ts_df.shape[0] >= 3:
                            yf = simple_forecast(ts_df, steps=3)
                            if yf is not None:
                                xf = np.arange(int(ts_df.index.max())+1, int(ts_df.index.max())+1+len(yf))
                                ax.plot(xf, yf, linestyle='--', marker='x', label='forecast')
                                ax.legend()
                        pdf.savefig(fig, bbox_inches='tight')
                        plt.close(fig)

        # Conclusions & prioritized actions
        summary_text = []
        if 'bod' in df.columns and pd.to_numeric(df['bod'], errors='coerce').dropna().size > 0 and pd.to_numeric(df['bod'], errors='coerce').mean() > 3:
            summary_text.append("Elevated BOD (organic load) — prioritize biological treatment upgrades and aeration.")
        if 'do' in df.columns and pd.to_numeric(df['do'], errors='coerce').dropna().size > 0 and pd.to_numeric(df['do'], errors='coerce').mean() < 5:
            summary_text.append("Low DO — increase aeration and reduce upstream organic discharges.")
        if 'cod' in df.columns and pd.to_numeric(df['cod'], errors='coerce').dropna().size > 0 and pd.to_numeric(df['cod'], errors='coerce').mean() > 50:
            summary_text.append("High COD — investigate industrial effluents; consider AOP for hard-to-destroy organics.")
        if not summary_text:
            summary_text.append("No immediate red flags detected by automated heuristics; inspect raw tables or provide Excel/CSV for best results.")

        fig, ax = plt.subplots(figsize=(8.27, 5.5))
        ax.axis('off')
        ax.text(0.02, 0.92, "Conclusions & Prioritized Actions", fontsize=16, weight='bold')
        for i, line in enumerate(summary_text):
            ax.text(0.02, 0.85 - i*0.07, f"- {line}", fontsize=11)
        ax.text(0.02, 0.35, "Next steps:", fontsize=12, weight='bold')
        nexts = [
            "1) Provide native Excel/CSV exports if possible (best data quality).",
            "2) Upload all year PDFs (2019..2023) for trend analysis & forecasting.",
            "3) For identified hotspots, run grab sample chemical analysis and upstream sampling."
        ]
        for i, n in enumerate(nexts):
            ax.text(0.02, 0.30 - i*0.05, n, fontsize=10)
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)

    return out_pdf_path

# -------------------------
# CLI
# -------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", "-i", default=str(DEFAULT_INPUT), help="Folder containing PDFs")
    parser.add_argument("--out", "-o", default=str(DEFAULT_OUTPUT_DIR / f"report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')}.pdf"), help="Output PDF report path")
    args = parser.parse_args()

    input_dir = Path(args.input)
    if not input_dir.exists():
        raise SystemExit(f"Input folder not found: {input_dir}")
    pdf_files = sorted(input_dir.glob("*.pdf"))
    if not pdf_files:
        raise SystemExit(f"No PDFs found in {input_dir}. Put your PDF files there and re-run.")

    print("Found PDFs:", [p.name for p in pdf_files])
    df = build_combined_dataframe(pdf_files)
    if df.empty:
        print("[WARN] No table-like data extracted from PDFs; the report will rely on regex parsing and text extraction.")
    else:
        print("Combined dataframe rows:", df.shape[0], "columns:", df.shape[1])

    out = create_pdf_report(df, pdf_files, Path(args.out))
    print("Report generated:", out)

if __name__ == "__main__":
    main()
