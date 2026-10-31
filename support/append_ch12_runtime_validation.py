# -*- coding: utf-8 -*-
"""Preview/apply CH12 Section 10 documenting PC-local speech-to-AIR E2E validation.

Place in the repository's support/ directory. From the repository root:
    py -3.11 support/append_ch12_runtime_validation.py
    py -3.11 support/append_ch12_runtime_validation.py --apply

Default is read-only. Apply appends Section 10 to CH12 and does not stage or commit.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import tempfile
from pathlib import Path

TARGET = Path("documents") / "CH12-Portable.md"
EXPECTED_SHA256 = "95154233298b693691a75d4eeb919d2ddeb016c2c82233a2a721362d7b33bb60"
SECTION_HEADING = "## 10. PC側Runtimeの実機再現性検証（2026-10-31 追補）"

SECTION = r"""## 10. PC側Runtimeの実機再現性検証（2026-10-31 追補）

この節は、前節までの設計・事前検証を踏まえ、2026年10月31日に事務・文書作成用PCで追加実施した**実機検証**の記録である。
第1～9節に残る「Runtime未インストール」「End-to-End未実施」等は**それぞれの節を作成した時点の状態**であり、本節が後日の到達状況を記録する。
過去の記述を事後的に成功へ書き換えない。

### 10.1 検証したPCと配置

| 項目 | 実際の検証環境 |
| --- | --- |
| PC | `DESKTOP-TIPMO1S`、Windows 11 Pro、Intel Core i7-1065G7、RAM 32GB、Intel Iris Plus Graphics |
| C：Portableリポジトリ | `E:\AI_MR_Sandbox`（当該PCでのドライブ文字） |
| A：PC側Python Runtime | `C:\AI_venvs\AI_MR_Sandbox_Runtime\Scripts\python.exe` |
| A：Ollamaモデル | `C:\AI_MR_Sandbox\models\ollama`（環境変数 `OLLAMA_MODELS`） |
| A：Whisperのモデル／キャッシュ | `C:\AI_MR_Sandbox\models\faster-whisper` を指定して使用 |
| B：ユーザWorkspace | `C:\Users\vruser_1\AI_MR_Workspace`（設定値。検証開始時点では未作成） |

このPCではPC側Runtimeを新規構築し、固定パッケージ27件をインストールした。
`pip check`、Level 3のPython import検査はPASSした。Portable SSD上の旧 `.venv` は保全した。

### 10.2 起動する実体と役割

| 実行実体／ファイル | 役割 | 通信・実行条件 |
| --- | --- | --- |
| `ollama.exe`（PC側） | `qwen3:8b` の推論を提供 | ローカルHTTP API `127.0.0.1:11434` |
| `C++/AIRManager_v2/x64/Debug/AIRManager.exe` | AIRの独立した実行系 | `127.0.0.1:50001` でTCP待受を実測 |
| Unity Editor：`unity/MREAL_OpenXR_Sample6_Haptic_Sandbox_ollama_test` | Sample6をPlayし、Action受信・表示・移動反映を行う | `TcpSpeechReceiver` が `127.0.0.1:50000` でTCP待受を実測 |
| `python/speech_to_unity_ollama.py` | マイク → Whisper → Ollama解釈 → JSON検証 → UnityへのTCP送信 | PC側Python Runtimeで実行。`--send` のときだけUnityへ送信 |
| Unity `TcpSpeechReceiver.cs` | JSON受信、UI更新、Permission判定、AIRへの送信呼び出し | `PermissionChecker.IsAllowed(request)` を実行 |
| Unity `AIRStateSender.cs` | `SendHumanState(direction)` によりAIR側へ状態を送る | 送信失敗時は `AIR Send Error` を記録 |
| Unity `AI_1` | 身体基準のAction実行対象 | 移動対象はUnity実装側で固定。Action JSONに対象名はない |

`AIRStateSender` とAIR Managerの**詳細な送受信JSON、AIR側での目標位置計算、Unityへの結果反映方式は、この試験ログだけでは確定できない**。
実機でAI_1の移動は観測できたが、これらのプロトコル内部の仕様はソースコード照合による追加文書化が必要である。

### 10.3 データフロー（観測結果と実装コードに基づく）

```mermaid
flowchart LR
    H["Human_1の発話"] --> MIC["マイク / sounddevice"]
    MIC --> W["Whisper base / CPU int8"]
    W --> TEXT["認識した日本語テキスト"]
    TEXT --> Q["Ollama qwen3:8b / HTTP :11434"]
    Q --> V["Python validate_command / JSON検証"]
    V -->|"moveの場合"| TCP["TCP :50000 / Action Request"]
    V -->|"noneの場合"| STOP["送信しない"]
    TCP --> U["Unity TcpSpeechReceiver / UI表示"]
    U --> P{"PermissionChecker"}
    P -->|"DENIED"| STOP
    P -->|"ALLOWED"| S["AIRStateSender.SendHumanState"]
    S --> AIR["AIR Manager / TCP :50001"]
    AIR -.->|"AIRからの結果反映: 内部詳細は要確認"| AI["Unity AI_1 / 移動を実測"]
```

マイク音声は `sounddevice` で44,100Hz・モノラル・5秒・16bitとして取得し、一時WAVへ保存してからWhisperで日本語認識する。
Whisperは `faster-whisper` の `base`、CPU、`int8` モード。
WAVは一時ディレクトリ内で扱われ、当該スクリプトでは録音データの恒久保存を行わない。

Pythonは認識文字列をOllamaの `/api/generate` に送り、`think:false`・`stream:false`・JSONスキーマ制約により
`{ "action": "move|none", "direction": "right|left|forward|none" }` の形式で分類させる。
PythonがActionと方向の組合せを検証してから、次のUnity用データを生成する（右側移動の例）。

```json
{
  "type": "action_request",
  "speaker": "Human_1",
  "action": "move",
  "reference": "Human_1",
  "direction": "right"
}
```

このJSONの送信先は `127.0.0.1:50000` である。移動対象 `AI_1` はJSONには含まれず、Unity側で固定する設計。
「Human_1の右／左／正面から水平1m」の移動を要求する仕様だが、**今回の実測では距離1mの数値測定までは行っていない**。

### 10.4 再現操作手順（このPCで確認した順序）

**前提：** Portable SSDを接続し、リポジトリルート `E:\AI_MR_Sandbox` を作業ディレクトリとする。
別PCではドライブ文字とマイク番号・Python実行パスをそのPCに合わせる。Unity Projectの資産と設定を変更する前に、現在の状態を保持する。

1. **Ollamaを起動する。** WindowsアプリとしてOllamaを起動したうえで、別PowerShellからHTTP APIが応答し `qwen3:8b` が登録されていることを確認する。

   ```powershell
   $r=Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/tags' -TimeoutSec 5; $r.models | Select-Object name
   ```

2. **AIR Managerを起動する。** Unityに移動命令を送る**前に**起動すること。研究用PCでの再現手順では、起動漏れが接続拒否につながった。

   ```powershell
   $exe=(Resolve-Path -LiteralPath '.\C++\AIRManager_v2\x64\Debug\AIRManager.exe').Path; Start-Process -FilePath $exe -WorkingDirectory (Split-Path -Parent $exe) -PassThru | Select-Object Id,ProcessName,HasExited
   ```

3. **Unityを起動する。** `unity/MREAL_OpenXR_Sample6_Haptic_Sandbox_ollama_test` の対象シーンを開き、Playモードにする。
   このPCではTMPの標準フォントを `LiberationSans SDF` に設定した。Hapticデバイスがない状態で `HapticsDirect` のDLLエラーは残ったが、今回のTCPおよびAI_1移動は実行できた。
   ただしHaptic機能は検証していない。

4. **ポート待受を別PowerShellから確認する。** 50000はUnity、50001はAIR Manager。単に待受中であるだけで、移動成功を意味しない。

   ```powershell
   Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -in @(50000,50001) } | Select-Object LocalAddress,LocalPort,OwningProcess
   ```

5. **まず確認モードでAction JSONを試す。** `--send` を付けない場合はUnityへ送信されない。

   ```powershell
   & "C:\AI_venvs\AI_MR_Sandbox_Runtime\Scripts\python.exe" ".\python\speech_to_unity_ollama.py" --text "私の前に来てください"
   ```

6. **テキストからのAIR移動を確認する。** UnityをPlay、AIR Managerを起動したまま実行する。

   ```powershell
   & "C:\AI_venvs\AI_MR_Sandbox_Runtime\Scripts\python.exe" ".\python\speech_to_unity_ollama.py" --text "私の右側に来てください" --send
   ```

   Pythonの `Unityへ送信しました` は送信の報告にすぎない。Unity側で `AI_1` のTransform Positionが変化し、右側へ移動したことを直接確認する。

7. **音声からの完全統合試験。** このPCでのマイク番号は `1`（Realtek Microphone Array）。別PCでは `sounddevice.query_devices()` で確認する。

   ```powershell
   $env:HF_HUB_CACHE='C:\AI_MR_Sandbox\models\faster-whisper'; & "C:\AI_venvs\AI_MR_Sandbox_Runtime\Scripts\python.exe" ".\python\speech_to_unity_ollama.py" --device 1 --send
   ```

   プログラムの案内に従ってEnterで5秒録音し、「私の左側に来てください」と発話する。
   Whisperの認識、Qwenの分類、Unity側のAction/Direction/Reference表示、**AI_1の左側への移動**を確認する。
   終了時は `q` を入力する。

### 10.5 実測結果と確認できた範囲

| 検証対象 | 結果 | 根拠・限界 |
| --- | --- | --- |
| PC側Python Runtime構築 | PASS | 27件の固定依存導入・`pip check` 成功 |
| マイク録音 | PASS | デフォルトRealtekマイク、5秒、44,100Hz。RMS 0.037354、Peak 0.298523 |
| Whisper日本語認識 | PASS | 発話「私の前に来てください」を一致して文字化 |
| Ollamaとモデル配置 | PASS | `qwen3:8b` 5.2GB、`C:\AI_MR_Sandbox\models\ollama` にblob 6件 |
| Qwen3:8bのCPU推論 | PASS | CPU 100%、初回応答10.9秒、モデル読込5.9秒、27 tokens、7.62 tokens/s、context 2048 |
| テキスト→Action JSON | PASS | `move/forward` と `move/right` が期待するスキーマで生成された |
| UnityのTCP受信 | PASS | `127.0.0.1:50000` にUnityが待受、Action/Direction/Reference表示を確認 |
| AIR Managerの起動・待受 | PASS | `AIRManager.exe`、`127.0.0.1:50001`、検証時PID 1380 |
| テキスト→Unity→AIR→AI_1 | PASS | AIR Manager起動後、右側へのAI_1移動を目視確認 |
| マイク→Whisper→Qwen→Unity→AIR→AI_1 | PASS | 「私の左側に来てください」でAI_1の移動を目視確認 |
| 移動距離1mの精度 | 未測定 | Transformの数値・許容誤差を記録していない |
| ActionVerifierの独立判定 | 未確認 | 本試験ではVerifierによる合否ログを検証していない |
| Experience／JSONL永続記録 | 未確認 | 本試験ではログの内容・保存先を確認していない |
| Hapticデバイスの稼働 | 未確認 | DLLロードエラーはあるが、主要な移動動作とは切り分けた |

### 10.6 失敗時の切り分けとログ解釈

- **Unityの画面にAction等が出るがAI_1が動かない場合：** AIR Managerの起動とTCPポート50001の待受を先に調べる。
- `AIR Send Error: ...接続できませんでした`：今回の実例ではAIR Managerの起動漏れと整合し、起動後に移動が成功した。ただし別の原因もあり得る。
- `Action executed through AIR Manager.`：`TcpSpeechReceiver.cs` が `SendHumanState` 呼出し後に出すログ。**AIRの受理・実行成功のACKではない**。エラー発生と同時に表示され得る。
- `Unityへ送信しました`：PythonのTCP `sendall` 完了表示であり、**Unity側の実行結果を受信したものではない**。
- `Permission: DENIED`：PermissionCheckerの判定とInspector参照を確認する。迂回や無条件許可への変更はしない。
- `HapticsDirect` の `DllNotFoundException`：今回のAI_1移動成功とは別問題として記録。必要になるまで関連プラグインの削除や設定変更をしない。
- `Default Font Asset`：別PCでTMP参照エラーが出た場合は、`LiberationSans SDF` と各UIのフォント・マテリアル参照を確認する。

### 10.7 本試験の意義と今後の検証

GPUを持たない事務用PCでも、**マイク → Whisper → Qwen3:8b → UnityのAction受信／Permission → AIR Manager → AI_1移動**の機能的再現性が確認された。
これは**動作する経路の確認**であり、リアルタイム性能、位置決め精度、AIR内部状態、Verification、Experienceまでのすべてが検証されたことを意味しない。

次段階では、`AIRStateSender.cs` と `AIRManager_v2` の通信データ形式・戻り値処理をソースで照合し、
許可判定・AIR実行・位置検証・Experience記録をログで独立に確認する。
起動順序、通信先、未確認項目は他PCの再現手順にも反映する。
"""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Append Section 10 (does not stage/commit).")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    target = root / TARGET
    if not target.is_file():
        raise SystemExit(f"BLOCKED: CH12 not found: {target}")
    original = target.read_bytes()
    if sha256(original) != EXPECTED_SHA256:
        raise SystemExit(
            "BLOCKED: CH12 has changed from the previously verified version. "
            f"Expected SHA256 {EXPECTED_SHA256}, got {sha256(original)}. No changes made."
        )
    text = original.decode("utf-8-sig")
    if SECTION_HEADING in text or "## 10." in text:
        raise SystemExit("BLOCKED: A Section 10 already exists. No changes made.")
    if "## 9. 文書体系の整理と履歴保全方針" not in text:
        raise SystemExit("BLOCKED: Section 9 is missing. No changes made.")
    if not (root / "documents" / "README.md").is_file():
        raise SystemExit("BLOCKED: documents/README.md missing. No changes made.")

    separator = "\n" if original.endswith(b"\n") else "\n\n"
    updated = original + (separator + SECTION.rstrip() + "\n").encode("utf-8")
    print("=== CH12 E2E reproduction documentation (" + ("APPLY" if args.apply else "PREVIEW") + ") ===")
    print("Repository:", root)
    print("Target:", target)
    print("Original SHA256:", sha256(original))
    print("Updated SHA256:", sha256(updated))
    print("Original lines:", len(text.splitlines()))
    print("New lines:", len(updated.decode("utf-8").splitlines()))
    print("Old document byte-for-byte preserved: YES")
    print("Added outline:")
    for line in SECTION.splitlines():
        if line.startswith("## ") or line.startswith("### "):
            print(" ", line)
    print("Git staging/commit: NOT PERFORMED")
    if not args.apply:
        print("PREVIEW ONLY: No files modified.")
        return 0

    # Create fully written temp beside target, replace only after rechecking.
    tmp: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(mode="wb", prefix=".ch12-e2e-", suffix=".tmp", dir=target.parent, delete=False) as handle:
            tmp = Path(handle.name)
            handle.write(updated)
            handle.flush()
            os.fsync(handle.fileno())
        if target.read_bytes() != original:
            raise RuntimeError("BLOCKED: CH12 changed during execution; no changes made.")
        os.replace(tmp, target)
        tmp = None
    finally:
        if tmp is not None and tmp.exists():
            tmp.unlink()
    print("APPLIED: Added CH12 Section 10. No other files or Git state changed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
