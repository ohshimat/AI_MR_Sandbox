# -*- coding: utf-8 -*-
"""Append CH12 documentation policy as Section 9, without changing existing text.

Usage from repo root:
  py -3.11 ".\bootstrap\append_ch12_document_policy.py"
  py -3.11 ".\bootstrap\append_ch12_document_policy.py" --apply

Default: READ ONLY preview. Apply: update only documents/CH12-Portable.md.
The script verifies the original CH12 SHA256 and refuses duplicate updates.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import tempfile
from pathlib import Path

EXPECTED_ORIGINAL_SHA256 = (
    "5f213a333e4f556bc1b90fc3cbe960c0527bcd8cefb78a54fa05a83bef14e279"
)
TARGET = Path("documents") / "CH12-Portable.md"
SECTION_TITLE = "## 9. 文書体系の整理と履歴保全方針"

APPEND_TEXT = """\
## 9. 文書体系の整理と履歴保全方針

本節は、Portable環境の再現性を支える文書管理規則を定める。
技術の実装状態だけでなく、各開発段階の記録・参照・原本の追跡可能性を維持する。

### 9.1 命名規則と章番号

- 正式な章ファイル名は `CH番号-主題.md` を用いる（例：`CH08-AIRManagerIntegration.md`）。
- 枝番号 `CH01.1`、`CH10.5`、`CH10.6`、`CH10.7` は開発履歴上の順序として維持する。
- CH01〜CH12の正式文書は計16件とし、正式な目録は `documents/README.md` とする。
- 章ファイル名を変更するときは、対応表を作り、衝突・欠落・参照先を事前確認する。

### 9.2 歴史的記述と運用参照を区別する

- 過去の検証名 `CHECKPOINT-1` など、本文中に残る歴史的表現は一括置換しない。
- 新しいファイルを指す実際のファイル名参照・リンクのみ、対象を限定して修正する。
- CH11に記録された当時のPC固有パスや `.venv` の表記は、
  その時点の再現手順を示すため、新方式に合わせて遡及変更しない。
- 変更内容の確認には、改名と内容差分を区別して確認できるGitを使用する。

### 9.3 原本・重複資料・変換作業の保全

- DOCXなどの原本は、Markdownへの変換が検証できても直ちに削除しない。
- CH11のMarkdown化では、原文段落・表の整合性を監査してから正式版を採用した。
- `documents/CH09-MREALIntegration.md` を正式版として整理した後も、
  内容が一致しない `python/CHECKPOINT-9.md` は未統合のため保全する。
- 変換ドラフト・補助スクリプトの採否や削除は、正式文書の確定後に別途判断する。

### 9.4 索引と参照整合性

- `documents/README.md` は各章の番号、正式ファイル名、主要主題を示す入口とする。
- READMEの旧来の3行の実装メモは原文のまま残すが、
  現行の実行環境と同一であることを保証するものではない。
- README内のリンク先について、ファイルの存在を確認してから索引を変更する。
- CH12でいう「検証済み」「未実施」「SKIPPED」は区別し、
  文書が存在することだけをもって実装・実行の成功とみなさない。

### 9.5 変更手順とGitの履歴

文書改名・本文修正・索引更新は、原則として
**Preview → 検証 → Apply → Git差分確認 → Commit** の順序で行う。
他の未登録スクリプトやドラフトを誤ってコミットしないよう、対象ファイルを指定する。

今回の文書整理で確定した主なGitコミット：

- `4aff369`：CH09の正式Markdown文書の整理。
- `39748b8`：CH11の正式Markdown文書を追加。
- `d7132b7`：CH01〜CH10の13件を改名し、運用上のファイル参照5件を修正。

本節の作成時点で、CH12本文とREADME索引の追加分は未コミット。
このため、コミット完了後に文書の記述とGit履歴の整合性を再確認する。
"""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true",
                        help="Append the section after safety checks")
    args = parser.parse_args()

    repo = Path(__file__).resolve().parent.parent
    target = repo / TARGET
    if not target.is_file():
        raise SystemExit(f"ERROR: Missing target {target}")
    original = target.read_bytes()
    original_hash = sha256(original)
    if original_hash != EXPECTED_ORIGINAL_SHA256:
        raise SystemExit(
            "ERROR: CH12 differs from the previously reviewed 163-line version. "
            f"Expected {EXPECTED_ORIGINAL_SHA256}, got {original_hash}. "
            "No changes made."
        )
    try:
        text = original.decode("utf-8")
    except UnicodeDecodeError:
        raise SystemExit("ERROR: CH12 not valid UTF-8. No changes made.")
    if SECTION_TITLE in text or "## 9." in text:
        raise SystemExit("ERROR: Section 9 already present. No changes made.")
    if not text.startswith("# CH12 — Portable Environment\n"):
        raise SystemExit("ERROR: Unexpected CH12 title. No changes made.")
    if "## 8. 安全運用原則" not in text:
        raise SystemExit("ERROR: Section 8 not found. No changes made.")

    # Preserve the byte-for-byte original text and append only Section 9.
    separator = "\n" if original.endswith(b"\n") else "\n\n"
    updated = original + separator.encode("utf-8") + APPEND_TEXT.encode("utf-8")
    print("=== CH12 document policy (" + ("APPLY" if args.apply else "PREVIEW") + ") ===")
    print("Repository:", repo)
    print("Target:", target)
    print("Original SHA256:", original_hash)
    print("New SHA256:", sha256(updated))
    print("Original lines:", len(text.splitlines()))
    print("Added lines:", len(APPEND_TEXT.splitlines()) + (1 if separator == "\n" else 2))
    print("Original text preserved: YES (byte-for-byte prefix)")
    print("README / other files modified: NO")
    print("Added headings:")
    for line in APPEND_TEXT.splitlines():
        if line.startswith("## ") or line.startswith("### "):
            print(" ", line)
    if not args.apply:
        print("PREVIEW ONLY: No files or Git index entries modified.")
        return 0

    if target.read_bytes() != original:
        raise SystemExit("ERROR: CH12 changed during preview. No changes made.")
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", prefix=".ch12-policy-", suffix=".tmp",
            dir=target.parent, delete=False
        ) as fh:
            temporary_path = Path(fh.name)
            fh.write(updated)
            fh.flush()
            os.fsync(fh.fileno())
        if target.read_bytes() != original:
            raise SystemExit("ERROR: CH12 changed during apply. No changes made.")
        os.replace(temporary_path, target)
        temporary_path = None
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()

    print("APPLIED: Section 9 appended. No Git staging or commit performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
