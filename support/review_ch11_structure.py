#!/usr/bin/env python3
"""Review and normalize the CH11 Markdown draft without changing the original.

Preview by default. --apply creates a separate reviewed draft and refuses to
overwrite an existing file. Python 3.11 standard library only.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Exact headings extracted from the first DOCX conversion (before -> after).
CHANGES = (
    ("### 3 作業用UnityとPython環境", "## 3 作業用UnityとPython環境"),
    ("### 5 1 必要な環境", "### 5.1 必要な環境"),
    ("### 5 2 ファイルを配置する", "### 5.2 ファイルを配置する"),
    ("### 5 3 会話用シーンを作成する", "### 5.3 会話用シーンを作成する"),
    ("### 6 1 Python環境を確認する", "### 6.1 Python環境を確認する"),
    ("### 6 2 Ollamaを起動する", "### 6.2 Ollamaを起動する"),
    ("### 6 3 AIRManagerとGUIを起動する", "### 6.3 AIRManagerとGUIを起動する"),
    ("### 6 4 Unityを再生する", "### 6.4 Unityを再生する"),
    ("### 8 会話機能を試す場合", "## 8 会話機能を試す場合"),
    ("### 9 うまく動かない場合", "## 9 うまく動かない場合"),
    ("### 10 終了する", "## 10 終了する"),
)


def table_blocks(text: str) -> list[list[str]]:
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in text.splitlines():
        if line.startswith("| ") and line.endswith(" |"):
            current.append(line)
        elif current:
            blocks.append(current)
            current = []
    if current:
        blocks.append(current)
    return blocks


def column_count(row: str) -> int:
    return len(re.split(r"(?<!\\)\|", row)) - 2


def main() -> int:
    parser = argparse.ArgumentParser(description="Preview/check CH11 heading hierarchy and table structure")
    parser.add_argument("--apply", action="store_true", help="Create a separate reviewed Markdown draft; do not overwrite")
    args = parser.parse_args()
    repo = Path(__file__).resolve().parent.parent
    original = repo / "documents" / "CH11-ConversionDraft.md"
    reviewed = repo / "documents" / "CH11-ReviewedDraft.md"
    if not original.is_file():
        raise ValueError(f"Source not found: {original}")

    raw = original.read_bytes()
    had_bom = raw.startswith(b"\xef\xbb\xbf")
    source = raw.decode("utf-8-sig")
    lines = source.splitlines(keepends=True)
    original_heads = [line.strip() for line in lines if re.match(r"^#{1,6} ", line)]
    if len(original_heads) != 18:
        raise ValueError(f"Expected 18 headings, found {len(original_heads)}. No changes made.")

    # Reject if conversion changed unexpectedly, rather than silently modifying content.
    for before, _ in CHANGES:
        count = sum(line.rstrip("\r\n") == before for line in lines)
        if count != 1:
            raise ValueError(f"Expected exactly one occurrence of {before!r}, found {count}. No changes made.")

    mapping = dict(CHANGES)
    adjusted = []
    for line in lines:
        body = line.rstrip("\r\n")
        newline = line[len(body):]
        adjusted.append(mapping.get(body, body) + newline)
    output = "".join(adjusted)

    before_tables = table_blocks(source)
    after_tables = table_blocks(output)
    if len(before_tables) != 8 or len(after_tables) != 8:
        raise ValueError(f"Expected 8 Markdown tables; found {len(before_tables)} / {len(after_tables)}. No changes made.")
    if any(len(set(map(column_count, rows))) != 1 for rows in after_tables):
        raise ValueError("A Markdown table has mismatched column counts. No changes made.")
    # Confirm that heading replacement is the *only* text difference.
    if [line for line in source.splitlines() if not line.startswith("#")] != [line for line in output.splitlines() if not line.startswith("#")]:
        raise ValueError("Non-heading text changed unexpectedly. No changes made.")

    print("=== CH11 structure review (" + ("APPLY" if args.apply else "PREVIEW") + ") ===")
    print(f"Source: {original}")
    print(f"Target: {reviewed}")
    print(f"Headings: {len(original_heads)}")
    print(f"Corrections: {len(CHANGES)} (4 hierarchy + 7 numbering)")
    print(f"Tables: {len(after_tables)} (all rows have consistent column counts)")
    for before, after in CHANGES:
        print(f"  {before}  ->  {after}")
    if not args.apply:
        print("PREVIEW ONLY: No files modified.")
        return 0

    data = (b"\xef\xbb\xbf" if had_bom else b"") + output.encode("utf-8")
    # Exclusive creation prevents overwriting a previously reviewed draft.
    with reviewed.open("xb") as target:
        target.write(data)
    print("APPLIED: New reviewed draft created; original Markdown and DOCX preserved.")
    print("NOT COMMITTED: Review against DOCX before selecting the canonical CH11 filename.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, UnicodeError) as exc:
        print("ERROR:", exc, file=sys.stderr)
        raise SystemExit(1)
