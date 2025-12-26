import pandas as pd

file_path = r"C:\Users\nbhav\Downloads\Weekly Market review _HK.xlsx"
output_path = r"d:\AntiGravity\stock_tracker\backend\excel_structure.txt"

try:
    xl = pd.ExcelFile(file_path)
    with open(output_path, "w") as f:
        for sheet in xl.sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet).head(1)
            f.write(f"Sheet: {sheet}\n")
            f.write(f"Columns: {list(df.columns)}\n")
            f.write("-" * 50 + "\n")
    print(f"Structure written to {output_path}")
except Exception as e:
    print(f"Error: {e}")
