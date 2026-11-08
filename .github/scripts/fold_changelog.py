#!/usr/bin/env python3
"""Fold changelog fragments and the Unreleased section into a version section.

usage: fold_changelog.py VERSION DATE [--root DIR]

Reads CHANGELOG.md and changelog.d/*.md (README.md excluded), writes the new
section under an empty Unreleased heading, deletes the fragments and prints
the new section's body to stdout.
"""
import argparse
import re
import sys
from pathlib import Path

ORDER = ["Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"]


def parse(text):
    """Return {heading: [bullet block, ...]} for a body of ### sections."""
    out, heading, block = {}, None, []

    def flush():
        if heading is not None and block:
            out.setdefault(heading, []).append("\n".join(block).rstrip())

    for line in text.splitlines():
        m = re.match(r"^###\s+(.+?)\s*$", line)
        if m:
            flush()
            heading, block = m.group(1), []
        elif line.startswith("- "):
            flush()
            block = [line]
        elif block and (line.startswith(" ") or not line.strip()):
            block.append(line)
        elif line.strip():
            raise ValueError(f"text outside a bullet under a heading: {line!r}")
    flush()
    return out


def merge(*parts):
    merged = {}
    for part in parts:
        for heading, blocks in part.items():
            merged.setdefault(heading, []).extend(blocks)
    return merged


def render(sections):
    names = [h for h in ORDER if h in sections]
    names += sorted(h for h in sections if h not in ORDER)
    return "\n\n".join(f"### {h}\n\n" + "\n".join(sections[h]) for h in names)


def fold(changelog, fragments, version, date):
    m = re.search(r"^## \[Unreleased\][ \t]*\n", changelog, re.M)
    if not m:
        raise ValueError("CHANGELOG.md has no Unreleased section")
    rest = changelog[m.end():]
    nxt = re.search(r"^## \[", rest, re.M)
    unreleased = rest[: nxt.start()] if nxt else rest
    tail = rest[nxt.start():] if nxt else ""
    body = render(merge(parse(unreleased), *[parse(f) for f in fragments]))
    if not body:
        raise ValueError("nothing to release: no fragments and Unreleased is empty")
    section = f"## [{version}] - {date}\n\n{body}\n"
    return changelog[: m.end()] + "\n" + section + "\n" + tail, body


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("version")
    ap.add_argument("date")
    ap.add_argument("--root", default=".")
    a = ap.parse_args()
    if not re.fullmatch(r"v\d+\.\d+\.\d+", a.version):
        sys.exit(f"not a version: {a.version}")
    root = Path(a.root)
    files = sorted(p for p in (root / "changelog.d").glob("*.md") if p.name != "README.md")
    path = root / "CHANGELOG.md"
    new, body = fold(path.read_text(), [p.read_text() for p in files], a.version, a.date)
    path.write_text(new)
    for p in files:
        p.unlink()
    print(body)


if __name__ == "__main__":
    main()
