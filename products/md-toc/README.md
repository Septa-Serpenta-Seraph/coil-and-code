# md-toc

Generate or insert a Table of Contents for Markdown files — with GitHub-exact
anchor links. No dependencies. One file. Python 3.8+.

## Why

Documentation grows. READMEs sprawl. A TOC keeps them navigable — but writing
it by hand means maintaining anchor links that silently break when a heading
changes. `md-toc` does it for you, the way GitHub resolves anchors:

- lowercases headings
- strips punctuation (`,`, `:`, `&`, `!`, ...)
- turns spaces into dashes
- suffixes duplicates (`Usage` → `#usage`, `Usage` → `#usage-1`) exactly like GitHub

## Install

```bash
# no pip needed — it's one file
cp md-toc.py /usr/local/bin/md-toc
chmod +x /usr/local/bin/md-toc
```

Or run it in place: `python3 md-toc.py ...`

## Usage

```bash
# print a TOC for a README (default: H1 + H2)
md-toc README.md

# include deeper headings
md-toc docs/guide.md --max-depth 4

# write the TOC into the file, after the first H1
md-toc API.md --insert

# machine-readable (for scripts / CI)
md-toc CHANGELOG.md --json
```

The `--insert` mode is idempotent: re-running it replaces the previous
generated TOC block (marked with `<!-- TOC -->` comments) instead of
duplicating.

## What it skips

- YAML front matter (`---`)
- headings inside ```code fences```
- indented code blocks

## Family

Part of the Coil and Code CLI toolkit:
`csv-report` · `log-analyzer` · `json-to-md` · `csv-merge` · **`md-toc`**

MIT licensed. The exit code is honest — `1` if any input file fails.