import pandas as pd



def file_cleaner(input_path, output_path):
    """
    Cleans a CSV/Excel file: strips whitespace from headers and text cells,
    removes fully-empty rows and duplicate rows.

    Args:
        input_path: path to the source .csv or .xlsx file
        output_path: path where the cleaned file will be saved

    Returns:
        The output_path, for chaining into other pipeline steps.
    """

    # 1. Load data based on file extension
    if input_path.lower().endswith(".csv"):
        df = pd.read_csv(input_path)
    elif input_path.lower().endswith([".xlsx", ".xls"]):
        df = pd.read_excel(input_path)
    else:
        print(f"Unsupported file format: {input_path}")
        return None
    
     # 2. Clean column headers
    df.columns = df.columns.str.strip()

    # 3. Clean text cells (handles both 'object' and 'string' types)

    for col in df.select_dtypes(include=["object", "string"]).columns:  
        df[col] = df[col].str.strip()

    # 4. Remove blank rows and duplicates
    df = df.dropna(how="all")
    df = df.drop_duplicates()
    df = df.reset_index(drop=True)

    # 5. Export clean data
    if input_path.lower().endswith(".csv"):
        df.to_csv(output_path, index=False)
    else:
        df.to_excel(output_path, index=False)   
    print(f"new file saved as {output_path}")

    return output_path
    