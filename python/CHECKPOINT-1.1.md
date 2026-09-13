はい．`CHECKPOINT-1.1.md` は **Checkpoint 1を前提とした差分マニュアル** にすると読みやすいです．特に今回は，Unity UI表示と日本語フォント設定が重要な再現ポイントです．そのまま貼れる形にします．

````markdown
# CHECKPOINT-1.1
## Speech Recognition → TCP/IP → Unity UI

### Status
**Completed**

### Date
2026-09-13

---

## 1. 目的

CHECKPOINT-1では，ユーザの発話をPythonで音声認識し，
認識結果をJSONメッセージとしてTCP/IP経由でUnityへ送信し，
JSON内の `text` フィールドをUnity Consoleへ表示した．

CHECKPOINT-1.1では，この認識結果をUnity Consoleだけでなく，
**Unity実行画面内のUIへリアルタイム表示する**．

---

## 2. 達成条件

ユーザが例えば，

> 私の右へ移動してください

と発話した場合，Pythonで音声認識された文字列がTCP/IP経由でUnityへ送信され，

Unity画面内のUIに，

> 私の右へ移動してください

と日本語で正しく表示されること．

また，Pythonを操作するためにUnityが非アクティブになっている場合でも，
Unity側の表示がリアルタイムに更新されること．

---

## 3. 前提

CHECKPOINT-1が完成していること．

情報経路は以下の状態から開始する．

```text
Human Speech
    ↓
Microphone
    ↓
Python
    ↓
faster-whisper
    ↓
Speech Recognition
    ↓
JSON
    ↓
TCP/IP
    ↓
Unity
    ↓
JSON Parse
    ↓
text
    ↓
Unity Console
````

CHECKPOINT-1.1では末尾にUnity UIを追加する．

```text
Human Speech
    ↓
Microphone
    ↓
Python / faster-whisper
    ↓
JSON
    ↓
TCP/IP
    ↓
Unity
    ↓
JsonUtility
    ↓
text
    ↓
TextMeshPro UI
```

---

## 4. Unity UIの作成

Hierarchyで，

```text
UI → Text - TextMeshPro
```

を選択する．

初回にTextMeshProのImportを要求された場合は，

```text
Import TMP Essentials
```

を実行する．

Canvasが自動生成され，その下にTextMeshProオブジェクトが生成される．

TextMeshProオブジェクトの名前を，

```text
SpeechText
```

とする．

Hierarchyは概ね以下となる．

```text
Canvas
└─ SpeechText

SpeechReceiver
```

---

## 5. TcpSpeechReceiver.csへのUI追加

冒頭にTextMeshProを使用するため，

```csharp
using TMPro;
```

を追加する．

`TcpSpeechReceiver` クラス内に，

```csharp
public TMP_Text speechText;
```

を追加する．

JSONから取り出した `speech.text` をUIへ設定する．

```csharp
void Update()
{
    while (messages.TryDequeue(out string message))
    {
        SpeechMessage speech =
            JsonUtility.FromJson<SpeechMessage>(message);

        Debug.Log(speech.text);

        if (speechText != null)
        {
            speechText.text = speech.text;
        }
    }
}
```

---

## 6. SpeechTextの割り当て

UnityのHierarchyで，

```text
SpeechReceiver
```

を選択する．

Inspectorの `Tcp Speech Receiver` コンポーネントに，

```text
Speech Text
```

というフィールドが追加される．

Hierarchy内の，

```text
SpeechText
```

をこのフィールドへドラッグ＆ドロップする．

これにより，

```text
speech.text
    ↓
SpeechText.text
```

が接続される．

---

## 7. Unityをバックグラウンドでも実行する

初期状態では，VS Codeを操作するためUnityが非アクティブになると，
UI表示の更新が停止し，Unityを再びアクティブにした時点で更新される現象が発生した．

この問題を解決するため，`Start()` に，

```csharp
Application.runInBackground = true;
```

を追加した．

例：

```csharp
void Start()
{
    Application.runInBackground = true;

    listenerThread = new Thread(Listen);
    listenerThread.IsBackground = true;
    listenerThread.Start();

    Debug.Log("TCP server started.");
}
```

これにより，VS Code側でPythonを操作している間もUnityの処理が継続し，
受信した音声認識結果がリアルタイムにUIへ反映される．

---

## 8. 日本語フォントへの対応

### 8.1 問題

TextMeshProの標準Font Assetでは日本語文字を十分に保持していないため，
日本語を表示すると一部または全部の文字が，

```text
□
```

として表示された．

TCP/IPやJSONの文字コードの問題ではなく，
TextMeshProのFont Assetに必要な日本語グリフが存在しないことが原因であった．

### 8.2 日本語フォントの導入

今回，日本語対応フォントとして，

```text
NotoSansJapaneseVariable
```

を使用した．

フォントファイルをUnityプロジェクトの，

```text
Assets/Fonts
```

へ配置した．

### 8.3 TextMeshPro Font Assetの作成

Unity上部メニューから，

```text
Window
→ TextMeshPro
→ Font Asset Creator
```

を開く．

`Source Font File` に，

```text
NotoSansJapaneseVariable
```

を指定する．

Font Atlasを生成し，Font Assetとして `Assets/Fonts` に保存する．

---

## 9. Dynamic Font Assetの設定

生成したTextMeshPro Font Assetを選択し，
Inspectorで，

```text
Atlas Population Mode = Dynamic
```

に設定する．

日本語では使用文字数が多いため，

```text
Multi Atlas Textures = ON
```

にも設定する．

この設定により，実行中に必要となった日本語文字を元フォントから追加し，
Atlasが不足した場合には追加Atlasを生成できる．

今回，一部の日本語文字が `□` になる問題は，

```text
Atlas Population Mode = Dynamic
Multi Atlas Textures = ON
```

の設定によって解決した．

---

## 10. SpeechTextへの日本語Font Asset設定

Hierarchyで，

```text
SpeechText
```

を選択する．

Inspectorの，

```text
Font Asset
```

へ，作成したNotoSansJapaneseVariableのTextMeshPro Font Assetを設定する．

これにより日本語の音声認識結果を正常に表示できるようになった．

---

## 11. 実行手順

1. UnityをPlayする．
2. Consoleに `TCP server started.` が表示されることを確認する．
3. VS Codeから `speech_to_unity.py` を実行する．
4. 「3秒間話してください」と表示されたら発話する．
5. Pythonで音声認識が行われる．
6. JSONメッセージがTCP/IP経由でUnityへ送信される．
7. UnityがJSONから `text` を抽出する．
8. 認識文字列が `SpeechText` に日本語でリアルタイム表示される．

---

## 12. 確認結果

以下を確認した．

```text
音声入力                     OK
faster-whisper日本語認識     OK
JSON生成                     OK
TCP/IP通信                   OK
Unity JSON解析               OK
textフィールド抽出           OK
TextMeshPro UI表示           OK
Unityバックグラウンド更新    OK
日本語表示                   OK
```

---

## 13. CHECKPOINT-1.1 判定

**達成**

CHECKPOINT-1.1では，

> ユーザの発話をPythonで音声認識し，認識結果をJSONとして
> TCP/IP経由でUnityへ送信し，Unity側で `text` を抽出して，
> 日本語を含む認識結果をリアルタイムにUI上へ表示する

一連の処理が実現した．

---

## 14. CHECKPOINT-1からの進展

CHECKPOINT-1：

```text
Speech
→ Recognition
→ JSON
→ TCP/IP
→ Unity
→ Console
```

CHECKPOINT-1.1：

```text
Speech
→ Recognition
→ JSON
→ TCP/IP
→ Unity
→ JSON Parse
→ TextMeshPro UI
```

これにより，音声認識結果がデバッグ用Console出力から，
Human-AI Interactionで利用可能なUnity内の表示情報へ移行した．

---

## 15. 補足：日本語フォント設定

TextMeshProで日本語を利用する場合には，以下を再現時の注意事項とする．

```text
日本語対応フォントを用意
        ↓
Assets/Fontsへ配置
        ↓
TextMeshPro Font Asset Creator
        ↓
Font Asset生成
        ↓
Atlas Population Mode = Dynamic
        ↓
Multi Atlas Textures = ON
        ↓
SpeechTextのFont Assetへ設定
```

日本語表示ではFont Asset設定が重要であり，
標準Font Assetのままでは文字が `□` と表示される場合がある．

GitHubへフォントデータ自体を公開する場合には，
使用フォントのライセンスおよび再配布条件を確認すること．

````

これを `AI_MR_Sandbox` 直下の **`CHECKPOINT-1.1.md`** として保存するのがよいです．

保存後はGitで，

```text
Checkpoint 1.1: Real-time Japanese speech display on Unity UI
````

あたりをコミットメッセージにすると，Checkpoint 1との進展も履歴から分かりやすくなります．
