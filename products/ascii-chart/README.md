# ascii-chart

Draw sparklines and bar charts in your terminal from CSV, plain numbers, or a regex-extracted stream. Zero dependencies, Python 3.8+ stdlib only.

Because sometimes you just want to *see* the numbers without opening a spreadsheet, a notebook, or a charting package that needs its own PhD.

## What it does

- **Bar charts** — clean Unicode `█░` bars, labeled, scaled to your data
- **Sparklines** — dense `▁▂▃▄▅▆▇█` mini-trends that fit in a tweet
- Reads from a **CSV column**, **inline numbers**, or **stdin**
- `--value-extract` regex pulls numbers out of messy cells (log lines, status codes, timings)

## Usage

```bash
# inline numbers (unquoted works — multiple args allowed)
python3 ascii-chart.py 3 1 4 1 5 9 2 6 --type bar

# sparkline shorthand
python3 ascii-chart.py 3 1 4 1 5 9 2 6 --spark

# CSV column
python3 ascii-chart.py sales.csv --column revenue --type bar

# extract status codes from a log-ish CSV column
python3 ascii-chart.py logs.csv --column entry --value-extract 'status:(\d+)' --spark

# pipe in
cat numbers.txt | python3 ascii-chart.py --spark
```

| Flag | Purpose |
|------|---------|
| `--column COL` | CSV column name to chart |
| `--value-extract RE` | regex to pull numbers from cells (e.g. `status:(\d+)`) |
| `--type bar\|spark` | chart type (default bar) |
| `--spark` | shorthand for `--type spark` |
| `--width N` | bar chart width (default 42) |

## Example

```bash
$ python3 ascii-chart.py sales.csv --column revenue --type bar
    100.00 |█░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░|
    250.00 |███████████████████░░░░░░░░░░░░░░░░░░░░░░|
    150.00 |██████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░|
    300.00 |█████████████████████████░░░░░░░░░░░░░░░░|
    420.00 |█████████████████████████████████████████|
```

## Nice touches

- Handles negative numbers, decimals, CSV headers, and empty input gracefully
- Auto-detects the first numeric column when you don't pass `--column`
- `--value-extract` turns messy log data into a trend in one command
- Works in any terminal, over SSH, in CI output — anywhere text flows

## License

MIT — see `LICENSE`.