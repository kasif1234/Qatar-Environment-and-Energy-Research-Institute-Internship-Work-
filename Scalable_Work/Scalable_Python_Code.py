import pandas as pd
from pathlib import Path

# =========================
# 1. File settings
# =========================
file_path = r"Scalable_Work\Complete Extraction Results.xlsx"  # change this
sheet_name = 0  # use 0 for first sheet, or put sheet name like "Sheet1"

# =========================
# 2. Load Excel file
# =========================
try:
    if not Path(file_path).exists():
        raise FileNotFoundError(f"Excel file not found: {file_path}")

    df = pd.read_excel(file_path, sheet_name=sheet_name)

except Exception as e:
    print(f"Error reading Excel file: {e}")
    raise

# =========================
# 3. Clean column names
# =========================
df.columns = [str(col).strip() for col in df.columns]

# =========================
# 4. Create indexed column table
# =========================
column_info = pd.DataFrame({
    "column_index": range(len(df.columns)),
    "column_name": df.columns
})

# =========================
# 5. Create useful mappings
# =========================
index_to_name = dict(enumerate(df.columns))
name_to_index = {name: idx for idx, name in enumerate(df.columns)}

# =========================
# 6. Display results
# =========================
print("\nColumns ready for analysis:\n")
print(column_info.to_string(index=False))

print("\nIndex to Name mapping:")
print(index_to_name)

print("\nName to Index mapping:")
print(name_to_index)

# =========================
# 7. Example usage
# =========================
# Access column by index
example_index = 0
print(f"\nColumn at index {example_index}: {index_to_name[example_index]}")

# Access data from a specific column
selected_column = index_to_name[example_index]
print(f"\nFirst 5 values from '{selected_column}':")
print(df[selected_column].head())

# =========================
# 8. Optional: save column info
# =========================
column_info.to_csv("column_info.csv", index=False)
print("\nColumn info saved as 'column_info.csv'")