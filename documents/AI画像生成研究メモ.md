# AI画像生成研究

## 研究記録

- 記録日：2026年10月7日
- 位置づけ：AI-MR研究から派生するスピンオフ研究
- 主題：AI画像学習とMR環境生成を接続するSandboxアーキテクチャ

## 1 研究の位置づけ

AI画像生成を単なる画像ファイルの出力として扱わず、人間が知覚し、解釈し、行動するMR環境の構成要素を生成する機構として扱う。

本研究は、自然言語の意味解釈と行動要求を扱う第二論文とは分離し、AI画像生成、追加学習、生成物の検証、MR環境への配置、人間による評価を対象とするスピンオフ論文として進める。

## 2 中心命題

AI画像生成は、画像コンテンツを生成するだけではなく、Sandboxを介してMR環境へ配置される Environment Artifact を生成する。

```text
Image Generation
  ↓
Environment Generation
  ↓
Human Perception and Action
  ↓
Evaluation and Learning
```

## 3 基盤構造

```text
Human or AI Instruction
  ↓
Sandbox Engine
  ↓
Image Generation Request
  ↓
Image Generation Interface
  ↓
Diffusers
  ↓
SDXL Base + Research LoRA
  ↓
Generated Image Artifact
  ↓
Verification and Permission
  ↓
MR Environment
  ↓
Human Evaluation and Experience
```

### 構成要素の責務

| 構成要素 | 責務 |
|---|---|
| Sandbox Engine | 画像生成要求、実行許可、MRへの配置、経験記録を管理する |
| Image Generation Interface | Sandboxと画像生成サブシステムの接続仕様を提供する |
| Diffusers | モデルの読込み、追加学習、画像生成を実行する |
| SDXL Base | 一般的な画像生成能力を提供する基盤モデル |
| DreamBooth | 特定対象や視覚的特徴を学習させる方法 |
| LoRA | 研究固有の学習結果を追加重みとして保存する |
| Environment Artifact | MR環境へ配置される生成画像と付随情報 |

## 4 画像学習の基本構造

SDXL Baseは原則として固定し、研究用画像とキャプションを用いてDreamBooth方式で学習する。学習対象はLoRAの追加重みに限定し、基盤モデルと研究固有の学習内容を分離する。

```text
Research Images and Captions
  ↓
DreamBooth Training Method
  ↓
Frozen SDXL Base
  ↓
LoRA Parameter Update
  ↓
Evaluation and Versioning
  ↓
Research LoRA
```

生成時にはSDXL Baseと研究用LoRAを組み合わせる。

```text
SDXL Base
  +
Research LoRA
  +
Prompt and Generation Conditions
  ↓
Generated Environment Artifact
```

## 5 AI画像学習生成サブシステムの9モジュール案

| No. | モジュール | 主な責務 |
|---:|---|---|
| 1 | Image Request Interface | Sandboxから画像生成要求と学習要求を受け取る |
| 2 | Dataset Manager | 学習画像、利用条件、訓練検証分割を管理する |
| 3 | Annotation Manager | キャプション、対象名、クラス情報を管理する |
| 4 | Training Manager | DreamBooth方式による学習処理を制御する |
| 5 | Base Model Manager | SDXL BaseのモデルID、版、ハッシュを管理する |
| 6 | Adapter Manager | LoRAの学習、保存、選択、適用を管理する |
| 7 | Generation Runtime | Diffusersを使用して画像を生成する |
| 8 | Evaluation and Verification | 学習結果と生成画像を評価し検証する |
| 9 | Artifact and Provenance Manager | 画像、LoRA、生成条件、学習履歴を記録する |

このサブシステムはSandbox Engineの既存モジュールを置き換えず、画像学習と画像生成を担当する専門サブシステムとして接続する。

## 6 現在のローカル実装環境

| 項目 | 現在の構成 |
|---|---|
| OS | Windows |
| GPU | NVIDIA RTX PRO 2000 Blackwell Generation Laptop GPU |
| VRAM | 8GB |
| Python | 3.11.9 |
| PyTorch | 2.13.0+cu132 |
| CUDA Runtime | 13.2 |
| Diffusers | 0.41.0 |
| Transformers | 5.19.0 |
| Accelerate | 1.15.0 |
| 基盤モデル | stabilityai/stable-diffusion-xl-base-1.0 |
| モデル容量 | 約7.11GB |

## 7 現在までの確認状況

```text
GPU Recognition                         DONE
PyTorch GPU Calculation                 DONE
Diffusers Installation                  DONE
SDXL Base Download                      DONE
SDXL Pipeline Loading                   DONE
Local Image Generation                  DONE
Local Model Cache                       DONE

Strict Offline Generation Verification NEXT
Dataset Design                          NEXT
DreamBooth LoRA Training                NEXT
LoRA Evaluation                         NEXT
Sandbox Interface Integration           NEXT
MR Environment Feedback                 NEXT
```

Diffusers 0.41.0では、モデル読込みに `dtype=torch.float16` を使用し、VAE slicingには `pipe.vae.enable_slicing()` を使用する。

## 8 研究における環境生成の段階

```text
Level 1  2D生成画像のMR表示
Level 2  テクスチャや背景の生成
Level 3  パノラマや空間的視覚環境の生成
Level 4  3Dオブジェクトやシーンの生成
Level 5  行動可能なMR環境の動的生成
```

現在のSDXL実装はLevel 1の技術基盤に位置づける。以後、Sandboxによる許可、配置、検証、経験記録を加え、環境生成機構へ発展させる。

## 9 研究課題

1. AIが生成した画像をSandboxを介してMR環境へ安全に配置できるか。
2. SDXL BaseとLoRAを分離し、研究固有の環境表現を再現可能に管理できるか。
3. モデル、学習データ、プロンプト、seed、生成条件を環境履歴として記録できるか。
4. 生成された視覚環境が人間の知覚、判断、行動へ与える影響を評価できるか。
5. Human Evaluationを次の画像学習へ戻す循環を構築できるか。

## 10 次の実装段階

1. ネットワークを遮断した状態でSDXLの完全ローカル生成を確認する。
2. 学習対象とする画像概念、対象物、視覚スタイルを定義する。
3. 学習画像、キャプション、利用条件、評価画像を準備する。
4. 8GB VRAM向け設定で小規模なDreamBooth LoRA学習を試す。
5. 学習前後を同一promptとseedで比較する。
6. LoRA、学習条件、評価結果をArtifact and Provenance Manager相当の形式で記録する。
7. `generate_image(request)` をSandbox側の画像生成インタフェースとして実装する。
8. 生成画像をMR空間へ提示し、人間による評価を記録する。

## 11 仮題

### 日本語

AI画像学習とMR環境生成を接続するSandboxアーキテクチャ

### 英語

Sandbox Mediated AI Image Learning and Environment Generation for Mixed Reality
