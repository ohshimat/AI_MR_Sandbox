# AI-MR Sandbox ポータブル環境 初期設定手順

## 1. 目的

この文書は、`AI_MR_Sandbox`を外部SSDなどへ配置し、別のPCまたは異なるドライブレターでも実行環境を再構築するための初回手順を示す。

仮想環境、AIモデル、Unityの生成キャッシュは持ち運ぶ前提にしない。Gitで管理するソースとブートストラップを基準に、PCごとに再生成する。

## 2. 保存領域の役割

| 保存先 | 内容 | Git管理 |
|---|---|---|
| ポータブルSSDの`AI_MR_Sandbox` | ソース、Unityプロジェクト、ブートストラップ、初期試験用EXE | 対象 |
| リポジトリ直下の`.venv` | そのPC専用のPython仮想環境 | 対象外 |
| `%USERPROFILE%\AI_MR_Workspace` | 実験記録、生成物、ユーザー作業データ | 対象外 |
| PC上のOllamaモデル領域 | `qwen3:8b`などの大容量モデル | 対象外 |
| Unityプロジェクト内の`Library`等 | Unityが再生成するキャッシュ | 対象外 |

この分離により、SSDのドライブレターが変わっても、リポジトリ内の相対パスで実行できる。

## 3. 前提条件

対象PCに次を準備する。

- Windows 11
- Git
- Python 3.11とPython Launcher（`py.exe`）
- Ollama
- Ollamaモデル`qwen3:8b`
- Unity Hub
- Unity Editor 2022.3.62f3
- 初回セットアップ時のインターネット接続
- C++を再ビルドする場合のみVisual Studio 2022のC++ビルド環境

MREAL、ハプティックデバイス、OpenXR実機は、PC画面上の初期連携試験だけであれば未接続でもよい。

## 4. リポジトリの取得

PowerShellでポータブルSSDのルートへ移動する。ドライブレターを文書やスクリプトへ固定しない。

```powershell
Set-Location "<ポータブルSSDのルート>"
git clone --branch portability-cleanup --single-branch https://github.com/ohshimat/AI_MR_Sandbox.git AI_MR_Sandbox
Set-Location ".\AI_MR_Sandbox"
```

`portability-cleanup`が`main`へ統合された後は、`--branch portability-cleanup --single-branch`を省略できる。

取得結果を確認する。

```powershell
git rev-parse --show-toplevel
git branch --show-current
git --no-pager log -1 --oneline
git status --short
```

最後のコマンドで何も表示されなければ、作業ツリーはクリーンである。

## 5. Python実行環境の構築

リポジトリのルートで実行ポリシーを現在のPowerShellだけ一時的に許可する。

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

ブートストラップを実行する。

```powershell
& ".\bootstrap\setup_python_environment.ps1"
```

この処理は次を自動実行する。

1. Python 3.11の確認
2. リポジトリ直下への`.venv`作成
3. `pip==26.2.1`の導入
4. `requirements-runtime-lock.txt`に基づく検証済み依存関係の導入
5. `pip check`と主要パッケージの確認

次が表示されれば成功である。

```text
No broken requirements found.
AI-MR Sandbox Python bootstrap completed.
```

## 6. OllamaとQwenの準備

Ollamaを起動し、モデルを確認する。

```powershell
ollama list
```

`qwen3:8b`がなければ、初回だけ取得する。

```powershell
ollama pull qwen3:8b
```

ローカル応答を確認する。

```powershell
ollama run qwen3:8b "日本語で「ローカル動作確認OK」とだけ答えてください。"
```

## 7. 環境の統合検証

Ollamaを起動した状態で実行する。

```powershell
& ".\bootstrap\verify_runtime_environment.ps1"
```

このスクリプトは次を確認する。

- Python仮想環境
- `sounddevice`と`faster-whisper`
- Tkinter GUI
- 主要Python・Unityファイル8件
- Ollama実行ファイル
- `qwen3:8b`
- Ollama API（`localhost:11434`）

次が表示されれば環境構築は合格である。

```text
CoreFilesChecked : 8
ErrorCount       : 0
AI-MR Sandbox environment verification: OK
```

## 8. マイクの確認

入力デバイス一覧を表示する。

```powershell
& ".\.venv\Scripts\python.exe" ".\python\speech_to_unity_ollama.py" --list-devices
```

使用するマイク番号を記録する。番号はPCや接続機器によって変わるため固定しない。GUIの「設定」から同じ番号を指定できる。

## 9. Unityプロジェクトの初回起動

対象プロジェクトは次である。

```text
unity\MREAL_OpenXR_Sample6_Haptic_Sandbox_ollama_test
```

要求されるEditorはUnity 2022.3.62f3である。Unity Hubから同じバージョンで開く。

初回は`Library`とパッケージキャッシュの生成に時間がかかる。完了後、次を確認する。

1. `Project Settings > Project Validation`に未解決項目がない。
2. Consoleに赤いコンパイルエラーがない。
3. `Assets/Scenes/Main_Conversation.unity`を開ける。
4. PlayとStopを正常に実行できる。

Project Validationで修正を行った場合は、直後に次を実行し、意図しない大量変更がないか確認する。

```powershell
git -c core.quotePath=false status --short
```

## 10. 初期設定の完了条件

次をすべて満たせば、ポータブル環境の初期設定は完了である。

- `.venv`がリポジトリ直下に作成された。
- 環境検証が`ErrorCount : 0`で終了した。
- `qwen3:8b`がローカル応答した。
- 入力マイクを確認できた。
- Unity 2022.3.62f3で対象プロジェクトを開けた。
- `Main_Conversation`をエラーなくPlay／Stopできた。

完了後は、`CURRENT_SYSTEM_TEST.md`に従って現在の統合機能を試験する。

## 11. 再構築と更新

`.venv`は別PCへコピーしない。破損時やPC変更時は削除後にブートストラップから再作成する。通常のリポジトリ更新後は、次を再実行すれば依存関係を同期できる。

```powershell
& ".\bootstrap\setup_python_environment.ps1"
& ".\bootstrap\verify_runtime_environment.ps1"
```

`requirements-runtime-lock.txt`は動作確認済みの全依存関係、`requirements-runtime.txt`は最小構成のフォールバックである。
