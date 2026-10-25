はい．Checkpoint 8は第二論文の大きな区切りなので，これまでより少し詳しく記録しておく価値があります．特に，**CP8.1 → CP8.2 → CP8.3という段階的実装，C++ AIR Manager，TCP往復通信，3方向の身体基準変換，連続実行，CP1〜7との統合**を明確に残しましょう．

そのまま `CHECKPOINT-8.md` に使える文案です．

```markdown
# CHECKPOINT-8
## Independent AIR Manager and End-to-End SIPF Integration

### Status
**Completed**

### Date
2026-10-02

---

## 1. 目的

CHECKPOINT-1からCHECKPOINT-7までに，

```text
Human Speech
↓
<Perception>
↓
<Context>
↓
<Permission>
↓
<Action>
↓
Environment
↓
<Verification>
↓
Human Evaluation
↓
<Experience>
```

というHuman-AI Interactionの主要な処理経路を実装した．

しかし，CHECKPOINT-7までの実装では，

```text
Human_1
AI_1
身体基準方向
目標位置
```

等の空間情報は主としてUnity内部のTransformとして保持されており，

```csharp
humanTransform.position +
humanTransform.right * moveDistance
```

のように，身体基準の空間計算もUnity側で直接実行していた．

CHECKPOINT-8では，
第一論文で定義したAIR
（AI Intermediate Representation）の最小実装として，

> 人間がMR環境を通して参照する対象と，
> AIが計算可能な形式で参照する対象との
> 意味的・空間的対応関係を扱う独立したRuntime Component

をC/C++によって実装する．

最終的には，

```text
Unity Environment
↓
Human_1 state
↓
TCP/IP
↓
AIR Manager
↓
Body-Centered Spatial Mapping
↓
Target Position
↓
TCP/IP
↓
Unity
↓
AI_1 Action
```

という往復経路を成立させる．

---

## 2. CHECKPOINT-8の構成

CHECKPOINT-8は，以下の3段階で実装した．

```text
CP8.1
AIR Manager単体実装
↓
CP8.2
Unity → AIR Manager
↓
CP8.3
AIR Manager → Unity
＋
既存SIPFへの統合
```

---

# CP8.1
## AIR Managerの独立C++実装

---

## 3. AIRManager Project

Visual Studioで新規C++ Project，

```text
AIRManager
```

を作成した．

主要Source：

```text
AIRManager.cpp
```

まず独立したExecutableとして，

```text
AIR Manager started.
```

を表示できることを確認した．

これにより，
UnityやPythonから独立したAIR Manager Processの
最小構成を成立させた．

---

## 4. Entity表現

AIR Manager内部で，
環境内主体をEntityとして表現する．

最小実装では，

```cpp
struct Entity
{
    std::string id;

    float x;
    float y;
    float z;

    float yaw;
};
```

とした．

初期Entity：

```text
Human_1
```

について，

```text
ID
Position
Orientation
```

をAIR Manager内部で保持する．

---

## 5. 身体基準座標の計算

Human_1のYawから，
身体基準の右方向を計算した．

```cpp
float yawRad =
    human.yaw * PI / 180.0f;

float rightX =
    std::cos(yawRad);

float rightZ =
    -std::sin(yawRad);
```

例えば，

```text
Yaw = 0 degree
```

では，

```text
Right Direction = (1, 0, 0)
```

となる．

```text
Yaw = 90 degree
```

では概ね，

```text
Right Direction = (0, 0, -1)
```

となる．

---

## 6. Target Positionの計算

Human_1から見て右1mの位置を，

```cpp
float targetX =
    human.x + rightX * moveDistance;

float targetY =
    human.y;

float targetZ =
    human.z + rightZ * moveDistance;
```

として計算した．

これにより，

```text
Human_1 Position + Orientation
↓
Body-Centered Direction
↓
World Coordinate
```

の変換をAIR Manager単体で実行できることを確認した．

これはCHECKPOINT-3でUnityが担当していた，

```csharp
humanTransform.position +
humanTransform.right * moveDistance
```

に相当する処理を，
Unity外部へ分離したものである．

---

## 7. CP8.1 判定

**達成**

AIR Manager単体で，

```text
Human_1 pose
↓
body-centered right
↓
target_position
```

を計算できることを確認した．

---

# CP8.2
## Unity Environment State → AIR Manager

---

## 8. TCP/IP通信

AIR ManagerとUnityの通信にはTCP/IPを使用した．

AIR Manager：

```text
Host = 127.0.0.1
Port = 50001
```

とした．

既存のPython → Unity通信で使用している，

```text
Port = 50000
```

とは分離した．

---

## 9. AIR Manager TCP Server

Windows Socketを用いて，
AIR ManagerをTCP Serverとして実装した．

使用：

```cpp
#include <winsock2.h>
#include <ws2tcpip.h>

#pragma comment(lib, "ws2_32.lib")
```

基本処理：

```text
WSAStartup
↓
socket
↓
bind
↓
listen
↓
accept
↓
recv
↓
AIR processing
↓
send
```

---

## 10. Unity側 AIRStateSender

Unity側に，

```text
AIRSender
```

GameObjectを作成し，

```text
AIRStateSender.cs
```

をアタッチした．

AIRへ送信するEntity Stateを，

```csharp
[System.Serializable]
public class AIREntityState
{
    public string type;
    public string id;
    public string direction;

    public float x;
    public float y;
    public float z;

    public float yaw;
}
```

として定義した．

---

## 11. Unity → AIR Protocol Message

Unityの `Human_1` Transformから，

```text
ID
Position
Yaw
Direction
```

を取得し，
JSONへ変換してAIR Managerへ送信する．

例：

```json
{
  "type": "air_entity_state",
  "id": "Human_1",
  "direction": "right",
  "x": 0.0,
  "y": 1.0,
  "z": 0.0,
  "yaw": 0.0
}
```

情報経路：

```text
Unity Human_1
↓
Transform
↓
AIREntityState
↓
JSON
↓
TCP/IP
↓
AIR Manager
```

---

## 12. AIR ManagerでのJSON解釈

CHECKPOINT-8では外部JSON Libraryを導入せず，
最小実装として，

```cpp
GetJsonString()
GetJsonFloat()
```

を用いてJSONから値を取得した．

受信したJSONから，

```text
id
direction
x
y
z
yaw
```

を抽出し，
AIR Manager内部の `Entity human` へ格納した．

これにより，

```text
Unity Human_1 Transform
↓
Protocol Message
↓
AIR Entity Human_1
```

というEnvironmentからAIRへの写像を実装した．

---

## 13. Unity実データによるAIR計算

CP8.1ではAIR Manager内部に
Human_1の値を直接記述していた．

CP8.2では，
Unityから受信した実際のHuman_1の，

```text
Position
Yaw
```

を使って身体基準座標を計算した．

例えば，

```text
Human_1 Position = (2, 1, 3)
Yaw = 90
```

の場合，

```text
right
→ target_position ≈ (2, 1, 2)
```

となることを確認した．

---

## 14. CP8.2 判定

**達成**

```text
Unity Human_1
↓
TCP/IP
↓
AIR Entity
↓
Body-Centered Spatial Mapping
↓
Target Position
```

が成立した．

---

# CP8.3
## AIR Manager → Unity → AI Actor Action

---

## 15. AIRからTarget Positionを返す

AIR Managerで計算したTarget Positionを，
JSONとしてUnityへ返送する．

例：

```json
{
  "type": "air_target_position",
  "reference": "Human_1",
  "direction": "right",
  "x": 2.0,
  "y": 1.0,
  "z": 2.0
}
```

---

## 16. UnityでAIR Responseを受信

Unity側に，

```csharp
[System.Serializable]
public class AIRTargetPosition
{
    public string type;
    public string reference;
    public string direction;

    public float x;
    public float y;
    public float z;
}
```

を定義した．

AIR ManagerからResponseを受信し，

```csharp
AIRTargetPosition target =
    JsonUtility.FromJson<AIRTargetPosition>(
        responseJson
    );
```

として解釈する．

---

## 17. AIR TargetによるAI_1移動

AIR Managerから返された，

```text
x
y
z
```

を用いて，

```csharp
aiTransform.position =
    new Vector3(
        target.x,
        target.y,
        target.z
    );
```

としてAI_1を移動する．

Unity側では，
Target Position算出のために，

```csharp
humanTransform.right
```

を使用しない．

したがって，

```text
Human_1から見て右
```

という身体基準表現を，

```text
Unity World Coordinate
```

へ変換する責務は，
AIR Managerへ移された．

---

# 3方向への拡張

## 18. Python側のDirection拡張

Python側の音声認識・命令解釈を，

```text
right
left
forward
```

の3方向へ拡張した．

使用Script：

```text
speech_to_unity_cp3.py
```

命令例：

```text
私の右へ移動してください
→ right

私の左へ移動してください
→ left

私の前へ移動してください
→ forward
```

---

## 19. Structured Action Request

Python側では，

```json
{
  "type": "action_request",
  "speaker": "Human_1",
  "action": "move",
  "reference": "Human_1",
  "direction": "right"
}
```

等のStructured Action Requestを生成する．

`direction` は，

```text
right
left
forward
```

のいずれかとなる．

---

## 20. AIRへのDirection送信

`AIRStateSender.SendHumanState()` を，

```csharp
SendHumanState(string direction)
```

へ変更した．

`TcpSpeechReceiver` から，

```csharp
airStateSender.SendHumanState(
    request.direction
);
```

として，
Action RequestのDirectionをAIR Managerへ渡す．

---

## 21. AIR Managerの3方向身体基準変換

AIR ManagerではHuman_1のYawから，

```text
right
forward
```

の身体基準Vectorを計算する．

```cpp
float rightX =
    std::cos(yawRad);

float rightZ =
    -std::sin(yawRad);

float forwardX =
    std::sin(yawRad);

float forwardZ =
    std::cos(yawRad);
```

Directionに応じて，

```cpp
if (direction == "right")
{
    dirX = rightX;
    dirZ = rightZ;
}
else if (direction == "left")
{
    dirX = -rightX;
    dirZ = -rightZ;
}
else if (direction == "forward")
{
    dirX = forwardX;
    dirZ = forwardZ;
}
```

とする．

Human_1が，

```text
Position = (0, 1, 0)
Yaw = 0
```

の場合，

```text
right
→ ( 1, 1, 0)

left
→ (-1, 1, 0)

forward
→ (0, 1, 1)
```

となる．

---

# 連続Runtime化

## 22. AIR Managerの連続待受

初期実装ではAIR Managerは，

```text
accept
↓
recv
↓
send
↓
終了
```

という単発動作であった．

CHECKPOINT-8では，

```cpp
while (true)
{
    accept();
    recv();
    AIR processing;
    send();
    closesocket(clientSocket);
}
```

という構造へ変更した．

処理構造：

```text
listen
↓
while
    ↓
    accept
    ↓
    recv
    ↓
    AIR processing
    ↓
    send
    ↓
    client close
    ↓
    next accept
```

これにより，
AIR Managerを再起動せずに
複数のInteractionを連続処理できる．

---

## 23. Python側の連続入力

Python側も単発の，

```text
record
↓
recognize
↓
send
↓
exit
```

から，

```text
Enter
↓
Speech Input
↓
Recognition
↓
Action Request
↓
Send
↓
次のEnter待ち
```

という連続入力方式へ変更した．

終了時には，

```text
q
```

を入力する．

これにより，

```text
right
↓
left
↓
forward
↓
right
...
```

という連続したInteractionが可能となった．

---

# Verificationの拡張

## 24. 3方向Verification

従来の，

```csharp
VerifyRightPosition()
```

を，

```csharp
VerifyPosition(ActionRequest request)
```

へ一般化した．

Directionに応じて，

```csharp
right
→ humanTransform.right

left
→ -humanTransform.right

forward
→ humanTransform.forward
```

を使用し，
期待されるPositionを独立に計算する．

---

## 25. AIRとVerificationの責務分離

AIR Managerは，

```text
Human_1 pose
+
direction
↓
target_position
```

を計算する．

一方ActionVerifierは，
AIR Managerから返されたTarget Positionを
Verificationの基準として直接使用しない．

Unity Environment内の，

```text
Human_1 Transform
AI_1 Transform
```

から期待位置を別途算出する．

したがって，

```text
AIR spatial mapping
```

と，

```text
Verification
```

の責務を分離している．

現段階では両者とも同じUnity Environment由来の
Human_1状態を使用するため，
物理的に独立した外部Verificationではない．

VICON等を用いた外部Verificationは今後の課題である．

---

# CP1～CP8統合

## 26. TcpSpeechReceiverとの統合

CHECKPOINT-7まで，
Action処理ではUnity内部で，

```csharp
humanTransform.position +
humanTransform.right * moveDistance
```

によってTarget Positionを計算していた．

CHECKPOINT-8ではこの処理をAction経路から削除し，

```csharp
airStateSender.SendHumanState(
    request.direction
);
```

によってAIR Managerへ問い合わせる．

---

## 27. 統合後の情報処理経路

CHECKPOINT-8完成時点の主要経路：

```text
Human Speech
↓
Python / faster-whisper
↓
<Perception>
↓
Natural Language Interpretation
↓
<Context>
↓
Structured Action Request
↓
<Permission>
↓
ALLOWED
↓
Unity Human_1 State
↓
AIR Manager
↓
Body-Centered Spatial Mapping
↓
Target Position
↓
Unity
↓
<Action>
↓
AI_1 Movement
↓
Environment
↓
<Verification>
↓
Human Evaluation
↓
<Experience>
↓
experience.jsonl
```

これにより，
CHECKPOINT-1からCHECKPOINT-8までの主要処理経路が
一本の実働Runtimeとして接続された．

---

# Experience Log

## 28. Experience Log保存先の変更

従来は，

```csharp
Application.persistentDataPath
```

へ `experience.jsonl` を保存していた．

保存場所が分かりにくいため，
CHECKPOINT-8ではRepository直下の，

```text
AI_MR_Sandbox
└─ tmp
   └─ experience.jsonl
```

へ変更した．

Unity Project：

```text
AI_MR_Sandbox
└─ unity
   └─ SpeechReceiver
      └─ Assets
```

からRepository Rootを取得し，

```csharp
string repositoryRoot =
    Path.GetFullPath(
        Path.Combine(
            Application.dataPath,
            "..",
            "..",
            ".."
        )
    );
```

としている．

`tmp` Directoryが存在しない場合は，

```csharp
Directory.CreateDirectory(
    tmpDirectory
);
```

によって自動生成する．

---

## 29. Git管理

`tmp` はRuntime Log保存用Directoryであり，
Git Repositoryには含めない．

`.gitignore` に，

```gitignore
tmp/
```

を追加する．

---

# End-to-End Test

## 30. 連続Interaction試験

AIR Managerを1回起動した状態で，
以下の命令を連続実行した．

```text
私の右へ移動してください
↓
right

私の左へ移動してください
↓
left

私の前へ移動してください
↓
forward
```

各Interactionについて，

```text
Speech Recognition
↓
Action Request
↓
Permission
↓
AIR
↓
Action
↓
Verification
↓
Human Evaluation
↓
Experience
```

が継続して実行されることを確認した．

---

## 31. Expected Result

Human_1：

```text
Position = (0, 1, 0)
Yaw = 0
```

の場合，

```text
right
→ AI_1 = ( 1, 1, 0)

left
→ AI_1 = (-1, 1, 0)

forward
→ AI_1 = (0, 1, 1)
```

となる．

各Actionについて，

```text
Verification: PASS
```

を確認し，
Human Evaluation後にExperience Recordが
`experience.jsonl` へ追記されることを確認した．

---

# CHECKPOINT-8 判定

## 32. CHECKPOINT-8達成

**達成**

CHECKPOINT-8では，

> Unity環境内のHuman_1の位置・姿勢と
> 身体基準Directionを独立したC++ AIR Managerへ送り，
> AIR Managerが意味的・空間的対応に基づいて
> World Coordinate上のTarget Positionを算出し，
> Unityへ返送してAI ActorのActionへ接続する

最小AIR Runtimeを実装した．

さらに，

```text
right
left
forward
```

の複数身体基準命令を，
AIR Managerを再起動することなく
連続処理できることを確認した．

---

## 33. AIRの現段階での意味

CHECKPOINT-8のAIRは，
完全なAIR実装ではなく，

> Humanが使用する身体基準の空間表現と，
> AI／Unityが計算可能なWorld Coordinateとの
> 対応関係を保持・変換する最小実装

である．

特に，

```text
"Human_1"
"right"
"left"
"forward"
```

という意味的参照を，

```text
Entity
Position
Orientation
World Coordinate
```

へ写像している．

したがってAIRを単なるTCP Relayとしてではなく，

```text
Semantic / Spatial Correspondence
```

を担うRuntime Componentとして実装した．

---

## 34. Protocol / Implementation分離

CHECKPOINT-8では，

```text
Protocol Message
```

として，

```text
Entity State
Target Position
Direction
```

を交換する．

一方，

```text
TCP/IP
JSON
C++
C#
```

はその実装手段である．

したがって，

```text
Protocol
≠
TCP/IP
```

という第一論文の設計原則を維持する．

将来，
通信方式や実装言語が変更されても，
Protocol上の意味を維持できる構造を目指す．

---

## 35. CHECKPOINT-7からの進展

CHECKPOINT-7までは，

```text
Human-AI Interaction Loop
```

の主要な責務を実装したが，
空間的共有参照はUnity内部のTransformへ依存していた．

CHECKPOINT-8では，

```text
Unity Environment
↓
AIR Manager
↓
Semantic / Spatial Mapping
↓
Unity Environment
```

という独立AIR層を挿入した．

これにより，

```text
HumanがMR環境で参照する空間
```

と，

```text
AIが計算可能な空間表現
```

との対応を
Unity内部実装から分離した．

---

# 第二論文における位置付け

## 36. 第二論文の実装上の区切り

CHECKPOINT-1からCHECKPOINT-8までに，

```text
Perception
Context
Permission
Action
AIR
Environment
Verification
Human Evaluation
Experience
```

を含む主要なHuman-AI Interaction Runtimeを
実際に動作させた．

CHECKPOINT-8によって，
第一論文で概念的に定義したAIRが
独立したRuntime Componentとして加わり，

```text
Python / AI
↕
Protocol
↕
AIR Manager
↕
Protocol
↕
Unity / MR Environment
```

という実装アーキテクチャが成立した．

このためCHECKPOINT-8を，

> 第二論文
> 「AI-MRメタ身体圏サンドボックスの実装
> ― SIPFに基づくHuman-AI相互作用エンジンの構築 ―」

における主要実装の一つの区切りとする．

---

## 37. 現段階の制約

現時点では，

- AIR Entityは主としてHuman_1を対象としている
- Directionはright / left / forwardのみ
- Distanceは1m固定
- OrientationはYaw中心
- JSON Parserは最小実装
- TCP接続はlocalhost
- AIR ManagerはWindows / C++実装
- AIRとUnityのProtocol Schemaは暫定
- `<Skill>` は独立Runtime Componentとして未実装
- `<Ethics>` は未実装
- PermissionはBooleanを中心とした最小実装
- VerificationはUnity内部Transformに依存
- VICONによる実Human pose入力は未接続
- MREALとの直接接続は未実装
- Experienceによる自動適応は未実装
- AIRによるSemantic State全般の管理は今後の課題

---

## 38. 今後の拡張

CHECKPOINT-8のAIR Managerは，
今後以下へ拡張できる．

```text
VICON
↓
Real Human Pose
↓
AIR Manager

MREAL
↓
MR Environment
↓
AIR Manager

AI / LLM
↓
Semantic Interpretation
↓
AIR Manager

Multiple Humans
↓
Shared Spatial Relations
↓
AIR Manager
```

さらに，

```text
Human_1
Human_2
AI_1
Objects
Places
Relations
States
```

を統一的にAIRへ保持することで，
複数主体・複数対象の
Human-AI Interactionへ拡張する．

---

## 39. Research Significance

CHECKPOINT-8の主要な意味は，
単にC++ Processを追加したことではない．

それまでUnity内部に埋め込まれていた，

```text
Human_1から見て右
Human_1から見て左
Human_1から見て前
```

という身体基準の意味と空間計算を
独立AIR Managerへ移し，

```text
Human Reference
↓
Semantic / Spatial Correspondence
↓
AI-computable World Coordinate
```

として実行可能にした点にある．

これにより，
MR Environmentの特定実装と
Human-AI Interactionの論理構造との
分離に向けた最小実装基盤が成立した．
```

コミットは，C++，Unity，Python，Scene，MarkdownをまとめてCheckpoint 8として固定するのがよいです．

```bash
git add .
git commit -m "Checkpoint 8: Independent AIR Manager and end-to-end SIPF integration"
git push
```

今回の `CHECKPOINT-8.md` では，特に **33．AIRの現段階での意味，34．Protocol / Implementation分離，36．第二論文の実装上の区切り，39．Research Significance** が第二論文へ直接使える部分になります．

そして研究上の現在地を一文で表すなら，

> **CP1〜7でSIPFの主要なHuman-AI Interaction Loopを実装し，CP8でHumanとAIの意味的・空間的対応を担う独立AIR ManagerをそのLoopへ統合した．**

となります．これは第二論文の実装成果をかなり端的に表しています．

はい．`CHECKPOINT-8.md` の末尾に，**Checkpoint 8で得られたUnityコンテンツ構成上の設計指針**として追記しましょう．  
既存の「39. Research Significance」の後に，以下を追加するのがよいと思います．

```markdown
---

# Unity Runtime Packaging

## 40. SandboxRuntime Prefab

CHECKPOINT-8では，
Human-AI Interaction RuntimeをScene固有要素から分離し，
再利用可能なUnity Prefabとして構成する方針を定めた．

Prefab Rootを，

```text
SandboxRuntime
```

とし，
その直下にRuntime Componentを配置する．

```text
SandboxRuntime Prefab
├─ SpeechReceiver
├─ Permission
├─ Verification
├─ HumanEvaluation
├─ Experience
└─ AIRSender
```

各ComponentはHierarchy上では
`SandboxRuntime` 直下の兄弟Nodeとして配置する．

これは，

```text
Permission
Verification
HumanEvaluation
Experience
AIRSender
```

等が `SpeechReceiver` に従属する機能ではなく，
それぞれ独立した責務を持つRuntime Componentであることを
Hierarchy上でも明確にするためである．

---

## 41. Prefab内部の参照関係

Hierarchy上では各Componentを並列に配置するが，
処理上の参照関係は以下となる．

```text
SpeechReceiver
 ├─ Permission      → Permission
 ├─ Verification    → Verification
 └─ AIRSender       → AIRSender

Verification
 └─ HumanEvaluator  → HumanEvaluation

HumanEvaluation
 └─ ExperienceLogger → Experience
```

したがって，

```text
Hierarchy
=
所有・構成関係
```

と，

```text
Reference
=
処理・依存関係
```

を区別する．

さらにModule間で交換される情報については，

```text
Protocol
=
情報授受の意味・条件・規則
```

として扱う．

本Projectでは，

```text
Hierarchy
Reference
Protocol
```

を異なる設計レベルとして区別する．

---

## 42. Scene側の基本Hierarchy

SandboxRuntimeとは別に，
Scene固有の要素についても役割ごとに階層化する．

基本構成を以下とする．

```text
SandboxScene
├─ Environment
│   ├─ Floor
│   ├─ Walls
│   ├─ Objects
│   └─ Lighting
│
├─ Entities
│   ├─ Human_1
│   └─ AI_1
│
├─ SandboxRuntime
│   ├─ SpeechReceiver
│   ├─ Permission
│   ├─ Verification
│   ├─ HumanEvaluation
│   ├─ Experience
│   └─ AIRSender
│
├─ UI
│   └─ Canvas
│       └─ SpeechText
│
├─ Systems
│   └─ EventSystem
│
└─ CameraRig
    └─ Main Camera
```

各階層の責務は以下とする．

```text
Environment
= 実験・体験固有の環境

Entities
= Human，AI Actor，Objects等の主体・対象

SandboxRuntime
= Human-AI Interactionの再利用可能な実行機構

UI
= Human Interface

Systems
= EventSystem等のUnity標準補助機構

CameraRig
= 視点・表示・XR Device依存部分
```

---

## 43. SandboxRuntimeに含めないもの

SandboxRuntime Prefabの再利用性を維持するため，
Scene固有またはDevice固有の要素は
原則としてPrefab内部へ含めない．

例：

```text
Human_1
AI_1
Environment Objects
Canvas
EventSystem
Main Camera
XR Rig
MREAL Camera
MREAL OpenXR Configuration
VICON-specific Objects
Quest-specific Objects
```

これらはScene側で管理し，
SandboxRuntimeから必要なものだけを
外部Referenceとして接続する．

一方，

```text
SpeechReceiver
Permission
Verification
HumanEvaluation
Experience
AIRSender
```

等のHuman-AI Interaction Logicは
SandboxRuntime内部に保持する．

---

## 44. MREAL Templateへの導入

今後，
Canon MREAL用Unity Templateへ
SandboxRuntime Prefabを導入する予定である．

想定構成：

```text
MREAL Scene
├─ MREALSystem
│   ├─ OpenXR
│   ├─ MREAL Camera / Tracking
│   └─ MREAL-specific Components
│
├─ Environment
│
├─ Entities
│   ├─ Human_1
│   └─ AI_1
│
├─ SandboxRuntime
│   ├─ SpeechReceiver
│   ├─ Permission
│   ├─ Verification
│   ├─ HumanEvaluation
│   ├─ Experience
│   └─ AIRSender
│
├─ UI
│
└─ Systems
```

この構造では，

```text
MREAL
=
表示・Tracking・MR Environment

SandboxRuntime
=
Human-AI Interaction Runtime
```

として責務を分離する．

これにより，
SandboxRuntimeそのものを変更せずに，

```text
通常Unity Scene
MREAL
Meta Quest
XV Arena
VICON連携Scene
```

等の異なるEnvironmentへ導入できる構造を目指す．

---

## 45. Unity Content Development Guideline

CHECKPOINT-8の実装を通して，
AI-MR Sandbox Projectにおける
Unity Content Developmentの基本指針を以下のように定める．

> Sceneは実験・体験固有のEnvironmentとEntityを定義し，
> SandboxRuntime PrefabはHuman-AI Interactionの実行機構を提供する．
> 両者は最小限の外部ReferenceおよびProtocolによって接続する．

したがって，
Unity Contentを開発する際には，

```text
Environment-dependent implementation
        ↕
SandboxRuntime
        ↕
External systems
```

を可能な限り分離する．

この分離により，

- Scene間でのRuntime再利用
- MREAL等の異なるXR Environmentへの移植
- Device固有実装とSandbox Logicの分離
- Component間依存関係の明確化
- Prefabによる配布・共有
- 実験条件間でのRuntime統一

を可能にする．

---

## 46. CHECKPOINT-8で得られた追加的成果

CHECKPOINT-8では，
独立AIR Managerの実装に加えて，

```text
AIR Runtime
+
Unity SandboxRuntime Prefab
+
Scene / Runtime Separation
```

という実装構成を得た．

したがってCHECKPOINT-8の成果は，

> AIRを独立Runtime Componentとして実装したこと

だけではなく，

> SandboxのHuman-AI Interaction Logicを
> SceneおよびXR Device固有実装から分離し，
> 再利用可能なUnity Runtime Unitとして構成する
> 実装指針を得たこと

を含む．

これは今後のMREAL Template，
VICON，
XV Arena等へのSandbox導入における
共通のUnity Content Development Guidelineとする．
```

特に **41節の**

> `Hierarchy = 所有・構成関係`  
> `Reference = 処理・依存関係`  
> `Protocol = 情報授受の意味・条件・規則`

という三層の整理は，第二論文でも使える重要な知見だと思います．

また，Checkpoint 8の最終成果が **「AIR Managerを作った」だけでなく，「SandboxRuntimeを移植可能な単位として切り出した」** ところまで広がったので，MREALテンプレートへの次の展開にも非常につながりやすくなりました．