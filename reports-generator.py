# === SCRIPT: sales report generation from multiple source files ===
import pandas as pd
from pathlib import Path
from cleaner import file_cleaner

def ask_yes_no(text):
    """Asks a yes/no question and validates the user's input.
 
    Loops until the user responds with something starting in "S" (yes)
    or "N" (no), case-insensitive.
 
    Args:
        text: The prompt text shown to the user, without the S/N hint.
 
    Returns:
        True if the user confirmed, False otherwise.
    """
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
    """Prints a 1-indexed numbered list of options to the console.
 
    Args:
        options: Any iterable of items to display.
    """
    for j, col_name in enumerate(options):
        print(j+1, " - ", col_name, "\n",)

def ask_from_list(text, options):
    """Prompts the user to pick an item from a list by its number.
 
    Assumes the list has already been shown to the user (e.g. via
    show_list). Loops until a valid, in-range integer is entered.
 
    Args:
        text: The prompt text shown to the user.
        options: The list of items the user is choosing from.
 
    Returns:
        The selected item from options (not its index).
    """
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



# Asks how many files the user will upload, validates it's an integer
def ask_file_amount():
    """Asks how many files the user will upload.
 
    Entering 0 signals the user wants to exit the program instead.
 
    Returns:
        The confirmed file count as a positive int, or None if the
        user chose to exit.
    """
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
    """Collects and cleans the source files the user wants to merge.
 
    For each expected file, prompts for a path, validates the
    extension and that the file exists, then cleans it via
    file_cleaner() before storing the cleaned path.
 
    Args:
        file_amount: How many files to prompt for.
 
    Returns:
        A list of paths to the cleaned files, in upload order.
    """
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
    """Loads already-cleaned files into pandas DataFrames.
 
    Args:
        file_list: Paths to cleaned .csv/.xlsx/.xls files.
 
    Returns:
        A list of DataFrames, in the same order as file_list.
    """
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
    """Finds shared columns between each pair of consecutive DataFrames.
 
    Only checks consecutive pairs (df_list[i] vs df_list[i+1]), not
    every possible combination, since files are merged in a chain.
 
    Args:
        df_list: DataFrames in the order they will be merged.
 
    Returns:
        A tuple (mutual_columns, invalid_pair):
            - mutual_columns: a list of shared-column Index objects,
              one per consecutive pair, or None if a pair shares nothing.
            - invalid_pair: the (i, i+1) indices of the first pair with
              no shared columns, or None if all pairs are valid.
    """
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
    """Resolves one merge key per consecutive file pair.
 
    Delegates the actual selection (automatic or manual) to
    choose_column_merge() for each pair.
 
    Args:
        mutual_columns: Shared-column lists per pair, from detect_mutual_columns().
        dataFrame_list: The DataFrames being merged.
 
    Returns:
        A list of chosen merge keys (one per pair), or None if the
        user cancelled the selection for any pair.
    """
    merge_keys = []
    for i, mutual_cols in enumerate(mutual_columns):
        chosen_column = choose_column_merge(mutual_cols, dataFrame_list[i].columns, dataFrame_list[i+1].columns)
        if chosen_column is None:
            return None
        else:
            merge_keys.append(chosen_column)

    return merge_keys

def choose_column_merge(mutual_cols, cols_current, cols_next):
    """Lets the user pick the merge key for one pair of files.
 
    Shows the shared columns and offers three paths: pick one from
    the list, enter a column name manually (validated against both
    files), or cancel the whole program.
 
    Args:
        mutual_cols: Columns shared between the two files.
        cols_current: Full column set of the first file in the pair.
        cols_next: Full column set of the second file in the pair.
 
    Returns:
        The chosen column name, or None if the user cancelled.
    """
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
    """Asks the user to type a merge column name that isn't in the shared list.
 
    Validates that the typed name exists in both files' columns, then
    confirms the choice before accepting it.
 
    Args:
        text: The prompt text shown to the user.
        cols_current: Full column set of the first file in the pair.
        cols_next: Full column set of the second file in the pair.
 
    Returns:
        The confirmed column name, or None if the user gave up trying.
    """
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
    """Merges a list of DataFrames in sequence using left joins.
 
    Each DataFrame is merged into the running result on the
    corresponding key in merge_keys, preserving every row from the
    first (primary) DataFrame.
 
    Args:
        dataframe_list: DataFrames to merge, in order.
        merge_keys: The merge key for each consecutive pair.
 
    Returns:
        The fully merged DataFrame.
    """
    df_final = dataframe_list[0]
    for i in range(len(merge_keys)):
        df_final = df_final.merge(dataframe_list[i+1], on=merge_keys[i], how="left")
    return df_final

def ask_report_columns(df):
    """Collects all the column choices needed to build the reports.
 
    Args:
        df: The merged DataFrame the reports will be generated from.
 
    Returns:
        A dict with keys group_column, name_column, value_column,
        quantity_column, totals_column, totals_exist, and date_column,
        ready to be unpacked into generate_reports().
    """
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

def ask_valid_column(df, text):
    """Asks for a column name and validates it exists in the DataFrame.
 
    Args:
        df: The DataFrame to validate the column name against.
        text: The prompt text shown to the user.
 
    Returns:
        The validated, non-blank column name.
    """
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
    """Asks for an existing totals column, or requests one be created.
 
    Args:
        df: The DataFrame to validate the column name against.
 
    Returns:
        A tuple (total_column, totals_exist):
            - total_column: the existing column name, or "Total" if
              a new one will be created.
            - totals_exist: True if the column already exists in df,
              False if it still needs to be calculated.
    """
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
    """Asks for an optional date column to enable monthly/yearly grouping.
 
    Args:
        df: The DataFrame to validate the column name against.
 
    Returns:
        The validated column name, or None if the user skipped it.
    """
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

def ask_output_format():
    """Asks the user to choose the export format for the reports.
 
    Returns:
        The chosen format as a string: "csv" or "xlsx".
    """
    valid_formats = ["csv", "xlsx"]
    show_list(valid_formats)
    chosen_format = ask_from_list("Please, use the numbers behind the names.\nSelect the format ", valid_formats)

    return chosen_format



def generate_reports(df, output_format, name_column, group_column, value_column, quantity_column, totals_column, totals_exist, date_column=None):
    """Builds and exports the three sales reports from a merged DataFrame.
 
    Generates:
        - Monthly_Report: sales by category and month (requires date_column).
        - Sellers_Report: pivot table of seller x category, with totals.
        - Detailed_Sellers_Report: sales by seller and category.
 
    If totals_exist is False, the totals column is calculated as
    value_column * quantity_column before generating any report.
 
    Args:
        df: The merged DataFrame to report on.
        output_format: Export format, "csv" or "xlsx".
        name_column: Column identifying the seller.
        group_column: Column identifying the category.
        value_column: Column with the sale price/value.
        quantity_column: Column with the quantity sold.
        totals_column: Column name to use for totals.
        totals_exist: Whether totals_column already exists in df.
        date_column: Optional column with the sale date, used to
            derive Month/Year for the monthly report.
 
    Returns:
        A tuple (reportMonthly, monthly_path, reportSellers, sellers_path,
        reportSellersDetailed, detailed_path) with each report's
        DataFrame and the path it was exported to.
    """
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
    """Exports a DataFrame to CSV or Excel.
 
    Args:
        df: The DataFrame to export.
        filename_no_ext: Output file name without its extension.
        output_format: Export format, "csv" or "xlsx".
        index: Whether to include the DataFrame's index in the
            output. Defaults to True, since the reports built by
            generate_reports() carry meaningful data in their index
            (from groupby/pivot_table).
 
    Returns:
        The full path (with extension) of the exported file.
    """
    if output_format == "csv":
        output_path = f"{filename_no_ext}.csv"
        df.to_csv(output_path, index=index)
    elif output_format == "xlsx":
        output_path = f"{filename_no_ext}.xlsx"
        df.to_excel(output_path, index=index)

    return output_path


def main():
    """Runs the full pipeline: upload, clean, merge, and report.
 
    Loops until the user chooses to exit. On each iteration, asks for
    files, cleans and merges them, asks which columns and output
    format to use, then generates and exports all three reports.
    """
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