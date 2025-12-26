import pandas as pd

file_path = r"C:\Users\nbhav\Downloads\Weekly Market review _HK.xlsx"

try:
    xl = pd.ExcelFile(file_path)
    for sheet in xl.sheet_names:
        df = pd.read_excel(file_path, sheet_name=sheet).head(1)
        print(f"Sheet: {sheet}")
        print(f"Columns: {list(df.columns)}")
        print("-" * 20)
except Exception as e:
    print(f"Error: {e}")
