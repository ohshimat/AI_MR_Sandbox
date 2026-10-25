# AI画像学習・生成GUI

SDXL BaseとDreamBooth LoRAを完全ローカルで学習・生成する研究用GUIである。

初回セットアップとモデル取得の完了後は、Hugging Face関連ライブラリをオフラインモードに固定し、Gradioの分析送信を無効化して実験する。

Git管理する実行原本は、`AI_MR_Sandbox`リポジトリ直下の`image_learning_gui`である。外部SSDのドライブレターが変わっても、GUI内のworkerと学習スクリプトは相対パスで解決される。

すべての操作は、リポジトリ直下の`setup_image_learning_gui.cmd`と`start_image_learning_gui.cmd`から開始する。GUI本体をCドライブへ複製する必要はない。

旧方式の`deploy_gui_to_pc`と`update_gui_on_pc`は、既存PCとの互換確認用として残している。新しいポータブル運用では使用しない。

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

画像生成・学習用Python環境とSDXL Baseを準備した後、リポジトリ直下の`setup_image_learning_gui.cmd`を実行する。

Gradioとpytestは`C:\AI_MR_Sandbox\runtime\image_gui_packages`へ分離して導入する。既存のAI_MR_Sandbox仮想環境にあるPyTorch、Diffusers等は変更しない。

画像別キャプションに必要な`datasets`も、`C:\AI_MR_Sandbox\runtime\image_training_packages`へ分離して導入する。旧運用フォルダーに検証済みパッケージがある場合、初回セットアップはそれを共通runtimeへ移行する。

## 起動

リポジトリ直下の`start_image_learning_gui.cmd`をダブルクリックする。

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
& ".\setup_image_learning_gui.ps1"
```

Gradio導入前でも、標準ライブラリのテスト実行方法を使用できる。

セットアップ処理の最後に、ポータブル側の`image_learning_gui\tests`が自動実行される。
