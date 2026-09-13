はい．`CHECKPOINT-3.md` は，**「構造化された意味表現を，身体基準の空間参照を介して実際のActionへ変換した段階」**として残しましょう．そのまま貼れる形にします．

````markdown
# CHECKPOINT-3
## Structured Action Request → Body-Centered Spatial Reference → AI Avatar Action

### Status
**Completed**

### Date
2026-09-13

---

## 1. 目的

CHECKPOINT-2では，ユーザの自然言語による音声指示をPython側で解釈し，
構造化された `action_request` としてUnityへ送信した．

CHECKPOINT-3では，この構造化された行動指示を，
Unity内の参照主体 `Human_1` の位置・姿勢に基づく身体基準座標へ対応付け，
AI Actorを表す `AI_1` を実際に移動させる．

---

## 2. 達成条件

ユーザが，

> 私の右へ移動してください

と発話した場合，Python側で以下の構造化メッセージを生成する．

```json
{
  "type": "action_request",
  "speaker": "Human_1",
  "action": "move",
  "reference": "Human_1",
  "direction": "right"
}
````

Unity側では，

* `reference = Human_1`
* `direction = right`

を解釈し，
`Human_1` の現在位置と向きを基準として右方向を算出する．

その結果，`AI_1` が `Human_1` の右側へ移動すること．

---

## 3. 前提

CHECKPOINT-2が完成していること．

CHECKPOINT-2までの情報経路：

```text
Human Speech
    ↓
Microphone
    ↓
Python / faster-whisper
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

CHECKPOINT-3では，Unity側に身体基準の空間参照とActionを追加する．

```text
Human Speech
    ↓
Speech Recognition
    ↓
Interpretation
    ↓
Action Request
    ↓
Human_1 Position / Orientation
    ↓
Body-Centered Direction
    ↓
Target Position
    ↓
AI_1 Action
```

---

## 4. Unity内の主体配置

Unity Scene内に，
人を表す参照主体として `Human_1`，
AI Actorを表す行動主体として `AI_1`
を配置した．

### Human_1

Unityの3D ObjectとしてCapsuleを作成し，

```text
Name: Human_1
Position:
X = 0
Y = 1
Z = 0

Rotation:
Y = 0
```

とした．

### AI_1

同様にCapsuleを作成し，

```text
Name: AI_1
Position:
X = 0
Y = 1
Z = 2
```

とした．

この段階ではVICON等の外部計測系は使用せず，
Unity内の `Human_1` を人の代理として使用する．

---

## 5. 身体基準空間参照

CHECKPOINT-3では，

```text
direction = right
```

をUnity世界座標の固定方向として扱わず，
`Human_1` 自身の向きに基づく右方向として解釈する．

Unityでは，

```csharp
humanTransform.right
```

によって，`Human_1` のローカル座標系における右方向ベクトルを取得できる．

したがって，

```text
Human_1の向き
    ↓
humanTransform.right
    ↓
身体基準の右方向
```

という対応を利用する．

---

## 6. TcpSpeechReceiver.csへの参照追加

`TcpSpeechReceiver` クラス内に，
HumanおよびAI ActorのTransform参照を追加した．

```csharp
public Transform humanTransform;
public Transform aiTransform;

public float moveDistance = 1.0f;
```

---

## 7. 行動指示から目標位置を算出

受信した `ActionRequest` が，

```text
action = move
reference = Human_1
direction = right
```

の場合，以下の処理を実行する．

```csharp
if (request.action == "move" &&
    request.reference == "Human_1" &&
    request.direction == "right")
{
    Vector3 targetPosition =
        humanTransform.position +
        humanTransform.right * moveDistance;

    aiTransform.position = targetPosition;

    Debug.Log("AI_1 moved to: " + targetPosition);
}
```

ここで，

```csharp
humanTransform.position
```

は `Human_1` の現在位置，

```csharp
humanTransform.right
```

は `Human_1` から見た右方向，

```csharp
moveDistance
```

は移動距離を示す．

今回の初期値は，

```text
moveDistance = 1.0
```

とした．

---

## 8. Inspectorでの参照設定

Hierarchy内の `SpeechReceiver` を選択し，
Inspectorの `Tcp Speech Receiver` コンポーネントに表示された，

```text
Human Transform
Ai Transform
Move Distance
```

へ，それぞれ，

```text
Human_1 → Human Transform
AI_1    → Ai Transform
```

をドラッグ＆ドロップした．

`Move Distance` は `1` とした．

---

## 9. 実行手順

1. UnityをPlayする．
2. TCP Serverが起動していることを確認する．
3. Python側で `speech_to_unity_cp2.py` を実行する．
4. 「私の右へ移動してください」と発話する．
5. faster-whisperが音声を認識する．
6. Python側で自然言語を構造化する．
7. 以下の `action_request` が生成される．

```json
{
  "type": "action_request",
  "speaker": "Human_1",
  "action": "move",
  "reference": "Human_1",
  "direction": "right"
}
```

8. TCP/IP経由でUnityへ送信する．
9. Unity側で `ActionRequest` を解析する．
10. `Human_1` の位置・姿勢を参照する．
11. `humanTransform.right` から身体基準の右方向を算出する．
12. 右方向1mの目標位置を求める．
13. `AI_1` をその位置へ移動する．

---

## 10. 確認結果

以下を確認した．

```text
音声入力                           OK
faster-whisper日本語認識           OK
自然言語の構造化                   OK
action_request生成                 OK
TCP/IP通信                         OK
Unity JSON解析                     OK
Human_1参照                        OK
身体基準右方向の算出               OK
目標位置算出                       OK
AI_1移動                           OK
```

---

## 11. 身体基準座標の確認

`Human_1` の `Rotation Y` を変更すると，
`humanTransform.right` の方向も同時に変化する．

例えば，

```text
Rotation Y = 0
```

の場合と，

```text
Rotation Y = 90
```

の場合で同じ，

> 私の右へ移動してください

という指示を与えると，
`AI_1` の移動方向も `Human_1` の向きに応じて変化する．

これにより，

```text
right
```

がUnity世界座標の固定方向ではなく，
`Human_1` を基準とした身体基準方向として解釈されていることを確認できる．

---

## 12. CHECKPOINT-3 判定

**達成**

CHECKPOINT-3では，

> 構造化された行動指示を，
> Human_1の位置・姿勢に基づく身体基準空間へ対応付け，
> AI_1を実際に移動させる

一連の処理を実現した．

---

## 13. CHECKPOINT-2からの進展

CHECKPOINT-2：

```text
Speech
→ Recognition
→ Interpretation
→ Structured Action Request
→ Unity
→ UI
```

CHECKPOINT-3：

```text
Speech
→ Recognition
→ Interpretation
→ Structured Action Request
→ Human_1 Reference
→ Body-Centered Direction
→ Target Position
→ AI_1 Action
```

CHECKPOINT-2では意味情報の構造化までであったが，
CHECKPOINT-3ではその意味表現を
実際のUnity空間上の行動へ変換した．

---

## 14. サンドボックス・アーキテクチャ上の位置付け

CHECKPOINT-3では，
SIPF上の情報処理が初めて環境へのActionまで到達した．

概略的には，

```text
Human
↓
<Perception>
↓
<Context>
↓
Structured Action Request
↓
Spatial Reference
↓
<Action>
↓
Unity Environment
```

となる．

`Human_1` の位置・姿勢を参照し，
人の「右」という身体基準表現を
Unity上の方向ベクトルへ対応付ける処理は，
AIRによる共有参照の最小実装に相当する．

---

## 15. AIRとの関係

CHECKPOINT-3では，
まだ独立したAIR Managerは実装していない．

しかし，

```text
reference = Human_1
direction = right
```

という意味表現を，

```text
Human_1 Transform
↓
Position / Orientation
↓
humanTransform.right
↓
Unity coordinate
```

へ対応付けた．

これは，

> 人が身体を通して参照する方向表現と，
> AIが計算可能な座標・方向表現との対応

を具体化した最小例であり，
AIRの基本的役割を部分的に実装している．

---

## 16. 現段階の制約

現時点では，

* `Human_1` はUnity内の仮想オブジェクトである
* 実際の人の位置・姿勢はまだ使用していない
* `right` のみを対象としている
* 移動は瞬間的な位置変更である
* `<Skill>`，`<Ethics>`，`<Permission>` の独立実装はまだ行っていない
* `<Verification>` はまだ実装していない
* AIR Managerは独立したC/C++モジュールとして未実装である

---

## 17. 次のCheckpoint

次段階では，
AI_1が実際に指示された位置へ移動したかを
Action処理とは独立して確認する．

例えば，

```text
Target Position
↓
AI_1 Actual Position
↓
Distance / Direction Error
↓
Verification Result
```

を計算する．

これはサンドボックスにおける，

```text
<Action>
↓
Environment
↓
<Verification>
```

の最小実装に相当する．

````

コミットメッセージは，例えばこれでよいと思います．

```text
Checkpoint 3: Body-centered reference and AI avatar action
````

今回のCheckpoint 3はかなり大きいです．**「話した内容が表示された」段階から，「人を基準とした意味が，環境への実際の作用になった」段階まで到達した**ので，第二論文の実装結果としても中核になりそうです．
