はい．Checkpoint 6は，**「能力が存在すること」と「その行為が許可されること」を分離した最小実装**として記録するのがよいです．
そのまま `CHECKPOINT-6.md` に貼れる形です．

````markdown
# CHECKPOINT-6
## Permission Control Before AI Avatar Action

### Status
**Completed**

### Date
2026-09-13

---

## 1. 目的

CHECKPOINT-5までに，

```text
Human Speech
↓
<Perception>
↓
<Context>
↓
Action Request
↓
<Action>
↓
Environment
↓
<Verification>
↓
<Experience>
````

という主要な情報処理経路を実装した．

しかし，CHECKPOINT-5までの実装では，
有効なAction Requestが生成されると，
AI_1はそのままActionを実行していた．

CHECKPOINT-6では，
Actionの実行前に独立した `<Permission>` を導入し，

> AI ActorがあるActionを実行できることと，
> そのActionの実行を許可されていることを分離する

ことを目的とする．

---

## 2. 達成条件

以下の2条件を確認する．

### Permissionが許可する場合

```text
Action Request
↓
<Permission>
↓
ALLOWED
↓
<Action>
↓
AI_1 Movement
```

AI_1が正常に移動すること．

### Permissionが拒否する場合

```text
Action Request
↓
<Permission>
↓
DENIED
↓
Actionを実行しない
```

同じAction Requestが存在していても，
AI_1が移動しないこと．

---

## 3. 基本概念

CHECKPOINT-6では，

```text
Capability ≠ Permission
```

という区別を実装する．

AI_1にはすでに，

```text
move
```

というActionを実行する機能が実装されている．

しかし，

```text
move能力が存在する
```

ことは，

```text
現在そのmoveを実行してよい
```

ことを意味しない．

このため，Actionの直前に
`PermissionChecker` を配置する．

---

## 4. 情報処理経路

CHECKPOINT-5まで：

```text
Action Request
↓
<Action>
↓
Environment
↓
<Verification>
↓
<Experience>
```

CHECKPOINT-6：

```text
Action Request
↓
<Permission>
↓
ALLOWED / DENIED
↓
<Action>
↓
Environment
↓
<Verification>
↓
<Experience>
```

PermissionがDENIEDの場合には，
Action以降へ進まない．

---

## 5. Permission GameObject

UnityのHierarchyに空のGameObjectを作成し，

```text
Permission
```

と命名した．

このGameObjectに，

```text
PermissionChecker.cs
```

をアタッチした．

これにより，
Permission判定をAction処理とは別の
Unity Componentとして実装した．

---

## 6. PermissionChecker.cs

CHECKPOINT-6では，
最小のPermission実装として
Inspectorから変更可能なBoolean値を使用した．

```csharp
using UnityEngine;

public class PermissionChecker : MonoBehaviour
{
    public bool allowMove = true;

    public bool IsAllowed(ActionRequest request)
    {
        if (request.action == "move")
        {
            return allowMove;
        }

        return false;
    }
}
```

---

## 7. Permission判定

`PermissionChecker` は，

```csharp
request.action
```

を確認する．

現在実装されている，

```text
move
```

に対しては，

```csharp
allowMove
```

の状態によってPermissionを決定する．

```text
allowMove = true
→ ALLOWED

allowMove = false
→ DENIED
```

それ以外のActionについては，
現在の最小実装では，

```text
DENIED
```

とする．

---

## 8. TcpSpeechReceiver.csとの接続

`TcpSpeechReceiver` に
`PermissionChecker` への参照を追加した．

```csharp
public PermissionChecker permissionChecker;
```

Actionを実行する直前に，
Permissionを問い合わせる．

```csharp
if (request.action == "move" &&
    request.reference == "Human_1" &&
    request.direction == "right")
{
    bool allowed = false;

    if (permissionChecker != null)
    {
        allowed = permissionChecker.IsAllowed(request);
    }

    if (allowed)
    {
        Debug.Log("Permission: ALLOWED");

        Vector3 targetPosition =
            humanTransform.position +
            humanTransform.right * moveDistance;

        aiTransform.position = targetPosition;

        Debug.Log("AI_1 moved to: " + targetPosition);

        if (actionVerifier != null)
        {
            actionVerifier.VerifyRightPosition(request);
        }
    }
    else
    {
        Debug.Log("Permission: DENIED");
    }
}
```

---

## 9. Inspector設定

Hierarchyの，

```text
SpeechReceiver
```

を選択し，

```text
Permission Checker
```

フィールドへHierarchy上の，

```text
Permission
```

GameObjectを割り当てた．

`Permission` GameObject側では，

```text
Allow Move
```

をInspectorからON / OFFできる．

---

## 10. ALLOWED試験

まず，

```text
Allow Move = ON
```

とした．

ユーザが，

> 私の右へ移動してください

と発話した．

処理経路：

```text
Speech
↓
Recognition
↓
Action Request
↓
PermissionChecker
↓
ALLOWED
↓
AI_1 Movement
↓
Verification
↓
Experience
```

Unity Consoleに，

```text
Permission: ALLOWED
AI_1 moved to: (...)
Verification: PASS  Error = ...
Experience saved: {...}
```

と表示され，
AI_1が移動したことを確認した．

---

## 11. DENIED試験

次に，

```text
Allow Move = OFF
```

とした．

同じく，

> 私の右へ移動してください

と発話した．

Unity Consoleに，

```text
Permission: DENIED
```

と表示され，
AI_1が移動しないことを確認した．

したがって，

```text
Action Requestが存在する
```

場合でも，

```text
Permission = DENIED
```

であればActionを実行しないことを確認した．

---

## 12. CHECKPOINT-6 判定

**達成**

CHECKPOINT-6では，

> Actionを実行する機能と，
> そのActionを実行する権限を分離し，
> `<Permission>` の判定結果によって
> `<Action>` の実行を制御する

最小実装を実現した．

---

## 13. CHECKPOINT-5からの進展

CHECKPOINT-5：

```text
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

CHECKPOINT-6：

```text
<Context>
↓
<Permission>
↓
ALLOWED / DENIED
↓
<Action>
↓
Environment
↓
<Verification>
↓
<Experience>
```

これにより，
Action Requestの生成とActionの実行との間に，
明示的なPermission判定が導入された．

---

## 14. サンドボックス・アーキテクチャ上の位置付け

AI-MRメタ身体圏サンドボックスでは，

```text
<Skill>
```

と，

```text
<Permission>
```

を異なる責務として扱う．

概念的には，

```text
<Skill>
= そのActionを実行する能力を持つか

<Permission>
= 現在そのActionを実行してよいか
```

という違いがある．

CHECKPOINT-6では，
`move` Actionそのものはすでに実装済みであり，
その実行可否を `PermissionChecker` が
独立して判断する構造を導入した．

これは，

```text
Capability ≠ Permission
```

という設計原則の最小実装である．

---

## 15. PermissionとActionの責務分離

Action側では，

```text
どこへ移動するか
どのように移動するか
```

を処理する．

Permission側では，

```text
その移動を実行してよいか
```

だけを判定する．

したがって，

```text
<Permission>
```

がActionの実装内容そのものを担当しない構造とした．

---

## 16. 現段階のPermission

現在のPermission判定は，

```text
allowMove = true / false
```

という単純なBoolean値である．

これは高度なPermission判断を実装することが目的ではなく，

> Permissionという責務をActionから分離し，
> SIPF上の独立した処理段階として実行可能であること

を確認するための最小実装である．

将来的には，

```text
ユーザ属性
AI Actor属性
対象物
空間領域
時刻
安全条件
実験条件
倫理条件
外部システム状態
```

等をPermission判定条件として利用できる．

---

## 17. 現段階の制約

現時点では，

* Permission対象は `move` のみ
* Permission条件はBoolean値のみ
* `<Skill>` は独立したComponentとして未実装
* `<Ethics>` は未実装
* Permission Ruleの外部設定は未実装
* ユーザごとのPermissionは未実装
* 空間領域によるPermissionは未実装
* Permission判定理由の構造化は未実装
* DENIED結果は現在Experienceへ保存していない
* AIR ManagerとのPermission連携は未実装

---

## 18. Experienceとの関係

現在，

```text
Permission = ALLOWED
```

の場合には，

```text
Action
↓
Verification
↓
Experience
```

へ進む．

一方，

```text
Permission = DENIED
```

の場合にはActionを実行しないため，
現在の実装では
`ExperienceLogger` への記録も行っていない．

将来的には，

```text
requested_action
permission_result
permission_reason
action_executed
```

等をExperience Recordへ追加し，

> 実行された経験だけでなく，
> 実行を拒否された判断もExperienceとして記録する

ことが可能である．

---

## 19. SIPF上の現在地

CHECKPOINT-6までに実働した主要経路は，

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
```

となった．

ただし，
9 Core Modulesすべてを実装したわけではなく，

```text
<Skill>
<Ethics>
```

については，
今後独立した責務として実装する必要がある．

---

## 20. 次の展開

CHECKPOINT-6以降では，

```text
<Skill>
<Ethics>
<Permission>
```

を段階的に分離することで，

第一論文で定義したSIPFに，
実装構造をさらに近づける．

また別の方向として，

```text
System Verification
+
Human Evaluation
↓
<Experience>
```

を実装し，
AI Actorの行為結果に対する
人間からの評価をExperienceへ統合する．

````

これを保存したら，今回のチェックインは次の3コマンドでよいです．

```bash
git add CHECKPOINT-6.md
git commit -m "Checkpoint 6: Permission control before AI avatar action"
git push
````

なお，**`PermissionChecker.cs` と `TcpSpeechReceiver.cs` の変更も今回まだコミットしていない**のであれば，`CHECKPOINT-6.md` だけではなくコードも一緒にstageする方がCheckpointとして完全です．その場合は `git add .` → commit → push でよいです．

これでGitHub上でも，**CP5＝Experienceまで到達，CP6＝PermissionによるAction抑止を導入**という研究の積み上がりがかなり明瞭になります．
