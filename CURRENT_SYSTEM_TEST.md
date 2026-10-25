# AI-MR Sandbox 現在機能 統合テスト手順

## 1. 目的と対象範囲

この文書は、現在の開発到達点である「音声または文字による移動命令をローカルLLMで解釈し、Unity内のAIエージェントへ反映する」一連の機能を再現・判定するための手順を示す。

今回の主要経路は次である。

```text
ユーザー入力
  → Whisper（音声の場合）
  → Ollama / Qwen3:8b
  → Python GUI・バックエンド
  → Unity MRConversationBridge
  → AIRManager
  → Unity内のAI_1移動
```

操作モードはローカル処理で完結する。OpenAI APIを使う「会話」モード、MREAL実機表示、ハンドトラッキング、ハプティック実機動作は、この基本試験の必須範囲に含めない。

## 2. 使用ポート

| ポート | 用途 | プロセス |
|---:|---|---|
| 11434 | ローカルLLM API | Ollama |
| 50001 | 座標計算要求と応答 | AIRManager_v2 |
| 50002 | Unityとの状態・命令連携 | Python GUIバックエンド |
| 50000 | 旧直接送信方式 | 現行GUI試験では使用しない |

`speech_to_unity_ollama.py --send`は旧方式の50000へ接続するため、現行の`Main_Conversation`試験には使用しない。

## 3. 事前確認

リポジトリのルートで、現在位置とGit状態を確認する。

```powershell
git rev-parse --show-toplevel
git branch --show-current
git status --short
```

Ollamaを起動し、環境検証を実行する。

```powershell
& ".\bootstrap\verify_runtime_environment.ps1"
```

次が表示されることを確認する。

```text
Ollama model qwen3:8b: OK
Ollama API: OK
ErrorCount : 0
AI-MR Sandbox environment verification: OK
```

## 4. AIRManagerの起動

PowerShellを1つ開き、リポジトリのルートで次を実行する。

```powershell
& ".\C++\AIRManager_v2\x64\Debug\AIRManager.exe"
```

次が表示された状態でウィンドウを開いておく。

```text
AIR Manager started.
AIR Manager waiting on port 50001...
```

旧版`C++\AIRManager`ではなく、継続待受けと複数方向に対応した`AIRManager_v2`を使用する。

## 5. Python GUIの起動

別のPowerShellを開き、リポジトリのルートで次を実行する。

```powershell
& ".\.venv\Scripts\python.exe" ".\python\mr_agent_gui.py"
```

GUIが表示されたら、次を確認する。

- タイトルが`MR Sandbox · AI_1`
- 初期モードが`操作 · Ollama`
- 二重起動によるポート50002エラーがない
- 「設定」で使用するマイク番号を選択できる

OpenAI APIキーは操作モードでは不要である。「会話 · OpenAI」を選んだ場合だけ必要となり、文字起こし、会話履歴、返答生成が外部APIへ送信され、利用料金が発生する。

## 6. Unityの起動

Unity 2022.3.62f3で次のプロジェクトを開く。

```text
unity\MREAL_OpenXR_Sample6_Haptic_Sandbox_ollama_test
```

`Assets/Scenes/Main_Conversation.unity`を開き、Playする。

GUI表示が次の状態になることを確認する。

```text
● Unity接続中
```

「話す」と「文字を送信」が有効になれば、Unity、GUI、バックエンドの接続は正常である。

## 7. ポートの確認

別のPowerShellで確認する。

```powershell
Get-NetTCPConnection -State Listen -LocalPort 50001,50002 -ErrorAction SilentlyContinue | Sort-Object LocalPort | Select-Object LocalAddress,LocalPort,OwningProcess
```

50001と50002の両方が表示されれば、必要な待受けは揃っている。Ollama APIは環境検証スクリプトで確認済みである。

## 8. 文字入力による移動試験

GUIで`操作 · Ollama`を選ぶ。入力欄へ次を1件ずつ入力し、「文字を送信」を押す。

```text
私の右へ移動してください
私の左へ移動してください
私の前へ移動してください
```

「私の右」のように表現する理由は、現在のAIRManagerが`Human_1`の位置とyawを基準に目標座標を計算するためである。移動対象は現在のシステムではAIエージェントとして暗黙に扱われる。

各命令で次を確認する。

- GUIが「完了」になる。
- AIRManagerに`Client connected.`、`Received:`、`Sent:`が表示される。
- AIRManagerの`Direction:`が入力した方向と一致する。
- Unity内の`AI_1`が意図した方向へ移動する。
- Unity Consoleに新しい赤いエラーがない。

## 9. 音声入力による移動試験

GUIの「設定」でマイク番号を確認し、`操作 · Ollama`を選ぶ。「● 話す（5秒）」を押し、表示に従って発話する。

推奨する試験発話：

```text
私の右へ移動してください
```

AIエージェント名を発音する必要がある場合、`AI_1`は「エーアイ・ワン」と発音する。アンダースコアは読まない。

次を確認する。

- 5秒間の録音が完了する。
- Whisperが日本語を文字起こしする。
- Qwenが`move`と方向を解釈する。
- Unity内の`AI_1`が移動する。

初回だけWhisper baseモデルの準備に時間がかかる場合がある。

## 10. 実験ログ

Sample6の実行ログは、リポジトリ内ではなくユーザー作業領域へ保存される。

```text
%USERPROFILE%\AI_MR_Workspace\gui_records\unity\experience.jsonl
```

PowerShellでは次で存在を確認できる。

```powershell
Get-Item -LiteralPath "$env:USERPROFILE\AI_MR_Workspace\gui_records\unity\experience.jsonl"
```

この分離により、実験ログをGitへ誤って追加せず、SSDのドライブレターにも依存しない。

## 11. 想定内の警告

### HapticsDirectの未使用フィールド

```text
warning CS0414: フィールド 'HapticPlugin.enablef' が割り当てられていますが、値は使用されていません
```

第三者プラグイン内のコンパイラ警告であり、今回の基本試験を妨げない。現時点ではプラグインを改変しない。

### Hand Tracking Subsystem

```text
Hand Tracking Subsystem not found or not running...
```

ヘッドセットやOpenXRハンドトラッキングを使用しないPC画面上の試験では想定内である。実機試験ではOpenXR設定と実機接続を別途確認する。

## 12. よくある問題

### GUIに「Unity未接続」と表示される

- `Main_Conversation`がPlay状態か確認する。
- GUIをUnityより先に終了していないか確認する。
- ポート50002が1つのGUIだけで待機しているか確認する。
- `MRConversationBridge`の参照設定を確認する。

### AIRManagerへ接続できない

- `AIRManager_v2`が起動中か確認する。
- ポート50001がListen状態か確認する。
- 旧版AIRManagerを同時起動しない。

### `WinError 10061`がポート50000で発生する

旧直接送信方式へ接続している。現行試験では`--send`を使用せず、GUI、`MRConversationBridge`、`AIRManager_v2`の経路を使用する。

### GUIを起動できない

- `.venv`のPythonを使っているか確認する。
- GUIを二重起動していないか確認する。
- `bootstrap\verify_runtime_environment.ps1`を再実行する。

### 音声を認識しない

- GUIの設定で入力マイク番号を確認する。
- Windowsのマイク許可を確認する。
- まず文字入力試験を行い、Unity連携と音声入力を切り分ける。

## 13. 終了手順

次の順で終了する。

1. UnityのPlayを停止する。
2. Python GUIを閉じる。
3. AIRManagerのPowerShellで`Ctrl+C`を押す。
4. 必要に応じてUnity EditorとOllamaを終了する。

終了後、ソースへ意図しない変更がないことを確認する。

```powershell
git -c core.quotePath=false status --short
```

何も表示されなければ正常である。Unityの`Library`、`Temp`、`Logs`、`.venv`はGit管理外である。

## 14. 合格基準

次をすべて満たせば、現在の開発到達点の基本試験は合格である。

- 環境検証が`ErrorCount : 0`で完了する。
- 50001と50002がListen状態になる。
- GUIが`Unity接続中`になる。
- 右・左・前の文字命令が正しく反映される。
- 音声入力が文字起こしされ、少なくとも1件の移動が成功する。
- AIRManagerの応答方向が入力方向と一致する。
- Unity Consoleに赤い実行エラーがない。
- 実験ログがユーザー作業領域へ保存される。
- 終了後のGit作業ツリーがクリーンである。

## 15. この手順で未検証の範囲

- OpenAI APIを使う会話・合成音声モード
- MREAL実機表示
- OpenXRハンドトラッキング
- ハプティックデバイスの実機動作
- 複数PC間通信

これらは基本試験と分離し、必要な機器・認証情報・費用条件を整えて個別に検証する。
