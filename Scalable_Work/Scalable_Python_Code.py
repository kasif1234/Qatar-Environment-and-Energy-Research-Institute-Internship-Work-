#=================================================================================================
# Libraries:
# 1. pandas — to load, clean, and organize the CSV data into tables you can analyze easily.
# 2. matplotlib — to create the bar chart, box plots, and histogram plots.
# 3. scipy — to calculate the Pearson correlation and other statistical values.
# 4. numpy — to handle numerical operations efficiently behind the scenes.
# 5. seaborn — to make the plots look cleaner and more polished with less code.
#=================================================================================================
# Types of Plots:
# 1. Bar Chart: To compare the average values of a specific column across different categories.
# 2. Box Plot: To visualize the distribution of a numerical column and identify outliers
# 3. Histogram: To show the frequency distribution of a numerical column and understand its shape.
# 4. Pearson Correlation: To measure the strength and direction of the linear relationship between two numerical columns.
#=================================================================================================
# Graphs we can make now - Transcribed from 08/04/2026 Meeting:

# https://chatgpt.com/c/69dd0506-45f4-8392-9f9b-efca2313721a


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
print(f"\nColumns in the sheet: {df.columns.tolist()[0:10]}")  # Show first 10 columns for brevity

# Make dictionary: key -> column name
column_dict = {i: col for i, col in enumerate(df.columns, start=1)}

print("\nColumn dictionary:")
for k, v in column_dict.items():
    print(f"{k}: {v}")


for k, v in column_dict.items():
    if k == 3:
        for index, value in df[v].items():
            print(f"Row {index}: {value}")