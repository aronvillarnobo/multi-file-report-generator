# Multi-File Report Generator

Python/Pandas tool that merges and analyzes multiple sales files (CSV/Excel), generating automated seller, monthly, and pivot-table reports.

## What it does
- Accepts a variable number of input files (CSV/Excel)
- Cleans each file automatically (via [csv-excel-cleaner](https://github.com/aronvillarnobo/csv-excel-cleaner))
- Detects shared columns between consecutive files and merges them in sequence
- Generates 3 reports:
  - **Detailed_Sellers_Report.csv** — sales by seller and category (sum, count, max)
  - **Monthly_Report.csv** — sales trend by category and month
  - **Sellers_Report.csv** — pivot table (seller × category) with totals

## Requirements
- Python 3.x
- pandas

## Usage
```bash
python reports-generator.py
```
Follow the prompts: number of files, file names (in correlation order), and merge key confirmation.

## Status
🚧 Work in progress — dynamic column selection for report generation (name/group/value columns) is pending. Currently uses a fixed merge pipeline.
