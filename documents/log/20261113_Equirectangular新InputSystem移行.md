# Equirectangular 新Input Systemへの移行

日付: 2026-11-13（日本時間）

対象: `G:\AI_MR_Sandbox\unity\Equirectangular_ViconStereo - 6000.3.11f1`

Unity: 6000.3.11f1 / Pipeline: 1.0.0

## 結果

旧Input Managerから新Input Systemのみの構成へ移行した。Unityを再起動し、Main／BoidsEquirectの両SceneでPlay開始・停止と新入力経路を確認。確認後のConsoleはエラー0件、警告0件で、旧Input Managerの非推奨警告は再発していない。

## 変更

- Unity Package Managerが提示したInput System 1.20.1を導入。manifest.json／packages-lock.jsonに記録。
- ProjectSettings/ProjectSettings.assetのactiveInputHandlerを0（旧方式）から1（新方式のみ）へ変更。Bothではない。PlayerSettingsの差分はこの1項目のみ。
- Assets/Work/ESCQUIT.cs: Input.GetKeyDown(KeyCode.Escape)をKeyboard.current.escapeKey.wasPressedThisFrameへ置換。Keyboard.currentがnullの環境では何もしないガードを追加。クラス名EscapeQuit、スクリプトGUID、既存Prefabからの参照は維持。
- Assets/Scenes/Main.unity、Assets/Scenes/BoidsEquirect.unityのStandaloneInputModuleを、それぞれInputSystemUIInputModuleへ置換。
- Assets/Work/UIInputActions.inputactionsと.metaを追加。Input System標準のUI Action Mapを複製し、ポイント・クリック・スクロール・移動・決定・取消等を各SceneのUIモジュールに割り当てて保存。
- Scene保存時、Unity 6によるシリアライズ形式の更新（RenderSettings／LightmapSettings等）も発生。Sceneの意図的な配置変更は行っていない。
- ProjectSettings/InputManager.assetは削除していないが、新方式のみの設定となり旧入力処理は使用しない。

## 検証

1. 移行対象の元ファイルを退避し、Sceneに既存の未保存変更がないことを確認。
2. 新パッケージ導入、コード・Scene・入力設定の移行を適用。
3. Unityを保存済み状態で再起動。起動後コンパイル失敗なし、新方式でKeyboardとMouseの認識を確認。
4. Assets配下のC#にUnityEngine.Input／旧Input API呼び出しが残っていないことを検索で確認。
5. Assets配下のScene／Prefabに旧StandaloneInputModuleのスクリプトGUIDが残っていないことを確認。
6. Main SceneをPlayし、一時的な仮想キーボードからEscapeの押下・解放を入力。新Keyboard APIの押下検出とUI Cancel Actionの検出が両方成功。EscapeQuit.Updateを呼び、例外なしでApplication.Quitの経路を通ることを確認。
7. BoidsEquirectでも同じテストを実施し成功。両Sceneとも旧UI入力モジュールは0個。各UIモジュールは保存したUIInputActionsを使用。
8. 仮想キーボード・一時テストオブジェクトを除去。両SceneでPlayを停止。
9. Main Sceneへ戻し、Play停止・未保存変更なしを確認。最終Consoleはエラー0件、警告0件。

確認セッション: `1bbd6d7ef5ef4747ba41008e0cd65b08`。最終cursor: 18。確認時間は21:34〜21:36頃（日本時間）。

## 検証範囲と残る確認

- Application.QuitはUnity Editorを終了しないため、実行ファイルがEscapeで終了すること自体はWindows Playerビルドで確認する必要がある。
- 仮想EscapeとUI Cancel Actionの入力経路は確認したが、全UI操作の目視確認・全デバイス・Vicon実機や撮影機能の検証は行っていない。
- Git add／commit／pushは行っていない。対象Unity 6プロジェクトは移行開始時点で親Gitリポジトリから未追跡だった。

本記録は前の`20261113_Equirectangular入力方式確認.md`に続く移行結果である。
