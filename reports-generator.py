# === SCRIPT: sales report generation from multiple source files ===
import pandas as pd
from pathlib import Path
from cleaner import file_cleaner

# Asks how many files the user will upload, validates it's an integer
def ask_file_amount():

    while True:
        try:
            print("Insert 0 to exit.")
            file_amount= int(input("Insert number of files "))
        except ValueError:
            print("It can't contain letters. \nTry again\n")
            continue

        if file_amount == 0:
            file_amount = None
            break
        elif file_amount >0:
            file_confirmation = input(f"Are you sure you want {file_amount} files? Press S/N ").upper()
            if file_confirmation.startswith("S"):
                break
        else:
            print("Insert a valid amount! \nTry again\n")

    return file_amount

def load_and_clean_files(file_amount):

    file_list = []
    print(
        "\nImportant: Upload files in the exact order of correlation. Incorrect sequencing won't be able to process your files correctly.\n",
        "Example sequence: sales.csv → sellers.xlsx → products.csv")
    # For each file: checks it exists on disk, cleans it via file_cleaner(), stores the clean path
    valid_extensions = (".csv", ".xlsx", ".xls")
    for i in range(0, file_amount):
        while True:
            file_name = input(f"Insert {i+1} file's name ")
            if file_name.lower().endswith(valid_extensions):
                path_check = Path(file_name)
                if path_check.is_file():
                    clean_file_name = file_cleaner(file_name, f"clean_{file_name}")
                    file_list.append(clean_file_name)
                    break
                else:
                    print("File doesn't exist. \nTry again.\n")
            else:
                print(f"Unsupported file format: {file_name}")

    return file_list

def load_dataframes(file_list):

    dataFrame_list = []
    # Loads each already-cleaned file into a DataFrame based on its extension
    for file_path in file_list:
        if file_path.endswith(".csv"):
            dataFrame_item = pd.read_csv(file_path)
            dataFrame_list.append(dataFrame_item)
        else:
            dataFrame_item = pd.read_excel(file_path)
            dataFrame_list.append(dataFrame_item)

    return dataFrame_list

def detect_mutual_columns(df_list):

    mutual_columns = []
    invalid_pair = None
    
    
    for i in range(0,  len(df_list)-1):
        shared_cols = df_list[i].columns.intersection(df_list[i+1].columns)
        if not shared_cols.empty:
            mutual_columns.append(shared_cols)
        else:
            invalid_pair = i, i+1
            return None, invalid_pair
            
    return mutual_columns, invalid_pair

def build_merge_keys(mutual_columns, dataFrame_list):

    merge_keys = []
    for i, mutual_cols in enumerate(mutual_columns):
        chosen_column = choose_column_merge(mutual_cols, dataFrame_list[i].columns, dataFrame_list[i+1].columns)
        if chosen_column is None:
            return None
        else:
            merge_keys.append(chosen_column)

    return merge_keys

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

def chained_merge(dataframe_list, merge_keys):
    df_final = dataframe_list[0]
    for i in range(len(merge_keys)):
        df_final = df_final.merge(dataframe_list[i+1], on=merge_keys[i], how="left")
    return df_final

# Generates 3 CSV reports from an already-merged dataframe.
#     - reportSellersDetailed: sales by seller and category (sum, count, max)
#     - reportMonthly: sales grouped by category and month
#     - reportSellers: pivot table seller x category, with totals
def generate_reports(df, name_column, group_column, value_column, quantity_column, totals_column, totals_exist, date_column=None):

    # If the file doesn't have a Total column, calculate it: price * quantity
    if totals_exist == False:
        df[totals_column] = df[value_column] *  df[quantity_column]

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
    reportMonthly = reportMonthly.sort_values(by=["Month", "sum"])
    reportMonthly.to_csv("Monthly_Report.csv")

    # Report 3: pivot table seller x category, with "All" row/column totals
    reportSellers = pd.pivot_table(df, index=name_column, columns=group_column, values=value_column, aggfunc="sum", margins=True, fill_value=0)
    reportSellers.to_csv("Sellers_Report.csv", index=True)

    return reportMonthly, reportSellers, reportSellersDetailed

def ask_valid_column(df, text):
    while True:
        column_name = input(text)
        if column_name in df.columns:
            break
        elif column_name == "":
            print("It can't be blank. \nTry again.\n")
        else:
            print(column_name + " doesn't exist.")

    return column_name

def ask_report_columns(df):
    group_column = ask_valid_column(df, "which is the categories column ")
    name_column = ask_valid_column(df, "which's the sellers column ")
    value_column = ask_valid_column(df, "which is the price column ")
    quantity_column = ask_valid_column(df, "which is the quantity column ")
    totals_column, totals_exist = ask_totals_column(df)
    date_column = ask_date_column(df)

    return {
        "group_column" : group_column, 
        "name_column" : name_column,
        "value_column" : value_column, 
        "quantity_column" : quantity_column,
        "totals_column" : totals_column,
        "totals_exist" : totals_exist,
        "date_column" : date_column
    }

def ask_totals_column(df):
    while True:
        print("If there is not totals Column, press Enter to create one.")
        total_column = input("Insert totals column ")
        if total_column in df.columns:
            totals_exist = True
            break
        elif total_column == "":
            total_column = "Total"
            totals_exist = False
            break
        else:
            print(total_column + " is not an existing column. \ntry again.\n")

    return total_column, totals_exist

def ask_date_column(df):
    while True:
        print("Date column is optional! Press Enter to skip if you don't have one.")
        date_column = input("Insert date column ")
        if date_column in df.columns:
            break
        elif date_column == "":
            date_column = None
            break
        else:
            print(date_column + " is not an existing column. \ntry again.\n")

    return date_column



def main():
    while True:
        file_amount = ask_file_amount()
        if file_amount is not None:
            file_list = load_and_clean_files(file_amount) 
            dataFrame_list = load_dataframes(file_list)
            mutual_columns, invalid_pair = detect_mutual_columns(dataFrame_list)
            if mutual_columns is None:
                idx1, idx2 = invalid_pair
                print(f"Files {file_list[idx1]} and {file_list[idx2]} don't share any columns.")
                break
                
            else:
                merge_keys = build_merge_keys(mutual_columns, dataFrame_list)
                if merge_keys is None:
                    print("Merge cancelled by user.")
                    continue
                else:
                    df = chained_merge(dataFrame_list, merge_keys)
                    report_columns = ask_report_columns(df)
                    monthly, sellers, detailed = generate_reports(df, **report_columns)
                    # print(monthly, "\n", sellers, "\n", detailed)

        else:
            close_confirmation = input("Do you wana close the program? S/N").upper()
            if close_confirmation == "S":
                print("Exiting program.")
                break

if __name__ == "__main__": main()