# report_generator.py
"""
Generate a multi-page PDF report (summary + plots + treatment suggestions)
for each PDF in data/pdfs/.

Usage:
  python report_generator.py            # process all PDFs once
  python report_generator.py --watch    # optional: watch folder for new PDFs (requires watchdog)
"""

import re
import sys
import argparse
from pathlib import Path
import pdfplumber
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime
import textwrap

ROOT = Path(__file__).resolve().parent
PDF_DIR = ROOT / "data" / "pdfs"
TEXT_DIR = ROOT / "output" / "text"
REPORT_DIR = ROOT / "output" / "reports"
TEXT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

# ---------- Helpers: parsing ----------
def parse_numbers_from_text(text: str):
    """Return numeric lists for common water params found in free-form text."""
    def find_nums(patterns):
        found = []
        for pat in patterns:
            for m in re.findall(pat, text, flags=re.IGNORECASE):
                v = m[-1] if isinstance(m, tuple) else m
                v = re.sub(r"[^\d\.\-]", "", v or "")
                try:
                    if v not in ("", ".", "-", "-."):
                        found.append(float(v))
                except ValueError:
                    pass
        return found

    bod = find_nums([r"bod[^\d\-\.]{0,6}([0-9]+(?:\.[0-9]+)?)", r"biochemical oxygen demand[^\d\-\.]{0,6}([0-9]+(?:\.[0-9]+)?)"])
    do  = find_nums([r"\bdo[^\d\-\.]{0,6}([0-9]+(?:\.[0-9]+)?)", r"dissolved oxygen[^\d\-\.]{0,6}([0-9]+(?:\.[0-9]+)?)"])
    cod = find_nums([r"\bcod[^\d\-\.]{0,6}([0-9]+(?:\.[0-9]+)?)", r"chemical oxygen demand[^\d\-\.]{0,6}([0-9]+(?:\.[0-9]+)?)"])
    ph  = find_nums([r"\bph[^\d\-\.]{0,6}([0-9]+(?:\.[0-9]+)?)"])
    tds = find_nums([r"\btds[^\d\-\.]{0,6}([0-9]+(?:\.[0-9]+)?)", r"total dissolved solids[^\d\-\.]{0,6}([0-9]+(?:\.[0-9]+)?)"])
    return {"bod": bod, "do": do, "cod": cod, "ph": ph, "tds": tds}

def extract_tables_from_pdf(pdf_path: Path):
    """Use pdfplumber's table extraction; return list of dataframes."""
    dfs = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            try:
                tables = page.extract_tables()
            except Exception:
                tables = None
            if not tables:
                continue
            for table in tables:
                # table is list[list], attempt header -> rows
                if not table or len(table) < 2:
                    continue
                header = table[0]
                rows = table[1:]
                # normalize header: replace None with col index
                header = [str(h).strip() if h not in (None, "") else f"col_{i}" for i, h in enumerate(header)]
                df = pd.DataFrame(rows, columns=header)
                dfs.append(df)
    return dfs

def extract_text(pdf_path: Path):
    t = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            s = page.extract_text()
            if s:
                t.append(s)
    return "\n".join(t)

# ---------- Scoring & labeling ----------
def compute_pollution_score(vals: dict) -> float:
    score = 0.0
    bod = vals.get("bod", [])
    do = vals.get("do", [])
    cod = vals.get("cod", [])
    ph = vals.get("ph", [])
    tds = vals.get("tds", [])

    if bod:
        if max(bod) > 6: score += 2
        elif max(bod) > 3: score += 1
    if do:
        if min(do) < 3: score += 2
        elif min(do) < 5: score += 1
    if cod and max(cod) > 250: score += 1
    if ph:
        p = np.mean(ph)
        if p < 6.5 or p > 8.5: score += 0.5
    if tds and max(tds) > 2000: score += 0.5
    return float(score)

def score_to_label(score: float) -> str:
    if score >= 3: return "POLLUTED"
    if score >= 1.5: return "MODERATE"
    return "GOOD"

# ---------- Treatment suggestions ----------
def recommended_treatments(stats: dict):
    recs = []
    bod_mean = stats.get("bod_mean")
    do_mean = stats.get("do_mean")
    cod_mean = stats.get("cod_mean")
    tds_mean = stats.get("tds_mean")
    ph_mean  = stats.get("ph_mean")

    if bod_mean is not None:
        if bod_mean > 30:
            recs.append("High-strength organics: anaerobic digestion + advanced biological processes (UASB/anaerobic + sequencing batch/activated sludge), followed by polishing.")
        elif bod_mean > 6:
            recs.append("Elevated BOD: activated sludge / aerated biological treatment, improve primary settling and return activated sludge control.")
        elif bod_mean > 3:
            recs.append("Moderate BOD: conventional biological treatment (SBR or aeration basins).")

    if do_mean is not None and do_mean < 5:
        recs.append("Low DO: increase aeration (diffused aeration), check mixing and organic load; consider fine-bubble diffusers or blowers upgrade.")

    if cod_mean is not None and cod_mean > 500:
        recs.append("High COD: consider advanced oxidation processes (AOP), Fenton/ozonation, or chemical pre-treatment for industrial loads.")

    if tds_mean is not None and tds_mean > 1500:
        recs.append("High TDS: membrane processes (RO / nano-filtration) or evaporative concentration; manage brine / concentrate disposal carefully.")

    if ph_mean is not None and (ph_mean < 6.5 or ph_mean > 8.5):
        recs.append("pH out of range: pH correction (acid/alkali dosing) before biological stages.")

    if not recs:
        recs.append("Primary + secondary biological treatment with regular monitoring; maintain adequate aeration and sludge handling.")

    return recs

# ---------- Plot helpers ----------
def plot_hist(series, title, ax=None):
    if ax is None:
        ax = plt.gca()
    ax.hist(series.dropna(), bins=20)
    ax.set_title(title)
    ax.set_xlabel("Value")
    ax.set_ylabel("Count")

def plot_bar_means(stats: dict, ax=None):
    if ax is None:
        ax = plt.gca()
    keys = []
    vals = []
    for k in ("bod_mean", "do_mean", "cod_mean", "ph_mean", "tds_mean"):
        v = stats.get(k)
        if v is not None and not np.isnan(v):
            keys.append(k.replace("_mean","").upper())
            vals.append(v)
    if not vals:
        ax.text(0.5,0.5,"No numeric means found", ha='center')
        return
    ax.bar(keys, vals)
    ax.set_title("Mean Parameter Values")
    ax.set_ylabel("Mean value")

def render_dataframe_as_table(df, ax=None, max_rows=20):
    if ax is None:
        ax = plt.gca()
    ax.axis("off")
    # limit rows
    show_df = df.head(max_rows).fillna("")
    table = ax.table(cellText=show_df.values, colLabels=show_df.columns, loc='center', cellLoc="left")
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, 1.2)

# ---------- Main per-file processing ----------
def process_pdf(pdf_path: Path):
    print("Processing:", pdf_path.name)
    text = extract_text(pdf_path)
    if text.strip():
        out_text = TEXT_DIR / f"{pdf_path.stem}.txt"
        out_text.write_text(text, encoding="utf-8")

    # parse numbers from text
    parsed = parse_numbers_from_text(text)
    # try to extract tables and parse numeric columns too
    tables = extract_tables_from_pdf(pdf_path)
    extra_vals = {"bod": [], "do": [], "cod": [], "ph": [], "tds": []}
    table_dfs = []
    for tdf in tables:
        # attempt to coerce numeric columns and search for typical parameter column names
        table_dfs.append(tdf)
        # lowercase column names to find matches
        for col in tdf.columns:
            col_lower = col.lower()
            if any(x in col_lower for x in ("bod","b.o.d","biochemical")):
                extra_vals["bod"].extend(pd.to_numeric(tdf[col], errors="coerce").dropna().tolist())
            if any(x in col_lower for x in ("do","dissolved")):
                extra_vals["do"].extend(pd.to_numeric(tdf[col], errors="coerce").dropna().tolist())
            if any(x in col_lower for x in ("cod","chemical")):
                extra_vals["cod"].extend(pd.to_numeric(tdf[col], errors="coerce").dropna().tolist())
            if "ph" == col_lower.strip() or "ph " in col_lower or "pH" in col:
                extra_vals["ph"].extend(pd.to_numeric(tdf[col], errors="coerce").dropna().tolist())
            if any(x in col_lower for x in ("tds","total dissolved")):
                extra_vals["tds"].extend(pd.to_numeric(tdf[col], errors="coerce").dropna().tolist())

    # merge parsed with extra
    merged = {}
    for k in ("bod","do","cod","ph","tds"):
        merged[k] = list(parsed.get(k, [])) + list(extra_vals.get(k, []))

    # compute basic stats
    stats = {}
    for k in ("bod","do","cod","ph","tds"):
        arr = np.array(merged[k], dtype=float) if merged[k] else np.array([])
        stats[f"{k}_count"] = int(arr.size)
        stats[f"{k}_mean"] = float(np.nanmean(arr)) if arr.size else None
        stats[f"{k}_min"] = float(np.nanmin(arr)) if arr.size else None
        stats[f"{k}_max"] = float(np.nanmax(arr)) if arr.size else None

    # pollution score from text values only (conservative) + label
    score = compute_pollution_score(parsed)
    label = score_to_label(score)

    # create report PDF
    report_path = REPORT_DIR / f"{pdf_path.stem}_report.pdf"
    with PdfPages(report_path) as pdf:
        # Title page
        plt.figure(figsize=(8.5, 11))
        plt.axis("off")
        plt.text(0.5, 0.85, f"Water Quality Report", ha='center', fontsize=20, weight="bold")
        plt.text(0.5, 0.78, pdf_path.name, ha='center', fontsize=12)
        plt.text(0.5, 0.72, f"Generated: {datetime.utcnow().isoformat()} UTC", ha='center', fontsize=8)
        plt.text(0.1, 0.6, "Summary:", fontsize=12, weight="bold")
        summ = [
            f"Parsed numeric counts: BOD={stats['bod_count']}, DO={stats['do_count']}, COD={stats['cod_count']}, pH={stats['ph_count']}, TDS={stats['tds_count']}",
            f"Score (heuristic): {score} -> {label}",
        ]
        plt.text(0.1, 0.56, "\n".join(summ), fontsize=10)
        plt.text(0.1, 0.3, "Top plain-text extract (first 4000 chars):", fontsize=10, weight="bold")
        excerpt = (text or "")[:4000]
        # wrap text
        wrapped = "\n".join(textwrap.wrap(excerpt, width=120))
        plt.text(0.1, 0.28, wrapped, fontsize=8, va='top')
        pdf.savefig()
        plt.close()

        # Parameter means and bar chart
        plt.figure(figsize=(8.5, 11))
        ax = plt.subplot(111)
        plot_bar_means(stats, ax=ax)
        pdf.savefig()
        plt.close()

        # Individual histograms for parameters (if present)
        for param in ("bod","do","cod","ph","tds"):
            arr = np.array(merged[param], dtype=float) if merged[param] else np.array([])
            if arr.size:
                plt.figure(figsize=(8.5, 5))
                plot_hist(pd.Series(arr), f"{param.upper()} distribution (n={arr.size})")
                pdf.savefig()
                plt.close()

        # Tables page (show first table if exists)
        if table_dfs:
            for tdf in table_dfs[:3]:
                plt.figure(figsize=(8.5, 11))
                render_dataframe_as_table(tdf, plt.gca(), max_rows=25)
                pdf.savefig()
                plt.close()

        # Treatments page
        plt.figure(figsize=(8.5, 11))
        plt.axis("off")
        plt.text(0.5, 0.92, "Recommended Treatment Actions", ha='center', fontsize=16, weight="bold")
        recs = recommended_treatments({
            "bod_mean": stats.get("bod_mean"),
            "do_mean": stats.get("do_mean"),
            "cod_mean": stats.get("cod_mean"),
            "tds_mean": stats.get("tds_mean"),
            "ph_mean": stats.get("ph_mean"),
        })
        y = 0.82
        for r in recs:
            wrapped = "\n".join(textwrap.wrap(r, width=100))
            plt.text(0.1, y, f"• {wrapped}", fontsize=10)
            y -= 0.09
        pdf.savefig()
        plt.close()

    print("Report generated:", report_path)
    return report_path, stats, label

# ---------- CLI ----------
def main(watch=False):
    if not PDF_DIR.exists():
        print("Create pdfs folder:", PDF_DIR)
        return

    pdf_files = sorted(PDF_DIR.glob("*.pdf"))
    if not pdf_files:
        print("No PDFs found in", PDF_DIR)
        return

    for p in pdf_files:
        try:
            process_pdf(p)
        except Exception as e:
            print("Error processing", p.name, e)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--watch", action="store_true", help="watch data/pdfs for new files (requires watchdog)")
    args = parser.parse_args()
    if args.watch:
        # optional watcher implementation using watchdog (install watchdog)
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler
            class Handler(FileSystemEventHandler):
                def on_created(self, event):
                    path = Path(event.src_path)
                    if path.suffix.lower() == ".pdf":
                        print("New PDF detected:", path.name)
                        try:
                            process_pdf(path)
                        except Exception as e:
                            print("Error:", e)
            obs = Observer()
            evt = Handler()
            obs.schedule(evt, str(PDF_DIR), recursive=False)
            obs.start()
            print("Watching", PDF_DIR, "for new PDFs. Ctrl-C to stop.")
            try:
                while True:
                    import time; time.sleep(1)
            except KeyboardInterrupt:
                obs.stop()
            obs.join()
        except ImportError:
            print("watchdog not installed. Run without --watch or install watchdog (pip install watchdog).")
            sys.exit(1)
    else:
        main()
