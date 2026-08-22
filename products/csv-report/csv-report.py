#!/usr/bin/env python3
"""csv-report — generate summary reports from CSV files via CLI.

A small, dependency-free tool for small businesses and teams that live in
spreadsheets. Reads a CSV, groups by a column, and prints sums/counts/means
for numeric columns — without opening Excel.

Examples:
  python3 csv-report.py sales.csv --group-by region --sum revenue --count
  python3 csv-report.py orders.csv --group-by product --sum total --mean qty
  python3 csv-report.py logs.csv --group-by level --count --sort count

Output: aligned table to stdout, or --json for machine-readable.

Python 3.8+ stdlib only. The truth is in the exit code.
"""

import argparse
import csv
import json
import sys
from collections import defaultdict


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Summary reports from CSV files.")
    p.add_argument("csv_file", help="Path to the input CSV (header row required)")
    p.add_argument("--group-by", required=True, help="Column name to group rows by")
    p.add_argument("--sum", action="append", default=[], metavar="COL",
                   help="Numeric column to sum (repeatable)")
    p.add_argument("--mean", action="append", default=[], metavar="COL",
                   help="Numeric column to average (repeatable)")
    p.add_argument("--count", action="store_true", help="Include row count per group")
    p.add_argument("--sort", choices=["count", "group"], default="group",
                   help="Sort output by count desc or group name asc (default: group)")
    p.add_argument("--json", dest="as_json", action="store_true",
                   help="Emit JSON instead of a table")
    return p.parse_args(argv)


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def to_number(val):
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip()
    if not s:
        return None
    # Excel-style thousands separators inside quotes: "1,234.56" -> 1234.56
    if "," in s:
        # Only strip commas when they are thousands separators (followed by 3 digits)
        import re as _re
        s = _re.sub(r",(?=\d{3}(?:\D|$))", "", s)
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def build_report(rows, group_by, sum_cols, mean_cols, want_count):
    groups = defaultdict(lambda: {"count": 0, "sums": defaultdict(float),
                                  "n_for_mean": defaultdict(int),
                                  "means": defaultdict(float)})
    for row in rows:
        key = row.get(group_by, "")
        if key is None:
            key = ""
        g = groups[key]
        g["count"] += 1
        for col in sum_cols:
            v = to_number(row.get(col))
            if v is not None:
                g["sums"][col] += v
        for col in mean_cols:
            v = to_number(row.get(col))
            if v is not None:
                g["means"][col] += v
                g["n_for_mean"][col] += 1
    return groups


def render_table(groups, sum_cols, mean_cols, want_count, sort_by):
    items = list(groups.items())
    if sort_by == "count":
        items.sort(key=lambda kv: -kv[1]["count"])
    else:
        items.sort(key=lambda kv: str(kv[0]).lower())
    headers = ["GROUP:" + ("" )] + []  # placeholder, replaced below
    headers = ["group"]
    if want_count:
        headers.append("count")
    headers += [f"sum({c})" for c in sum_cols]
    headers += [f"mean({c})" for c in mean_cols]

    widths = [len(h) for h in headers]
    lines = []
    for key, g in items:
        vals = [str(key)]
        if want_count:
            vals.append(str(g["count"]))
        for col in sum_cols:
            vals.append(f"{g['sums'][col]:,.2f}" if g["sums"][col] else "0.00")
        for col in mean_cols:
            n = g["n_for_mean"][col]
            avg = g["means"][col] / n if n else 0.0
            vals.append(f"{avg:,.2f}" if n else "—")
        for i, v in enumerate(vals):
            widths[i] = max(widths[i], len(v))
        lines.append(vals)

    def fmt_row(cells):
        return "  ".join(c.ljust(widths[i]) for i, c in enumerate(cells)).rstrip()

    out = [fmt_row(headers), "-" * sum(widths) + "-" * (2 * (len(widths) - 1))]
    out += [fmt_row(vals) for vals in lines]
    return "\n".join(out)


def main(argv=None):
    args = parse_args(argv)
    try:
        rows = read_csv(args.csv_file)
    except FileNotFoundError:
        print(f"ERROR: file not found: {args.csv_file}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"ERROR reading CSV: {e}", file=sys.stderr)
        return 2

    if not rows:
        print("ERROR: CSV has no data rows", file=sys.stderr)
        return 2

    if args.group_by not in rows[0]:
        print(f"ERROR: group-by column '{args.group_by}' not in header: {list(rows[0])}",
              file=sys.stderr)
        return 2

    for col in args.sum + args.mean:
        if col not in rows[0]:
            print(f"ERROR: column '{col}' not in header: {list(rows[0])}", file=sys.stderr)
            return 2

    groups = build_report(rows, args.group_by, args.sum, args.mean, args.count)

    if args.as_json:
        out = {}
        for key, g in sorted(groups.items(), key=lambda kv: str(kv[0]).lower()):
            entry = {"count": g["count"]}
            for col in args.sum:
                entry[f"sum_{col}"] = g["sums"][col]
            for col in args.mean:
                n = g["n_for_mean"][col]
                entry[f"mean_{col}"] = (g["means"][col] / n) if n else None
            out[str(key)] = entry
        print(json.dumps(out, indent=2, sort_keys=True))
        return 0

    print(render_table(groups, args.sum, args.mean, args.count, args.sort))
    return 0


if __name__ == "__main__":
    sys.exit(main())
