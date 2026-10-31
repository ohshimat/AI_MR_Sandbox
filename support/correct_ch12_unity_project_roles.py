# -*- coding: utf-8 -*-
"""Correct the Unity project used for the CH12 E2E experiment.

Save this file to support/correct_ch12_unity_project_roles.py.
Run from PowerShell at the repository root:
  py -3.11 ".\support\correct_ch12_unity_project_roles.py"
  py -3.11 ".\support\correct_ch12_unity_project_roles.py" --apply

Default: PREVIEW (read-only). Apply changes only documents/CH12-Portable.md.
Existing document content is preserved except two precise path substitutions
and one explicit project-role clarification in Section 10.1.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import tempfile
from pathlib import Path

EXPECTED_SHA256 = "3da8cd4922b1221302ba0c21dcf2ba152d5e4534abd2d1b32ccef35ea3e2c874"

OLD_PATH = "unity/MREAL_OpenXR_Sample6_Haptic_Sandbox_ollama_test"
CANONICAL_PATH = "unity/MREAL_OpenXR_Sample6_Haptic_Sandbox"
HEADING_10_1 = "### 10.1 検証したPCと配置"
HEADING_10_2 = "### 10.2 起動する実体と役割"

PROJECT_ROLE_NOTE = """**Unityプロジェクトの役割区分（2026-10-31の検証対象）**

- 公式基準版：`unity/MREAL_OpenXR_Sample6_Haptic_Sandbox`。
  Unityプロジェクトには最小限の機能を維持する方針であり、
  今回のマイク → Whisper → Qwen3:8b → Unity → AIR Manager → AI_1移動の
  End-to-End実機検証には、この公式基準版を使用した。
- GUIテスト派生版：`unity/MREAL_OpenXR_Sample6_Haptic_Sandbox_ollama_test`。
  共同研究者が、音声認識・Qwenの代わりにUnity上のGUIから操作を試せるよう、
  テスト用機能を追加したプロジェクト。開発時系列では後発だが、
  公式基準版を置き換えるものではない。
- したがって、**開発時系列上の新しさ**と**公式基準版としての採用**を
  混同しない。GUIテスト派生版の機能を公式基準版へ無条件に取り込まない。
"""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Apply the audited correction")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    target = root / "documents" / "CH12-Portable.md"
    if not target.is_file():
        raise SystemExit(f"ERROR: File not found: {target}")

    original = target.read_bytes()
    original_sha = sha256(original)
    if original_sha != EXPECTED_SHA256:
        raise SystemExit(
            "ERROR: CH12 SHA256 differs from the reviewed baseline; no changes made.\n"
            f"Expected: {EXPECTED_SHA256}\nActual:   {original_sha}"
        )
    try:
        text = original.decode("utf-8")
    except UnicodeDecodeError:
        raise SystemExit("ERROR: CH12 is not UTF-8; no changes made")

    if text.count(HEADING_10_1) != 1 or text.count(HEADING_10_2) != 1:
        raise SystemExit("ERROR: Section 10.1/10.2 headings differ; no changes made")
    section_start = text.index(HEADING_10_1)
    section_end = text.index(HEADING_10_2)
    if section_end <= section_start:
        raise SystemExit("ERROR: Chapter heading order is invalid")

    # The two erroneous paths occur in Sections 10.2 and 10.4.
    if text.count(OLD_PATH) != 2:
        raise SystemExit("ERROR: Expected exactly two outdated project references")
    if "## 10. PC側Runtimeの実機再現性検証" not in text:
        raise SystemExit("ERROR: Chapter 10 is missing")
    chapter10_start = text.index("## 10. PC側Runtimeの実機再現性検証")
    if text[:chapter10_start].count(OLD_PATH):
        raise SystemExit("ERROR: Outdated reference outside Chapter 10")

    # Insert a factual clarification at the end of Section 10.1.
    newline = "\r\n" if b"\r\n" in original else "\n"
    note = PROJECT_ROLE_NOTE.replace("\n", newline)
    # Substitution is restricted to the chapter-10 suffix.
    prefix = text[:chapter10_start]
    chapter10 = text[chapter10_start:].replace(OLD_PATH, CANONICAL_PATH)
    text2 = prefix + chapter10
    insertion_point = text2.index(HEADING_10_2)
    before = text2[:insertion_point]
    after = text2[insertion_point:]
    # Section 10.1 ends just before next heading. Keep a blank line on either side.
    before = before.rstrip("\r\n") + newline + newline
    updated_text = before + note + newline + after
    updated = updated_text.encode("utf-8")

    print("=== CH12 Unity project role correction (" + ("APPLY" if args.apply else "PREVIEW") + ") ===")
    print("Repository:", root)
    print("Target:", target)
    print("Original SHA256:", original_sha)
    print("Updated SHA256:", sha256(updated))
    print("Corrections: 2 outdated Unity project paths")
    print("Insertion: Section 10.1 project-role note")
    print("Canonical: unity/MREAL_OpenXR_Sample6_Haptic_Sandbox")
    print("GUI test branch: unity/MREAL_OpenXR_Sample6_Haptic_Sandbox_ollama_test")
    print("Other files / Git index modified: NO")
    if not args.apply:
        print("PREVIEW ONLY: No files changed.")
        return 0

    if target.read_bytes() != original:
        raise SystemExit("ERROR: Document changed during check; no changes made")
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", prefix=".ch12-project-correction-", suffix=".tmp",
            dir=target.parent, delete=False
        ) as stream:
            temporary_path = Path(stream.name)
            stream.write(updated)
            stream.flush()
            os.fsync(stream.fileno())
        if target.read_bytes() != original:
            raise SystemExit("ERROR: Document changed before replace; no changes made")
        os.replace(temporary_path, target)
        temporary_path = None
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()
    print("APPLIED: Two path corrections and the project-role note were added.")
    print("Git staging/commit: NOT PERFORMED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
