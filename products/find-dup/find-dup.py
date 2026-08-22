#!/usr/bin/env python3
"""find-dup — find duplicate files fast, using size-then-hash.

Zero dependencies. Python 3.8+, stdlib only.

Usage:
  python3 find-dup.py /path/to/dir [more/dirs...] [--min-size 1KB] [--json]

Groups files that share identical content. First pass groups by size,
second pass hashes only the files whose size was seen more than once, so
big unique files are never read twice.
"""

import argparse
import hashlib
import json
import os
import sys

CHUNK = 1024 * 1024  # 1 MiB


def file_size(path):
    try:
        return os.path.getsize(path)
    except OSError:
        return None


def hash_file(path):
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            while True:
                chunk = f.read(CHUNK)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def walk_files(paths):
    for root_dir in paths:
        for dirpath, dirnames, filenames in os.walk(root_dir):
            # skip common noise dirs
            dirnames[:] = [d for d in dirnames if d not in (".git", "__pycache__", "node_modules", ".venv", "venv")]
            for name in filenames:
                full = os.path.join(dirpath, name)
                yield full


def find_duplicates(paths, min_size=1):
    by_size = {}
    for path in walk_files(paths):
        size = file_size(path)
        if size is None or size < min_size:
            continue
        by_size.setdefault(size, []).append(path)

    groups = []
    for size, files in by_size.items():
        if len(files) < 2:
            continue
        # hash only the files in this size group
        by_hash = {}
        for path in files:
            digest = hash_file(path)
            if digest is None:
                continue
            by_hash.setdefault(digest, []).append(path)
        for digest, dupes in by_hash.items():
            if len(dupes) > 1:
                groups.append((size, dupes))
    return groups


def human_size(n):
    units = ["B", "KB", "MB", "GB", "TB"]
    val = float(n)
    for unit in units:
        if val < 1024 or unit == units[-1]:
            return f"{val:.1f} {unit}" if unit != "B" else f"{int(val)} B"
        val /= 1024
    return f"{n} B"


def main():
    parser = argparse.ArgumentParser(
        description="Find duplicate files by content (size + SHA-256).")
    parser.add_argument("paths", nargs="+", help="directories to scan")
    parser.add_argument("--min-size", type=int, default=1,
                        help="ignore files smaller than this many bytes (default 1)")
    parser.add_argument("--json", action="store_true",
                        help="output machine-readable JSON")
    parser.add_argument("--total", action="store_true",
                        help="only print total wasted bytes")
    parser.add_argument("--remove-duplicates", action="store_true",
                        help="DELETE all but the first file in each duplicate group "
                             "(irreversible — use with care)")
    args = parser.parse_args()

    groups = find_duplicates(args.paths, min_size=args.min_size)

    if args.json:
        print(json.dumps([
            {"bytes": size, "files": dupes}
            for size, dupes in groups
        ], indent=2))
        return

    total = sum(size * (len(dupes) - 1) for size, dupes in groups)
    if args.total or args.remove_duplicates:
        print(f"{total} bytes reclaimable"
              + (f" across {len(groups)} group(s)" if not args.total else ""))
        if args.remove_duplicates:
            removed = 0
            for size, dupes in groups:
                for path in dupes[1:]:
                    try:
                        os.remove(path)
                        removed += size
                    except OSError as e:
                        print(f"  !! could not remove {path}: {e}", file=sys.stderr)
            print(f"removed {removed} bytes")
        return

    if not groups:
        print("No duplicates found.")
        return
    total = 0
    for size, dupes in groups:
        total += size * (len(dupes) - 1)
        print(f"{human_size(size)} × {len(dupes)} → {human_size(size * (len(dupes) - 1))} wasted")
        for p in dupes:
            print(f"   {p}")
    print(f"\n{total} bytes ({human_size(total)}) reclaimable total")


if __name__ == "__main__":
    main()