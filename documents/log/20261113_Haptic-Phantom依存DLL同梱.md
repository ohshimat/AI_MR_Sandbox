# Hapticデバイス依存DLLの同梱・検証記録

日付: 2026-11-13（日本時間）

対象: `G:\AI_MR_Sandbox\unity\MREAL_OpenXR_Sample6_Haptic_Sandbox - 6000.3.11f1`

## 結果

未同梱だった64bit版 `PhantomIoLib42.dll` を追加し、実機なしでも既存のHaptic機能を有効にしたままUnityのPlay開始・停止ができることを確認した。今回の検証中、Haptic由来の例外は0件だった。Touchデバイスドライバーはインストールしていない。

## 入手元と検証

- 配布元: `https://s3.amazonaws.com/dl.3dsystems.com/binaries/Sensable/driver/Touch_Device_Driver_2023.10.11.exe`
- 配布リンク確認ページ: `https://www.ddd.co.jp/support/haptics-driver/`
- パッケージサイズ: 159,880,576 bytes
- パッケージ署名: 有効、3D SYSTEMS, INC.
- パッケージSHA-256: `994075D632948D371562F0658F0E24F86EEE48340DAD4C5B15C603708A11048B`
- DLLバージョン: `2023.10.11.1213`
- DLLアーキテクチャ: x86_64（PE Machine 0x8664）
- DLL SHA-256: `B09964DB545DC9974FB461A694918D3CD8EAA9F96E8F3E7B834C56D5D739121A`
- DLL単体の署名: なし。上記の署名済み公式パッケージから改変せず抽出した。
- 既存hd.dllが要求するPhantom関数76個と照合し、欠ける関数がないことを確認。これは静的な関数名照合であり、実機の全機能の互換性保証ではない。
- 作業フォルダーに展開した7-Zip公式ツールでパッケージ内容を抽出。7-ZipおよびTouchドライバーのWindowsへのインストールは行っていない。

## プロジェクトに反映した内容

配置先: `Assets/3DSystems/HapticsDirect/HapticPlugin/`

追加:

- `PhantomIoLib42.dll` と `.meta`
- `PHANTOM-RUNTIME-MANIFEST.json` とUnity生成の `.meta`

更新:

- `HapticsDirect.dll.meta`、`hd.dll.meta`: Windows Editor x86_64／Windows Player x64を有効化。他プラットフォームを無効化し、起動時プリロードを無効化。
- `NATIVE-RUNTIME-PORTABILITY.md`: 検証結果・残る依存・同梱の管理方法を更新。
- `VC2013-RUNTIME-MANIFEST.json`: 解決済みだった未同梱・読み込み設定の項目を更新。

既存HapticsDirect.dll／hd.dll本体、Hapticスクリプト、Scene、XR設定は変更していない。前回同梱したmsvcr120.dll／msvcp120.dllも変更していない。元のHapticsDirect.dll.meta／hd.dll.metaの内容はPHANTOM-RUNTIME-MANIFEST.json内のoriginalImporterMetadataに保持。

## 動作確認

1. Unityとは別のプロセスで、作業フォルダーのmsvcr120、msvcp120、PhantomIoLib42、hd、HapticsDirectを順にロード。すべて成功し、その読み込み元を確認。
2. Unity 6000.3.11f1で同梱DLLと読み込み対象設定を反映。
3. TouchActorを有効にしたまま、実機未接続でPlayを実行。XR自動起動設定は元の有効状態を維持。
4. Play中のログに `Haptic Plugin Version : PluginVersion=1.0, PluginBuild=Oct 27 2021, OpenHapticsVersion=3.50.0` を確認。
5. Play中のHaptic例外0件、停止時もHaptic例外0件。`Disconnecting from Haptic` が正常に記録された。
6. Unityのロード済みモジュールを調査。HapticsDirect.dll、hd.dll、PhantomIoLib42.dll、MSVCP120.dll、MSVCR120.dllの5個すべてが対象プロジェクトのHapticPluginフォルダーから読み込まれていた。
7. 最終状態: Play停止、TouchActor有効、Scene未保存変更なし、XR自動起動有効。

Consoleセッション: `9cf5eaf76c484c619196666834a7d031`、今回の検証範囲: seq 43〜49。開始は18:06:50頃、停止は18:06:56頃（日本時間）。

## 別件として残るログ

- Hand Tracking Subsystem未稼働の警告1件。
- Play停止時の `TcpSpeechReceiver.cs:69` によるSocketException 1件。
- Playにより既存ExperienceLoggerは `G:\AI_MR_Sandbox\tmp\experience.jsonl` を通常どおり使用。このファイルは検証前からGit変更ありで、巻き戻していない。

## 残るPC依存と未検証事項

- VC++ 14のMSVCP140.dll／VCRUNTIME140.dllはこのUnityプロセスではWindows System32からロードされている。WindowsのUniversal CRT／OS DLLも必要。
- このPCにはVC++ 2013もインストール済みだが、今回のUnityプロセスは同梱したVC++ 2013 DLLをロードしていた。クリーンPC全体での動作保証を意味しない。
- Windows Playerビルドと、その配布物のクリーンPCでの動作は未検証。今回確認したのはEditorと単独プロセスでのロード。
- 実機の接続・力覚出力・校正は未検証。実機利用時のドライバー／サービス等の要否は別途確認が必要。
- 3D Systemsランタイムの外部への再配布権はこの技術検証で確認していない。外部配布前に適用される契約条件を確認する。

## Gitの保護

Unity 6用フォルダー全体は作業前から親リポジトリで未追跡。既存の追跡ファイル変更はimage_learning_gui配下5件とtmp/experience.jsonlに存在。これらには手を加えず、Git add／commit／reset／グローバル設定変更は行っていない。
