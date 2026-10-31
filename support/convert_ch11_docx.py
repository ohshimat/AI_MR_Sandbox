#!/usr/bin/env python3
"""CH11 DOCX -> Markdown draft (Preview by default; --apply creates a new file).

Requires only Python 3.11 standard library. The input DOCX is always read-only.
The converter preserves paragraph order, recognized heading styles, basic inline
emphasis, list markers, and eight or more ordinary Word tables where feasible.
Merged cells are flattened and must be checked against the original DOCX.
"""

from __future__ import annotations

import argparse
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"


def tag(local: str) -> str:
    return W + local


def read_xml(zf: zipfile.ZipFile, name: str) -> ET.Element | None:
    try:
        return ET.fromstring(zf.read(name))
    except KeyError:
        return None


def styles_lookup(styles_root: ET.Element | None) -> dict[str, tuple[str, str | None]]:
    result = {}
    if styles_root is None:
        return result
    for style in styles_root.findall(".//" + tag("style")):
        key = style.get(tag("styleId"))
        if not key:
            continue
        label = style.find(tag("name"))
        base = style.find(tag("basedOn"))
        result[key] = ((label.get(tag("val")) if label is not None else key) or key,
                       base.get(tag("val")) if base is not None else None)
    return result


def paragraph_style(p: ET.Element, styles: dict[str, tuple[str, str | None]]) -> str:
    prop = p.find(tag("pPr"))
    elt = prop.find(tag("pStyle")) if prop is not None else None
    key = elt.get(tag("val")) if elt is not None else None
    if not key:
        return ""
    return styles.get(key, (key, None))[0]


def heading_level(p: ET.Element, styles: dict[str, tuple[str, str | None]]) -> int | None:
    prop = p.find(tag("pPr"))
    if prop is not None:
        outline = prop.find(tag("outlineLvl"))
        if outline is not None:
            try:
                return min(6, int(outline.get(tag("val"))) + 1)
            except (ValueError, TypeError):
                pass
        elt = prop.find(tag("pStyle"))
        key = elt.get(tag("val")) if elt is not None else None
        for _ in range(5):
            if not key:
                break
            label, parent = styles.get(key, (key, None))
            for candidate in (key, label):
                match = re.search(r"(?:heading|見出し)\s*([1-6])$", candidate, re.I)
                if match:
                    return int(match.group(1))
            key = parent
    label = paragraph_style(p, styles)
    if label.lower() == "title":
        return 1
    return None


def run_text(run: ET.Element) -> str:
    chars = []
    for elt in run.iter():
        if elt.tag == tag("t") or elt.tag == tag("delText"):
            if elt.tag == tag("t"):
                chars.append(elt.text or "")
        elif elt.tag in (tag("br"), tag("cr")):
            chars.append("\n")
        elif elt.tag == tag("tab"):
            chars.append("\t")
        elif elt.tag == tag("noBreakHyphen"):
            chars.append("-")
    return "".join(chars)


def inline_runs(container: ET.Element):
    for child in container:
        if child.tag == tag("r"):
            yield child
        elif child.tag in (tag("hyperlink"), tag("smartTag"), tag("sdt"), tag("sdtContent"), tag("ins")):
            yield from inline_runs(child)


def paragraph_text(p: ET.Element, markdown: bool = True) -> str:
    chunks = []
    for run in inline_runs(p):
        value = run_text(run)
        if not value:
            continue
        rpr = run.find(tag("rPr"))
        if markdown and rpr is not None:
            b = rpr.find(tag("b"))
            i = rpr.find(tag("i"))
            bold = b is not None and b.get(tag("val"), "1") not in ("0", "false", "off")
            italic = i is not None and i.get(tag("val"), "1") not in ("0", "false", "off")
            # Skip whitespace-only spans to avoid dangling Markdown syntax.
            if value.strip():
                # Retain spaces outside of Markdown delimiters.
                match = re.match(r"^(\s*)(.*?)(\s*)$", value, re.S)
                if match:
                    lead, core, trail = match.groups()
                    if bold:
                        core = "**" + core + "**"
                    if italic:
                        core = "*" + core + "*"
                    value = lead + core + trail
        chunks.append(value)
    # Fallback for field/content-control elements not covered as regular runs.
    if not chunks:
        for t in p.iter(tag("t")):
            chunks.append(t.text or "")
    return "".join(chunks).strip()


def text_in_cell(cell: ET.Element) -> str:
    # Flatten lines inside a cell; keep source text even with merged Word cells.
    items = []
    for para in cell.findall("./" + tag("p")):
        s = paragraph_text(para, markdown=False)
        if s:
            items.append(s)
    for table in cell.findall("./" + tag("tbl")):
        for para in table.iter(tag("p")):
            s = paragraph_text(para, markdown=False)
            if s:
                items.append(s)
    return "<br>".join(items).replace("|", r"\|").replace("\n", "<br>")


def render_table(tbl: ET.Element) -> tuple[str, int]:
    rows = []
    spans_found = 0
    for tr in tbl.findall("./" + tag("tr")):
        cells = []
        for tc in tr.findall("./" + tag("tc")):
            text = text_in_cell(tc)
            pr = tc.find(tag("tcPr"))
            span_element = pr.find(tag("gridSpan")) if pr is not None else None
            span = 1
            if span_element is not None:
                try:
                    span = max(1, int(span_element.get(tag("val"), "1")))
                except ValueError:
                    pass
            if span > 1:
                spans_found += 1
            vm = pr.find(tag("vMerge")) if pr is not None else None
            if vm is not None:
                spans_found += 1
            cells.append(text)
            cells.extend([""] * (span - 1))
        rows.append(cells)
    if not rows:
        return "", spans_found
    ncols = max(len(r) for r in rows)
    rows = [r + [""] * (ncols - len(r)) for r in rows]
    head, *rest = rows
    lines = ["| " + " | ".join(head) + " |", "| " + " | ".join(["---"] * ncols) + " |"]
    lines += ["| " + " | ".join(row) + " |" for row in rest]
    return "\n".join(lines), spans_found


def is_list_paragraph(p: ET.Element, styles: dict[str, tuple[str, str | None]]) -> bool:
    pr = p.find(tag("pPr"))
    if pr is not None and pr.find(tag("numPr")) is not None:
        return True
    return "list" in paragraph_style(p, styles).lower()


def convert(docx: Path) -> tuple[str, dict]:
    with zipfile.ZipFile(docx) as z:
        root = read_xml(z, "word/document.xml")
        if root is None:
            raise ValueError("Invalid DOCX: word/document.xml is missing")
        styles = styles_lookup(read_xml(z, "word/styles.xml"))
        body = root.find(tag("body"))
        if body is None:
            raise ValueError("Invalid DOCX: document body is missing")
        stats = {"paragraphs": len(root.findall(".//" + tag("p"))),
                 "tables": len(root.findall(".//" + tag("tbl"))),
                 "images": len(root.findall(".//" + tag("drawing"))) + len(root.findall(".//" + tag("pict"))),
                 "merged_cells": 0, "heading_count": 0, "preview_lines": []}
        blocks = []
        title_seen = False
        for child in body:
            if child.tag == tag("p"):
                value = paragraph_text(child)
                if not value:
                    continue
                level = heading_level(child, styles)
                if level is not None:
                    is_title = paragraph_style(child, styles).lower() == "title"
                    if is_title:
                        title_seen = True
                    adjusted_level = min(6, level + (1 if title_seen and not is_title else 0))
                    value = "#" * adjusted_level + " " + value
                    stats["heading_count"] += 1
                elif is_list_paragraph(child, styles):
                    value = "- " + value
                blocks.append(value)
                if len(stats["preview_lines"]) < 12:
                    stats["preview_lines"].append(re.sub(r"\s+", " ", paragraph_text(child, markdown=False))[:140])
            elif child.tag == tag("tbl"):
                value, merges = render_table(child)
                stats["merged_cells"] += merges
                if value:
                    blocks.append(value)
        output = "\n\n".join(blocks).strip() + "\n"
        return output, stats


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert CH11 Word report to a Markdown draft")
    parser.add_argument("--apply", action="store_true", help="Create Markdown draft; never overwrite")
    args = parser.parse_args()
    repo = Path(__file__).resolve().parent.parent
    documents = repo / "documents"
    if not documents.is_dir():
        raise SystemExit(f"ERROR: documents folder not found: {documents}")
    sources = sorted(documents.glob("CP_11_*.docx"))
    if len(sources) != 1:
        raise SystemExit(f"ERROR: Expected exactly one CH11 DOCX; found {len(sources)}")
    source = sources[0]
    target = documents / "CH11-ConversionDraft.md"
    output, stats = convert(source)
    print("=== CH11 DOCX to Markdown (" + ("APPLY" if args.apply else "PREVIEW") + ") ===")
    print(f"Repository:         {repo}")
    print(f"Source:             {source.relative_to(repo)}")
    print(f"Draft target:       {target.relative_to(repo)}")
    print(f"Word paragraphs:    {stats['paragraphs']}")
    print(f"Word tables:        {stats['tables']}")
    print(f"Word images:        {stats['images']}")
    print(f"Recognized headings:{stats['heading_count']:>5}")
    print(f"Merged cell markers:{stats['merged_cells']:>5}")
    print(f"Draft lines:        {len(output.splitlines())}")
    print("First nonempty paragraphs:")
    for line in stats["preview_lines"]:
        print("  - " + line)
    if stats["images"]:
        raise SystemExit("ERROR: Image content detected; conversion blocked to avoid dropping it")
    if not args.apply:
        print("PREVIEW ONLY: No files or environments were modified.")
        print("Review table rendering and headings against original DOCX after applying.")
        return 0
    try:
        with target.open("x", encoding="utf-8", newline="\n") as f:
            f.write(output)
    except FileExistsError:
        raise SystemExit(f"ERROR: Draft already exists; refusing to overwrite: {target}")
    print("APPLIED: New Markdown draft created. Original DOCX unchanged.")
    print("NOT COMMITTED: Inspect heading levels, merged tables and wording before naming CH11.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, zipfile.BadZipFile, ET.ParseError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
