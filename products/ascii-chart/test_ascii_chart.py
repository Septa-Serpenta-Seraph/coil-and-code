#!/usr/bin/env python3
"""Tests for ascii-chart.py — run with: python3 test_ascii_chart.py"""
import json
import subprocess
import sys
import tempfile
import os

HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = os.path.join(HERE, "ascii-chart.py")


def run(*args, stdin=None):
    return subprocess.run(
        [sys.executable, TOOL] + list(args),
        capture_output=True, text=True,
        input=stdin,  # None → inherit (no stdin pipe), str → feed it
    )


def expect(cond, msg):
    if not cond:
        print(f"FAIL: {msg}")
        sys.exit(1)
    print(f"ok: {msg}")


def tmp_file(content, ext=".csv"):
    f = tempfile.NamedTemporaryFile(suffix=ext, delete=False, mode="w")
    f.write(content)
    f.close()
    return f.name


def main():
    # 1. inline numbers → bar chart
    r = run("3 1 4 1 5 9 2 6", "--type", "bar")
    expect(r.returncode == 0, "inline bar chart exits 0")
    expect("█" in r.stdout and "|" in r.stdout, "bar chart renders bars")

    # 2. sparkline
    r = run("3 1 4 1 5 9 2 6", "--spark")
    expect(r.returncode == 0, "--spark exits 0")
    expect(len(r.stdout.strip()) == 8, f"spark has 8 chars, got {len(r.stdout.strip())}")
    expect(any(c in r.stdout for c in "▁▂▃▄▅▆▇█"), "spark uses unicode blocks")

    # 3. CSV with column
    f = tmp_file("day,revenue\nmon,100\ntue,250\nwed,150\n")
    r = run(f, "--column", "revenue")
    expect(r.returncode == 0, "csv --column exits 0")
    expect("100.00" in r.stdout and "250.00" in r.stdout, "csv values reflected")
    os.unlink(f)

    # 4. CSV auto numeric detection
    f = tmp_file("a,b\n1,2\n3,4\n")
    r = run(f, "--column", "b")
    expect(r.returncode == 0, "csv --column b exits 0")
    expect("2.00" in r.stdout and "4.00" in r.stdout, "column b values")
    os.unlink(f)

    # 5. value-extract regex (real CSV with header + --column)
    f = tmp_file("row,log\n1,status:200\n2,status:404\n3,latency:37ms\n")
    r = run(f, "--column", "log", "--value-extract", r"status:(\d+)")
    expect(r.returncode == 0, "value-extract exits 0")
    expect("200.00" in r.stdout and "404.00" in r.stdout, "extracted status codes")
    os.unlink(f)

    # 6. stdin pipeline
    r = run("--type", "spark", stdin="5 10 15 20")
    expect(r.returncode == 0, "stdin spark exits 0")
    expect(len(r.stdout.strip()) == 4, "stdin spark has 4 points")

    # 7. empty / no data
    r = run()
    expect(r.returncode == 1, "no args exits 1 (no data)")
    r = run("")
    expect("no numeric data" in (r.stdout + r.stderr) or r.returncode == 1, "empty source handled")

    # 8. negative + decimals
    r = run("-1.5 0 1.5 3", "--spark")
    expect(r.returncode == 0, "negatives/decimals ok")
    expect(len(r.stdout.strip()) == 4, "4 spark points")

    # 9. larger input stability
    r = run(" ".join(str(i) for i in range(50)), "--type", "bar", "--width", "30")
    expect(r.returncode == 0, "50-point bar exits 0")
    expect(r.stdout.count("\n") >= 49, "50 bar rows")

    # 10. missing file errors gracefully
    r = run("/nonexistent/file.csv", "--column", "x")
    expect(r.returncode == 1, "missing file returns non-zero")

    print("ALL TESTS PASS")


if __name__ == "__main__":
    main()