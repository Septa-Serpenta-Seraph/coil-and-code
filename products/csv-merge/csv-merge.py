#!/usr/bin/env python3
"""csv-merge — merge two CSVs on a key column, safely.

Totals/augments rows by a shared key (like a VLOOKUP, but honest).
Any number of merge CSV files; the first file is the base key set.
Output rows keep the base row's columns plus any non-key columns from
the merge files (suffixes _2, _3 on name collisions). Values from
later files overwrite earlier ones for the same key when columns
collide.

Zero external dependencies. Python 3.8+ stdlib only.

Usage:
  csv-merge.py base.csv merge1.csv [merge2.csv ...] --key id [--output out.csv]

Examples:
  csv-merge.py customers.csv orders.csv --key customer_id
  csv-merge.py a.csv b.csv c.csv --key sku --output combined.csv
"""
import argparse
import csv
import sys


def read_rows(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def clean_key(v):
    return "" if v is None else str(v).strip()


def build_merged(base, merges, key, merge_names=None):
    """Return (out_rows, out_fieldnames).

    Consistent collision naming: for each merge file, any column that
    already exists gets the SAME suffixed name for every row in that
    file (e.g. region -> region2 across the whole file), never a
    per-row orphan name.
    """
    merge_names = merge_names or [f"merge#{i}" for i in range(len(merges))]
    if not base:
        return [], []
    if key not in base[0]:
        raise ValueError(f"key column '{key}' not in base header: {list(base[0])}")

    key_to_row = {}
    for row in base:
        k = clean_key(row.get(key, ""))
        if k in key_to_row:
            print(f"WARNING: duplicate key '{k}' in base file — later base row wins", file=sys.stderr)
        key_to_row[k] = dict(row)

    fieldnames = list(base[0])
    for extra, extra_name in zip(merges, merge_names):
        if not extra:
            continue
        if key not in extra[0]:
            raise ValueError(f"key column '{key}' not in merge header: {list(extra[0])}")
        # Build a per-file rename map for colliding columns (stable across rows)
        col_map = {}
        for col in extra[0]:
            if col == key or col not in fieldnames:
                col_map[col] = col
            else:
                n = 2
                while f"{col}{n}" in fieldnames:
                    n += 1
                col_map[col] = f"{col}{n}"
                fieldnames.append(f"{col}{n}")
        # Apply to rows present in base
        seen = set()
        for row in extra:
            k = clean_key(row.get(key, ""))
            if not k or k in seen:
                if k:
                    print(f"WARNING: duplicate key '{k}' in {extra_name} — later rows collapsed (first match wins)", file=sys.stderr)
                continue
            seen.add(k)
            if k not in key_to_row:
                continue  # inner-ish join: keep base rows only
            target = key_to_row[k]
            for col, val in row.items():
                if col == key:
                    continue
                target[col_map[col]] = val

    out_rows = list(key_to_row.values())
    for r in out_rows:
        for c in r:
            if c not in fieldnames:
                fieldnames.append(c)
    return out_rows, fieldnames


def main(argv=None):
    ap = argparse.ArgumentParser(description="Merge CSV files on a key column.")
    ap.add_argument("files", nargs="+", help="base.csv then one or more merge CSVs")
    ap.add_argument("--key", required=True, help="key column for merging")
    ap.add_argument("--output", default=None, help="output file (default stdout)")
    args = ap.parse_args(argv)

    if len(args.files) < 2:
        ap.error("need at least base.csv and one merge.csv")

    try:
        base = read_rows(args.files[0])
        merges = [read_rows(p) for p in args.files[1:]]
    except FileNotFoundError as e:
        print(f"ERROR: file not found: {e.filename}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"ERROR: failed to read CSV: {e}", file=sys.stderr)
        return 2

    try:
        out_rows, fieldnames = build_merged(base, merges, args.key, args.files[1:])
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    if args.output:
        with open(args.output, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
            w.writeheader()
            w.writerows(out_rows)
        print(f"Wrote {len(out_rows)} merged rows ({len(fieldnames)} columns) to {args.output}")
    else:
        w = csv.DictWriter(sys.stdout, fieldnames=fieldnames, lineterminator="\n")
        w.writeheader()
        w.writerows(out_rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())