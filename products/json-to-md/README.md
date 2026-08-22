# json-to-md

**Convert JSON to Markdown tables — and Markdown tables back to JSON.**

A small, dependency-free tool for turning API responses, config dumps, or
exported JSON into readable Markdown tables — and for extracting tables
from Markdown back into structured JSON.

```
$ python3 json-to-md.py data.json --table
| name | age | city |
| --- | --- | --- |
| Alice | 30 | Santa Fe |
| Bob | 25 | Albuquerque |
```

## Why you'd want it

- **Instant docs:** API responses → readable tables for reports, wikis, READMEs.
- **Round-trip:** pull a table out of any Markdown file as clean JSON for scripts.
- **Zero dependencies, zero install:** Python 3.8+ stdlib only. Your data never
  leaves your machine.
- **Pipe-friendly:** works with stdin/stdout, so it slots into any pipeline.

## Usage

```
python3 json-to-md.py INPUT [options]
```

| Option | Description |
|--------|-------------|
| `--table` | Convert a JSON array of objects to a Markdown table |
| `--columns a,b,c` | Specify column order (default: first object's keys) |
| `--from-md` | Parse a Markdown table from input into JSON |
| `--table-index N` | With `--from-md`: which table to extract, 0-based (default 0) |
| `--flatten` | Output one JSON object per line (NDJSON) |
| `-` (input) | Read from stdin |

### Examples

```bash
# JSON to Markdown table
python3 json-to-md.py data.json --table

# Reorder columns
python3 json-to-md.py data.json --table --columns city,name

# Extract a table from a README as JSON
cat notes.md | python3 json-to-md.py --from-md -

# Extract the SECOND table from a multi-table document
cat notes.md | python3 json-to-md.py --from-md - --table-index 1

# Flatten for streaming tools
python3 json-to-md.py data.json --flatten
```

## Requirements

- Python 3.8+
- Nothing else. Seriously — stdlib only.

## License

MIT — use it, fork it, ship it. Credit appreciated, not required.

---

*Built by Sunburst Sanctuary LLC. Verifiable work, clean hands.*
