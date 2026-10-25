# AI画像生成・学習GUI 共有環境セットアップ手順

## 1. 目的

この文書は、`AI_MR_Sandbox`に収録された画像生成・学習GUIを別のPCで配備し、SDXL Baseによる生成とDreamBooth LoRA学習の基本動作を確認する手順を示す。

GUIのソースはGitで共有する。大容量またはPC固有の実体はGitへ入れず、PCごとに構築する。

## 2. 保存方針

| 保存先 | 内容 | Git管理 |
|---|---|---|
| `image_learning_gui` | GUI、テスト、worker、固定版DreamBoothスクリプト | 対象 |
| `C:\AI_venvs\AI_MR_Sandbox` | PyTorch、Diffusers等の画像AI実行環境 | 対象外 |
| `C:\AI_MR_Sandbox\models` | SDXL Base | 対象外 |
| `%USERPROFILE%\AI_MR_Workspace` | 学習画像、LoRA、生成画像、実験記録 | 対象外 |
| `.gui_packages`、`.training_packages` | GUI固有の導入済みパッケージ | 対象外・PCごとに再生成 |
| `.preview`、`.datasets_cache` | 再生成可能な一時データ | 対象外 |

## 3. 前提条件

- `CP10.6_InstallImageGeneration.md`に相当する画像生成環境が構築済みである。
- `CP10.7_InstallImageLearning.md`に相当するLoRA学習環境が構築済みである。
- `C:\AI_venvs\AI_MR_Sandbox\Scripts\python.exe`からCUDAを利用できる。
- `C:\AI_MR_Sandbox\models\huggingface`以下にSDXL Baseがある。
- GPUメモリを使用するUnity、Ollama、LM Studioなどは画像試験前に終了する。

確認する。

```powershell
& "C:\AI_venvs\AI_MR_Sandbox\Scripts\python.exe" -c "import torch, diffusers, transformers, peft, accelerate; print('PyTorch:', torch.__version__); print('Diffusers:', diffusers.__version__); print('CUDA:', torch.cuda.is_available())"
```

`CUDA: True`が表示されることを確認する。

## 4. GUIをPC本体へ配備

リポジトリ直下から次を実行する。

```powershell
& ".\image_learning_gui\deploy_gui_to_pc.cmd"
```

既に`C:\AI_MR_Sandbox\image_learning_gui`が存在するPCでは、GUIを終了してから次を実行する。

```powershell
& ".\image_learning_gui\update_gui_on_pc.cmd"
```

配備処理は、ソースと主要ファイルのSHA-256を照合する。`.gui_packages`、`.training_packages`、キャッシュ、プレビュー、ユーザー設定はコピーしない。

## 5. GUI固有依存関係の導入

初回だけ、PC本体へ配備したGUIフォルダーで次を順に実行する。

```powershell
Set-Location "C:\AI_MR_Sandbox\image_learning_gui"
& ".\install_gui_dependencies.cmd"
& ".\install_training_dependencies.cmd"
```

Gradio等は`.gui_packages`、`datasets`等は`.training_packages`へ分離して導入される。既存のPyTorchやDiffusersを上書きしない。

## 6. 自動テスト

```powershell
Set-Location "C:\AI_MR_Sandbox\image_learning_gui"
$env:PYTHONPATH = "$PWD\.gui_packages"
& "C:\AI_venvs\AI_MR_Sandbox\Scripts\python.exe" -m pytest -q
```

全テストが成功することを確認する。

## 7. GUIの起動

```powershell
& "C:\AI_MR_Sandbox\image_learning_gui\start_gui.cmd"
```

ブラウザで`http://127.0.0.1:7860`が開く。外部公開は行わない。

「環境・履歴」で次を確認する。

- CUDAが利用可能
- SDXL Baseが見つかる
- DreamBooth学習スクリプトが見つかる
- 必須Pythonパッケージが読み込まれる
- GUIのバージョンが表示される

## 8. 画像生成試験

1. 「画像生成」で利用するLoRAを必要に応じて指定する。
2. LoRA係数、prompt、seed、幅、高さ、保存先を確認する。
3. 画像を1枚生成する。
4. 指定した保存先へPNGと生成条件JSONが作成されることを確認する。
5. LoRAを指定しないSDXL Baseのみの生成も確認する。

既存の研究用LoRAがないPCでは、SDXL Baseのみの生成成功を必須とし、LoRA生成は利用可能な試験データを準備してから行う。

## 9. 最小学習試験

本番の学習フォルダーを使わず、専用の試験用画像・出力フォルダーを用意する。

1. 「学習」で試験用画像フォルダーを選択する。
2. 画像検査で破損画像が0件であることを確認する。
3. 共通プロンプトまたは画像別キャプションを確認する。
4. `1画像あたりの総学習回数`を1に設定する。
5. 表示された目標ステップを確認して学習を開始する。
6. LoRAファイル、学習manifest、ログが試験用出力先へ作成されることを確認する。

既存のLoRA出力先や`first_test`を新規学習で上書きしない。

## 10. Git状態の確認

GUIを終了し、リポジトリ直下で次を実行する。

```powershell
git -c core.quotePath=false status --short
```

モデル、LoRA、生成画像、`.gui_packages`、`.training_packages`、キャッシュが表示されないことを確認する。意図しない変更がなければ正常である。

## 11. 合格条件

- GUIソースがGitから取得できる。
- PC運用配置へ配備または更新できる。
- GUI固有依存関係をロックファイルから再構築できる。
- 自動テストがすべて成功する。
- CUDAとSDXL BaseがGUIで認識される。
- SDXL Baseによる画像生成が成功する。
- 利用可能なLoRAがある場合、LoRAを適用した生成が成功する。
- 最小学習試験が完了し、LoRAと記録がユーザー作業領域へ保存される。
- Git作業ツリーへ大容量データや実験生成物が混入しない。
