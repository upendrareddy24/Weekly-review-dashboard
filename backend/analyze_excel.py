import pandas as pd
import sys

file_path = r"C:\Users\nbhav\Downloads\Weekly Market review _HK.xlsx"

try:
    xl = pd.ExcelFile(file_path)
    print(f"Sheets: {xl.sheet_names}")
    for sheet in xl.sheet_names:
        df = pd.read_excel(file_path, sheet_name=sheet).head(5)
        print(f"\n--- Sheet: {sheet} ---")
        print(df.columns.tolist())
        print(df.head(2))
except Exception as e:
    print(f"Error: {e}")
