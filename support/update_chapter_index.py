# -*- coding: utf-8 -*-
"""CH01-CH12 chapter index for AI_MR_Sandbox documents/README.md.

Place in bootstrap/ and run from any directory:
    py -3.11 bootstrap/update_chapter_index.py
    py -3.11 bootstrap/update_chapter_index.py --apply

Default mode only previews. Apply appends a delimited index to the existing
README and preserves its original bytes (including the three legacy memo lines).
Never changes the CH documents or the Git index.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import tempfile
from pathlib import Path

START_MARKER = "<!-- CHAPTER_INDEX_BEGIN -->"
END_MARKER = "<!-- CHAPTER_INDEX_END -->"
LEGACY_LINES = [
    "Unity: SpeechReceiver_v3_prefab",
    "py: speech_to_unity_loop.py",
    "C++: AIRManager_v2",
]
CHAPTERS = [
    ("CH01", "CH01-SpeechToUnityConsole.md", "音声認識 → TCP/IP → Unity Console"),
    ("CH01.1", "CH01.1-SpeechToUnityUI.md", "音声認識結果をUnity UIに表示"),
    ("CH02", "CH02-NaturalLanguageCommand.md", "自然言語を構造化行動指示へ変換"),
    ("CH03", "CH03-BodyCenteredAction.md", "身体基準の空間参照とAIアバター行動"),
    ("CH04", "CH04-ActionVerification.md", "Actionと独立したVerification"),
    ("CH05", "CH05-ExperienceLogging.md", "ExperienceのJSONL永続記録"),
    ("CH06", "CH06-PermissionControl.md", "AIアバター行動前の権限確認"),
    ("CH07", "CH07-HumanEvaluation.md", "人間による評価とExperienceの統合"),
    ("CH08", "CH08-AIRManagerIntegration.md", "独立AIR ManagerとEnd-to-End統合"),
    ("CH09", "CH09-MREALIntegration.md", "MREALへのSandbox Runtime導入・統合"),
    ("CH10", "CH10-PhysicalSpaceTracking.md", "MREAL Head Trackingと実空間への接続"),
    ("CH10.5", "CH10.5-LocalLLM.md", "ローカルLLM導入準備"),
    ("CH10.6", "CH10.6-ImageGeneration.md", "ローカルAI画像生成環境の導入とテスト"),
    ("CH10.7", "CH10.7-ImageLearning.md", "AI画像学習環境の導入とテスト"),
    ("CH11", "CH11-DemoReproduction.md", "音声操作・会話GUIとデモ再現手順"),
    ("CH12", "CH12-Portable.md", "PC・ユーザ・Portableの環境分離と検証"),
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Append the index to documents/README.md")
    args = parser.parse_args()

    repo = Path(__file__).resolve().parent.parent
    docs = repo / "documents"
    readme = docs / "README.md"

    if not readme.is_file():
        raise SystemExit(f"ERROR: README not found: {readme}")
    missing = [name for _, name, _ in CHAPTERS if not (docs / name).is_file()]
    if missing:
        raise SystemExit("ERROR: Missing chapter files: " + ", ".join(missing))

    original = readme.read_bytes()
    try:
        decoded = original.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise SystemExit("ERROR: README is not UTF-8. Refusing to modify.")
    if START_MARKER in decoded or END_MARKER in decoded:
        raise SystemExit("ERROR: An index marker already exists. Refusing duplicate update.")
    if decoded.strip().splitlines() != LEGACY_LINES:
        raise SystemExit("ERROR: README differs from the three-line legacy memo. Review before updating.")

    rows = [
        START_MARKER,
        "## 開発Checkpoint索引（CH01〜CH12）",
        "",
        "番号は開発の順序、ファイル名の主題は各段階の主要成果を示す。",
        "CH10.5〜10.7はCH11に向けた補助的な導入・検証記録である。",
        "",
        "| 章 | 記録・再現手順 | 主題 |",
        "| --- | --- | --- |",
    ]
    rows.extend(f"| {num} | [{name}]({name}) | {description} |" for num, name, description in CHAPTERS)
    rows.extend([
        "",
        "**検証範囲の注意：** CH11の会話・音声応答のOpenAI API実機確認、および"
        "CH12の新PC側Runtime構築・GPU実行は、各文書で未検証として区別する。",
        "",
        "このREADME冒頭の3行は従来の実装メモとして保全しており、"
        "現在の構成が同一であることを保証しない。",
        END_MARKER,
    ])
    # Preserve original bytes; append using its existing newline convention.
    nl = "\r\n" if b"\r\n" in original else "\n"
    separator = "" if decoded.endswith(("\n", "\r")) else nl
    append_text = separator + nl + nl.join(rows) + nl
    updated = original + append_text.encode("utf-8")
    print("=== CH01-CH12 README index (" + ("APPLY" if args.apply else "PREVIEW") + ") ===")
    print("Repository:", repo)
    print("Target:", readme)
    print("Original bytes:", len(original))
    print("Chapters:", len(CHAPTERS))
    print("Expected SHA256:", hashlib.sha256(updated).hexdigest())
    print("Legacy memo preserved: YES")
    print("Other files modified: NO")
    print("Index:")
    for num, name, desc in CHAPTERS:
        print(f"  {num:6} {name}  - {desc}")
    if not args.apply:
        print("PREVIEW ONLY: No files or Git index entries were modified.")
        return 0

    # Re-check before writing and atomically replace only README.
    if readme.read_bytes() != original:
        raise SystemExit("ERROR: README changed during inspection; refusing update.")
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="wb", prefix=".readme-ch-index-", suffix=".tmp",
                                         dir=docs, delete=False) as temp:
            temp_path = Path(temp.name)
            temp.write(updated)
            temp.flush()
            os.fsync(temp.fileno())
        if readme.read_bytes() != original:
            raise SystemExit("ERROR: README changed while preparing update; refusing replace.")
        os.replace(temp_path, readme)
        temp_path = None
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()
    print("APPLIED: README index appended. No Git staging or commit performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
