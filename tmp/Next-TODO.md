# Next TODO — AI_MR_Sandbox / CH12 実装・実機検証

**最終更新:** 2026-11-01（JST）  
**作業再開地点:** CH12の成功ケースE2E検証・文書化・GitHub保存まで完了。次は実験証拠のバックアップ確認と、Verification `FAIL`／Human Evaluation `incorrect` の追加実機試験。  
**作業ブランチ:** `portability-cleanup`  
**直近のGitHub反映コミット:** `70bec9e` — *Update CH12 sequence diagram with verified AIR and Experience flow*

> このファイルは次回作業の申し送り用。ここに書かれた未検証項目を、完了済みと取り違えないこと。実験前後は **Preview → Apply → Verify → Commit → Push** と進める。PowerShellコマンドは各々1行で実行する。

## 1. 現時点で完了していること

- **公式Unity基準版**は `unity/MREAL_OpenXR_Sample6_Haptic_Sandbox`。Unityプロジェクトは最小構成を維持する。
- `unity/MREAL_OpenXR_Sample6_Haptic_Sandbox_ollama_test` は共同研究者による**GUI入力テスト機能付き派生版**（時系列上は後発）。公式基準版とは混同しない。
- 別PCのCPU環境で **マイク → Whisper base（CPU/int8） → Ollama/Qwen3:8b → Unity TCP :50000 → PermissionChecker → AIR Manager TCP :50001 → UnityによるAI_1移動** が成功。
- C#・C++ソース照合で、`AIRStateSender.cs` はHuman_1の `x,y,z,yaw,direction` を `air_entity_state` として送信し、`AIRManager.cpp` は基準位置と方向から目標座標を計算して `air_target_position` を返信し、**Unityが** `aiTransform.position` を更新すると確認。AIR Managerが直接AI_1を操作するのではない。
- `ActionVerifier.cs` はAIR返信値をそのまま使わずUnity側で期待位置を別途計算し、誤差を判定。`HumanEvaluator.cs` はY/Nキー、`ExperienceLogger.cs` はJSONL追記を担当。
- **2026-10-31 23:53:33 JST** の `right` 成功ケース：`Verification: PASS Direction = right Error = 0`、Yキー `correct`、JSONLが**3件→4件**に増加。既存3件は2026-10-02の別実験であり、今回の実験データではない。
- CH12 `documents/CH12-Portable.md` 第10.8節に記録済み。編集済み2枚構成のシーケンス図 `documents/CH12-AIRManager-Sequence.pptx` もGitHub保存済み。
- 直近のPushで `origin/portability-cleanup` は `70bec9e` まで反映済み。Unityの5つの `.cs.meta` は `3e6d9a3` で正規化を採用済み。意図しないOpenXRの空のiPhone設定は復元済み。

## 2. 実験証拠・バックアップ（最優先で確認）

- Git管理下の**現在の未コミット変更**：`tmp/experience.jsonl`。**安易に `git restore`、削除、上書き、`git add -A` しないこと。**
- 2026-11-01時点の4件入りログのSHA256：`D04444C9EC73D2D490DBACBEFE58EB977257D8534B09FDE019A0976482BA268F`。
- 更新前3件のファイルサイズ：586バイト。先頭586バイトのSHA256：`5785D37E53F80F2E02D1A6FA4098499E8B7649D4127A195616037DC26E24A9A4`（先頭3件保全確認済み）。
- **B側Workspace**：`C:\Users\vruser_1\AI_MR_Workspace`。
- 保存予定／保存先：`C:\Users\vruser_1\AI_MR_Workspace\evidence\CH12\experience-2026-10-31-success.jsonl`。
- **直近のユーザー報告はバックアップ操作に対する「OK」**。コピー先のハッシュを表示したログは未取得なので、次回最初に同一性を確認する。バックアップが実在するまでは成功証拠の保全完了を断定しない。

### 次回最初のコマンド（読み取り専用・PowerShell 1行）

```powershell
$src='.\tmp\experience.jsonl'; $dst='C:\Users\vruser_1\AI_MR_Workspace\evidence\CH12\experience-2026-10-31-success.jsonl'; $expected='D04444C9EC73D2D490DBACBEFE58EB977257D8534B09FDE019A0976482BA268F'; if(!(Test-Path -LiteralPath $src) -or !(Test-Path -LiteralPath $dst)){throw 'Evidence file missing'}; $hs=(Get-FileHash -LiteralPath $src -Algorithm SHA256).Hash; $hd=(Get-FileHash -LiteralPath $dst -Algorithm SHA256).Hash; Write-Output "Source SHA256: $hs"; Write-Output "Backup SHA256: $hd"; if($hs -ne $expected -or $hd -ne $expected){throw 'Evidence hash mismatch'}; Write-Output 'Evidence backup: VERIFIED / PASS'; git -c safe.directory=E:/AI_MR_Sandbox status -sb
```

※このコマンドは、**次の追加実験を開始する前の4件状態**で実行すること。追加実験後は元ファイルのハッシュが変わるため、別の時点の記録として扱う。

## 3. 次の実機検証：成功例の先へ

実験は公式基準版で実施。まず現在のログ・シーン・設定値を確認し、**一度に1条件だけ**変える。

- [ ] **準備確認**：証拠バックアップのSHA256一致、Git `status -sb`、Unity停止状態を確認。`tmp/experience.jsonl` は未コミットのまま保全。
- [ ] **起動確認**：Ollama TCP `11434`、AIR Manager TCP `50001`、Unity Play時 TCP `50000` の待受を確認。音声Runtimeは `C:\AI_venvs\AI_MR_Sandbox_Runtime\Scripts\python.exe` を使う。二重起動を避ける。
- [ ] **Verification FAIL試験の方法を先に設計**：コードを変更せず、例えばUnity Play中のみ `ActionVerifier.targetDistance` を現行`1.0`から試験値へ変えて、正常なAIR座標計算とは独立に期待位置をずらす方法を検討。**提案であり未実施**。Inspectorで参照対象と元の値を確認し、変更・復元がPlay停止時に残らないことを確認する。`tolerance=0.05`、Human_1のpitch/roll・現在姿勢にも注意。
- [ ] **FAILを観測**：Unity Consoleの`Verification: FAIL`、`Error`値、AI_1の位置を記録する。通信成功ログを移動成功ACKと取り違えない。
- [ ] **Human Evaluation `incorrect`試験**：評価要求時にNキーを入力し、`humanEvaluation="incorrect"` を確認。FAILとincorrectの組合せ、またはPASSとincorrectの不一致ケースを区別して記録する。
- [ ] **JSONL追記の検証**：新しいtimestamp、direction、error、`verificationPassed`、`humanEvaluation` を読み、増加件数と保存先を検証。実験ごとにB側Workspaceへ識別可能なスナップショットを保存する。
- [ ] **通信障害時の分離検証**：AIR Manager停止などの条件では、Unityの`AIR Send Error`、`Action executed through AIR Manager.`、Verification呼び出しとExperience保存挙動を区別する。実行中の作業を壊さないよう、正常系を保全してから行う。
- [ ] Unity Editorを終了後に `git status` を確認し、OpenXRの空のiPhone設定などの予期しない変更を個別に評価。Experience証拠は復元しない。

### 実験上の注意点（コード照合から）

- `AIRStateSender.SendHumanState()` は`void`で通信例外を内部ログ化するため、呼出し側の`Action executed through AIR Manager.`は**成功ACKではない**。通信失敗時にもVerificationが続き得る。
- C++ AIR Managerはyawのみで水平面方向を計算。UnityのActionVerifierはTransformの`right/forward`を用いるため、pitch/rollを含む姿勢では差が生じ得る。
- `AIRTargetPosition`のC#クラスには提示されたソース上で`[System.Serializable]`がない。実行ファイルと提示ソースの厳密な一致は未確認。**コード変更前に**Unity Consoleと稼働状態を改めて照合する。
- C#／C++のTCP受信はいずれも単発`Read`／`recv`。部分受信・タイムアウト・切断・不正JSON時の堅牢性は未検証。
- `HumanEvaluator`の評価待ちは1件のみ。次の命令で上書きされ得る。Y/N入力は**Unity Gameウィンドウのフォーカス**が必要。
- `ExperienceLogger.cs` は**CP932（Shift-JIS系）**で保存されている。確認時には文字コードに注意。ソース変換は別作業とする。
- Experienceは現状C側の `tmp/experience.jsonl` に保存される。将来的なB側Workspaceへの出力経路変更は、今回の検証とは分ける。

## 4. 次の文書化・Git管理

- [ ] 試験が終わったらCH12第10.8節の次に結果を**追補**する（過去の試験時点の記述を消さない）。PASS・FAIL・incorrect・通信障害の**コード確認／実測／未検証**を分ける。
- [ ] `documents/README.md` の検証範囲の注意書きは、10月31日のVerification・Experience成功実験より**古い状態**を示す可能性がある。CH12第10.8節と照合して改訂する。
- [ ] 編集済み2枚の `documents/CH12-AIRManager-Sequence.pptx` を**原本として保持**する。レイアウトを修正する場合はユーザー整形版から作業し、勝手に前の生成版へ戻さない。
- [ ] 実験データをGitに含めるかは**別途方針決定**。今は `tmp/experience.jsonl` の未コミット変更を保持する。追加の資料をコミットする際はファイルを個別指定し、`git add -A` は使わない。
- [ ] 各変更でPreview → Apply → Verify → Commit → Push。コミットID・Push後の `git status -sb` を確認する。
- [ ] `tmp/Next-TODO.md` 自身も、別PC・別チャットから継続するなら**Git追跡の是非を確認**する。`tmp/` のignore設定と実験ログの扱いを混同しない。

## 5. 再開時に参照する主な実装・記録

| 種別 | リポジトリ内の参照先 |
| --- | --- |
| 実機再現性・検証記録 | `documents/CH12-Portable.md`（第10節、特に10.8） |
| 編集済みUMLシーケンス図 | `documents/CH12-AIRManager-Sequence.pptx`（2枚） |
| 文書索引 | `documents/README.md` |
| Python音声・LLM→Unity | `python/speech_to_unity_ollama.py` |
| TCP受信・Permission呼出し | `unity/MREAL_OpenXR_Sample6_Haptic_Sandbox/Assets/MyWork/TcpSpeechReceiver.cs` |
| AIR送受信・AI_1移動 | `unity/MREAL_OpenXR_Sample6_Haptic_Sandbox/Assets/MyWork/AIRStateSender.cs` |
| C++目標座標計算 | `C++/AIRManager_v2/AIRManager/AIRManager.cpp` |
| 独立位置検証 | `unity/MREAL_OpenXR_Sample6_Haptic_Sandbox/Assets/MyWork/ActionVerifier.cs` |
| Y/N人間評価 | `unity/MREAL_OpenXR_Sample6_Haptic_Sandbox/Assets/MyWork/HumanEvaluator.cs` |
| Experience JSONL追記 | `unity/MREAL_OpenXR_Sample6_Haptic_Sandbox/Assets/MyWork/ExperienceLogger.cs` |
| 現在の実験ログ | `tmp/experience.jsonl` |

## 6. 次回の会話で伝える短い申し送り

「`E:\AI_MR_Sandbox\tmp\Next-TODO.md` の続きです。CH12の成功ケースE2EとUML図のGitHub保存（コミット`70bec9e`）は完了、Experienceは4件で10月31日のright/PASS/correctを含みます。まずB側Workspaceへの証拠バックアップのSHA256を確認し、その後、Verification FAIL／Human Evaluation incorrect／通信障害の試験を1段階ずつ進めたいです。公式Unity版は `_ollama_test` ではありません。PowerShellは1行ずつ、Preview→Apply→Verifyの順でお願いします。」
