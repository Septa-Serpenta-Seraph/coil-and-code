#!/usr/bin/env python3
"""md-toc — generate or insert a Table of Contents for Markdown files.

Scans ATX headings (# .. ######) and produces a nested, GitHub-flavored
Table of Contents with correct anchor links (lowercased, spaces -> dashes,
punctuation stripped, duplicate headings de-duplicated the way GitHub does).

Two modes:
  - Default: print the TOC to stdout (great for pasting into a README).
  - --insert: write the TOC into the file right after the first H1.

Zero external dependencies. Python 3.8+ stdlib only.

Examples:
  md-toc.py README.md
  md-toc.py docs/guide.md --max-depth 3 --json
  md-toc.py API.md --insert            # rewrites API.md with a TOC added
  md-toc.py CHANGELOG.md --skip-changelog-headings
"""
import argparse
import json
import re
import sys

# GitHub anchor rules: lowercase, strip punctuation, spaces -> dashes
ANCHOR_RE = re.compile(r"[^\w\- ]", re.UNICODE)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
FENCE_RE = re.compile(r"^(`{3,}|~{3,})")

# front-matter guard: YAML front matter (--- ... ---) is not markdown headings
SMART_FRONT_PATTERN = re.compile(r"^---\s*$")


def slugify(text):
    """GitHub-compatible anchor for a heading line."""
    lowered = text.strip().lower()
    lowered = ANCHOR_RE.sub("", lowered)
    lowered = lowered.replace(" ", "-")
    return lowered


def extract_headings(lines):
    """Return [(level, text, anchor)] for markdown headings outside code fences."""
    headings = []
    in_fence = False
    fence_char = None
    in_front = False
    front_checked = False
    counts = {}

    for line in lines:
        stripped = line.rstrip("\n")
        # YAML front matter: skip lines between leading --- pairs
        if not front_checked:
            if SMART_FRONT_PATTERN.match(stripped):
                in_front = not in_front
                if not in_front:
                    front_checked = True
                continue
            if in_front:
                continue
        # code fences: ignore headings inside them
        fm = FENCE_RE.match(stripped)
        if fm:
            if not in_fence:
                in_fence = True
                fence_char = fm.group(1)[0]
            elif fence_char == fm.group(1)[0] and stripped.strip(fence_char) == "":
                in_fence = False
            continue
        if in_fence:
            continue

        hm = HEADING_RE.match(stripped)
        if not hm:
            continue
        level = len(hm.group(1))
        text = hm.group(2).strip()
        # skip empty headings and pure-markdown-link headings?
        if not text:
            continue

        base = slugify(text)
        if base in counts:
            counts[base] += 1
            anchor = f"{base}-{counts[base]}"  # GitHub numbering starts at 1
        else:
            counts[base] = 0
            anchor = base
        yield level, text, anchor


def build_toc(headings, max_depth=6):
    """Nested markdown list of links."""
    out = []
    stack = [0]  # current degree at each level
    for level, text, anchor in headings:
        if level > max_depth:
            continue
        indent = "  " * (level - 1)
        out.append(f"{indent}- [{text}](#{anchor})")
    return out


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="Generate or insert a Table of Contents for Markdown files."
    )
    p.add_argument("files", nargs="+", help="Markdown file(s) to scan")
    p.add_argument("--max-depth", type=int, default=2,
                   help="Include headings up to this level (default: 2)")
    p.add_argument("--insert", action="store_true",
                   help="Insert the TOC into the file(s) after the first H1/H2")
    p.add_argument("--json", dest="as_json", action="store_true",
                   help="Emit JSON instead of markdown")
    p.add_argument("--no-front-matter", dest="respect_front", action="store_false",
                   help="Disable YAML front-matter skipping")
    return p.parse_args(argv)


def insert_toc(path, toc_lines, heading_lines):
    """Insert TOC after the first top-level heading (or after title)."""
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    lines = text.splitlines(keepends=True)

    # find insertion point: after first H1, else after first non-empty line
    idx = 0
    h_line_idx = None
    front_checked = False
    in_front = False
    for i, line in enumerate(lines):
        stripped = line.rstrip("\n")
        if SMART_FRONT_PATTERN.match(stripped):
            in_front = not in_front
            if not in_front:
                front_checked = True
            continue
        if in_front:
            continue
        m = HEADING_RE.match(stripped)
        if m and len(m.group(1)) == 1:
            h_line_idx = i
            break
    if h_line_idx is None:
        # no H1 — put after the first content line
        for i, line in enumerate(lines):
            if line.strip():
                h_line_idx = i
                break
    idx = (h_line_idx + 1) if h_line_idx is not None else 0

    toc = build_toc(heading_lines)
    block = "\n\n<!-- TOC: generated by md-toc -->\n" + "\n".join(toc) + "\n<!-- /TOC -->\n\n"
    # avoid double-inserting
    if "<!-- TOC: generated by md-toc -->" in text:
        # replace old block
        new = re.sub(
            r"<!-- TOC: generated by md-toc -->.*?<!-- /TOC -->\n*",
            block.lstrip("\n"),
            text,
            count=1,
            flags=re.S,
        )
    else:
        new = "".join(lines[:idx] + [block] + lines[idx:])
    with open(path, "w", encoding="utf-8") as f:
        f.write(new)
    return True


def main(argv=None):
    args = parse_args(argv)
    any_error = False
    for path in args.files:
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except OSError as e:
            print(f"md-toc: error: {e}", file=sys.stderr)
            any_error = True
            continue

        headings = list(extract_headings(lines))
        if args.as_json:
            payload = [
                {"level": lv, "text": tx, "anchor": a}
                for lv, tx, a in headings
            ]
            if len(args.files) == 1:
                print(json.dumps(payload, indent=2))
            else:
                print(json.dumps({path: payload}, indent=2))
        else:
            toc = build_toc(headings, args.max_depth)
            if args.insert:
                try:
                    insert_toc(path, "\n".join(toc), headings)
                    print(f"md-toc: inserted {len(toc)} entries into {path}")
                except OSError as e:
                    print(f"md-toc: {path}: {e}", file=sys.stderr)
                    any_error = True
            else:
                print("\n".join(toc))
    return 1 if any_error else 0


if __name__ == "__main__":
    sys.exit(main())