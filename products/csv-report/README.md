# csv-report

**Generate summary reports from CSV files — no spreadsheet app required.**

A small, dependency-free command-line tool for teams that live in
spreadsheets. Reads a CSV, groups by any column, and prints sums, counts,
and averages for numeric columns — as a clean table or machine-readable JSON.

```
$ python3 csv-report.py sales.csv --group-by region --sum revenue
group  sum(revenue)
-------------------
East   550.00
North  75.00
South  50.00
West   450.00
```

## Why you'd want it

- **Stop opening Excel for a two-second question.** Need this month's total
  by region? One command.
- **Automation-friendly:** drop it in a cron job or n8n workflow, pipe the
  JSON anywhere.
- **Zero dependencies, zero install:** Python 3.8+ stdlib only. Works on any
  machine with Python. No cloud, no accounts, no data leaves your computer.
- **Auditable:** the truth is in the output — every number is computed from
  your file, right there.

## Usage

```
python3 csv-report.py FILE --group-by COL [options]
```

| Option | Description |
|--------|-------------|
| `--group-by COL` | Column to group rows by (required) |
| `--sum COL` | Sum a numeric column (repeatable) |
| `--mean COL` | Average a numeric column (repeatable) |
| `--count` | Include row count per group |
| `--sort count` | Sort by count descending (default: group name) |
| `--json` | Output JSON instead of a table |

### Examples

```bash
# Total sales by region
python3 csv-report.py sales.csv --group-by region --sum revenue

# Full breakdown by product
python3 csv-report.py orders.csv --group-by product --sum total --mean qty --count

# Machine-readable output for scripts
python3 csv-report.py logs.csv --group-by level --count --json
```

## Requirements

- Python 3.8+
- Nothing else. Seriously — stdlib only.

## License

MIT — use it, fork it, ship it. Credit appreciated, not required.

---

*Built by Sunburst Sanctuary LLC. Verifiable work, clean hands.*
