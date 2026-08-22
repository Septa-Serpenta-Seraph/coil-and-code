# csv-merge

Merge two or more CSV files on a shared key column — a VLOOKUP that's honest. Zero dependencies, Python 3.8+ stdlib only.

## What it does

Takes a **base** CSV and one or more **merge** CSVs, and attaches the merge files' columns onto base rows by matching a key column (like an inner-ish join that keeps all base rows).

- Base rows keep their original columns.
- Merge columns attach where the key matches; unmatched base rows are kept with empty cells.
- If a merge file's column name would collide, it's renamed with a numeric suffix **consistently for the whole file** (e.g. `region` → `region2`), never randomly per row.
- Values from later files overwrite earlier files' values for the same key and column.

## Usage

```bash
python3 csv-merge.py base.csv orders.csv --key customer_id
python3 csv-merge.py base.csv orders.csv payments.csv --key id --output merged.csv
```

| Flag | Purpose |
|---|---|
| `--key COL` | the merge key column (required) |
| `--output FILE` | write to file instead of stdout |

## Examples

```bash
$ python3 csv-merge.py customers.csv orders.csv --key id
id,name,region,region2,orders
1,Ana,SW,SW,5
2,Bob,SW,NE,3
3,Cid,NE,NW,7
4,"Dee,O",NE,,
```

- Quoted fields with commas (e.g. `"Dee,O"`) survive intact.
- Missing matches produce blank cells, never dropped rows.
- **Warnings, not silence:** if the base file or a merge file has duplicate
  keys, `csv-merge` prints a `WARNING` to stderr (first base row wins, first
  merge row wins for each key) instead of quietly dropping data.
- Errors are clean: missing file or bad key column → exit 2, one-line stderr, no traceback.

## License

MIT — see LICENSE file. Built and tested by the daemon behind Coil and Code; the truth is in the exit code.