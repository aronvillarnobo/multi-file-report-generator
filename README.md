# Multi-File Report Generator
 
A Python CLI tool that cleans, merges, and generates sales reports from multiple CSV/Excel files — built for freelance/small-business use cases where sales data lives scattered across several source files (orders, product catalogs, seller lists, region tables, etc.).
 
## What it does
 
1. **Cleans** each uploaded file (strips whitespace, drops empty/duplicate rows) using the companion [`csv-excel-cleaner`](https://github.com/aronvillarnobo/csv-excel-cleaner) module.
2. **Detects shared columns** between consecutive files and lets you choose the merge key for each pair — with a manual fallback if no column matches automatically.
3. **Merges** all files into a single dataset via chained left joins, preserving every row from your primary sales file.
4. **Generates three reports** from the merged data:
   - `Detailed_Sellers_Report` — sales by seller and category (sum, count, max)
   - `Monthly_Report` — sales by category and month
   - `Sellers_Report` — pivot table of seller × category, with row/column totals
5. **Exports** each report as CSV or Excel, based on your choice.
## Requirements
 
- Python 3.10+
- pandas
- openpyxl (for `.xlsx` export)
```bash
pip install pandas openpyxl
```
 
## Usage
 
```bash
python reports-generator.py
```
 
You'll be prompted to:
 
1. Enter the number of files to upload (in the order they should be merged).
2. Provide the path to each file (`.csv`, `.xlsx`, or `.xls`).
3. Choose the merge key for each pair of files (or enter one manually if none match).
4. Identify the relevant columns in your merged dataset: category, seller name, price, quantity, an optional totals column, and an optional date column.
5. Choose the output format (CSV or Excel).
The three reports are saved in the working directory.
 
## Example dataset
 
A ready-to-use fictional sales dataset is available for testing the full pipeline without uploading your own data:
 
- `ventas.csv` — sales transactions (order, product, quantity, price, date)
- `productos.csv` — product catalog (linked to `ventas.csv` via `ProductID`, and to `vendedores.csv` via `SellerID`)
- `vendedores.csv` — seller directory (linked to `regiones.csv` via `Region`)
- `regiones.csv` — regional manager lookup
Upload them in that exact order to walk through the full merge chain.
 
## Project structure
 
```
multi-file-report-generator/
├── reports-generator.py   # main pipeline: merge orchestration + report generation
├── cleaner.py              # standalone file cleaning module
└── README.md
```
 
## Use cases
 
This tool fits businesses that track sales across multiple disconnected sources — e-commerce sellers with separate product/seller/region spreadsheets, marketplaces consolidating data from different systems, or any team manually copy-pasting CSVs into a single report every month.
 
## Known limitations
 
- Merge order matters: the tool checks for shared columns between *consecutive* files only, not across the whole set.
- Column name matching is case- and whitespace-sensitive (normalization is planned).
- Corrupted or malformed source files are not yet handled gracefully.

## License
MIT