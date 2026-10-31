# -*- coding: utf-8 -*-
r"""Append CH12 §10.8 after validating the exact prior document.

Save to support/append_ch12_verification_experience.py and run from repo root:
    py -3.11 ".\support\append_ch12_verification_experience.py"          # Preview
    py -3.11 ".\support\append_ch12_verification_experience.py" --apply  # Apply

Old document bytes are preserved. Only CH12 is modified; Git and experiment data are untouched.
"""
from __future__ import annotations
import argparse
import hashlib
import os
import tempfile
from pathlib import Path

EXPECTED_HASH = "566e145b1bb6160d6253cf4c8b5858a9679b9e3ed21c596523482937ab5e8996"
HEADING = "### 10.8 Action Verification・Human Evaluation・Experienceの実機検証（2026-10-31）"
SECTION = """### 10.8 Action Verification・Human Evaluation・Experienceの実機検証（2026-10-31）

本節は10.5節のE2E接続試験に続く**別段階のコード照合と実機検証**を記録する。10.5節の「Verification／Experience未確認」は、その試験時点の判定として保持する。実機試験に使用した公式基準版は `unity/MREAL_OpenXR_Sample6_Haptic_Sandbox` であり、共同研究者によるGUI操作テスト派生版 `_ollama_test` ではない。

#### 10.8.1 Unity／AIR Manager間の実装照合

| 段階 | 実装 | コード上確認した処理 |
| --- | --- | --- |
| ① Python → Unity | `TcpSpeechReceiver.cs` | TCP `127.0.0.1:50000`で受信したAction JSONをキューから処理し、`PermissionChecker.IsAllowed`を呼び出す |
| ② Unity → AIR | `AIRStateSender.cs` | `humanTransform`からHuman_1の`x,y,z,yaw`を取得し、`direction`とともに`air_entity_state` JSONをTCP `127.0.0.1:50001`へ送る |
| ③ AIRで目標計算 | `C++/AIRManager_v2/AIRManager/AIRManager.cpp` | Human_1の位置・yaw・方向に基づき水平面上の身体基準方向ベクトルを算出し、距離`1.0`を加算する。`targetY`はHuman_1のyと同じ |
| ④ AIR → Unity | `AIRManager.cpp` → `AIRStateSender.cs` | `air_target_position`（`reference`、`direction`、`x,y,z`）を同じTCP接続で返信し、Unityが受信する |
| ⑤ UnityでAI_1移動 | `AIRStateSender.cs` | `type == "air_target_position"`の場合、`aiTransform.position = new Vector3(target.x,target.y,target.z)`で直接位置を更新する |

**AIR Manager自身はAI_1を移動させない。** AIR Managerの現行コードはリクエストごとに座標を計算する構成で、複数エンティティ状態や履歴の永続管理が実装済みとはいえない。上表は提示されたC#・C++**ソースの照合**であり、稼働した実行ファイルとソースの厳密なビルド同一性は別途検証が必要である。

#### 10.8.2 Verification・人間評価・Experienceの連鎖

- `ActionVerifier.VerifyPosition(request)`は、Unity側でHuman_1のTransformと方向から期待位置を**別途算出**し、AI_1の実位置との距離誤差を測る。既定値は`targetDistance=1.0`、`tolerance=0.05`であり、`error <= tolerance`をPASSとする。AIR返信値を直接検証の正解値に流用しないが、同じHuman_1のTransformに依存するため完全独立の計測系ではない。
- `HumanEvaluator.StartEvaluation(request,error,passed)`は評価待ちを開始し、Yキーを`correct`、Nキーを`incorrect`として`ExperienceLogger.SaveExperience`へ渡す。
- `ExperienceLogger.cs`は`timestamp, speaker, action, reference, direction, error, verificationPassed, humanEvaluation`の8項目を、リポジトリ直下の`tmp/experience.jsonl`に追記する。ユーザーWorkspace（B側）への保存先分離は未実施である。

#### 10.8.3 2026年10月31日の実機検証結果

| 項目 | 判定 | 実測・観測結果 |
| --- | --- | --- |
| 音声命令によるAIR経由の行動 | PASS | 公式基準版に「私の右側に来てください」を入力 |
| Action Verification | PASS | Unity Console：`Verification: PASS Direction = right Error = 0` |
| Human Evaluation | PASS | Yキーによる`correct`を新規Experience記録で確認 |
| Experience JSONL追記 | PASS | 既存3件から4件へ増加。追加レコードのtimestampは`2026-10-31T23:53:33.5156727+09:00` |
| 既存3件の保全 | PASS | 先頭586バイトのSHA256が、試験前のファイル全体のSHA256と一致 |
| 新規レコードの内容 | PASS | `direction=right`、`error=0.0`、`verificationPassed=true`、`humanEvaluation=correct`。JSONとして正常に解析可能 |
| FAIL・incorrect・通信障害 | **未検証** | 今回の実機試験は成功ケース1件 |

先頭586バイトの事前SHA256は`5785d37e53f80f2e02d1a6fa4098499e8b7649d4127a195616037dc26e24a9a4`。従前の3件は**2026年10月2日**の記録であり、10月31日の試験と区別する。

#### 10.8.4 制約と次の検証

- `SendHumanState()`は`void`で、接続失敗を内部でログ出力する。呼び出し側の`Action executed through AIR Manager.`は成功ACKではなく、通信失敗時にも表示され得る。
- 提示された`AIRTargetPosition`クラスには`[System.Serializable]`がない。JSON復元と実機での動作との整合を別途確認する。
- C#／C++のTCP受信はそれぞれ単発のRead／recvで、分割受信・タイムアウトなどの堅牢性試験は未実施。
- AIR側はyawのみで水平面上の目標位置を計算する一方、VerifierはUnityの`Transform.right/forward`を用いる。Human_1にpitch／rollがある場合の一致は未検証。
- 未評価データの上書き、FAIL／incorrect、通信障害、複数命令時のExperience記録の成否は未検証。
- UML補助図`CH12-AIRManager-Sequence.pptx`の⑦〜⑨は本節のコード照合で裏付けられた。⑩Verification、⑪Human Evaluation、⑫Experience保存は図の次版で追加する。

**到達点：** GPUのない別PCでも、音声解釈からAIR計算・Unity移動に加え、Verification、Yキー評価、JSONL永続記録まで、**成功ケース1件のE2E動作**を実機で確認した。未検証の失敗ケースや性能まで保証するものではない。
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    target = root / 'documents' / 'CH12-Portable.md'
    if not target.is_file():
        raise SystemExit(f'ERROR: CH12 not found: {target}')
    old = target.read_bytes()
    current_sha = hashlib.sha256(old).hexdigest()
    if current_sha != EXPECTED_HASH:
        raise SystemExit(f'ERROR: SHA256 mismatch, untouched. Expected {EXPECTED_HASH}, actual {current_sha}')
    text = old.decode('utf-8')
    if text.count('### 10.7 本試験の意義と今後の検証') != 1 or '### 10.8 ' in text:
        raise SystemExit('ERROR: Unexpected CH12 section structure; untouched')
    newline = '\r\n' if b'\r\n' in old else '\n'
    separator = newline if old.endswith(b'\n') else newline + newline
    updated = old + separator.encode('utf-8') + SECTION.replace('\n', newline).encode('utf-8')
    print('=== CH12 §10.8 (' + ('APPLY' if args.apply else 'PREVIEW') + ') ===')
    print('Repository:', root)
    print('Target:', target)
    print('Original SHA256:', current_sha)
    print('Updated SHA256:', hashlib.sha256(updated).hexdigest())
    print('Old document byte-for-byte preserved: YES')
    print('Added heading:', HEADING)
    print('Git/Unity/Experience files changed by this script: NO')
    if not args.apply:
        print('PREVIEW ONLY: No files changed.')
        return
    if target.read_bytes() != old:
        raise SystemExit('ERROR: CH12 changed after validation')
    tmp = None
    try:
        with tempfile.NamedTemporaryFile('wb', dir=target.parent, prefix='.ch12-10-8-', suffix='.tmp', delete=False) as stream:
            tmp = Path(stream.name)
            stream.write(updated)
            stream.flush()
            os.fsync(stream.fileno())
        if target.read_bytes() != old:
            raise SystemExit('ERROR: CH12 changed before replacement')
        os.replace(tmp, target)
        tmp = None
    finally:
        if tmp and tmp.exists():
            tmp.unlink()
    print('APPLIED: Section 10.8 appended. Git staging/commit NOT performed.')


if __name__ == '__main__':
    main()
