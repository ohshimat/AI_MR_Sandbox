# AI_MR_Sandbox 初回PCセットアップGUI（試作）

Windows標準のTkinterだけで動く、CH10.5 / CH10.6 / CH10.7 用の確認・準備GUIです。**完成済みの自動インストーラではありません。**

## 配置

`setup_environment_gui.py` をAI_MR_Sandboxのリポジトリ直下にコピーします。`documents/` の存在から参照文書を判断します。

## 起動（PowerShell 1行）

```powershell
py -3.11 .\setup_environment_gui.py
```

## 機能

- ソース／PC固有のPython venv／モデル・実行資源／ユーザ成果物を別領域へ分離
- Python 3.11、Git、NVIDIA GPU、Ollamaの事前チェック
- 既存PC側の仮想環境は変更せず再利用、新しいものだけ作成
- 作業領域を既存ファイルを消さずに作成
- OllamaローカルAPIと `qwen3:8b` を確認（取得は手動）
- CUDAと各種Python依存ライブラリの確認（導入は手動）
- SDXL Baseモデルの候補探索（完全性・生成成功の検証は別途）
- 既存 `setup_image_learning_gui.cmd` の場所を案内（自動実行なし）

## 重要な限界

1. Windows上の実機では未検証です。
2. CH10.6/10.7には古い `.venv` 構成と新しい `C:\AI_venvs` 構成が併記されているため、後者を標準にしています。
3. モデルの自動ダウンロード、CUDA版PyTorchインストール、LoRAの実行試験、GUI依存パッケージ導入はまだ未実装です。
4. ローカル `setup_image_learning_gui.cmd` は環境固定パスを持つ場合があるため、読み合わせるまで自動起動しません。
5. 既存のモデル、Python環境、Git管理対象は削除せず、Git commit/pushも行いません。

## 次の開発工程

リポジトリの現物（セットアップ `.cmd`、requirements、`image_learning_gui`）を照合し、検証済みのステージ別実行コマンドとログ・復旧処理をGUIへ接続します。
