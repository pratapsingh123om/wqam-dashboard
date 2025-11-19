import pdfplumber
import pandas as pd
from pathlib import Path

PDF_DIR = Path("pdfs")
OUT_DIR = Path("output")
OUT_DIR.mkdir(exist_ok=True)

OUTPUT_CSV = OUT_DIR / "combined.csv"


def extract_tables_from_pdf(pdf_path):
    print(f"📄 Processing: {pdf_path.name}")
    tables = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            extracted = page.extract_tables()
            for table in extracted:
                df = pd.DataFrame(table)
                # Remove empty rows
                df = df.dropna(how="all")
                if df.shape[1] > 1:
                    tables.append(df)
    print(f"   ✔ Extracted {len(tables)} tables")
    return tables


def main():
    pdf_files = list(PDF_DIR.glob("*.pdf"))
    if not pdf_files:
        print("❗ No PDFs found in ml/pdfs/")
        return

    all_frames = []

    for pdf in pdf_files:
        frames = extract_tables_from_pdf(pdf)
        for df in frames:
            all_frames.append(df)

    if not all_frames:
        print("❗ No tables found in any PDFs")
        return

    combined = pd.concat(all_frames, ignore_index=True)
    combined.to_csv(OUTPUT_CSV, index=False)
    print(f"✅ Combined CSV saved to: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
