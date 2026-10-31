# -*- coding: utf-8 -*-
"""Create CH12-Portable.md from the agreed, verified Chapter 12 milestones.

Usage (from any directory):
    py -3.11 bootstrap/create_ch12_portable.py
    py -3.11 bootstrap/create_ch12_portable.py --apply

Default: preview only. Apply: creates documents/CH12-Portable.md exclusively.
No changes to existing documentation, Git, venvs, or PC configurations.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

DOCUMENT = """# CH12 — Portable Environment

## 1. 目的と位置づけ

本章は、AI_MR_Sandbox の研究・実装環境を複数の Windows PC で再現するため、
従来の「Portable SSD 上にソースと Python 仮想環境が同居する方式」を見直し、
環境の責務を A・B・C の3区分に分離した経緯、実装、検証結果を記録する。

本章で検証したのは**環境パスの解決、環境診断、Bootstrap の事前安全検査**である。
新しい PC 側 Runtime の実インストール、GPU 動作、Unity / AIR の End-to-End 動作、
旧 PC での新方式再検証は、まだ完了していない。

## 2. A・B・C の環境分離

| 区分 | 責務 | 代表的な保存先 |
| --- | --- | --- |
| A: PC 環境 | 仮想環境、AI モデル、キャッシュ、PC 固有設定 | `C:\\AI_MR_Sandbox`、`C:\\AI_venvs` |
| B: ユーザ Workspace | 学習データ、生成物、実験ログ、ユーザ固有データ | `user.json` で指定 |
| C: Portable 環境 | 共通ソース、Unity 資産、bootstrap、依存記述、文書 | Portable SSD 内の `AI_MR_Sandbox` |

SSD ドライブ文字や Windows ユーザ名をプログラム内に固定しない。
C 区分の既存 `.venv` は、従来環境の復元性を確保するため、削除・更新しない。

### 2.1 PC 設定（A）

既定の設定ファイルは `C:\\AI_MR_Sandbox\\config\\machine.json`。
別の場所を指定する場合は環境変数 `AI_MR_MACHINE_CONFIG` を使用できる。

```json
{
  "schema_version": 1,
  "pc_root": "C:\\\\AI_MR_Sandbox",
  "venv_root": "C:\\\\AI_venvs"
}
```

### 2.2 ユーザ設定（B）

`%APPDATA%\\AI_MR_Sandbox\\user.json` に `workspace_root` を記述する。
実際のパスは各 PC・Windows アカウントごとに設定する。

```json
{
  "schema_version": 1,
  "workspace_root": "D:\\\\Research\\\\AI_MR_Workspace"
}
```

設定値は例示であり、Workspace の実在や書き込み可能性を保証するものではない。

## 3. CH12 で追加したスクリプト

| ファイル（`bootstrap/`） | 役割 |
| --- | --- |
| `resolve_environment.ps1` | A・B・C の設定を読み、各パスを解決する |
| `setup_python_environment_pc.ps1` | PC 側 Runtime 環境構築用。通常は Preview のみ |
| `verify_runtime_environment_pc.ps1` | Level 2：ソースと実行環境の存在確認 |
| `verify_runtime_health_pc.ps1` | Level 3：環境が存在する場合だけ基本的な実行診断 |

これら4ファイルは、安全対策を含めて `portability-cleanup` ブランチの
Git コミット `ee814c7` に記録した。新方式の実インストールは未検証である。

### 3.1 Resolver の出力

`RepoRoot`, `PcRoot`, `VenvRoot`, `RuntimePython`, `ImagePython`,
`ModelsRoot`, `CacheRoot`, `WorkspaceRoot` を返す。
Resolver は設定を読み込むのみで、ディレクトリを作成しない。
設定欠落・必須項目欠落は例外で報告する。

### 3.2 新 Bootstrap の動作モード

| 指定 | 動作 |
| --- | --- |
| 指定なし | 設定とインストール先を表示し、変更しない |
| `-CheckInstallSafety` | 安全条件を検査し、インストール前に終了する |
| `-Install` | 条件を満たす場合にのみ PC 側 Runtime を新規構築する |

既存 `AI_MR_Sandbox_Runtime` ディレクトリがある場合は構築を拒否する。
Portable リポジトリ内部、およびそのリポジトリと同じドライブ文字への
仮想環境配置を拒否する。指定パスが再解析ポイントである場合も一部拒否する。

**注意：** 同一物理ボリュームを指す異なるドライブ文字、親ディレクトリの
ジャンクションやマウントポイントなど、すべての経路転送を検出できるわけではない。
`-Install` は本章の検証では実行していない。保護コードの完成を意味しない。

### 3.3 Level 2 と Level 3 の判定

Level 2 は主要ソース8ファイルと Runtime / Image Python、Workspace、
旧 `.venv` の存在状況を報告する。
Level 3 は Runtime がある場合に import と `pip check` を、
Ollama が PATH にある場合にモデルと API を確認する。

未構築時は `SKIPPED` / `NOT INSTALLED` 等と表示する。
**検証スクリプトの正常終了は、未構築システムの実行可能性を意味しない。**
現行 Level 3 は FAIL を必ずしも終了コードへ反映しないため、
自動合否判定への利用前に改修が必要である。

## 4. 実施した検証と結果

| 項目 | 結果 | 留意点 |
| --- | --- | --- |
| Resolver 正常系 | PASS | 異なる PC・SSD ドライブ文字で確認 |
| Resolver：設定ファイル欠落 | PASS | 期待どおり例外を検出 |
| Resolver：必須キー欠落 | PASS | `pc_root` 不足を検出 |
| Bootstrap 通常 Preview | PASS | インストールなし |
| Bootstrap 安全検査 | PASS | Runtime 未構築時に正常終了 |
| SSD 同一ドライブ拒否 | PASS | テスト設定を用いた拒否確認 |
| 既存 Runtime 拒否 | PASS | 一時ディレクトリを使って確認 |
| Level 2 診断 | PASS | ソース8件存在、PC側 Runtime は未構築 |
| Level 3 診断 | PASS（スキップ動作） | Python・Ollama の実行検証は未実施 |
| requirements lock の pip dry-run | PASS | Python 3.11 / Windows x64、27固定パッケージ |
| `pip==26.2.1` dry-run | PASS と報告 | 実インストールなし |
| `-Install` | 未実施 | 実環境構築・実行テストは今後 |
| GPU / CUDA / Unity / AIR | 未実施 | End-to-End 再現性は未評価 |

複数 PC でのパス解決例：

- ある PC：Portable リポジトリが `F:\\AI_MR_Sandbox`、Workspace はその PC のユーザ設定による。
- `DESKTOP-TIPMO1S`：Portable リポジトリが `E:\\AI_MR_Sandbox`、
  ユーザ Workspace 設定は `C:\\Users\\vruser_1\\AI_MR_Workspace`。
  この Workspace は当時未作成、PC 側 Runtime と Image Python も未構築であった。

上記は別PCで異なる設定が使われることの検証であり、
同一ソースによる一連の実験が両PCで成功したことまでは示さない。

## 5. Runtime パッケージ再現性

`bootstrap/requirements-runtime-lock.txt` の固定27パッケージを用い、
Python 3.11.9 / Windows x64 の `pip install --dry-run --ignore-installed
--only-binary=:all:` で依存解決を確認した。

これは Python パッケージのインストール計画の検査であり、
インストール済み環境の import 成功、Whisper 推論、Ollama 接続、
CUDA / cuDNN 対応、GPU 動作を保証しない。

## 6. CH11 の環境記述との関係

`CH11-DemoReproduction.md` は当時のデモ再現手順として保存する。
そこに記録されたリポジトリ直下の `.venv` や個別 PC のパスは
**CH11 当時の実装環境を示す歴史的記録**である。
CH12 の3区分設計に合わせて遡及的に書き換えない。

また、従来の `setup_python_environment.ps1` と
`verify_runtime_environment.ps1` は初期移行段階では保持する。
新しい PC 対応版とは並行して取り扱い、旧機の互換性を確認したのちに移行を判断する。

## 7. 未完了事項・次段階への申し送り

1. Python Runtime を PC 側に実際に新規構築し、import・`pip check`・実処理を検証する。
2. `-Install` 前に、親ディレクトリの再解析ポイント、実ボリューム等を含む安全条件を再検討する。
3. Runtime と画像生成・学習環境の起動スクリプト全体を Resolver 参照へ順次移行する。
4. Unity プロジェクトの PC 固有キャッシュと Portable 資産の分離方式を決定する。
5. Ollama / Whisper / Unity / AIRManager を結ぶ動作確認、GPU 検証を実施する。
6. 元の PC と、複数の別PCで同一実験を再現し、結果を記録する。
7. 新旧ドキュメントの索引・参照を確認し、正式な移行手順を整備する。

## 8. 安全運用原則

- 新旧スクリプトを混同せず、`-Install` は保護条件の再確認まで実行しない。
- Portable SSD の既存 `.venv` は維持する。
- A/B の設定ファイルと実行環境は各 PC で独立して扱う。
- 変更操作は Preview → 検証 → Apply → Git 差分確認 → Commit の順に行う。
- 文書化した PASS / SKIPPED / 未実施の境界を明示する。
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Create the Markdown file. Refuse overwrite.")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    target = root / "documents" / "CH12-Portable.md"
    expected = (
        "resolve_environment.ps1",
        "setup_python_environment_pc.ps1",
        "verify_runtime_environment_pc.ps1",
        "verify_runtime_health_pc.ps1",
    )
    missing = [name for name in expected if not (root / "bootstrap" / name).is_file()]
    if missing:
        raise SystemExit("Missing CH12 scripts in bootstrap/: " + ", ".join(missing))
    if not (root / "documents").is_dir():
        raise SystemExit("documents directory is missing.")
    if target.exists():
        raise SystemExit(f"Target already exists; refusing overwrite: {target}")

    text = DOCUMENT.strip() + "\n"
    headings = [line for line in text.splitlines() if line.startswith("# " ) or line.startswith("## ")]
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    print("=== CH12 Portable documentation (" + ("APPLY" if args.apply else "PREVIEW") + ") ===")
    print("Repository:       ", root)
    print("Target:           ", target)
    print("Sections:         ", len(headings))
    print("Lines:            ", len(text.splitlines()))
    print("SHA256:           ", digest)
    for heading in headings:
        print(" ", heading)
    if not args.apply:
        print("PREVIEW ONLY: No files were modified.")
        return 0

    # 'x' refuses overwrite even if another process creates the target after the existence check.
    with target.open("x", encoding="utf-8", newline="\n") as fp:
        fp.write(text)
    print("APPLIED: Created CH12 Markdown. Git staging and commit NOT performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
