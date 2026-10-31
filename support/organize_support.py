# -*- coding: utf-8 -*-
"""Move CH09-CH12 support artifacts to support/ and create support/README.md.

Place this script in bootstrap/. Run from any working directory:
  py -3.11 "bootstrap/organize_support.py"          (preview)
  py -3.11 "bootstrap/organize_support.py" --apply  (move)

Preview is read-only. Apply performs exact-path moves within the same repository.
The migration script itself moves last into support/. Rollback is attempted if a
move or verification fails. No source files are edited or deleted, and Git is
never staged or committed by this script.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

# Same-level relocation: scripts using parent.parent / $PSScriptRoot\..
# continue to resolve the repository root.
MOVES = [
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
    ("bootstrap/organize_support.py", "support/organize_support.py"),  # always last
]
README = """# Support: documentation migration and audit tools

This folder contains the **supporting materials** that were used to organize and
verify the CH01–CH12 research records. They are not part of the runtime bootstrap.
The original chapter documents remain in `../documents/`; current runtime setup
and verification scripts remain in `../bootstrap/`.

## Audit and validation

| Tool | Purpose |
| --- | --- |
| `audit_ch11_fidelity.py` | Check paragraph and table fidelity of the CH11 DOCX-to-Markdown conversion |
| `audit_chapter_renames.py` | Preview and audit the 13 chapter-name changes and old references |
| `audit_checkpoint_documents.ps1` | Inspect checkpoint document structure |

## Transformation and historical reproducibility

| Tool | Purpose |
| --- | --- |
| `convert_ch11_docx.py` | Convert the original CH11 DOCX to a Markdown draft |
| `review_ch11_structure.py` | Normalize the draft headings and section-number punctuation |
| `prepare_ch09_document_fixed.ps1` | Clean and normalize CH09 before adopting its canonical Markdown version |
| `migrate_checkpoint_names.py` | Migrate 13 chapter filenames and five operational file references |
| `create_ch12_portable.py` | Recreate the initial 163-line CH12 draft, **not** the later final 215-line document |
| `update_chapter_index.py` | Append the CH01–CH12 index to the pre-index README |
| `append_ch12_document_policy.py` | Append the CH12 Section 9 documentation policy |
| `preview_support_layout.py` | Read-only preview of this support-folder migration |
| `organize_support.py` | Apply this support-folder migration; intended for historical reference after it is run |

Tools that derive the repository root from their own parent folder retain
the same relative level when moved from `bootstrap/` to `support/`.
Other tools must still be reviewed before historical reuse.
**However, examples in their source comments may still show `bootstrap/`**; for
manual reruns substitute `support/`. Do not use these one-time migration scripts to
overwrite the final documents: several explicitly refuse to run a second time.

The runtime status, validation limits, and original-PC caveats are documented in
[`../documents/CH12-Portable.md`](../documents/CH12-Portable.md).
The chapter index is in [`../documents/README.md`](../documents/README.md).

## Archive: preserve, do not execute

- `archive/prepare_ch09_document.ps1`: earlier CH09 preparation attempt that did
  not complete successfully; retained for comparison with the fixed script.
- `archive/CH11-ConversionDraft.md`: first Markdown conversion from the CH11 DOCX.
  The final [`CH11-DemoReproduction.md`](../documents/CH11-DemoReproduction.md)
  differs by **11 heading-only substitutions** (four heading levels and seven
  section-number corrections). The original DOCX is retained in `../documents/`.

## Traceability

- `4aff369`: canonical CH09 Markdown normalization.
- `39748b8`: canonical CH11 Markdown addition.
- `d7132b7`: chapter filename harmonization.
- `981c741`: CH12 and the chapter README index.

The 14 relocated assets above were untracked at the time of this migration.
The migration utility does **not** automatically stage or commit any of them.
Review the resulting files before explicitly adding `support/` to Git.

## Operating principles

1. Preserve original documents and historical CHECKPOINT language.
2. Update real filename references without rewriting historical prose.
3. Keep machine-specific Python environments out of this support folder.
4. Use Preview → Validate → Apply → Git diff → Commit.
5. Preserve archive items until content equivalence and migration traceability
   have been reviewed; do not execute archived failed scripts.
"""


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Move 14 files and create README")
    args = parser.parse_args()

    here = Path(__file__).resolve()
    root = here.parent.parent
    readme_path = root / "support" / "README.md"

    errors = []
    if here != (root / "bootstrap" / "organize_support.py").resolve():
        errors.append("Script must be executed at bootstrap/organize_support.py before first migration")
    if not (root / "documents" / "CH12-Portable.md").is_file():
        errors.append("CH12-Portable.md is missing")
    if not (root / "documents" / "README.md").is_file():
        errors.append("documents/README.md is missing")
    if readme_path.exists():
        errors.append("support/README.md already exists; refusing overwrite")

    checksums = {}
    destinations = set()
    for old, new in MOVES:
        source, dest = root / old, root / new
        if not source.is_file():
            errors.append(f"Missing source: {old}")
        else:
            checksums[old] = digest(source.read_bytes())
        if dest.exists():
            errors.append(f"Destination already exists: {new}")
        if new.casefold() in destinations:
            errors.append(f"Duplicate destination in plan: {new}")
        destinations.add(new.casefold())

    print("=== Support migration (" + ("APPLY" if args.apply else "PREVIEW") + ") ===")
    print("Repository:", root)
    print("Movable assets:", len(MOVES))
    print("Additional file:", "support/README.md")
    print("README SHA256:", digest(README.encode("utf-8")))
    for old, new in MOVES:
        print(f"  {old}  ->  {new}")
    print("Existing runtime bootstrap scripts and chapter files: UNCHANGED")
    print("Content edits to moved files: NONE")
    if errors:
        print("BLOCKED:")
        for err in errors:
            print(" ", err)
        return 2

    if not args.apply:
        print("PREVIEW PASS: Sources and destinations checked.")
        print("READ ONLY: No files, directories or Git index entries changed.")
        return 0

    moved = []
    readme_created = False
    try:
        (root / "support" / "archive").mkdir(parents=True, exist_ok=True)
        for old, new in MOVES:
            src, dst = root / old, root / new
            if digest(src.read_bytes()) != checksums[old]:
                raise RuntimeError("Source changed during migration: " + old)
            # Every move is on the same repository volume. Destination absent.
            src.rename(dst)
            moved.append((src, dst))
            if digest(dst.read_bytes()) != checksums[old]:
                raise RuntimeError("Content digest mismatch after move: " + new)

        # No overwriting an existing support README, including races.
        with readme_path.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(README)
        readme_created = True
        if digest(readme_path.read_bytes()) != digest(README.encode("utf-8")):
            raise RuntimeError("support/README.md content verification failed")
    except Exception as exc:
        print("ERROR: Migration failed:", exc)
        # If README was created by this script on this attempt, discard it only
        # when the exact expected contents match. Do not touch unexpected edits.
        if readme_created and readme_path.exists() and digest(readme_path.read_bytes()) == digest(README.encode("utf-8")):
            readme_path.unlink()
        for src, dst in reversed(moved):
            try:
                if dst.is_file() and not src.exists():
                    dst.rename(src)
            except Exception as rollback_exc:
                print("ROLLBACK FAILURE:", dst, "->", src, rollback_exc)
        print("Migration aborted; inspect both directories before retrying.")
        return 3

    print("APPLIED: 14 assets moved without content changes.")
    print("CREATED: support/README.md")
    print("Git staging and commit: NOT PERFORMED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
