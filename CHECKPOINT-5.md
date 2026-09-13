はい．`CHECKPOINT-5.md` は，**`<Verification>` の結果まで含む一連の相互作用を `<Experience>` として永続記録できた段階**としてまとめるのがよいです．そのまま貼れる形にします．

````markdown
# CHECKPOINT-5
## Verification Result → Experience Record → Persistent JSONL Log

### Status
**Completed**

### Date
2026-09-13

---

## 1. 目的

CHECKPOINT-4では，AI_1のAction結果を，
Action処理とは異なる `ActionVerifier` によって検証し，

```text
PASS / FAIL
````

および位置誤差を得るところまで実装した．

CHECKPOINT-5では，

```text
Instruction
↓
Interpretation
↓
Action
↓
Verification
↓
Experience
```

という一連の相互作用を，
`<Experience>` に相当する永続的な記録として保存する．

最小実装として，各相互作用を1件の
`ExperienceRecord` としてJSON形式で記録し，
JSON Lines形式のログファイルへ追記する．

---

## 2. 達成条件

ユーザが，

> 私の右へ移動してください

と発話し，AI_1のActionとVerificationが完了した後，

以下の情報を含むExperience Recordが生成されること．

```text
timestamp
speaker
action
reference
direction
error
verificationPassed
```

さらに，実行するたびに新しいRecordが
ログファイルへ1行ずつ追記されること．

例：

```json
{"timestamp":"2026-09-13T18:00:00.0000000+09:00","speaker":"Human_1","action":"move","reference":"Human_1","direction":"right","error":0.0,"verificationPassed":true}
```

---

## 3. 前提

CHECKPOINT-4が完成していること．

CHECKPOINT-4までの基本経路：

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
Body-Centered Spatial Reference
    ↓
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

CHECKPOINT-5では，その後段に `<Experience>` を追加する．

```text
<Verification>
    ↓
Verification Result
    ↓
<Experience>
    ↓
Persistent Log
```

---

## 4. Experienceオブジェクトの作成

UnityのHierarchyに空のGameObjectを作成し，

```text
Experience
```

と命名した．

`Assets/Scripts` に，

```text
ExperienceLogger.cs
```

を作成し，`Experience` GameObjectへアタッチした．

---

## 5. ExperienceRecord

1回のHuman-AI Interactionを記録するデータ構造として，
`ExperienceRecord` を定義した．

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
}
```

各Recordは，

```text
指示主体
行動
参照主体
方向
Verification誤差
Verification結果
時刻
```

を保持する．

---

## 6. ExperienceLogger.cs

CHECKPOINT-5では，以下の最小実装を使用した．

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
        bool verificationPassed)
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

---

## 7. ログファイル

ログファイル名は，

```text
experience.jsonl
```

とした．

保存場所には，

```csharp
Application.persistentDataPath
```

を使用する．

Unity起動時にConsoleへ，

```text
Experience log: C:\...\experience.jsonl
```

のように実際の保存場所を表示する．

---

## 8. JSON Lines形式

ログ形式にはJSON Lines（JSONL）を使用した．

1回のInteractionを1行のJSONとして記録する．

例：

```json
{"timestamp":"2026-09-13T18:00:00+09:00","speaker":"Human_1","action":"move","reference":"Human_1","direction":"right","error":0.0,"verificationPassed":true}
{"timestamp":"2026-09-13T18:01:00+09:00","speaker":"Human_1","action":"move","reference":"Human_1","direction":"right","error":0.0,"verificationPassed":true}
```

この形式により，

```text
Interaction 1
Interaction 2
Interaction 3
...
```

を順次追記できる．

---

## 9. ActionVerifierとの接続

CHECKPOINT-4の `ActionVerifier` に，
`ExperienceLogger` への参照を追加した．

```csharp
public ExperienceLogger experienceLogger;
```

Verification結果を，

```text
error
passed
```

として取得した後，ExperienceLoggerへ渡す．

```csharp
public void VerifyRightPosition(ActionRequest request)
{
    Vector3 expectedPosition =
        humanTransform.position +
        humanTransform.right * targetDistance;

    float error =
        Vector3.Distance(
            aiTransform.position,
            expectedPosition
        );

    bool passed = error <= tolerance;

    if (passed)
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

    if (experienceLogger != null)
    {
        experienceLogger.SaveExperience(
            request,
            error,
            passed
        );
    }
}
```

---

## 10. ActionRequestをVerificationへ渡す

Experience Recordには，

```text
speaker
action
reference
direction
```

が必要である．

そのため，CHECKPOINT-4までの，

```csharp
VerifyRightPosition()
```

を，

```csharp
VerifyRightPosition(ActionRequest request)
```

へ変更した．

`TcpSpeechReceiver.cs` 側では，

```csharp
actionVerifier.VerifyRightPosition(request);
```

として現在のActionRequestをVerificationへ渡す．

---

## 11. 実装時の注意

`VerifyRightPosition()` に
`ActionRequest request` 引数を追加した際，

古い呼び出し，

```csharp
actionVerifier.VerifyRightPosition();
```

が残っていると，

```text
error CS7036:
There is no argument given that corresponds to
the required formal parameter 'request'
```

というコンパイルエラーが発生する．

この場合，

```csharp
actionVerifier.VerifyRightPosition(request);
```

へ変更する．

CHECKPOINT-4からCHECKPOINT-5への変更時の
再現上の注意点として記録する．

---

## 12. Inspector設定

Hierarchyの，

```text
Verification
```

を選択する．

`Action Verifier` に追加された，

```text
Experience Logger
```

へ，Hierarchyの，

```text
Experience
```

を割り当てる．

接続関係は，

```text
TcpSpeechReceiver
        ↓
ActionVerifier
        ↓
ExperienceLogger
```

となる．

---

## 13. 実行手順

1. UnityをPlayする
2. `Experience log:` の保存先を確認する
3. TCP Serverが起動していることを確認する
4. Python側の音声認識プログラムを実行する
5. 「私の右へ移動してください」と発話する
6. 音声を認識する
7. `action_request` を生成する
8. Unityへ送信する
9. AI_1を移動する
10. ActionVerifierが結果を検証する
11. PASS / FAILおよび誤差を得る
12. ExperienceLoggerへ結果を渡す
13. `experience.jsonl` へ1Record追記する

---

## 14. 実行結果

正常動作時，Unity Consoleには概ね，

```text
AI_1 moved to: (...)
Verification: PASS  Error = 0
Experience saved: {...}
```

と表示された．

さらに，

```text
experience.jsonl
```

を確認した結果，
Interaction実行ごとに新しいRecordが
1行ずつ追記されていることを確認した．

---

## 15. CHECKPOINT-5 判定

**達成**

CHECKPOINT-5では，

> 音声指示，意味解釈，Action，Verificationの結果を，
> 1件のExperience Recordとして構造化し，
> JSONL形式の永続ログへ追記保存する

一連の処理を実現した．

---

## 16. CHECKPOINT-4からの進展

CHECKPOINT-4：

```text
Speech
→ Recognition
→ Interpretation
→ Action
→ Verification
→ PASS / FAIL
```

CHECKPOINT-5：

```text
Speech
→ Recognition
→ Interpretation
→ Action
→ Verification
→ Experience Record
→ Persistent Log
```

Verification結果が一時的なConsole表示ではなく，
後から参照可能なExperienceとして保持されるようになった．

---

## 17. サンドボックス・アーキテクチャ上の位置付け

CHECKPOINT-5では，SIPF上の，

```text
<Verification>
↓
<Experience>
```

を最小実装した．

現在の主要経路は，

```text
Human
↓
<Perception>
↓
<Context>
↓
<Action>
↓
Environment
↓
<Verification>
↓
<Experience>
```

まで実働している．

これにより，
SIPFで想定した循環的情報処理の主要経路が，
Experienceへの記録まで到達した．

---

## 18. <Experience>の現段階での意味

現時点の `<Experience>` は，

```text
相互作用履歴の保存
```

までを実装した段階である．

すなわち，

```text
Experience
→ Contextの改善
Experience
→ Skillの改善
Experience
→ Protocolの変更
```

といった経験に基づく機能更新は，
まだ実装していない．

したがって現段階では，

> **Experienceの蓄積**

は成立したが，

> **Experienceに基づく適応・学習・機能的可塑性**

の実装は今後のCheckpointとする．

---

## 19. 現段階の制約

現時点では，

* Human Evaluationは未実装
* Experienceは保存のみ
* Experienceの読み戻しは未実装
* Experienceによる行動変更は未実装
* `<Skill>` は独立実装していない
* `<Ethics>` は独立実装していない
* `<Permission>` は独立実装していない
* AIR Managerは独立したC/C++実装に未移行
* VerificationはUnity内部情報を利用している
* VICON等の外部Verificationは未接続

---

## 20. 次の展開

次段階では，二つの方向が考えられる．

### Human Evaluation

Action後にユーザから，

```text
正しい
違う
```

等の評価を取得し，

```text
System Verification
+
Human Evaluation
↓
Experience
```

として記録する．

### 残るコアモジュールの実装

現在省略している，

```text
<Skill>
<Ethics>
<Permission>
```

を独立した責務として段階的に導入し，
SIPF全体の最小実装へ近づける．

````

コミットメッセージは，

```text
Checkpoint 5: Persistent experience logging after verification
````

あたりが分かりやすいと思います．

今回のCheckpoint 5で重要なのは，単に「ログファイルを書けた」ということではなく，**相互作用の入口だった発話が，認識・意味解釈・環境への作用・検証を経て，最後にExperienceとして永続化された**ことです．第二論文では，ここまでのCheckpoint 1〜5を一本の実装進展としてかなり明瞭に示せます．
