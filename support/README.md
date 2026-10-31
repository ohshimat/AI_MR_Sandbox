# Support: documentation migration and audit tools

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
