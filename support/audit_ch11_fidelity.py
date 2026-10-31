#!/usr/bin/env python3
"""Audit CH11 DOCX -> reviewed Markdown fidelity; NEVER writes files.

Python 3.11 standard library only. Run from any working directory:
  py -3.11 .\bootstrap\audit_ch11_fidelity.py

Checks table count, row/column layout and cell text, and checks each nonempty
body-level Word paragraph for a counterpart in the generated Markdown.
A PASS establishes textual coverage, not visual or semantic equivalence.
"""
from __future__ import annotations

import re
import sys
import unicodedata
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def t(name: str) -> str:
    return W + name


def para_text(p: ET.Element) -> str:
    result = []
    for e in p.iter():
        if e.tag == t("t"):
            result.append(e.text or "")
        elif e.tag in (t("tab"),):
            result.append("\t")
        elif e.tag in (t("br"), t("cr")):
            result.append("\n")
    return "".join(result).strip()


def compact(s: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", s))


def extract_docx(path: Path) -> tuple[list[str], list[list[list[str]]]]:
    with zipfile.ZipFile(path, "r") as zf:
        root = ET.fromstring(zf.read("word/document.xml"))
    body = root.find(t("body"))
    if body is None:
        raise ValueError("Word document body missing")
    paragraphs: list[str] = []
    tables: list[list[list[str]]] = []
    for block in body:
        if block.tag == t("p"):
            s = para_text(block)
            if s:
                paragraphs.append(s)
        if block.tag == t("tbl"):
            rows: list[list[str]] = []
            for tr in block.findall(t("tr")):
                cells: list[str] = []
                for tc in tr.findall(t("tc")):
                    cell_lines: list[str] = []
                    for p in tc.findall(t("p")):
                        ptext = para_text(p)
                        if ptext:
                            cell_lines.append(ptext)
                    for nested in tc.findall(t("tbl")):
                        for p in nested.iter(t("p")):
                            ptext = para_text(p)
                            if ptext:
                                cell_lines.append(ptext)
                    cells.append("\n".join(cell_lines))
                    pr = tc.find(t("tcPr"))
                    if pr is not None:
                        span = pr.find(t("gridSpan"))
                        if span is not None:
                            cells.extend([""] * (max(1, int(span.get(t("val"), "1"))) - 1))
                rows.append(cells)
            if rows:
                width = max(len(row) for row in rows)
                tables.append([row + [""] * (width - len(row)) for row in rows])
    return paragraphs, tables


def split_md_row(line: str) -> list[str]:
    raw = line.strip()[1:-1]
    result = re.split(r"(?<!\\)\|", raw)
    return [cell.strip().replace(r"\|", "|").replace("<br>", "\n") for cell in result]


def md_tables(text: str) -> list[list[list[str]]]:
    groups: list[list[str]] = []
    current: list[str] = []
    for line in text.splitlines() + [""]:
        if line.startswith("| ") and line.endswith(" |"):
            current.append(line)
        elif current:
            groups.append(current)
            current = []
    out = []
    for block in groups:
        if len(block) < 2:
            raise ValueError("Malformed Markdown table: missing separator")
        separator = split_md_row(block[1])
        if not all(re.fullmatch(r":?-{3,}:?", cell) for cell in separator):
            raise ValueError("Malformed Markdown table: invalid separator")
        out.append([split_md_row(block[0])] + [split_md_row(row) for row in block[2:]])
    return out


def markdown_prose(text: str) -> str:
    lines = []
    for line in text.splitlines():
        if line.startswith("| ") and line.endswith(" |"):
            continue
        line = re.sub(r"^#{1,6}\s+", "", line)
        line = re.sub(r"^[-*]\s+", "", line)
        line = line.replace("**", "").replace("`", "")
        lines.append(line)
    return compact("\n".join(lines))


def main() -> int:
    repo = Path(__file__).resolve().parent.parent
    docs = repo / "documents"
    sources = sorted(docs.glob("CP_11_*.docx"))
    if len(sources) != 1:
        raise ValueError(f"Expected one CP_11_*.docx; found {len(sources)}")
    docx = sources[0]
    reviewed = docs / "CH11-ReviewedDraft.md"
    if not reviewed.is_file():
        raise ValueError(f"Reviewed Markdown missing: {reviewed}")
    src_paras, src_tables = extract_docx(docx)
    text = reviewed.read_text(encoding="utf-8-sig")
    dst_tables = md_tables(text)
    mismatches = []
    if len(src_tables) != len(dst_tables):
        mismatches.append(f"Table count: DOCX {len(src_tables)}, Markdown {len(dst_tables)}")
    for i, (src, dst) in enumerate(zip(src_tables, dst_tables), 1):
        if len(src) != len(dst):
            mismatches.append(f"Table {i}: row count DOCX {len(src)}, Markdown {len(dst)}")
        for r, (srow, drow) in enumerate(zip(src, dst), 1):
            if len(srow) != len(drow):
                mismatches.append(f"Table {i}, row {r}: column count DOCX {len(srow)}, Markdown {len(drow)}")
            for c, (scell, dcell) in enumerate(zip(srow, drow), 1):
                if compact(scell) != compact(dcell):
                    mismatches.append(f"Table {i}, row {r}, col {c}: DOCX={scell[:55]!r} MD={dcell[:55]!r}")
    md_prose = markdown_prose(text)
    missing_paragraphs = []
    for i, paragraph in enumerate(src_paras, 1):
        norm = compact(paragraph)
        if norm in md_prose:
            continue
        # The approved CH11 heading normalization changes '5 1' to '5.1'.
        heading_norm = re.sub(r"^([0-9]+)\s+([0-9]+)", r"\1.\2", paragraph)
        if compact(heading_norm) not in md_prose:
            missing_paragraphs.append(f"Paragraph {i}: {paragraph[:100]}")
    print("=== CH11 content fidelity audit (READ ONLY) ===")
    print("DOCX:", docx.relative_to(repo))
    print("Markdown:", reviewed.relative_to(repo))
    print("DOCX body paragraphs:", len(src_paras))
    print("Paragraphs not matched:", len(missing_paragraphs))
    print("Tables (DOCX / MD):", len(src_tables), "/", len(dst_tables))
    print("Table cell/layout mismatches:", len(mismatches))
    for item in (missing_paragraphs[:12] + mismatches[:12]):
        print(" -", item)
    if len(missing_paragraphs) > 12 or len(mismatches) > 12:
        print("(Additional differences omitted from terminal output)")
    if missing_paragraphs or mismatches:
        print("REVIEW REQUIRED: Differences detected; no files modified.")
        return 1
    print("PASS: All Word body paragraphs and table cells matched in Markdown.")
    print("No files modified. This is a text-coverage test, not a visual QA test.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, zipfile.BadZipFile, ET.ParseError) as exc:
        print("ERROR:", exc, file=sys.stderr)
        sys.exit(2)
