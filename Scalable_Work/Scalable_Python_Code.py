# 1. pandas — to load, clean, and organize the CSV data into tables you can analyze easily.
# 2. matplotlib — to create the bar chart, box plots, and histogram plots.
# 3. scipy — to calculate the Pearson correlation and other statistical values.
# 4. numpy — to handle numerical operations efficiently behind the scenes.
# 5. seaborn — to make the plots look cleaner and more polished with less code.

import pandas as pd

file_path = "Complete Extraction Results.xlsx"

# Open the Excel file
excel_file = pd.ExcelFile(file_path, engine="openpyxl")

# Show all sheet names
print("Available sheets:")
for i, sheet in enumerate(excel_file.sheet_names, start=1):
    print(f"{i}. {sheet}")

# Select a sheet by number
choice = int(input("Enter sheet number: "))
selected_sheet = excel_file.sheet_names[choice - 1]

# Read that sheet
df = pd.read_excel(file_path, sheet_name=selected_sheet, engine="openpyxl", header=1)

print(f"\nLoaded sheet: {selected_sheet}")
print(df.head())
print(f"\nColumns in the sheet: {df.columns.tolist()}")