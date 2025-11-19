import re
from pathlib import Path
import pdfplumber

def extract_text(pdf_path):
    full = []
    with pdfplumber.open(pdf_path) as pdf:
        for p in pdf.pages:
            text = p.extract_text() or ""
            full.append(text)
    return "\n".join(full)

def analyze(text):
    findings = {}

    findings["BOD"] = re.findall(r"BOD[^0-9]*([\d\.]+)", text, re.I)
    findings["COD"] = re.findall(r"COD[^0-9]*([\d\.]+)", text, re.I)
    findings["DO"]  = re.findall(r"DO[^0-9]*([\d\.]+)",  text, re.I)

    # simple pollution scoring
    score = 0
    for v in findings["BOD"]:
        if float(v) > 3:
            score += 1
    for v in findings["DO"]:
        if float(v) < 5:
            score += 1

    findings["pollution_score"] = score
    findings["status"] = (
        "POLLUTED" if score >= 2 else "MODERATE" if score == 1 else "GOOD"
    )

    return findings

if __name__ == "__main__":
    pdf_file = "pdfs/Water_Quality_Canals_Sea_Water_Drains_STPs_2019.pdf"
    text = extract_text(pdf_file)
    result = analyze(text)
    print(result)
