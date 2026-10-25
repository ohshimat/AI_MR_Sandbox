# AI画像生成・学習GUI 共有環境セットアップ手順

## 1. 目的

この文書は、`AI_MR_Sandbox`に収録された画像生成・学習GUIをポータブル側から起動し、別のPCでSDXL Baseによる生成とDreamBooth LoRA学習の基本動作を確認する手順を示す。

GUIのソースはGitで共有する。大容量またはPC固有の実体はGitへ入れず、PCごとに構築する。

## 2. 保存方針

| 保存先 | 内容 | Git管理 |
|---|---|---|
| `image_learning_gui` | GUI、テスト、worker、固定版DreamBoothスクリプト | 対象 |
| `C:\AI_venvs\AI_MR_Sandbox` | PyTorch、Diffusers等の画像AI実行環境 | 対象外 |
| `C:\AI_MR_Sandbox\models` | SDXL Base | 対象外 |
| `%USERPROFILE%\AI_MR_Workspace` | 学習画像、LoRA、生成画像、実験記録 | 対象外 |
| `C:\AI_MR_Sandbox\runtime` | GUI・学習固有の導入済みパッケージ | 対象外・PCごとに再生成 |
| `C:\AI_MR_Sandbox\temp` | プレビュー、datasets、pipの一時データ | 対象外 |

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

## 4. ポータブル入口から初期設定

リポジトリ直下から次を実行する。

```powershell
& ".\setup_image_learning_gui.cmd"
```

この処理は、GUI本体をポータブル側に保ったまま、次を実行する。

1. 画像AI用Pythonを確認する。
2. Gradio等を`C:\AI_MR_Sandbox\runtime\image_gui_packages`へ準備する。
3. `datasets`等を`C:\AI_MR_Sandbox\runtime\image_training_packages`へ準備する。
4. 旧運用GUIに検証済みパッケージがある場合は、ダウンロードせず共通runtimeへ移行する。
5. GUIの自動テストを実行する。

`57 passed`と`Tests : OK`が表示されれば成功である。既存のPyTorchやDiffusersは上書きしない。

初回セットアップでロック済み依存パッケージがPC内にない場合だけ、インターネット接続が必要になる。セットアップとSDXL Baseの配置が完了した後は、ネットワークを切断して実験できる。

## 5. 保存層と操作入口

操作は常にポータブルリポジトリから始める。Cドライブ側はPython、依存パッケージ、モデル、一時データだけを保存する実行資源層であり、C側のGUIコピーを直接操作しない。

外部SSDのドライブレターが変わっても、リポジトリ直下の同じ起動ファイルを使用する。

GUI起動時には、Hugging Face Hub、Transformers、Datasetsをオフラインモードにし、Gradioの分析送信を無効化する。SDXLは`local_files_only=True`で読み込む。学習・生成データを外部サービスへ自動送信しない。

## 6. GUIの起動

```powershell
& ".\start_image_learning_gui.cmd"
```

ブラウザで`http://127.0.0.1:7860`が開く。外部公開は行わない。

「環境・履歴」で次を確認する。

- CUDAが利用可能
- SDXL Baseが見つかる
- DreamBooth学習スクリプトが見つかる
- 必須Pythonパッケージが読み込まれる
- GUIのバージョンが表示される
- オフライン実験モードが有効
- Gradio分析送信が無効

## 7. 画像生成試験

1. 「画像生成」で利用するLoRAを必要に応じて指定する。
2. LoRA係数、prompt、seed、幅、高さ、保存先を確認する。
3. 画像を1枚生成する。
4. 指定した保存先へPNGと生成条件JSONが作成されることを確認する。
5. LoRAを指定しないSDXL Baseのみの生成も確認する。

既存の研究用LoRAがないPCでは、SDXL Baseのみの生成成功を必須とし、LoRA生成は利用可能な試験データを準備してから行う。

## 8. 最小学習試験

本番の学習フォルダーを使わず、専用の試験用画像・出力フォルダーを用意する。

1. 「学習」で試験用画像フォルダーを選択する。
2. 画像検査で破損画像が0件であることを確認する。
3. 共通プロンプトまたは画像別キャプションを確認する。
4. `1画像あたりの総学習回数`を1に設定する。
5. 表示された目標ステップを確認して学習を開始する。
6. LoRAファイル、学習manifest、ログが試験用出力先へ作成されることを確認する。

既存のLoRA出力先や`first_test`を新規学習で上書きしない。

## 9. Git状態の確認

GUIを終了し、リポジトリ直下で次を実行する。

```powershell
git -c core.quotePath=false status --short
```

モデル、LoRA、生成画像、`.gui_packages`、`.training_packages`、キャッシュが表示されないことを確認する。意図しない変更がなければ正常である。

## 10. 合格条件

- GUIソースがGitから取得できる。
- ポータブルリポジトリからセットアップと起動ができる。
- GUI固有依存関係をロックファイルから再構築できる。
- 自動テストがすべて成功する。
- CUDAとSDXL BaseがGUIで認識される。
- SDXL Baseによる画像生成が成功する。
- 利用可能なLoRAがある場合、LoRAを適用した生成が成功する。
- 最小学習試験が完了し、LoRAと記録がユーザー作業領域へ保存される。
- Git作業ツリーへ大容量データや実験生成物が混入しない。
