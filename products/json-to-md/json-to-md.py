#!/usr/bin/env python3
"""json-to-md — convert JSON arrays into Markdown tables (or back).

A small, dependency-free tool for turning API responses, config dumps, or
exported JSON into readable Markdown tables — and for extracting tables
from Markdown back into JSON.

Examples:
  python3 json-to-md.py data.json --table
  python3 json-to-md.py data.json --table --columns name,age,city
  python3 json-to-md.py data.json --flatten          # array of objects -> NDJSON lines
  cat table.md | python3 json-to-md.py --from-md -

Python 3.8+ stdlib only. The truth is in the exit code.
"""

import argparse
import json
import re
import sys


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Convert JSON <-> Markdown tables.")
    p.add_argument("input", nargs="?", default="-",
                   help="Input file, or - for stdin")
    p.add_argument("--table", action="store_true",
                   help="Convert array of objects to a Markdown table")
    p.add_argument("--columns", default="",
                   help="Comma-separated column order (default: first object's keys)")
    p.add_argument("--from-md", action="store_true",
                   help="Parse a Markdown table from input into JSON")
    p.add_argument("--table-index", type=int, default=0,
                   help="Which table to extract with --from-md (0-based, default 0)")
    p.add_argument("--flatten", action="store_true",
                   help="Flatten array of objects to one JSON object per line (NDJSON)")
    return p.parse_args(argv)


def read_input(path):
    if path == "-":
        return sys.stdin.read()
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def to_md_table(data, columns):
    if not isinstance(data, list) or not data:
        raise ValueError("--table requires a non-empty JSON array of objects")
    if not all(isinstance(r, dict) for r in data):
        raise ValueError("--table requires an array of objects")
    cols = columns.split(",") if columns else list(data[0].keys())
    # Include any keys that appear later too
    for r in data:
        for k in r:
            if k not in cols:
                cols.append(k)

    def cell(v):
        if v is None:
            return ""
        if isinstance(v, (dict, list)):
            return json.dumps(v).replace("|", "\\|").replace("\n", "\\n")
        return str(v).replace("|", "\\|").replace("\n", "\\n")

    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join("---" for _ in cols) + " |"
    lines = [header, sep]
    for r in data:
        lines.append("| " + " | ".join(cell(r.get(c, "")) for c in cols) + " |")
    return "\n".join(lines)


def unescape_cell(s):
    """Reverse the \\| and \\n escaping applied by to_md_table."""
    return s.replace("\\n", "\n").replace("\\|", "|")


def split_row(line):
    """Split a Markdown table row into cells, respecting escaped pipes (\\|)."""
    body = line.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|"):
        body = body[:-1]
    cells = []
    cur = []
    i = 0
    while i < len(body):
        ch = body[i]
        if ch == "\\" and i + 1 < len(body) and body[i + 1] == "|":
            cur.append("\\|")
            i += 2
            continue
        if ch == "|":
            cells.append("".join(cur).strip())
            cur = []
            i += 1
            continue
        cur.append(ch)
        i += 1
    cells.append("".join(cur).strip())
    return cells


def from_md(text, table_index=0):
    """Parse Markdown table(s) from text. Returns list[dict] for one table.

    Tables are detected by a header row followed by a separator row. Each
    table is parsed independently (multi-table documents no longer merge).
    table_index selects which table to return (0-based).
    """
    lines = text.splitlines()
    tables = []  # each: {"header": [...], "rows": [[...], ...]}
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not (line.startswith("|") and line.endswith("|")):
            i += 1
            continue
        header = [unescape_cell(c) for c in split_row(line)]
        # separator row must immediately follow
        if i + 1 >= len(lines):
            i += 1
            continue
        sep = lines[i + 1].strip()
        if not (sep.startswith("|") and sep.endswith("|")):
            i += 1
            continue
        sep_cells = split_row(sep)
        if not all(set(c) <= set("-: ") and c for c in sep_cells):
            i += 1
            continue  # not actually a table header
        rows = []
        j = i + 2
        while j < len(lines):
            rline = lines[j].strip()
            if not (rline.startswith("|") and rline.endswith("|")):
                break
            cells = [unescape_cell(c) for c in split_row(rline)]
            if all(set(c) <= set("-: ") and c for c in cells):
                break  # start of another separator (e.g. next table boundary)
            rows.append(cells)
            j += 1
        tables.append({"header": header, "rows": rows})
        i = j

    if not tables:
        raise ValueError("no Markdown table found in input")
    if table_index < 0 or table_index >= len(tables):
        raise ValueError(
            f"table index {table_index} out of range (found {len(tables)} table(s))"
        )
    t = tables[table_index]
    out = []
    for cells in t["rows"]:
        out.append({h: c for h, c in zip(t["header"], cells)})
    return out


def main(argv=None):
    args = parse_args(argv)
    try:
        raw = read_input(args.input)
    except FileNotFoundError:
        print(f"ERROR: file not found: {args.input}", file=sys.stderr)
        return 2

    try:
        if args.from_md:
            result = from_md(raw, args.table_index)
            print(json.dumps(result, indent=2))
            return 0

        data = json.loads(raw)

        if args.table:
            print(to_md_table(data, args.columns))
            return 0

        if args.flatten:
            if not isinstance(data, list):
                raise ValueError("--flatten requires a JSON array")
            for item in data:
                print(json.dumps(item))
            return 0

        # Default: pretty-print
        print(json.dumps(data, indent=2))
        return 0

    except (json.JSONDecodeError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
