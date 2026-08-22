# log-analyzer

**Summarize Apache/nginx access logs from the CLI — no BI tool required.**

A small, dependency-free tool for anyone running a web server who wants quick
answers from their access logs: top clients, top paths, error statuses, and
request volume by hour — as a clean table or machine-readable JSON.

```
$ python3 log-analyzer.py access.log --top-ips 5 --status-errors
Lines parsed: 12,345   Bytes served: 1,024,567   Unique IPs: 312   Unique paths: 89

Top 5 client IPs:
    1234  203.0.113.7
     987  198.51.100.2
     ...
```

## Why you'd want it

- **Immediate answers:** "who's hammering my server?" or "how many 500s today?"
  — one command, no dashboard setup.
- **Parses the standard:** Apache Combined Log Format (also the nginx default).
- **Zero dependencies, zero install:** Python 3.8+ stdlib only. Your logs never
  leave your machine.
- **Automation-friendly:** pipe the `--json` output into monitoring, cron, or
  an n8n workflow.

## Usage

```
python3 log-analyzer.py LOG_FILE [options]
```

| Option | Description |
|--------|-------------|
| `--top-ips N` | Show top N client IPs by request count |
| `--top-paths N` | Show top N requested paths |
| `--top-methods N` | Show top N HTTP methods |
| `--status-errors` | List 4xx/5xx statuses with counts |
| `--hourly` | Group requests by hour (from log timestamps) |
| `--json` | Output JSON instead of tables |

### Examples

```bash
# Who are the top visitors?
python3 log-analyzer.py access.log --top-ips 10

# What paths are most popular, and are there errors?
python3 log-analyzer.py access.log --top-paths 10 --status-errors

# Feed hourly volume into your monitoring pipeline
python3 log-analyzer.py access.log --hourly --json
```

## Requirements

- Python 3.8+
- Nothing else. Seriously — stdlib only.

## License

MIT — use it, fork it, ship it. Credit appreciated, not required.

---

*Built by Sunburst Sanctuary LLC. Verifiable work, clean hands.*
