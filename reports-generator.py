# === SCRIPT: sales report generation from multiple source files ===
import pandas as pd
from pathlib import Path
from cleaner import file_cleaner


# Generates 3 CSV reports from an already-merged dataframe.
#     - reportSellersDetailed: sales by seller and category (sum, count, max)
#     - reportMonthly: sales grouped by category and month
#     - reportSellers: pivot table seller x category, with totals
def generate_reports(df, name_column, group_column, value_column, quantity_column, total_column, total_exist, date_column=None):

    # If the file doesn't have a Total column, calculate it: price * quantity
    if total_exist == False:
        df[total_column] = df[value_column] * df[quantity_column]

    # If a date column exists, derive Month and Year for grouping reports
    if date_column:
        df[date_column] = pd.to_datetime(df[date_column])
        df["Month"] = df[date_column].dt.month
        df["Year"] = df[date_column].dt.year

    # Report 1: sales detail by (seller, category) -> sum, sale count, max sale
    reportSellersDetailed = df.groupby([name_column, group_column])[value_column].agg(["sum", "count", "max"])
    reportSellersDetailed = reportSellersDetailed.sort_values(by=[name_column, "sum"], ascending=False)
    reportSellersDetailed.to_csv("Detailed_Sellers_Report.csv")

    # Report 2: sales by (category, month) -> monthly trend
    reportMonthly = df.groupby([group_column, "Month"])[value_column].agg(["sum", "count", "max"])
    reportMonthly = reportMonthly.sort_values(by=["Month", "sum"], ascending=False)
    reportMonthly.to_csv("Monthly_Report.csv")

    # Report 3: pivot table seller x category, with "All" row/column totals
    reportSellers = pd.pivot_table(df, index=name_column, columns=group_column, values=value_column, aggfunc="sum", margins=True, fill_value=0)
    reportSellers.to_csv("Sellers_Report.csv", index=True)

    
    return reportMonthly, reportSellers, reportSellersDetailed

# For each file pair, decide which column to use as the merge key:
# - 1 shared column -> confirm it, or ask for a manual one
# - 2+ shared columns -> user picks one by number from a list
def choose_column_merge(mutual_cols, cols_current, cols_next):

    if len(mutual_cols) == 1:
        while True:
            confirmation = input(f"There is 1 mutual column.\n Do you want to use '{mutual_cols[0]}'? S/N ").upper()
            if confirmation.startswith("S"):
                chosen_column = mutual_cols[0]
                break
            elif confirmation.startswith("N"):
                while True:
                    print("Insert 0 to close.")
                    column_given = input("Insert the column you want to use ")
                    if column_given in cols_current and column_given in cols_next:
                        chosen_column = column_given
                        break
                    elif column_given == "0":
                        chosen_column = None
                        break
                    else:
                        print(f"'{column_given}' was not found in both files. Please check the spelling or try a different column.")
                break
            else:
                print("Invalid character, use S or N.")
            


    elif len(mutual_cols) >= 2:
        print("There are more than 1 mutual columns.")
        for j, col_name in enumerate(mutual_cols):
            print(j+1, " - ", col_name, "\n",)
        
        while True:
            try:
                print("Insert 0 to close.")
                selected_number = int(input("Enter the number of the column to use "))

            except ValueError:
                print("It can't contain letters. \nTry again\n")
                continue

            if selected_number == 0:
                chosen_column = None
                break
            elif selected_number > 0 and selected_number <= len(mutual_cols):
                confirmation = input("Are you sure you want to use this column? S/N").upper()
                if confirmation.startswith("S"):
                    chosen_column = mutual_cols[selected_number-1]
                    break
                else:
                    continue
            else:
                print("Invalid position")

    return chosen_column

# Asks how many files the user will upload, validates it's an integer
while True:
    try:
        print("Insert 0 to exit.")
        file_amount= int(input("Insert number of files "))
    except ValueError:
        print("It can't contain letters. \nTry again\n")
        continue

    if file_amount == 0:
        print("Exiting program.")
        break
    elif file_amount <0:
        print("Insert a valid amount! \nTry again\n")
    else:
        file_confirmation = input(f"Are you sure you want {file_amount} files? Press S/N ").upper()
        if file_confirmation.startswith("S"):
            break

file_list = []
print(
    "\nImportant: Upload files in the exact order of correlation. Incorrect sequencing won't be able to process your files correctly.\n",
    "Example sequence: sales.csv → sellers.xlsx → products.csv")
# For each file: checks it exists on disk, cleans it via file_cleaner(), stores the clean path
for i in range(0, file_amount):
    while True:
        file_name = input(f"Insert {i+1} file's name ")
        path_check = Path(file_name)
        if path_check.is_file():
            clean_file_name = file_cleaner(file_name, f"clean_{file_name}")
            file_list.append(clean_file_name)
            break
        else:
            print("File doesn't exist. \nTry again.\n")

dataFrame_list = []
# Loads each already-cleaned file into a DataFrame based on its extension
for i in range(0, file_amount):
    if file_list[i].endswith(".csv"):
        dataFrame_item = pd.read_csv(file_list[i])
        dataFrame_list.append(dataFrame_item)
    else:
        dataFrame_item = pd.read_excel(file_list[i])
        dataFrame_list.append(dataFrame_item)
    

invalid_pair = None
valid_merge = True
mutual_columns = []
# Detects shared columns between each pair of consecutive files
# If a pair has zero shared columns, they can't be merged -> invalid_pair
for i in range(0, file_amount-1):
    shared_cols = dataFrame_list[i].columns.intersection(dataFrame_list[i+1].columns)
    if not shared_cols.empty:
        mutual_columns.append(shared_cols)
    else:
        invalid_pair = i, i+1
        valid_merge = False
        break



merge_keys = []

for i, mutual_cols in enumerate(mutual_columns):
    result = choose_column_merge(mutual_cols ,dataFrame_list[i].columns, dataFrame_list[i+1].columns)
    if result is None:
        valid_merge = False
        break
    else:
        merge_keys.append(result)


# WIP: pending dynamic column selection
# TODO: temporarily disabled — pending replacement with dynamic inputs
# while True:
#     name_column = input("Insert name's column ")
#     if name_column in df.columns:
#         break
#     elif name_column == "":
#         print("It can't be blank. \nTry again.\n")
#     else:
#         print(name_column + " doesn't exist.")

# while True:
#     group_column = input("Insert name's column ")
#     if group_column in df.columns:
#         break
#     elif group_column == "":
#         print("It can't be blank. \nTry again.\n")
#     else:
#         print(group_column + " doesn't exist.")

# while True:
#     value_column = input("Insert name's column ")
#     if value_column in df.columns:
#         break
#     elif value_column == "":
#         print("It can't be blank. \nTry again.\n")
#     else:
#         print(value_column + " doesn't exist.")

# while True:
#     quantity_column = input("Insert name's column ")
#     if quantity_column in df.columns:
#         break
#     elif quantity_column == "":
#         print("It can't be blank. \nTry again.\n")
#     else:
#         print(quantity_column + " doesn't exist.")

# while True:
#     print("If there's isn't a Total Column, press Enter to create one.")
#     total_column = input("Insert name's column ")
#     if total_column in df.columns:
#         total_exist = True
#         break
#     elif total_column == "":
#         total_column = "Total"
#         total_exist = False
#         break
#     else:
#         print(total_column + " is not an existing column. \ntry again.\n")

        

# print("Date column is optional! Press Enter to skip.")
# date_column = input("Insert data's column ")
# if date_column == "":
#     date_column = None

# df = path1.merge(path2, on=id_column)

# monthly, sellers, detailed = generate_reports(df, name_column, group_column, value_column, quantity_column, total_column, total_exist, id_column, date_column)
# print(monthly, "\n", sellers, "\n", detailed)