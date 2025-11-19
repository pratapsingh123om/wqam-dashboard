import pdfplumber
from pathlib import Path

def extract_pdf_text(pdf_path):
    all_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            txt = page.extract_text() or ""
            all_text.append(txt)
    return "\n".join(all_text)

if __name__ == "__main__":
    folder = Path("pdfs")
    output_folder = Path("output/text")
    output_folder.mkdir(parents=True, exist_ok=True)

    for pdf_file in folder.glob("*.pdf"):
        text = extract_pdf_text(pdf_file)
        out_file = output_folder / f"{pdf_file.stem}.txt"
        out_file.write_text(text, encoding="utf-8")
        print("Extracted:", out_file)
