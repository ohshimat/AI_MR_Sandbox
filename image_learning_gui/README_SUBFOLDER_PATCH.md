# AI_MR_Sandbox 学習画像サブフォルダ対応パッチ

## 適用範囲

画像学習GUIの「学習画像フォルダ」直下に、`サブフォルダ内の画像も学習対象に含める` チェックボックスを追加。

- OFF（既定）：従来どおり直下の画像だけを使用
- ON：指定フォルダ以下の画像を再帰検索し、検査・ステップ計算・キャプション閲覧/保存・学習に反映
- 学習前の一時コピーはON時にファイル名へ連番を付けてフラット化するため、異なる階層の同名画像も衝突しない
- 画像別キャプション `.txt` は各画像に隣接。欠落時は共通プロンプトを使用
- manifestに `include_subfolders` と元画像の相対パスを記録
- 元の画像・キャプション・モデル・既存LoRAには一切変更しない（ただしGUIの「キャプション保存」は従来どおり選択 `.txt` を作成/更新する）

## Windowsでの適用方法

現在起動中の画像学習GUIを終了し、Gitの状態を確認する。コミットしていない変更があればバックアップし、内容を比較してから適用すること。

PowerShell 1行コマンド例（ZIPをダウンロードした場所は適宜読み替え）：

```powershell
 git -C E:\AI_MR_Sandbox status --short
```

ZIPの `image_learning_gui/` を既存の `E:\AI_MR_Sandbox\image_learning_gui\` に上書き配置する。Gitで差分を確認する。

```powershell
 git -C E:\AI_MR_Sandbox diff --check
```

```powershell
 git -C E:\AI_MR_Sandbox diff --stat
```

本パッチはGUI本体とテストのみを含む。Python仮想環境・PC側runtime・モデル/学習データの再インストールは不要。

## テスト

GUIの通常の起動入口（`start_image_learning_gui.cmd`）で起動し、学習画面で以下を確認する。

1. OFF時、下位フォルダの画像が枚数に含まれない
2. ON時、下位フォルダの画像が枚数に含まれる
3. 異なるサブフォルダに同じ `one.png` があっても、学習用一時コピーに重複/上書きがない
4. 画像別キャプションを使用する場合、各階層の `.txt` が正しい画像に対応する
5. **本番データは使わず、試験専用フォルダ・新しい出力先で1ステップ学習を確認する**

追加の小規模テスト（PC側のPython環境を使用）：

```powershell
 Push-Location "E:\AI_MR_Sandbox\image_learning_gui"; & "C:\AI_venvs\AI_MR_Sandbox\Scripts\python.exe" -m unittest tests.test_recursive_training; Pop-Location
```

このコマンドはカレントディレクトリに依存せず動作する。既存の回帰テストは `image_learning_gui` フォルダをカレントにして実施する構成のため、現地のテスト起動手順に従う。

## 検証状況

- 2026-11-21: 添付されたソースに対してパッチ作成
- Linuxサンドボックスで、関連する24件のunit tests PASS（dataset/captions/recursive/app-events/preview/process-manager/records）
- ZIPに含まれていない `config/defaults.yaml` やWindows固有処理を要するテストは、ここでは完全な回帰テストを実施できていない
- Gradio画面での手動操作・SDXL実学習は未検証。Windowsの実環境でPreview → Apply → Verifyの順に評価する
- コミットおよびPushは未実施
