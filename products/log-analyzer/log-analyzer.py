#!/usr/bin/env python3
"""log-analyzer — summarize Apache/nginx access logs from the CLI.

A small, dependency-free tool for anyone running a web server who wants
quick answers from their access logs without loading them into a BI tool.

Examples:
  python3 log-analyzer.py access.log --top-ips 10
  python3 log-analyzer.py access.log --top-paths 10 --status-errors
  python3 log-analyzer.py access.log --hourly --json

Parses the Apache Combined Log Format (the nginx default too).
Python 3.8+ stdlib only. The truth is in the exit code.
"""

import argparse
import json
import re
import sys
from collections import Counter, defaultdict

_LOG_LINE = re.compile(
    r'^(\S+) (\S+) (\S+) \[([^\]]+)\] "(\S+) (\S+) (\S+)" (\d{3}) (\S+)'
    r'(?: "([^"]*)" "([^"]*)")?$'
)


def parse_log(log_text):
    rows = []
    for line in log_text.splitlines():
        line = line.strip()
        if not line:
            continue
        m = _LOG_LINE.match(line)
        if not m:
            continue
        ip, _identd, user, timestamp, method, path, protocol, status, size = m.groups()[:9]
        referer = m.group(9) if m.lastindex and m.lastindex >= 10 else None
        user_agent = m.group(10) if m.lastindex and m.lastindex >= 10 else None
        rows.append({
            "ip": ip,
            "user": None if user == "-" else user,
            "timestamp": timestamp,
            "method": method,
            "path": path,
            "protocol": protocol,
            "status": int(status),
            "bytes": 0 if size == "-" else int(size),
            "referer": referer,
            "user_agent": user_agent,
        })
    return rows


def read_log(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Summarize Apache/nginx access logs.")
    p.add_argument("log_file", help="Path to the access log")
    p.add_argument("--top-ips", type=int, default=0, metavar="N",
                   help="Show top N client IPs")
    p.add_argument("--top-paths", type=int, default=0, metavar="N",
                   help="Show top N requested paths")
    p.add_argument("--top-methods", type=int, default=0, metavar="N",
                   help="Show top N HTTP methods")
    p.add_argument("--status-errors", action="store_true",
                   help="List 4xx/5xx statuses with counts")
    p.add_argument("--hourly", action="store_true",
                   help="Group requests by hour (from the log timestamp)")
    p.add_argument("--json", dest="as_json", action="store_true",
                   help="Emit JSON instead of tables")
    return p.parse_args(argv)


def hour_of(timestamp):
    # Apache format: 10/Oct/2000:13:55:36 -0700
    m = re.match(r"\d{2}/\w{3}/\d{4}:(\d{2})", timestamp)
    return m.group(1) if m else "?"


def main(argv=None):
    args = parse_args(argv)
    try:
        rows = parse_log(read_log(args.log_file))
    except FileNotFoundError:
        print(f"ERROR: file not found: {args.log_file}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"ERROR reading log: {e}", file=sys.stderr)
        return 2

    if not rows:
        print("ERROR: no parseable lines in log (Apache Combined format expected)",
              file=sys.stderr)
        return 2

    total_bytes = sum(r["bytes"] for r in rows)
    ip_counter = Counter(r["ip"] for r in rows)
    path_counter = Counter(r["path"] for r in rows)
    method_counter = Counter(r["method"] for r in rows)
    status_counter = Counter(r["status"] for r in rows)
    errors = Counter(r["status"] for r in rows if r["status"] >= 400)
    hourly = Counter(hour_of(r["timestamp"]) for r in rows)

    if args.as_json:
        out: dict = {
            "lines_parsed": len(rows),
            "total_bytes": total_bytes,
            "unique_ips": len(ip_counter),
            "unique_paths": len(path_counter),
        }
        if args.top_ips:
            out["top_ips"] = dict(ip_counter.most_common(args.top_ips))
        if args.top_paths:
            out["top_paths"] = dict(path_counter.most_common(args.top_paths))
        if args.top_methods:
            out["top_methods"] = dict(method_counter.most_common(args.top_methods))
        if args.status_errors:
            out["error_statuses"] = dict(errors.most_common())
        if args.hourly:
            out["hourly_requests"] = {h: hourly[h] for h in sorted(hourly)}
        print(json.dumps(out, indent=2))
        return 0

    print(f"Lines parsed: {len(rows)}   Bytes served: {total_bytes:,}   "
          f"Unique IPs: {len(ip_counter)}   Unique paths: {len(path_counter)}")
    print()
    if args.top_ips:
        print(f"Top {args.top_ips} client IPs:")
        for ip, n in ip_counter.most_common(args.top_ips):
            print(f"  {n:>6}  {ip}")
        print()
    if args.top_paths:
        print(f"Top {args.top_paths} paths:")
        for path, n in path_counter.most_common(args.top_paths):
            print(f"  {n:>6}  {path}")
        print()
    if args.top_methods:
        print(f"Top {args.top_methods} methods:")
        for method, n in method_counter.most_common(args.top_methods):
            print(f"  {n:>6}  {method}")
        print()
    if args.status_errors:
        print("Error statuses (4xx/5xx):")
        if errors:
            for status, n in errors.most_common():
                print(f"  {status}: {n}")
        else:
            print("  (none)")
        print()
    if args.hourly:
        print("Requests by hour (00-23):")
        for h in sorted(hourly):
            bar = "#" * hourly[h]
            print(f"  {h}:00 {hourly[h]:>4}  {bar}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
