#!/usr/bin/env python3
"""ascii-chart — draw sparklines and bar charts in your terminal from CSV or plain numbers.

Zero dependencies. Python 3.8+, stdlib only.

Usage:
  python3 ascii-chart.py data.csv --column revenue
  python3 ascii-chart.py 3 1 4 1 5 9 2 6 5
  python3 ascii-chart.py http.log --value-extract 'code:(\d+)'

Charts render as clean ASCII/Unicode bars right in the terminal —
screenshot-grade, no GUI, no cloud.
"""

import argparse
import csv
import re
import sys


def parse_numbers(value, numeric_re=None):
    """Extract numbers from a string. If numeric_re, only match that pattern."""
    if numeric_re:
        try:
            return [float(m) for m in re.findall(numeric_re, value)]
        except (TypeError, ValueError):
            return []
    # default: find all numbers in the string
    matches = re.findall(r'-?\d+(?:\.\d+)?', value)
    return [float(m) for m in matches]


def load_values(arg, column=None, value_extract=None):
    """Return a list of floats from a CSV file path or inline numbers."""
    if arg.endswith('.csv'):
        try:
            with open(arg, newline='') as f:
                reader = csv.DictReader(f)
                if column:
                    out = []
                    for row in reader:
                        v = row.get(column, '')
                        nums = parse_numbers(v, value_extract)
                        out.extend(nums)
                    return out
                # try to find first numeric column — accumulate across all rows
                picked = None
                out = []
                for row in reader:
                    for k, v in row.items():
                        nums = parse_numbers(v, value_extract)
                        if nums:
                            if picked is None:
                                picked = k
                            if k == picked:
                                out.extend(nums)
                return out
        except Exception as e:
            print(f"error reading {arg}: {e}", file=sys.stderr)
            return []
    else:
        # inline numbers: treat every token as value
        return [float(x) for x in arg.split() if x.replace('.', '', 1).lstrip('-').isdigit()]


def bar_chart(values, width=40):
    if not values:
        return "(no data)"
    mn, mx = min(values), max(values)
    span = (mx - mn) or 1.0
    lines = []
    for i, v in enumerate(values):
        bar_len = max(1, int((v - mn) / span * (width - 1))) if mx != mn else 1
        bar = "█" * bar_len + "░" * ((width - 1) - bar_len)
        label = f"{v:.2f}" if isinstance(v, float) else str(v)
        lines.append(f"{label:>10} |{bar}|")
    return "\n".join(lines)


def sparkline(values, width=None):
    """Unicode sparkline — tiny, dense, great for terminals."""
    if not values:
        return "(no data)"
    # 8 vert levels: ▁▂▃▄▅▆▇█
    blocks = "▁▂▃▄▅▆▇█"
    mn, mx = min(values), max(values)
    span = (mx - mn) or 1.0
    points = [blocks[min(7, int((v - mn) / span * 7))] for v in values]
    return "".join(points)


def main():
    p = argparse.ArgumentParser(description="ASCII sunburst chart from CSV or numbers.")
    p.add_argument("source", nargs="*", help="CSV file or inline numbers (space separated — quote as one arg, or pass multiple)")
    p.add_argument("--column", help="CSV column name to chart")
    p.add_argument("--value-extract", help="regex to extract numeric values from CSV cells")
    p.add_argument("--width", type=int, default=42, help="bar chart width (default 42)")
    p.add_argument("--type", choices=["bar", "spark"], default="bar",
                   help="chart type: bar (default) or spark")
    p.add_argument("--spark", action="store_true", help="shorthand for --type spark")
    args = p.parse_args()

    if not args.source:
        # read from stdin if piped, else show help
        if sys.stdin.isatty():
            p.print_help()
            return 1
        source = sys.stdin.read().strip()
        values = [float(x) for x in source.split() if x.replace('.', '', 1).lstrip('-').isdigit()]
    else:
        # if first arg is a CSV path, use it; else join inline numbers
        joined = " ".join(args.source)
        if args.source[0].endswith('.csv'):
            values = load_values(args.source[0], args.column, args.value_extract)
        else:
            values = [float(x) for x in joined.split() if x.replace('.', '', 1).lstrip('-').isdigit()]

    if not values:
        print("no numeric data found", file=sys.stderr)
        return 1

    stype = "spark" if args.spark else args.type
    if stype == "spark":
        print(sparkline(values))
    else:
        print(bar_chart(values, width=args.width))
    return 0


if __name__ == "__main__":
    sys.exit(main())