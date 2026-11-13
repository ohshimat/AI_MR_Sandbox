# Haptic DLL 同梱結果

対象: `G:\AI_MR_Sandbox\unity\MREAL_OpenXR_Sample6_Haptic_Sandbox - 6000.3.11f1`

## 完了した操作

- Microsoft Visual C++ 2013 Redistributable (x64) 12.0.40664 を実行。終了コード0、再起動なし。
- インストーラーとコピー元DLLのMicrosoft署名を確認。
- 以下のファイルを `Assets/3DSystems/HapticsDirect/HapticPlugin/` に追加。
  - `msvcr120.dll`、対応する `.meta`
  - `msvcp120.dll`、対応する `.meta`
  - `VC2013-RUNTIME-MANIFEST.json`、Unity生成の `.meta`
  - `NATIVE-RUNTIME-PORTABILITY.md`、Unity生成の `.meta`
- DLLのコピー元と同梱先のSHA-256一致を確認。
- Unityが両方をネイティブプラグインとして認識し、Editor OS=Windows、CPU=x86_64、Windows x64有効、Android無効であることを確認。
- 既存のHapticsDirect.dll、hd.dll、スクリプト、Scene、XR設定は変更せず。Playは実行せず、Unityは停止状態。

## 同梱DLL

| ファイル | バージョン | SHA-256 |
|---|---|---|
| msvcr120.dll | 12.0.40664.0 | 753AC30C30AAE62415CC225E3D057B8B6254AFE280696E0A43F1A7C3132632A6 |
| msvcp120.dll | 12.0.40664.0 | 3B92E964404E3F94531E7D7C4C7419561D9ECA6ACCD98DC3979C9E3596DB444C |

## 未完了の移植性

2つのVC++ 2013 DLLの同梱は完了しましたが、プロジェクト全体のPC依存解消は未完了です。

- hd.dll が必要とする PhantomIoLib42.dll は未入手・未同梱。
- 既存HapticsDirect.dllとhd.dllはEditor／Windows x64読み込みが無効のまま。依存関係解決後に有効化と検証が必要。
- HapticsDirect.dllが必要とするVC++ 14ランタイム／Universal CRTは今回の同梱対象外。
- 実機利用時のドライバー、OpenXR追跡を使う場合の対応ランタイム・入力元は別要件。
- このPCにはVC++ 2013がインストール済み。Unity認識の成功だけでは、クリーンPCでの同梱DLLからの読み込み成功を証明できません。EditorとWindowsビルドの両方で追加検証が必要です。
- 同梱DLLの更新はプロジェクト側で管理します。

## Git

Unity 6用プロジェクトは親リポジトリ内でフォルダー全体が未追跡でした。今回、Git add／commit／設定変更は行っていません。既存の追跡済みプロジェクトとの差分や、今回追加したDLLの保存管理は別途必要です。

## 入手元・参照

- インストーラー: https://aka.ms/highdpimfc2013x64jpn
- Microsoft公式パッケージ説明: https://support.microsoft.com/en-us/servicing/visual-studio/update/2020/11/update-for-visual-c-2013-redistributable-package
- ローカル配置: https://learn.microsoft.com/en-us/cpp/windows/deployment-in-visual-cpp
- 再配布対象・条件: https://learn.microsoft.com/en-us/visualstudio/releases/2013/2013-redistribution-vs

再配布はMicrosoftのライセンス条件に従います。
