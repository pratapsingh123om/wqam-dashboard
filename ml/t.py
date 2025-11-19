# ml/test_tabula.py
import tabula, sys
print("tabula-py:", getattr(tabula, "__version__", "unknown"))
try:
    tables = tabula.read_pdf(r"ml/data/Water_Quality_Canals_Sea_Water_Drains_STPs_2019.pdf",
                             pages=1, multiple_tables=True)
    print("tables found on page 1:", len(tables))
    if tables:
        import pandas as pd
        print("first table shape:", tables[0].shape)
        print(tables[0].head(3).to_string())
except Exception as e:
    print("tabula error:", e)
    sys.exit(2)
