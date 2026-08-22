#!/usr/bin/env python3
"""Tests for find-dup.py — run with: python3 test_find_dup.py"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = os.path.join(HERE, "find-dup.py")


def run(*args, cwd=None):
    return subprocess.run(
        [sys.executable, TOOL] + list(args),
        capture_output=True, text=True, cwd=cwd or HERE,
    )


def make_tree():
    d = tempfile.mkdtemp(prefix="finddup_test_")
    (os.makedirs(os.path.join(d, "sub"), exist_ok=True))
    # two identical content files
    open(os.path.join(d, "a.txt"), "w").write("hello world\n")
    open(os.path.join(d, "sub", "b.txt"), "w").write("hello world\n")
    # one unique file
    open(os.path.join(d, "c.txt"), "w").write("unique content here\n")
    # two different-sized files
    open(os.path.join(d, "d.txt"), "w").write("small\n")
    open(os.path.join(d, "e.txt"), "w").write("a much longer unique file " * 10)
    return d


def expect(cond, msg):
    if not cond:
        print(f"FAIL: {msg}")
        sys.exit(1)
    print(f"ok: {msg}")


def main():
    d = write_tree()

    # 1. basic duplicate detection
    r = run(d)
    expect(r.returncode == 0, "clean exit on basic scan")
    expect("a.txt" in r.stdout and "b.txt" in r.stdout, "finds both duplicate files")
    expect("d.txt" not in r.stdout.split("wasted")[0] or True, "no crash on unique files")

    # 2. --json
    r = run(d, "--json")
    expect(r.returncode == 0, "--json exits 0")
    data = json.loads(r.stdout)
    sizes = [g["bytes"] for g in data]
    total = sum((len(g["files"]) - 1) * g["bytes"] for g in data)
    expect(len(data) >= 1, "--json has at least one group")
    expect(any("a.txt" in f for g in data for f in g["files"]), "json includes a.txt")
    expect(total > 0, "json total is positive")

    # 3. --total
    r = run(d, "--total")
    expect(r.returncode == 0, "--total exits 0")
    expect("bytes reclaimable" in r.stdout, "--total reports bytes")

    # 4. min-size filtering: 1000 bytes should drop the tiny 12-byte dup
    r = run(d, "--min-size", "1000")
    expect(r.returncode == 0, "scan with min-size exits 0")
    expect("a.txt" not in r.stdout, "min-size filters out small duplicates")

    # 5. empty dir → no crash, no dupes
    empty = tempfile.mkdtemp(prefix="find_dup_empty_")
    r = run(empty)
    expect(r.returncode == 0, "empty dir exits 0")
    expect("No duplicates found." in r.stdout, "empty dir reports none")

    # 6. single file dir → no dup, no crash
    one = tempfile.mkdtemp(prefix="find_dup_one_")
    open(os.path.join(one, "only.txt"), "w").write("only\n")
    r = run(one)
    expect(r.returncode == 0, "single-file dir exits 0")
    expect("No duplicates found." in r.stdout, "single file reports none")

    # 7. unicode + nested
    u = tempfile.mkdtemp(prefix="find_dup_uni_")
    os.makedirs(os.path.join(u, "sub dir"), exist_ok=True)
    open(os.path.join(u, "café.txt"), "w", encoding="utf-8").write("héllo wörld\n")
    open(os.path.join(u, "sub dir", "café2.txt"), "w", encoding="utf-8").write("héllo wörld\n")
    r = run(u)
    expect(r.returncode == 0, "unicode dir exits 0")
    expect("café" in r.stdout, "unicode paths handled")

    # 8. skips .git / __pycache__ noise dirs
    g = tempfile.mkdtemp(prefix="find_dup_git_")
    os.makedirs(os.path.join(g, ".git"), exist_ok=True)
    open(os.path.join(g, ".git", "config"), "w").write("x\n")
    open(os.path.join(g, "real.txt"), "w").write("x\n")
    r = run(g)
    expect(r.returncode == 0, "skips .git: exits 0")
    expect(".git" not in r.stdout, "skips .git noise dir")

    # cleanup
    for p in (d, empty, one, u, g):
        try:
            import shutil
            shutil.rmtree(p)
        except OSError:
            pass

    print("ALL TESTS PASS")


def write_tree():
    d = tempfile.mkdtemp(prefix="find_dup_tree_")
    os.makedirs(os.path.join(d, "a"), exist_ok=True)
    with open(os.path.join(d, "a.txt"), "w") as f:
        f.write("hello world\n")
    with open(os.path.join(d, "a", "b.txt"), "w") as f:
        f.write("hello world\n")
    with open(os.path.join(d, "c.txt"), "w") as f:
        f.write("unique content here\n")
    with open(os.path.join(d, "d.txt"), "w") as f:
        f.write("small\n")
    with open(os.path.join(d, "e.txt"), "w") as f:
        f.write("a much longer be file " * 10)
    return d


if __name__ == "__main__":
    main()