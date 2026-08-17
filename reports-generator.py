# === SCRIPT: sales report generation from multiple source files ===
import pandas as pd
from pathlib import Path
from cleaner import file_cleaner

# Asks how many files the user will upload, validates it's an integer
def ask_file_amount():

    while True:
        try:
            print("Insert 0 to exit.")
            file_amount= int(input("Input number of files "))
        except ValueError:
            print("It can't contain letters. \nTry again\n")
            continue

        if file_amount == 0:
            file_amount = None
            break
        elif file_amount >0:
            wants_confirmed = ask_yes_no(f"Are you sure you want {file_amount} files?")
            if wants_confirmed:
                break
        else:
            print("Input a valid amount! \nTry again\n")

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
            file_name = input(f"Input {i+1} file's name ")
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
    chosen_column = None
    show_list(mutual_cols)
    while True:
        wants_selected = ask_yes_no("Do you want to use any of this columns?")
        if wants_selected:
            chosen_column = ask_from_list("Please, use the numbers behind the names.\nInput the selected column ", mutual_cols)
            break
        else:
            wants_manual = ask_yes_no("Do you want to manually input the column name?")
            if wants_manual:
                chosen_column = ask_manual_column("Please, input the name ", cols_current, cols_next)
                if chosen_column is not None:
                    break
                
        if chosen_column is None:            
            wants_close = ask_yes_no("Do you want to close the program?")
            if wants_close:
                break

    return chosen_column

def ask_manual_column(text, cols_current, cols_next):
    while True:
        column_given = input(text)
        if column_given in cols_current and column_given in cols_next:
            wants_column = ask_yes_no(f"Do you want to use {column_given}?")
            if wants_column:
                chosen_manual_column = column_given
                break
            else:
                wants_another_one = ask_yes_no(f"Do you want to try with another one?")
                if not wants_another_one:
                    chosen_manual_column = None
                    break
        else:
            print(f"{column_given} doesn't exist")

    return chosen_manual_column        

def chained_merge(dataframe_list, merge_keys):
    df_final = dataframe_list[0]
    for i in range(len(merge_keys)):
        df_final = df_final.merge(dataframe_list[i+1], on=merge_keys[i], how="left")
    return df_final

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

# Generates 3 CSV reports from an already-merged dataframe.
#     - reportSellersDetailed: sales by seller and category (sum, count, max)
#     - reportMonthly: sales grouped by category and month
#     - reportSellers: pivot table seller x category, with totals
def generate_reports(df, output_format, name_column, group_column, value_column, quantity_column, totals_column, totals_exist, date_column=None):

    # If the file doesn't have a Total column, calculate it: price * quantity
    if totals_exist == False:
        df[totals_column] = df[value_column] *  df[quantity_column]

    # If a date column exists, derive Month and Year for grouping reports
    if date_column:
        df[date_column] = pd.to_datetime(df[date_column])
        df["Month"] = df[date_column].dt.month
        df["Year"] = df[date_column].dt.year

    # Report 1: sales by (category, month) -> monthly trend
    reportMonthly = df.groupby([group_column, "Month"])[value_column].agg(["sum", "count", "max"])
    reportMonthly = reportMonthly.sort_values(by=["Month", "sum"])
    monthly_path = export_dataframe(reportMonthly, "Monthly_Report", output_format)

    # Report 2: pivot table seller x category, with "All" row/column totals
    reportSellers = pd.pivot_table(df, index=name_column, columns=group_column, values=value_column, aggfunc="sum", margins=True, fill_value=0)
    sellers_path = export_dataframe(reportSellers, "Sellers_Report", output_format)

    # Report 3: sales detail by (seller, category) -> sum, sale count, max sale
    reportSellersDetailed = df.groupby([name_column, group_column])[value_column].agg(["sum", "count", "max"])
    reportSellersDetailed = reportSellersDetailed.sort_values(by=[name_column, "sum"], ascending=False)
    detailed_path = export_dataframe(reportSellersDetailed, "Detailed_Sellers_Report", output_format)

    return reportMonthly, monthly_path, reportSellers, sellers_path, reportSellersDetailed, detailed_path

def export_dataframe(df, filename_no_ext, output_format, index=True):

    if output_format == "csv":
        output_path = f"{filename_no_ext}.csv"
        df.to_csv(output_path, index=index)
    elif output_format == "xlsx":
        output_path = f"{filename_no_ext}.xlsx"
        df.to_excel(output_path, index=index)

    return output_path

def ask_yes_no(text):
    while True:
        confirmation_input = input(text + "press S/N ").upper()
        if confirmation_input.startswith("S"):
            is_confirmed = True
            break
        elif confirmation_input.startswith("N"):
            is_confirmed = False
            break
        else:
            print("Please, use S or N.")

    return is_confirmed

def show_list(options):
    for j, col_name in enumerate(options):
        print(j+1, " - ", col_name, "\n",)

def ask_from_list(text, options):
    while True:
        try:
            selected_num = int(input(text))
        except ValueError:
            print("It can't contain letters.\nTry again\n")
            continue
            
        if selected_num > 0 and selected_num <= len(options):
            selected_option = options[selected_num-1]
            break
        else:
            print(f"{selected_num} is not a valid number.\nPlease use the ones shown in the list.")
            continue

    return selected_option

def ask_output_format():
    valid_formats = ["csv", "xlsx"]
    show_list(valid_formats)
    chosen_format = ask_from_list("Please, use the numbers behind the names.\nSelect the format ", valid_formats)

    return chosen_format

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
                    output_format = ask_output_format()
                    monthly, monthly_path, sellers, sellers_path, detailed, detailed_path = generate_reports(df, output_format, **report_columns)
                    # print(monthly, "\n", sellers, "\n", detailed)

        else:
            wants_to_close = ask_yes_no("Do you wana close the program?")
            if wants_to_close:
                print("Exiting program.")
                break

if __name__ == "__main__": main()