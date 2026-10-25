# AI-MR Sandbox ブートストラップ

このフォルダーは、`AI_MR_Sandbox`を別のPCまたは別のドライブへクローンした後、AI-MR SandboxのPython実行環境を再構築するために使用する。

仮想環境そのものは持ち運ばない。各PCでリポジトリ直下の`.venv`を作成するため、ドライブレターが変わっても同じ手順を使用できる。

## 前提条件

- Windows 11
- Python 3.11とPython Launcher (`py.exe`)
- Ollama
- Ollamaモデル `qwen3:8b`
- 初回インストール時のインターネット接続

Ollama、Qwen、Unity、MREAL関連ソフトウェアはPythonパッケージではないため、このブートストラップでは自動インストールしない。検証スクリプトで利用可能かを確認する。

## 1. Python環境の構築

リポジトリのルートでPowerShellを開き、次を実行する。

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
& ".\bootstrap\setup_python_environment.ps1"
```

スクリプトは自身の配置場所からリポジトリのルートを取得し、次を実行する。

1. Python 3.11を確認する。
2. リポジトリ直下に`.venv`を作成する。
3. 検証済みの`requirements-runtime-lock.txt`を優先し、音声入力・音声認識ライブラリと依存関係を導入する。ロックファイルがない場合は`requirements-runtime.txt`を使用する。
4. `pip check`とパッケージのimport確認を行う。

### 依存関係ファイル

- `requirements-runtime-lock.txt`：動作確認済み環境の全依存パッケージを固定した再現用ファイル。
- `requirements-runtime.txt`：直接必要なパッケージだけを記載した最小構成・フォールバック用ファイル。

## 2. 環境検証

Ollamaを起動してから次を実行する。

```powershell
& ".\bootstrap\verify_runtime_environment.ps1"
```

この検証では、次を確認する。

- AI-MR SandboxのPython・Unity主要ファイル8件
- `.venv`内のPythonパッケージ
- Tkinter GUI
- Ollamaの実行ファイル
- `qwen3:8b`モデル
- `http://localhost:11434`のOllama API

`AI-MR Sandbox environment verification: OK`と表示されれば、次の機能試験へ進める。

## 保存方針

- `.venv`はGit管理外とし、接続先PCごとに再作成する。
- Whisper baseのモデルキャッシュはユーザー側のHugging Faceキャッシュへ保存される。
- 研究データや生成物は`%USERPROFILE%\AI_MR_Workspace`へ保存する。
- ポータブルSSDには、ソース、ブートストラップ、初期機能テストだけを保持する。
