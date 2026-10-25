# AI画像学習・生成GUI

SDXL BaseとDreamBooth LoRAを完全ローカルで学習・生成する研究用GUIである。

Git管理する開発原本は、`AI_MR_Sandbox`リポジトリ直下の`image_learning_gui`である。外部SSDのドライブレターが変わっても、GUI内のworkerと学習スクリプトは相対パスで解決される。

正式なPC運用配置は`C:\AI_MR_Sandbox\image_learning_gui`とする。リポジトリ上の`deploy_gui_to_pc.cmd`を実行すると、運用用コピーを作成できる。リポジトリ上のGUIを直接起動して試験することもできる。

正式配置済みGUIを更新する場合は、開発原本の`update_gui_on_pc.cmd`を実行する。更新前のGUIは`C:\AI_MR_Sandbox\backups`へ退避され、主要ファイルのSHA-256照合後に切り替えられる。

GUIのソースは持ち運べるが、SDXL Base、LoRA、生成画像、Python仮想環境はGitへ含めない。PC共通リソースとユーザー作業領域をGUIから参照する。

関連文書：

- `docs\USER_GUIDE.md`
- `docs\IMPLEMENTATION_STATUS.md`
- リポジトリ直下の`IMAGE_LEARNING_GUI_SETUP.md`

## 現在の実装範囲

- ローカル環境とGPUの確認
- 学習画像フォルダの検査
- 固定プロンプト／画像別キャプションを選択したDreamBooth LoRA学習（個別`.txt`のない画像は共通プロンプトで補完）
- 継続元`checkpoint-N`をGUIで明示選択する継続学習
- 画像と同名の`.txt`キャプション編集、完全性検査、学習への適用
- 新規学習とcheckpointからの継続学習
- 学習・生成プロセスのログ表示と停止
- 学習済みLoRA、係数、prompt、seedによる画像生成
- 実験一式の外部ストレージ保存、SHA-256検査、PCへの復元
- PNG、生成条件JSON、学習manifest、SHA-256の保存
- 一つのGPUジョブだけを許可する排他制御

## 初回だけ行うこと

画像生成・学習用Python環境とSDXL Baseを準備した後、`install_gui_dependencies.cmd`と`install_training_dependencies.cmd`を実行する。

Gradioとpytestはプロジェクト内の `.gui_packages` へ分離して導入する。既存のAI_MR_Sandbox仮想環境にあるPyTorch、Diffusers等は変更しない。

画像別キャプションに必要な`datasets`も、プロジェクト内の`.training_packages`へ分離して導入する。学習時の一時キャッシュは`.datasets_cache`を使用する。

## 起動

リポジトリ上または正式配置後の`image_learning_gui\start_gui.cmd`をダブルクリックする。

ブラウザで `http://127.0.0.1:7860` が開く。外部公開は行わない。

GUIフォルダはPC本体・外部ストレージのどちらへ置いても起動できる。AI実行環境はPC本体のPython、SDXL Base、DreamBoothスクリプトを参照する。

生成画像は指定した保存先へ保存した後、ブラウザ表示用の複製だけを `.preview` へ置く。Gradioへ公開するローカル領域はこのプレビューフォルダに限定する。

## 最初の確認

1. 「環境・履歴」でCUDAと必須パスを確認する。
2. 「学習」で学習画像フォルダを検査する。
3. 「画像生成」でstep 600 LoRA、係数1.0、seed 42を指定する。
4. 既存LoRAから画像を1枚生成する。
5. 学習試験は専用の空フォルダを指定し、`1画像あたりの総学習回数`を1にして実行する。20枚なら目標は自動的に20ステップになる。

既存の `first_test` フォルダを新規学習の出力先として指定してはならない。継続学習に使用する場合も、実験前にGUIが表示するcheckpointと保存予定ファイルを確認する。

## 外部ストレージへの保存と復元

`保存・復元`タブでは、学習画像とキャプション、学習結果、生成結果を実験単位で保存する。保存先には`AI_MR_Research\experiments\実験名`が自動作成される。

全ファイルの相対パス、容量、SHA-256を`archive_manifest.json`へ記録する。復元時は完全性を検査し、PC側の新規フォルダへコピーする。既存フォルダは上書きしない。checkpointは継続学習が必要な実験だけ保存する。

## 学習スクリプトの配置

DreamBooth SDXL学習スクリプトはGUI内の`vendor\diffusers-0.41.0`に固定コミット版を収録する。GUIは相対パスで参照するため、PC本体と外部ストレージのどちらへGUIフォルダを置いても同じ構成で起動できる。外部SSD上の旧スクリプトには依存しない。

## テスト

```powershell
$env:PYTHONPATH = "$PWD\.gui_packages"
& "C:\AI_venvs\AI_MR_Sandbox\Scripts\python.exe" -m pytest -q
```

Gradio導入前でも、標準ライブラリのテスト実行方法を使用できる。

```powershell
& "C:\AI_venvs\AI_MR_Sandbox\Scripts\python.exe" -m unittest discover -s tests -v
```
