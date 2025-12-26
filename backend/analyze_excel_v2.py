import pandas as pd
import json

file_path = r"C:\Users\nbhav\Downloads\Weekly Market review _HK.xlsx"

try:
    xl = pd.ExcelFile(file_path)
    structure = {}
    for sheet in xl.sheet_names:
        df = pd.read_excel(file_path, sheet_name=sheet).head(1)
        structure[sheet] = df.columns.tolist()
    
    print(json.dumps(structure, indent=2))
except Exception as e:
    print(f"Error: {e}")
