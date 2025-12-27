import pandas as pd
EXCEL_PATH = r"C:\Users\nbhav\Downloads\Weekly Market review _HK.xlsx"
xl = pd.ExcelFile(EXCEL_PATH)
relevant_sheets = ['3Swing-HK', '4POS-BO-HK', '1 week swings', 'Week48']
with open('d:/AntiGravity/stock_tracker/backend/inspect_cols.txt', 'w') as f:
    for sheet in relevant_sheets:
        if sheet in xl.sheet_names:
            df = pd.read_excel(EXCEL_PATH, sheet_name=sheet, nrows=5)
            f.write(f"Sheet: {sheet}\n")
            f.write(f"Columns: {df.columns.tolist()}\n")
            f.write(f"First Row: {df.iloc[0].tolist()}\n")
            f.write("-" * 40 + "\n")
print("Inspection complete. Check inspect_cols.txt")
