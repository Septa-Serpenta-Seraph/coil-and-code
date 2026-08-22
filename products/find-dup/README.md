# find-dup

Find duplicate files fast, using **size-then-hash**. Zero dependencies, Python 3.8+ stdlib only.

Ever had three `final_final_v2 (1).pdf` copies scattered across folders? `find-dup` groups files that are genuinely identical by content — not just same-named — and tells you exactly how much space they're wasting.

## What it does

- Walks one or more directories recursively
- Groups files by **size first** — so big unique files are never read twice
- Then SHA-256-hashes only the files whose size appeared more than once
- Reports each duplicate group + the reclaimable bytes

## Usage

```bash
python3 find-dup.py ~/Downloads ~/Documents
python3 find-dup.py . --min-size 1000 --json
python3 find-dup.py ~/Pictures --total
```

| Flag | Purpose |
|------|---------|
| `--min-size N` | ignore files smaller than N bytes (default 1) |
| `--json` | machine-readable JSON output |
| `--total` | just the total reclaimable bytes (script-friendly) |
| `--remove-duplicates` | **DELETE** all but the first file in each group — irreversible, use with care |

## Example

```bash
$ python3 find-dup.py ~/Downloads
1.2 MB × 3 → 2.4 MB wasted
   /home/you/Downloads/report.pdf
   /home/you/Downloads/old/report.pdf
   /home/you/backups/report.pdf

2.4 MB (2.4 MB) reclaimable total
```

## Nice touches

- Skips `.git`, `__pycache__`, `node_modules`, `.venv`, `venv` automatically
- Handles unicode paths, nested dirs, empty dirs, and permission errors gracefully
- `--remove-duplicates` keeps the **first** path and removes the rest — but you got the list first, right?

## License

MIT — see `LICENSE`.