はい．`CHECKPOINT-4.md` は，**`<Action>` と `<Verification>` の責務を分離し，実行結果を独立した処理で検証した段階**として記録しましょう．そのまま貼れる形です．

````markdown
# CHECKPOINT-4
## AI Avatar Action → Independent Verification

### Status
**Completed**

### Date
2026-09-13

---

## 1. 目的

CHECKPOINT-3では，ユーザの音声指示

> 私の右へ移動してください

を構造化された `action_request` に変換し，
`Human_1` の位置・姿勢を基準として身体基準の右方向を算出し，
`AI_1` を実際に移動させた．

CHECKPOINT-4では，このActionの結果を，
Actionを実行する処理とは別の処理によって確認する．

すなわち，

```text
<Action>
    ↓
AI_1移動
    ↓
Unity Environment
    ↓
<Verification>
    ↓
PASS / FAIL
````

という最小の検証系を構成する．

---

## 2. 達成条件

ユーザが，

> 私の右へ移動してください

と発話し，`AI_1` が `Human_1` の右1mへ移動した後，

Actionとは別のVerification処理が，

1. 期待される目標位置を独立に算出する
2. `AI_1` の実際の位置を取得する
3. 両者の距離誤差を計算する
4. 許容誤差以内なら `PASS`
5. 許容誤差を超えれば `FAIL`

と判定できること．

---

## 3. 前提

CHECKPOINT-3が完成していること．

CHECKPOINT-3までの情報経路：

```text
Human Speech
    ↓
<Perception>
    ↓
Natural Language Interpretation
    ↓
<Context>
    ↓
Structured Action Request
    ↓
Human_1 Reference
    ↓
Body-Centered Direction
    ↓
Target Position
    ↓
<Action>
    ↓
AI_1 Movement
```

CHECKPOINT-4では，この後段にVerificationを追加する．

```text
<Action>
    ↓
AI_1 Movement
    ↓
Environment State
    ↓
<Verification>
    ↓
PASS / FAIL
```

---

## 4. Verificationオブジェクトの作成

UnityのHierarchyに空のGameObjectを作成し，

```text
Verification
```

と命名した．

このGameObjectに，Verification専用のC#スクリプト，

```text
ActionVerifier.cs
```

をアタッチする．

Actionの実行処理とVerification処理を
異なるコンポーネントとして分離することを基本方針とした．

---

## 5. ActionVerifier.cs

CHECKPOINT-4では以下の最小実装を使用した．

```csharp
using UnityEngine;

public class ActionVerifier : MonoBehaviour
{
    public Transform humanTransform;
    public Transform aiTransform;

    public float targetDistance = 1.0f;
    public float tolerance = 0.05f;

    public void VerifyRightPosition()
    {
        Vector3 expectedPosition =
            humanTransform.position +
            humanTransform.right * targetDistance;

        float error =
            Vector3.Distance(
                aiTransform.position,
                expectedPosition
            );

        if (error <= tolerance)
        {
            Debug.Log(
                "Verification: PASS  Error = " + error
            );
        }
        else
        {
            Debug.Log(
                "Verification: FAIL  Error = " + error
            );
        }
    }
}
```

---

## 6. Verificationの処理内容

### 6.1 期待位置の算出

`Human_1` の現在位置と身体基準の右方向から，
期待されるAI_1の位置を算出する．

```csharp
Vector3 expectedPosition =
    humanTransform.position +
    humanTransform.right * targetDistance;
```

今回，

```text
targetDistance = 1.0 m
```

とした．

---

### 6.2 実際の位置との差

`AI_1` の実際の位置と期待位置との差を，

```csharp
Vector3.Distance()
```

によって求める．

```csharp
float error =
    Vector3.Distance(
        aiTransform.position,
        expectedPosition
    );
```

---

### 6.3 判定

許容誤差を，

```text
tolerance = 0.05 m
```

とした．

したがって，

```text
error <= 0.05 m
```

なら，

```text
PASS
```

それ以外なら，

```text
FAIL
```

とする．

---

## 7. Inspector設定

Hierarchyの `Verification` を選択し，
`ActionVerifier` のInspectorで以下を設定した．

```text
Human Transform  → Human_1
AI Transform     → AI_1
Target Distance  → 1
Tolerance        → 0.05
```

---

## 8. TcpSpeechReceiver.csとの接続

`TcpSpeechReceiver` クラスに，

```csharp
public ActionVerifier actionVerifier;
```

を追加した．

AI_1のAction実行後に，
Verificationを呼び出す．

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

    if (actionVerifier != null)
    {
        actionVerifier.VerifyRightPosition();
    }
}
```

---

## 9. Unity Inspectorでの接続

Hierarchyの `SpeechReceiver` を選択し，
`Tcp Speech Receiver` コンポーネントに追加された，

```text
Action Verifier
```

へ，Hierarchyの

```text
Verification
```

を設定した．

これにより，

```text
<Action>
    ↓
ActionVerifier
    ↓
<Verification>
```

が接続された．

---

## 10. 実行手順

1. UnityをPlayする
2. TCP Serverの起動を確認する
3. Python側の音声認識・構造化プログラムを実行する
4. 「私の右へ移動してください」と発話する
5. Pythonが `action_request` を生成する
6. TCP/IP経由でUnityへ送信する
7. Unityが `Human_1` を基準として右1mの目標位置を算出する
8. `AI_1` を目標位置へ移動する
9. `ActionVerifier` が期待位置を独立に算出する
10. AI_1の実位置との誤差を計算する
11. PASS / FAILをConsoleへ表示する

---

## 11. 実行結果

正常動作時，Unity Consoleに概ね，

```text
AI_1 moved to: (...)
Verification: PASS  Error = 0
```

と表示された．

これにより，

```text
Action実行
↓
環境状態変化
↓
Verification
↓
PASS
```

の処理が成立したことを確認した．

---

## 12. CHECKPOINT-4 判定

**達成**

CHECKPOINT-4では，

> AI_1を移動させるAction処理と，
> その結果が目標条件を満たしたかを確認するVerification処理を分離し，
> 実際の位置と期待位置の誤差に基づいてPASS / FAILを判定する

一連の処理を実現した．

---

## 13. CHECKPOINT-3からの進展

CHECKPOINT-3：

```text
Speech
→ Recognition
→ Interpretation
→ Structured Action Request
→ Body-Centered Reference
→ Target Position
→ AI_1 Action
```

CHECKPOINT-4：

```text
Speech
→ Recognition
→ Interpretation
→ Structured Action Request
→ Body-Centered Reference
→ Target Position
→ AI_1 Action
→ Environment State
→ Independent Verification
→ PASS / FAIL
```

CHECKPOINT-3ではActionまでであったが，
CHECKPOINT-4ではActionの結果を独立して確認する処理を追加した．

---

## 14. サンドボックス・アーキテクチャ上の位置付け

CHECKPOINT-4では，SIPF上の，

```text
<Action>
↓
Environment
↓
<Verification>
```

に相当する最小実装を行った．

重要なのは，

```text
Actionを実行した処理自身が
「成功した」と自己申告する
```

だけではなく，

```text
期待される状態
        ↓
実際の環境状態
        ↓
比較
        ↓
Verification
```

という別の責務を設けたことである．

---

## 15. <Action>と<Verification>の責務分離

CHECKPOINT-4では，

```text
TcpSpeechReceiver
```

側がActionを実行し，

```text
ActionVerifier
```

側が結果を確認する．

したがって，

```text
<Action>
```

と，

```text
<Verification>
```

をプログラム上でも異なるコンポーネントとして実装した．

これはAI-MRメタ身体圏サンドボックスにおける，

> 認識・行為と独立検証を分離する

という設計原則の最小実装である．

---

## 16. 現段階における「独立」の意味

現時点のVerificationは，
Action処理とは別のC#コンポーネントとして実装されているが，

```text
Human_1 Transform
AI_1 Transform
```

という同じUnity環境内の情報を参照している．

したがって，現段階では，

> **論理的・ソフトウェア的な責務分離**

を実現した段階であり，

VICON等の外部計測系による，

> **物理的に独立した外部Verification**

にはまだ到達していない．

将来的には，

```text
Unity internal state
```

とは独立した，

```text
VICON
External Sensor
External Evaluation
Human Evaluation
```

等をVerification情報源として追加する．

---

## 17. 現段階の制約

現時点では，

* 検証対象は `right` 方向の移動のみ
* 目標距離は1m固定
* toleranceは0.05m固定
* Unity内部のTransformを検証に使用
* VICON等の独立外部計測は未接続
* Human Evaluationは未実装
* Verification結果はConsole表示のみ
* Verification結果の保存は未実装
* `<Experience>` は未実装

---

## 18. 次のCheckpoint

次段階では，

```text
Instruction
Interpretation
Action
Verification Result
```

を相互作用履歴として保存する．

基本的な流れは，

```text
Human Instruction
↓
Interpretation
↓
Action
↓
Verification
↓
<Experience>
```

とする．

さらに将来的には，
ユーザによる，

```text
正しい
違う
```

というHuman Evaluationも
Verification / Experienceへ統合する．

````

コミットメッセージは，

```text
Checkpoint 4: Independent verification of AI avatar action
````

が分かりやすいと思います．

一点だけ大切なのは，今回の`ActionVerifier`を「完全に独立した外部検証」とはまだ呼ばないことです．**責務としては独立した`<Verification>`を実装したが，計測情報源はまだ同じUnity内部にある**，という整理にしておくと，第一論文との整合性も非常にきれいです．
