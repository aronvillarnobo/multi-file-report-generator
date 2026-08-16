# Multi-File Report Generator

Python/Pandas tool that merges and analyzes multiple sales files (CSV/Excel), generating automated seller, monthly, and pivot-table reports.

## What it does

- Accepts a variable number of input files (CSV/Excel)
- Cleans each file automatically (via [csv-excel-cleaner](https://github.com/aronvillarnobo/csv-excel-cleaner))
- Detects shared columns between consecutive files and merges them in sequence, letting the user confirm or pick the merge key when there's ambiguity
- Asks the user to map their own column names (seller, category, price, quantity) — no fixed schema required
- Optionally calculates a Total column (price × quantity) if the source file doesn't have one
- Optionally derives Month/Year breakdowns if a date column is provided
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

Follow the prompts:
1. Number of files to upload
2. File names, in correlation order (e.g. `sales.csv` → `sellers.xlsx`)
3. Merge key confirmation for each file pair
4. Column mapping (seller, category, price, quantity, total, date)

## Sample output

```
                      sum  count    max
Category    Month
Computers   1      157000      4  45000
Peripherals 1       11100      7   3500
Audio       1        4400      2   2200
...

Category        Audio  Computers  Office  Peripherals     All
Name
Carla Nunez      4400     226000   24000         8500  262900
Martin Alvarez   6600     292000   16000        12900  327500
...
```

## Status

Core pipeline is functional end-to-end: file cleaning → merge → column mapping → report generation. Tested with real multi-file sales datasets.

**Pending:**
- Refactor repeated S/N confirmation prompts into a single reusable function
- Friendlier error handling when no shared columns are found or merge is cancelled (currently restarts the whole flow)
- Type hints and docstrings across all functions
- Input validation edge cases
- Automated tests

## Notes

This is a portfolio project built to demonstrate practical Python data-automation skills for freelance work (small/medium business use cases: sales consolidation, seller performance tracking, monthly reporting).
