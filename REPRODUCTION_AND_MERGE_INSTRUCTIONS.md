# AI-MR Sandbox 再現確認・統合指示書

## 目的

`portability-cleanup`ブランチを別環境で再現確認し、問題がなければ`main`へ統合してください。

## 実施手順

1. `portability-cleanup`ブランチの最新版を取得してください。
2. `PORTABLE_ENVIRONMENT_SETUP.md`に従い、初期環境を構築してください。
3. `IMAGE_LEARNING_GUI_SETUP.md`に従い、画像生成・学習GUIを配備して確認してください。
4. `CURRENT_SYSTEM_TEST.md`に従い、現在の開発到達点を一通りテストしてください。
5. 次の主要項目を確認してください。
   - Python環境検証がエラー0件で完了する。
   - Ollamaと`qwen3:8b`が正常に動作する。
   - Python GUI、Unity、`AIRManager_v2`が連携する。
   - 文字または音声による前・右・左方向の移動命令が、Unity内の`AI_1`へ反映される。
   - 画像生成・学習GUIが起動し、SDXL BaseとLoRAを認識する。
   - GUIからローカル画像生成と最小学習試験を実行できる。
   - 実行後もGit管理対象に意図しない変更が残らない。
6. 問題がある場合は、統合せず、実行手順、エラー表示、使用PC環境を共有してください。
7. 問題がない場合は、再現確認結果を共有したうえで、`portability-cleanup`を`main`へ統合してください。

## 参照文書

- `PORTABLE_ENVIRONMENT_SETUP.md`：初回のポータブル環境構築
- `IMAGE_LEARNING_GUI_SETUP.md`：画像生成・学習GUIの配備と確認
- `CURRENT_SYSTEM_TEST.md`：現在機能の統合テスト

## 対象ブランチ

```text
portability-cleanup
```
