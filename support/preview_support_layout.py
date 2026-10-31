# -*- coding: utf-8 -*-
"""Read-only preview for moving AI_MR_Sandbox document tools into support/.

Place this file in bootstrap/ and run:
  py -3.11 "bootstrap/preview_support_layout.py"

No --apply mode exists. This script never changes files or Git.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

# 12 existing untracked items + this new preview tool (item 13).
PLAN = [
    ("bootstrap/audit_ch11_fidelity.py", "support/audit_ch11_fidelity.py"),
    ("bootstrap/audit_chapter_renames.py", "support/audit_chapter_renames.py"),
    ("bootstrap/audit_checkpoint_documents.ps1", "support/audit_checkpoint_documents.ps1"),
    ("bootstrap/convert_ch11_docx.py", "support/convert_ch11_docx.py"),
    ("bootstrap/review_ch11_structure.py", "support/review_ch11_structure.py"),
    ("bootstrap/prepare_ch09_document_fixed.ps1", "support/prepare_ch09_document_fixed.ps1"),
    ("bootstrap/migrate_checkpoint_names.py", "support/migrate_checkpoint_names.py"),
    ("bootstrap/create_ch12_portable.py", "support/create_ch12_portable.py"),
    ("bootstrap/update_chapter_index.py", "support/update_chapter_index.py"),
    ("bootstrap/append_ch12_document_policy.py", "support/append_ch12_document_policy.py"),
    ("bootstrap/prepare_ch09_document.ps1", "support/archive/prepare_ch09_document.ps1"),
    ("documents/CH11-ConversionDraft.md", "support/archive/CH11-ConversionDraft.md"),
    ("bootstrap/preview_support_layout.py", "support/preview_support_layout.py"),
]
SEARCH_WORDS = (
    "psscriptroot", "__file__", "parent.parent", "parent.parent.parent",
    "split-path", "bootstrap", "resolve-path",
)


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    print("=== Support organization (READ ONLY) ===")
    print("Repository:", root)
    print("Plan: 12 existing assets + this inspection script = 13 items")
    if not (root / "documents" / "CH12-Portable.md").is_file():
        print("ERROR: CH12-Portable.md not found at expected repository root.")
        return 2

    errors = []
    destination_names = set()
    for old, new in PLAN:
        src, dst = root / old, root / new
        state = "OK"
        if not src.is_file():
            errors.append(f"Missing source: {old}")
            state = "MISSING"
        if dst.exists():
            errors.append(f"Destination already exists: {new}")
            state = "COLLISION"
        if new.lower() in destination_names:
            errors.append(f"Duplicate destination: {new}")
        destination_names.add(new.lower())
        size = src.stat().st_size if src.is_file() else 0
        print(f"  [{state}] {old} -> {new} ({size:,} bytes)")

    print("\nSource path-sensitive expressions (manual review before move):")
    for old, new in PLAN:
        src = root / old
        if not src.is_file() or src.suffix.lower() not in (".py", ".ps1"):
            continue
        lines = src.read_text(encoding="utf-8-sig", errors="replace").splitlines()
        matches = [
            (number, line.strip())
            for number, line in enumerate(lines, start=1)
            if any(word in line.lower() for word in SEARCH_WORDS)
        ]
        if matches:
            print(f"  {old} ({len(matches)} potentially relevant lines):")
            for number, line in matches[:5]:
                print(f"    L{number}: {line[:150]}")
            if len(matches) > 5:
                print(f"    ... {len(matches) - 5} more")
        else:
            print(f"  {old}: no simple path tokens found")
    print("\nSafety notes:")
    print("  - `support/` keeps the same nesting depth as `bootstrap/`.")
    print("  - `support/archive/` is one level deeper; archive items are NOT for execution.")
    print("  - This is a text-level check, not proof that scripts still run after moving.")
    print("  - Existing tracked runtime bootstrap scripts are NOT part of the plan.")
    print("  - Original files, CH chapters, .venv, and Git index are unchanged.")
    if errors:
        print("\nPREVIEW BLOCKED:")
        for err in errors:
            print("  ", err)
        return 1
    print("\nPREVIEW PASS: All sources exist and destination names are free.")
    print("READ ONLY: No moves, deletes, edits, stages, or commits performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
