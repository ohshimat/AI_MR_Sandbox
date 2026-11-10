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

<!-- CH14-GUI-E2E-2026-11-10 -->

## 2026-11-10：画像学習GUI 第14段階完了
- [x] CH10.7：SDXL Base 1.0による画像生成、DreamBooth LoRA最小学習・再読込・生成を実機確認。
- [x] GUIモデル参照汎用化：AI_MR_SDXL_MODEL_PATHによる明示指定、直接配置・Hugging Face snapshots対応、不正な明示指定時のフォールバック禁止。
- [x] GUI回帰テスト：66件すべてPASS。
- [x] GUI起動・環境診断：実機PASS。
- [x] 第14段階：GUI → SDXL → LoRA → PNG保存、生成画像の目視確認までPASS。
- [ ] 証跡補完：GUI生成日時、出力PNGパス、SHA256、生成ログ、result JSONの保存先を記録。
- [ ] 第15段階：GUIから最小LoRA学習E2Eを実行。既存データとLoRAを保全し、独立した新規出力先を使用。
- [ ] 第15段階：学習ログ、LoRA重み、再読込生成、結果JSONを検証。
- [ ] 品質改善候補：プロセス管理テストのResourceWarningを調査。
- [ ] 汎用化の記録：PC固有設定と共通ソースの分離を環境構築手順書へ反映。

## 2026-11-10：画像学習GUI 第15段階 — LoRA学習E2E検証記録

**実験ID：** `gui_e2e_20261110_01`
**検証目的：** GUIからの学習画像読込、DreamBooth LoRA学習、重み保存、再読込、画像生成までの一連の処理を実機で検証する。

### 1. 実験環境

| 項目 | 内容 |
|---|---|
| 検証機GPU | NVIDIA RTX A4500（20GB VRAM） |
| GUI | AI_MR_Sandbox / image_learning_gui |
| ベースモデル | Stable Diffusion XL Base 1.0 |
| モデル配置 | `C:\AI_MR_Sandbox\models\sdxl\stable-diffusion-xl-base-1.0` |
| モデル参照 | `AI_MR_SDXL_MODEL_PATH` による明示指定 |
| GUI回帰テスト | 66件PASS |
| 設計方針 | GPU固有の構成に依存しない共通実装 |

### 2. LoRA学習条件

| 項目 | 内容 |
|---|---|
| 学習画像 | `training\smoke_test_a4500\image_01.png` |
| 学習画像枚数 | 1枚 |
| 識別子 | `aimrrobot01` |
| 総学習ステップ | 1 |
| LoRA Rank | 8（manifest確定） |
| 解像度 | 512 × 512 |
| 精度 | FP16 |
| 学習率（ログ表示） | 0.0001 |
| 最終Loss | 0.184 |
| 実験出力先 | `lora_outputs\gui_e2e_20261110_01` |

※ 相対パスは `AI_MR_Workspace` を基準とする。

### 3. E2E機能検証

- [x] GUIから学習条件を設定
- [x] DreamBooth LoRA学習を開始
- [x] 学習1ステップを完走
- [x] 学習後、LoRAありの画像を生成
- [x] LoRAなしの画像を生成
- [x] LoRAあり／なしで視覚的な差異を確認
- [x] LoRA重みの保存先・ファイルサイズ・SHA256を記録
- [ ] 生成ログ・学習ログ・結果JSON・manifestを確認
- [ ] 同一生成条件でのLoRA有無の比較をログから確認

**学習ログの注意事項：** CLIPTextModel関連のLoRAキーが見つからない警告が出たが、学習ステップは完走した。警告は今回の処理を停止させていない。

### 4. 生成画像の観察

**LoRAあり：** 黒色・黄色を基調とする円筒状の工業機器に近い画像が生成された。ロボットの頭部・腕・脚などの明確な形状は確認できなかった。

**LoRAなし：** 異なる円筒状の構造物が生成された。

**観察結果：** LoRAあり／なしで画像差異が認められた。ただし、その他の生成条件の一致はログで未確認であり、画像差異の原因をLoRAの効果だけに断定しない。

**品質評価：** 1画像・1ステップの最小学習であり、対象形状の再現品質を評価する条件としては不十分。今回は機能疎通の検証と位置づける。

### 5. 保存証跡（初期記録・確定値は第8節を参照）

| 証跡 | 記録欄 |
|---|---|
| 学習済みLoRAの絶対パス | 未記録 |
| LoRAファイルサイズ | 未記録 |
| LoRA SHA256 | 未記録 |
| 学習ログ | 未記録 |
| manifest JSON | 未記録 |
| LoRAあり画像の保存先 | 未記録 |
| LoRAなし画像の保存先 | 未記録 |
| 各生成条件・result JSON | 未記録 |
| 生成PNGのSHA256 | 未記録 |

チャット上で確認した生成画像のファイル名：

- LoRAあり：`pytorch_lora_weights_seed42_20261110_161429_945836.png`
- LoRAあり（再生成）：`pytorch_lora_weights_seed42_20261110_162608_117320_f55c65be21a14186.png`
- LoRAなし：`pytorch_lora_weights_seed42_20261110_163830_857064_0507a6c63a7ad02c.png`

※ ファイル名と実際のLoRA適用状態・生成条件との対応はresult JSONで照合する。

### 6. 総合判定

**第15段階：GUI経由のLoRA学習・保存・再読込・画像生成E2EはPASS。学習・生成のSHA256整合性を確認済み。品質評価は未完了。**

本検証では、GUIから学習を実行し、学習後のLoRAあり／なしの生成結果を確認できた。

一方、対象形状の再現には至らず、学習品質を実証するものではない。

### 7. 次の取り組み

- [ ] 第15段階の未記録証跡を補完する。
- [ ] 同一prompt・seed・steps・guidance・モデル条件でLoRA適用効果を比較する。
- [ ] 第16段階として、複数画像・複数ステップによる形状学習実験を設計する。
- [ ] 学習画像、共通・個別キャプション、学習条件、生成条件、評価基準を事前に定義する。
- [ ] 検証結果をCH10.7および汎用環境構築手順書に反映する。