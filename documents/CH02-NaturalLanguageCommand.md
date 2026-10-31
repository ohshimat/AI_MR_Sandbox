はい．`CHECKPOINT2.md` は，Checkpoint 1.1との差分を明確にしつつ，**「自然言語を構造化された行動指示へ変換する段階」**として残すのがよいです．そのまま貼れる形にします．

````markdown
# CHECKPOINT-2
## Natural Language Command → Structured Action Request → Unity UI

### Status
**Completed**

### Date
2026-09-13

---

## 1. 目的

CHECKPOINT-1.1では，ユーザの発話をPythonで音声認識し，
認識結果をJSONとしてTCP/IP経由でUnityへ送信し，
Unity画面内のUIへリアルタイム表示した．

CHECKPOINT-2では，音声認識された自然言語をそのまま表示するのではなく，
**行動指示として解釈し，構造化された `action_request` メッセージへ変換する**．

---

## 2. 達成条件

ユーザが，

> 私の右へ移動してください

と発話した場合，Python側で自然言語を解釈し，

```json
{
  "type": "action_request",
  "speaker": "Human_1",
  "action": "move",
  "reference": "Human_1",
  "direction": "right"
}
````

という構造化されたJSONメッセージを生成する．

Unity側ではこのJSONを受信・解析し，

```text
Action: move
Reference: Human_1
Direction: right
```

とUIに表示すること．

---

## 3. 前提

CHECKPOINT-1.1が完成していること．

CHECKPOINT-1.1までの情報経路：

```text
Human Speech
    ↓
Microphone
    ↓
Python / faster-whisper
    ↓
Speech Recognition
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

CHECKPOINT-2では，Python側に自然言語解釈処理を追加する．

```text
Human Speech
    ↓
Speech Recognition
    ↓
Natural Language Interpretation
    ↓
Structured Action Request
    ↓
JSON
    ↓
TCP/IP
    ↓
Unity
    ↓
ActionRequest
    ↓
Unity UI
```

---

## 4. Python側の構造化処理

CHECKPOINT-2用として，

```text
speech_to_unity_cp2.py
```

を作成した．

自然言語の解釈は，最初の「小さな動くもの」として，
ルールベースで実装した．

```python
def interpret_command(text):
    action = "unknown"
    reference = "Human_1"
    direction = "unknown"

    if "移動" in text or "来て" in text:
        action = "move"

    if "右" in text:
        direction = "right"

    return {
        "type": "action_request",
        "speaker": "Human_1",
        "action": action,
        "reference": reference,
        "direction": direction
    }
```

---

## 5. 音声認識結果からAction Request生成

Whisperによる音声認識結果：

```text
私の右へ移動してください
```

を，

```python
message = interpret_command(text)
```

によって構造化する．

生成例：

```json
{
  "type": "action_request",
  "speaker": "Human_1",
  "action": "move",
  "reference": "Human_1",
  "direction": "right"
}
```

---

## 6. 構造化メッセージの意味

### type

```text
action_request
```

このメッセージが単なる音声認識結果ではなく，
行動要求であることを示す．

### speaker

```text
Human_1
```

発話主体を示す．

### action

```text
move
```

要求された行動の種類を示す．

### reference

```text
Human_1
```

空間指示を解釈する基準主体を示す．

今回の「私の右」は，Human_1を参照基準とする．

### direction

```text
right
```

要求された方向を示す．

---

## 7. Unity側のActionRequest定義

Unity側では，受信JSONに対応するデータ構造として，

```csharp
[System.Serializable]
public class ActionRequest
{
    public string type;
    public string speaker;
    public string action;
    public string reference;
    public string direction;
}
```

を定義した．

---

## 8. Unity側でのJSON解析

受信したJSONを，

```csharp
ActionRequest request =
    JsonUtility.FromJson<ActionRequest>(message);
```

によって `ActionRequest` として解析する．

---

## 9. Unity UIへの表示

解析した内容をTextMeshPro UIへ表示する．

```csharp
void Update()
{
    while (messages.TryDequeue(out string message))
    {
        ActionRequest request =
            JsonUtility.FromJson<ActionRequest>(message);

        Debug.Log(
            $"Action: {request.action}, " +
            $"Reference: {request.reference}, " +
            $"Direction: {request.direction}"
        );

        if (speechText != null)
        {
            speechText.text =
                "Action: " + request.action + "\n" +
                "Reference: " + request.reference + "\n" +
                "Direction: " + request.direction;
        }
    }
}
```

---

## 10. 実行手順

1. UnityをPlayする．
2. TCP Serverが起動していることを確認する．
3. VS Codeから `speech_to_unity_cp2.py` を実行する．
4. 「私の右へ移動してください」と発話する．
5. faster-whisperが音声を認識する．
6. Python側で自然言語を解釈する．
7. `action_request` JSONを生成する．
8. TCP/IP経由でUnityへ送信する．
9. UnityがJSONを `ActionRequest` として解析する．
10. Unity UIに構造化された行動指示を表示する．

---

## 11. 確認結果

以下を確認した．

```text
音声入力                         OK
faster-whisper日本語認識         OK
自然言語のルールベース解釈       OK
action_request生成               OK
JSON生成                         OK
TCP/IP通信                       OK
Unity JSON解析                   OK
ActionRequestへの変換            OK
Unity UI表示                     OK
```

---

## 12. CHECKPOINT-2 判定

**達成**

CHECKPOINT-2では，

> 自然言語による音声指示を，Python側で行動要求として解釈し，
> 構造化されたJSONメッセージへ変換し，
> TCP/IP経由でUnityへ送信してUI上で確認する

一連の処理を実現した．

---

## 13. CHECKPOINT-1.1からの進展

CHECKPOINT-1.1：

```text
Speech
→ Recognition
→ JSON
→ TCP/IP
→ Unity
→ UI
```

CHECKPOINT-2：

```text
Speech
→ Recognition
→ Interpretation
→ Structured Action Request
→ JSON
→ TCP/IP
→ Unity
→ UI
```

CHECKPOINT-1.1では認識文字列そのものをUnityへ送信していたが，
CHECKPOINT-2では自然言語を意味解釈し，
行動に必要な情報を構造化して送信するようになった．

---

## 14. サンドボックス・アーキテクチャ上の位置付け

CHECKPOINT-1.1までは，主として，

```text
Human
↓
<Perception>
```

の実装であった．

CHECKPOINT-2では，

```text
<Perception>
↓
<Context>
```

への最初の実装段階へ進んだ．

自然言語として認識された指示を，
行動に必要な意味情報へ変換する処理を，
`<Context>` の内部機能の一例として位置付ける．

---

## 15. ProtocolとImplementationの分離

CHECKPOINT-2では，解釈処理自体は単純なルールベースで実装した．

しかし，Unityへ渡すメッセージ形式は，

```json
{
  "type": "action_request",
  "speaker": "Human_1",
  "action": "move",
  "reference": "Human_1",
  "direction": "right"
}
```

として独立している．

したがって，将来，

```text
Rule-based Interpreter
```

を，

```text
LLM
AI Model
その他の自然言語理解方式
```

へ置き換えた場合でも，
同じ `action_request` Protocolを維持することが可能である．

これは，

```text
Architecture
Protocol
Implementation
```

を分離するサンドボックスの設計方針に対応する．

---

## 16. 現段階の制約

今回の自然言語解釈は，
Checkpoint達成を目的とした最小構成であり，
一般的な自然言語理解を実現するものではない．

現時点では，

```text
移動
来て
右
```

等の限定された語に基づくルールベース処理である．

また，

```text
reference = Human_1
direction = right
```

は意味的には構造化されているが，
まだ実際のUnity座標やユーザの身体姿勢とは対応付けられていない．

---

## 17. 次のCheckpoint

次段階では，

```text
reference = Human_1
direction = right
```

という意味表現を，

```text
Human_1の位置・姿勢
↓
身体基準座標系
↓
右方向ベクトル
↓
Unity座標系
```

へ対応付ける．

これはAIRによる共有参照の最小実装に相当する．

````

この `CHECKPOINT2.md` を保存したら，コミットメッセージは例えば，

```text
Checkpoint 2: Structured action request from speech command
````

でよいと思います．

今回のCheckpoint 2は研究上もかなり重要です．**単なる音声認識システムから，初めて「意味を構造化するHuman-AI相互作用エンジン」へ踏み込んだ地点**だからです．
