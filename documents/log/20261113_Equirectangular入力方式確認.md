# Equirectangularプロジェクトの入力方式確認

日付: 2026-11-13（日本時間）

対象: `G:\AI_MR_Sandbox\unity\Equirectangular_ViconStereo - 6000.3.11f1`

Unity: 6000.3.11f1 / Pipeline: 1.0.0

## 結果

- 接続先は上記プロジェクト。以前検証したMREAL Hapticプロジェクトとは別。
- ProjectSettings/ProjectSettings.assetのactiveInputHandlerは0（Input Manager / Old）。
- manifest.jsonおよびpackages-lock.jsonではcom.unity.inputsystemが見つからず、新Input Systemはパッケージ一覧上で未導入。
- Assets配下のC# 13ファイルを検索したところ、旧UnityEngine.Inputの使用はAssets/Work/ESCQUIT.cs:7のInput.GetKeyDown(KeyCode.Escape)で確認した。EscapeキーでApplication.Quit()を呼ぶ処理。
- 現在のConsoleはエラー0件、警告1件。その警告は旧Input Managerの将来的な廃止対象という案内。
- コンパイル失敗フラグなし。Play停止中。Assets/Scenes/Main.unityは開いており未保存変更なし。

## 判断

この警告だけでは現時点の動作不良を示さない。旧入力APIを使用するコードが残っているため、設定だけをInput System (New)へ変更しない。

新方式へ移行する場合はInput Systemパッケージの導入、Escape終了処理の書き換え、UI等の入力構成の確認、設定変更後のPlay／ビルド確認を一組として行う。今回のC#検索だけで外部DLLや全UI設定の互換性を保証するものではない。

今回は接続・設定・コード・Consoleを読み取りで確認した。プロジェクトの設定・コード・Sceneは変更せず、Play操作、Git登録、コミット、プッシュは行っていない。この確認記録のみdocuments/logに追加する。
