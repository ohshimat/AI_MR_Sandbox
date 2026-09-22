# Unity3Dプラグイン
Unity3Dプラグインは、Unity Package Managerで配布されています。

 



Unity3d Package ManagerからVoluME Clientをインポートした状態

 

 

Get Start
(1) Unity Package Managerからインポート

Unity Package Manager → add package from gitURLに下記URLを入力してインポートしてください。

 

========

git+https://CreVirtools@dev.azure.com/CreVirtools/volume-public/_git/volume-client-unity?path=Assets/Crescent/VoluME

========

 

(2) Prefabを設置する

ProjectフォルダのPackages > VoluME Client > StreamingSDK > Runtime > Prefabsから「VM Object With Audio」をシーンにドラッグしてください。

 

(3) パラメータを設定する

Inspectorにて、VM Object With Audioのパラメータを設定してください。

ストリーミングサーバーからデータを受け取る場合は下記の設定を変更してください。

Streaming Mode : Online
Online Streaming Parameters
Server URL: ストリーミングサーバーのIP or ドメイン
fps : 受信するフレームレートを設定してください。 
Online Streaming Parameters Audio : ストリーミングサーバーのIP or ドメイン
Server URL: ストリーミングサーバーのIP or ドメイン
fps : 受信するフレームレートを設定してください。 
※ その他の設定は変更不要です。

 

サポート対象
Unityプラグイン v1.3.0は、下記のビルドをサポートします。

Windows
Android
iOS