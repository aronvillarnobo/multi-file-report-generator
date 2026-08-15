import pandas as pd



def file_cleaner(input_path, output_path):
    

    if input_path.endswith(".csv"):
        df = pd.read_csv(input_path)
    else:
        df = pd.read_excel(input_path)

    df.columns = df.columns.str.strip()

    for columns in df.select_dtypes(include="str").columns:  
        df[columns] = df[columns].str.strip()

    df = df.dropna(how="all")
    df = df.drop_duplicates()
    df = df.reset_index(drop=True)

    if input_path.endswith(".csv"):
        df.to_csv(output_path, index=False)
    else:
        df.to_excel(output_path, index=False)
    print(f"new file saved as {output_path}")

    return output_path
    