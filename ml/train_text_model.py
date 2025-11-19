# train_text_model.py
"""
Robust text-based classifier for NWMP PDF documents.

Place this file at: <repo_root>/ml/train_text_model.py
Ensure you have text files in: <repo_root>/ml/output/text/*.txt
If no text files exist, the script will try to extract text from PDFs in:
  <repo_root>/ml/data/pdfs/*.pdf

Outputs saved to:
  model/vectorizer.pkl
  model/text_model.pkl
"""

import re
import sys
from pathlib import Path
from collections import Counter
import joblib

# sklearn imports
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import numpy as np

# pdf extractor (optional; used only if no .txt present)
try:
    import pdfplumber
except Exception:
    pdfplumber = None


ROOT = Path(__file__).resolve().parent
TEXT_DIR = ROOT / "output" / "text"
PDF_DIR = ROOT / "data" / "pdfs"
MODEL_DIR = ROOT / "model"
MODEL_DIR.mkdir(parents=True, exist_ok=True)


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract text using pdfplumber if available."""
    if pdfplumber is None:
        raise RuntimeError("pdfplumber not installed or import failed. Install pdfplumber or create output/text files.")
    text_parts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text_parts.append(t)
    return "\n".join(text_parts)


def ensure_text_files():
    """If no text files exist, try to generate them by extracting PDFs from data/pdfs."""
    TEXT_DIR.mkdir(parents=True, exist_ok=True)
    txts = list(TEXT_DIR.glob("*.txt"))
    if txts:
        return txts

    # try to create from PDFs
    pdfs = list(PDF_DIR.glob("*.pdf"))
    if not pdfs:
        raise FileNotFoundError("No text files and no PDFs to extract. Put extracted .txt into output/text/ or PDFs into data/pdfs/")

    if pdfplumber is None:
        raise RuntimeError("No text files and pdfplumber not available to extract PDFs. Install pdfplumber or pre-extract text.")

    created = []
    for p in pdfs:
        try:
            txt = extract_text_from_pdf(p)
            out = TEXT_DIR / f"{p.stem}.txt"
            out.write_text(txt, encoding="utf-8")
            created.append(out)
            print(f"Extracted text -> {out}")
        except Exception as e:
            print(f"Failed to extract {p}: {e}")
    if not created:
        raise RuntimeError("Failed to extract any PDFs to text.")
    return created


def parse_numbers_from_text(text: str):
    """Return lists of floats found for each parameter using multiple regex patterns."""
    # make a lower-case normalized copy for robust matching
    text_low = text

    def find_nums(patterns):
        found = []
        for pat in patterns:
            for m in re.findall(pat, text_low, flags=re.IGNORECASE):
                # m could be a tuple (if groups). get last group if tuple
                v = m[-1] if isinstance(m, tuple) else m
                # strip trailing non numeric
                v = re.sub(r"[^\d\.\-]", "", v or "")
                try:
                    if v not in ("", ".", "-", "-."):
                        found.append(float(v))
                except ValueError:
                    pass
        return found

    bod = find_nums([r"bod[^\d\-\.]{0,6}([0-9]+(?:\.[0-9]+)?)",
                     r"biochemical oxygen demand[^\d\-\.]{0,6}([0-9]+(?:\.[0-9]+)?)"])
    do = find_nums([r"\bdo[^\d\-\.]{0,6}([0-9]+(?:\.[0-9]+)?)",
                    r"dissolved oxygen[^\d\-\.]{0,6}([0-9]+(?:\.[0-9]+)?)"])
    cod = find_nums([r"\bcod[^\d\-\.]{0,6}([0-9]+(?:\.[0-9]+)?)",
                     r"chemical oxygen demand[^\d\-\.]{0,6}([0-9]+(?:\.[0-9]+)?)"])
    ph = find_nums([r"\bph[^\d\-\.]{0,6}([0-9]+(?:\.[0-9]+)?)"])
    tds = find_nums([r"\btds[^\d\-\.]{0,6}([0-9]+(?:\.[0-9]+)?)",
                     r"total dissolved solids[^\d\-\.]{0,6}([0-9]+(?:\.[0-9]+)?)"])

    return {"bod": bod, "do": do, "cod": cod, "ph": ph, "tds": tds}


def compute_pollution_score(vals: dict) -> float:
    """Compute an interpretable pollution score from parsed numeric lists.

    The score is heuristic:
      - BOD: >6 severe (+2), >3 moderate (+1)
      - DO: <3 severe (+2), <5 moderate (+1)  (lower DO is worse)
      - COD: >250 severe (+1)
      - pH: outside [6.5, 8.5] small penalty (+0.5)
      - TDS: >2000 small penalty (+0.5)
    """
    score = 0.0
    bod = vals.get("bod", [])
    do = vals.get("do", [])
    cod = vals.get("cod", [])
    ph = vals.get("ph", [])
    tds = vals.get("tds", [])

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

    return float(score)


def label_from_score(score: float) -> str:
    """Map numeric score to label."""
    if score >= 3:
        return "POLLUTED"
    elif score >= 1.5:
        return "MODERATE"
    else:
        return "GOOD"


def load_documents_and_labels():
    txt_files = ensure_text_files()
    documents = []
    scores = []
    parsed_info = []

    for txt in sorted(txt_files):
        try:
            text = txt.read_text(encoding="utf-8")
        except Exception:
            text = ""
        vals = parse_numbers_from_text(text)
        score = compute_pollution_score(vals)
        label = label_from_score(score)

        documents.append(text)
        scores.append(score)
        parsed_info.append({"path": str(txt.name), "vals": vals, "score": score, "label": label})

    # create labels array
    labels = [p["label"] for p in parsed_info]

    # If we have only one unique class, create a fallback by splitting by score percentile
    unique_labels = set(labels)
    if len(unique_labels) == 1:
        print("⚠️  All detected labels are the same. Applying percentile-split fallback to create multiple classes.")
        # compute percentiles and re-label
        arr = np.array(scores)
        if len(arr) < 3:
            # not enough docs: fallback to splitting by median (two classes)
            median = np.median(arr) if len(arr) > 0 else 0.0
            labels = ["LOW" if s <= median else "HIGH" for s in arr]
            # map to our canonical labels
            labels = ["GOOD" if l == "LOW" else "POLLUTED" for l in labels]
        else:
            q33 = np.quantile(arr, 0.33)
            q66 = np.quantile(arr, 0.66)
            def q_label(s):
                if s <= q33:
                    return "GOOD"
                elif s <= q66:
                    return "MODERATE"
                else:
                    return "POLLUTED"
            labels = [q_label(s) for s in arr]
        # overwrite parsed_info labels
        for i, l in enumerate(labels):
            parsed_info[i]["label"] = l

    return documents, labels, parsed_info


def train():
    print("Loading documents and labels...")
    X, y, info = load_documents_and_labels()
    if len(X) == 0:
        raise RuntimeError("No documents found to train.")

    print("Sample parsed info (first 5):")
    for p in info[:5]:
        print(" -", p["path"], "score=", p["score"], "label=", p["label"])

    counter = Counter(y)
    print("Label distribution:", dict(counter))

    # vectorize
    vectorizer = TfidfVectorizer(stop_words="english", max_features=20000, ngram_range=(1,2))
    X_vec = vectorizer.fit_transform(X)

    # If after all we still have only one class (edge case), stop with a helpful message
    classes = list(set(y))
    if len(classes) == 1:
        raise ValueError(f"Training aborted: still only one class found ({classes[0]}). Provide more diverse documents or label manually.")

    # train/test split
    X_train, X_test, y_train, y_test = train_test_split(X_vec, y, test_size=0.2, random_state=42, stratify=y)

    # classifier
    clf = LogisticRegression(max_iter=2000)
    clf.fit(X_train, y_train)

    preds = clf.predict(X_test)
    print("\n--- Evaluation ---")
    print("Accuracy:", accuracy_score(y_test, preds))
    print(classification_report(y_test, preds))
    print("Confusion matrix:\n", confusion_matrix(y_test, preds))

    # save model + vectorizer
    joblib.dump(vectorizer, MODEL_DIR / "vectorizer.pkl")
    joblib.dump(clf, MODEL_DIR / "text_model.pkl")
    print(f"\nSaved vectorizer -> {MODEL_DIR/'vectorizer.pkl'}")
    print(f"Saved model      -> {MODEL_DIR/'text_model.pkl'}")


if __name__ == "__main__":
    try:
        train()
    except Exception as exc:
        print("ERROR:", exc)
        sys.exit(1)
