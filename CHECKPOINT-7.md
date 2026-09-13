はい．Checkpoint 7は，これまでより**クラス間参照が一段複雑になったCheckpoint**なので，処理内容だけでなく，Unity Inspector上の接続関係を明示的に記録しておくことが重要です．

そのまま `CHECKPOINT-7.md` に貼れる形でまとめます．

````markdown
# CHECKPOINT-7
## Human Evaluation and Experience Integration

### Status
**Completed**

### Date
2026-09-13

---

## 1. 目的

CHECKPOINT-6までに，

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
<Experience>
````

という主要な処理経路を実装した．

CHECKPOINT-7では，システムによるVerificationとは別に，
Humanによる評価を導入する．

目的は，

```text
System Verification
        +
Human Evaluation
        ↓
<Experience>
```

という構造を実装し，

* システムによる客観的・幾何学的Verification
* 人間による意味的・主観的Evaluation

を異なる評価情報として保持することである．

---

## 2. 達成条件

AI_1がActionを実行し，
System Verificationが完了した後に，

```text
Y = Correct
N = Incorrect
```

としてHuman Evaluationを入力できること．

さらに，

```text
verificationPassed
humanEvaluation
```

の両方を同一のExperience Recordとして，
`experience.jsonl` に保存できること．

---

## 3. CHECKPOINT-6からの変更

CHECKPOINT-6まで：

```text
<Action>
↓
Environment
↓
<Verification>
↓
<Experience>
```

CHECKPOINT-7：

```text
<Action>
↓
Environment
↓
System Verification
↓
Human Evaluation
↓
<Experience>
```

CHECKPOINT-7では，
Verification直後にExperienceを保存するのではなく，
Human Evaluationが入力されるまで保存を待つ．

---

## 4. 基本設計

System VerificationとHuman Evaluationは，
同一の判定として統合せず，
別々の情報として記録する．

例えば，

```text
System Verification = PASS
Human Evaluation    = CORRECT
```

だけでなく，

```text
System Verification = PASS
Human Evaluation    = INCORRECT
```

という不一致も記録可能とする．

この違いは重要である．

System Verificationは，

```text
AI_1が期待された幾何学的位置へ到達したか
```

を判定する．

一方Human Evaluationは，

```text
そのActionが人間の意図から見て正しかったか
```

を評価する．

したがって，両者は異なる評価情報源として扱う．

---

## 5. HumanEvaluation GameObject

UnityのHierarchyに，

```text
HumanEvaluation
```

GameObjectを作成した．

このGameObjectに，

```text
HumanEvaluator.cs
```

をアタッチした．

HumanEvaluatorは，

```text
System Verification完了
↓
Human Evaluation開始
↓
Y / N入力待ち
↓
ExperienceLoggerへ結果を渡す
```

という責務を持つ．

---

## 6. ExperienceRecordの拡張

CHECKPOINT-5で作成した
`ExperienceRecord` に，

```csharp
public string humanEvaluation;
```

を追加した．

現在のRecordは概ね以下である．

```csharp
[System.Serializable]
public class ExperienceRecord
{
    public string timestamp;
    public string speaker;
    public string action;
    public string reference;
    public string direction;

    public float error;
    public bool verificationPassed;

    public string humanEvaluation;
}
```

これにより，

```text
Action Request
System Verification
Human Evaluation
```

を一つのInteraction Recordとして保持できる．

---

## 7. ExperienceLogger.cs

ファイルへの永続保存は，
`ExperienceLogger` に集約する．

HumanEvaluatorやActionVerifierから，
直接ファイル操作は行わない．

主要部分：

```csharp
using UnityEngine;
using System;
using System.IO;

[System.Serializable]
public class ExperienceRecord
{
    public string timestamp;
    public string speaker;
    public string action;
    public string reference;
    public string direction;

    public float error;
    public bool verificationPassed;

    public string humanEvaluation;
}

public class ExperienceLogger : MonoBehaviour
{
    private string logFilePath;

    void Start()
    {
        logFilePath =
            Path.Combine(
                Application.persistentDataPath,
                "experience.jsonl"
            );

        Debug.Log(
            "Experience log: " + logFilePath
        );
    }

    public void SaveExperience(
        ActionRequest request,
        float error,
        bool verificationPassed,
        string humanEvaluation)
    {
        ExperienceRecord record =
            new ExperienceRecord();

        record.timestamp =
            DateTime.Now.ToString("o");

        record.speaker = request.speaker;
        record.action = request.action;
        record.reference = request.reference;
        record.direction = request.direction;

        record.error = error;
        record.verificationPassed =
            verificationPassed;

        record.humanEvaluation =
            humanEvaluation;

        string json =
            JsonUtility.ToJson(record);

        File.AppendAllText(
            logFilePath,
            json + Environment.NewLine
        );

        Debug.Log(
            "Experience saved: " + json
        );
    }
}
```

実際にファイルへ追記する処理は，

```csharp
File.AppendAllText(
    logFilePath,
    json + Environment.NewLine
);
```

である．

---

## 8. HumanEvaluator.cs

CHECKPOINT-7では，
Human Evaluationの最小実装として
キーボード入力を使用する．

```csharp
using UnityEngine;

public class HumanEvaluator : MonoBehaviour
{
    public ExperienceLogger experienceLogger;

    private bool waitingForEvaluation = false;

    private ActionRequest pendingRequest;
    private float pendingError;
    private bool pendingVerificationPassed;

    public void StartEvaluation(
        ActionRequest request,
        float error,
        bool verificationPassed)
    {
        pendingRequest = request;
        pendingError = error;
        pendingVerificationPassed =
            verificationPassed;

        waitingForEvaluation = true;

        Debug.Log(
            "Human Evaluation: " +
            "Press Y = Correct / N = Incorrect"
        );
    }

    void Update()
    {
        if (!waitingForEvaluation)
        {
            return;
        }

        if (Input.GetKeyDown(KeyCode.Y))
        {
            Debug.Log(
                "Human Evaluation: CORRECT"
            );

            if (experienceLogger != null)
            {
                experienceLogger.SaveExperience(
                    pendingRequest,
                    pendingError,
                    pendingVerificationPassed,
                    "correct"
                );
            }

            waitingForEvaluation = false;
        }

        if (Input.GetKeyDown(KeyCode.N))
        {
            Debug.Log(
                "Human Evaluation: INCORRECT"
            );

            if (experienceLogger != null)
            {
                experienceLogger.SaveExperience(
                    pendingRequest,
                    pendingError,
                    pendingVerificationPassed,
                    "incorrect"
                );
            }

            waitingForEvaluation = false;
        }
    }
}
```

---

## 9. pending情報

Human Evaluationは，
System Verificationと同じフレームで
即時に入力されるとは限らない．

そのため，

```csharp
private ActionRequest pendingRequest;
private float pendingError;
private bool pendingVerificationPassed;
```

として，
評価対象となっているInteractionの情報を
HumanEvaluator内部に一時保持する．

HumanがYまたはNを入力した時点で，
これらの情報とHuman Evaluationを組み合わせて
ExperienceLoggerへ渡す．

---

## 10. ActionVerifier.csの変更

CHECKPOINT-6以前では，
Verification完了後に
ExperienceLoggerへ直接保存していた．

CHECKPOINT-7では，
この直接保存経路を削除する．

Verification完了後は，

```csharp
if (humanEvaluator != null)
{
    humanEvaluator.StartEvaluation(
        request,
        error,
        passed
    );
}
else
{
    Debug.LogWarning(
        "HumanEvaluator is not assigned."
    );
}
```

とする．

したがって現在の経路は，

```text
ActionVerifier
↓
HumanEvaluator
↓
ExperienceLogger
↓
experience.jsonl
```

となる．

---

## 11. 重要：旧Experience保存経路の削除

CHECKPOINT-5までの，

```csharp
if (experienceLogger != null)
{
    experienceLogger.SaveExperience(
        request,
        error,
        passed
    );
}
```

という直接保存処理は，
CHECKPOINT-7では使用しない．

この経路が残っていると，

```text
System Verification
↓
Experience保存
```

が先に実行され，
Human Evaluationを待たずにExperienceが保存される．

CHECKPOINT-7では，

```text
System Verification
↓
Human Evaluation
↓
Experience保存
```

という順序を維持する．

---

## 12. クラス間参照関係

CHECKPOINT-7では，
Unity Component間の参照関係が増加した．

主要な参照構造は以下である．

```text
TcpSpeechReceiver
    │
    ├── PermissionChecker
    │
    ├── Human_1 Transform
    │
    ├── AI_1 Transform
    │
    └── ActionVerifier
            │
            ├── Human_1 Transform
            ├── AI_1 Transform
            │
            └── HumanEvaluator
                    │
                    └── ExperienceLogger
```

情報の流れとして見ると，

```text
TcpSpeechReceiver
        ↓
PermissionChecker
        ↓
Action
        ↓
ActionVerifier
        ↓
HumanEvaluator
        ↓
ExperienceLogger
```

となる．

---

## 13. Unity Inspector上の参照設定

CHECKPOINT-7では，
C#コードだけではなく，
Unity Inspector上の参照設定が必須である．

### SpeechReceiver

```text
SpeechReceiver
└─ TcpSpeechReceiver
     ├─ Human Transform     → Human_1
     ├─ AI Transform        → AI_1
     ├─ Permission Checker  → Permission
     └─ Action Verifier     → Verification
```

### Verification

```text
Verification
└─ ActionVerifier
     ├─ Human Transform   → Human_1
     ├─ AI Transform      → AI_1
     └─ Human Evaluator   → HumanEvaluation
```

### HumanEvaluation

```text
HumanEvaluation
└─ HumanEvaluator
     └─ Experience Logger → Experience
```

この参照関係は，
CHECKPOINT-7の再現に必須である．

---

## 14. 実装時に発生した問題

Human Evaluationが実行されず，
System Verification後に処理が
スルーされる現象が発生した．

原因は，

```text
Verification
└─ ActionVerifier
     └─ Human Evaluator → None
```

となっており，
Unity Inspector上で
`HumanEvaluation` GameObjectが
設定されていなかったことであった．

コードでは，

```csharp
if (humanEvaluator != null)
{
    humanEvaluator.StartEvaluation(
        request,
        error,
        passed
    );
}
```

としているため，
`humanEvaluator == null` の場合，
コンパイルエラーや例外を発生させずに
Human Evaluation処理が実行されなかった．

Inspectorで，

```text
Human Evaluator → HumanEvaluation
```

を設定することで解決した．

---

## 15. 再現上の注意

CHECKPOINT-7では，
コードが正しくても
Inspector参照が設定されていなければ動作しない．

特に以下を確認する．

```text
Verification
→ HumanEvaluation

HumanEvaluation
→ Experience
```

したがって，

> C#コードとUnity Inspector上の参照関係を
> 一体としてCheckpointの実装状態とみなす

必要がある．

---

## 16. 実行手順

1. UnityをPlayする
2. `Allow Move = ON` を確認する
3. Python側の音声認識処理を起動する
4. 「私の右へ移動してください」と発話する
5. Action Requestが生成される
6. PermissionがALLOWEDになる
7. AI_1が移動する
8. System Verificationが実行される
9. Human Evaluation入力待ちになる
10. Game画面をアクティブにする
11. YまたはNを入力する
12. Experience Recordが生成される
13. `experience.jsonl` に追記される

---

## 17. CORRECT試験

発話：

> 私の右へ移動してください

System Verification：

```text
Verification: PASS
```

Human Evaluation：

```text
Y
```

Console：

```text
Human Evaluation: CORRECT
Experience saved: {...}
```

Experience Recordには，

```json
"verificationPassed": true,
"humanEvaluation": "correct"
```

が記録される．

---

## 18. INCORRECT試験

同じActionを実行した後，
Human Evaluationとして，

```text
N
```

を入力する．

Console：

```text
Human Evaluation: INCORRECT
Experience saved: {...}
```

Experience Recordには，

```json
"verificationPassed": true,
"humanEvaluation": "incorrect"
```

を記録できる．

---

## 19. System VerificationとHuman Evaluationの不一致

CHECKPOINT-7では，

```text
System Verification = PASS
Human Evaluation    = INCORRECT
```

というRecordを保存できる．

これは，

```text
物理的・幾何学的には指示された位置へ移動した
```

ことと，

```text
人間が期待した結果であった
```

ことが必ずしも同一ではないことを意味する．

この差異を失わずに記録することが，
Human-AI InteractionのExperienceを扱う上で重要である．

---

## 20. CHECKPOINT-7 判定

**達成**

CHECKPOINT-7では，

> System VerificationとHuman Evaluationを
> 異なる評価情報源として取得し，
> 両者を同一のExperience Recordへ保存する

処理を実装した．

---

## 21. CHECKPOINT-6からの進展

CHECKPOINT-6：

```text
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
<Experience>
```

CHECKPOINT-7：

```text
<Context>
↓
<Permission>
↓
<Action>
↓
Environment
↓
System Verification
↓
Human Evaluation
↓
<Experience>
```

これにより，
AI Actor自身の処理経路だけではなく，
Humanを評価情報源として
Interaction Loopへ再導入した．

---

## 22. サンドボックス・アーキテクチャ上の位置付け

CHECKPOINT-7では，

```text
Environment
↓
<Verification>
↓
<Experience>
```

という内部経路に加えて，

```text
Human Evaluation
↓
<Experience>
```

という外部評価経路を導入した．

System VerificationとHuman Evaluationを
区別して保持することで，

```text
環境状態としての成功
```

と，

```text
人間にとっての成功
```

を別々に扱える．

これは将来のExperience利用，
Human-AI Interaction評価，
および機能的可塑性の実装に向けた
基礎となる．

---

## 23. <Experience>の現在の構造

CHECKPOINT-7時点のExperienceは，

```text
timestamp
speaker
action
reference
direction
error
verificationPassed
humanEvaluation
```

を保持する．

したがって，
単なるAction履歴ではなく，

```text
Instruction
↓
Action
↓
System Result
↓
Human Evaluation
```

を関連付けたInteraction Recordとなった．

---

## 24. 現段階の制約

現時点では，

* Human EvaluationはY/Nキーのみ
* Human Evaluationは2値評価のみ
* 評価理由は記録していない
* Human Evaluationの音声入力は未実装
* UIボタンによる評価は未実装
* 複数の未評価Interactionを同時保持できない
* Permission DENIED時のExperience記録は未実装
* `<Skill>` は独立Componentとして未実装
* `<Ethics>` は未実装
* AIR Managerは独立実装されていない
* VerificationはUnity内部Transformを使用している
* VICON等の独立外部計測は未接続
* Experienceに基づく学習・適応は未実装

---

## 25. 実装構造上の課題

CHECKPOINT-7まで進んだことで，
Component間の参照関係が複雑化し始めた．

現在，

```text
TcpSpeechReceiver
→ PermissionChecker
→ ActionVerifier
→ HumanEvaluator
→ ExperienceLogger
```

という依存関係が形成されている．

現段階では最小実装として許容できるが，
今後Core Moduleの実装が増加すると，
直接参照のみで構成する方式は
管理が困難になる可能性がある．

したがって今後，

* Module間Protocolの明示化
* Messageによる疎結合化
* Sandbox Runtime全体の責務整理
* AIR Managerとの接続

を検討する必要がある．

この複雑化自体も，
概念アーキテクチャを実装アーキテクチャへ変換する際の
重要な設計課題として記録する．

---

## 26. 次の展開

CHECKPOINT-7以降は，

```text
<Skill>
<Ethics>
```

を独立した責務として導入する方向と，

```text
AIR Manager
```

を独立したC/C++プロセスとして導入する方向がある．

また，

```text
Permission DENIED
Human Evaluation
System Verification
```

をすべてExperienceへ記録することで，
Interaction Record自体をさらに一般化できる．

````

今回のコミットは，コード変更も含めて一緒に固定するのがよいです．

```bash
git add .
git commit -m "Checkpoint 7: Human evaluation integrated with experience"
git push
````

特に今回の `CHECKPOINT-7.md` の **「12．クラス間参照関係」「13．Unity Inspector上の参照設定」「14．実装時に発生した問題」** は重要です．Checkpoint 7から，実装上の本質的な課題として**モジュール同士の依存関係の管理**が見え始めました．これは単なるトラブル記録ではなく，第二論文で「概念的なProtocolを実装時にどのように接続するか」を論じる材料になってきています．
