もちろんです．**CP10で実現したヘッドトラッキングはまだ含めず，CP9終了時点の状態**として再掲します．そのまま `CHECKPOINT-9.md` に保存できる形です．

```markdown
# CHECKPOINT-9
# MREAL × AI-MR Sandbox Integration

## 1. Purpose

CHECKPOINT-9では，
CHECKPOINT-8までに構築したAI-MR Sandbox Runtimeを，
Canon MREAL用Unity Templateへ導入し，
MR EnvironmentとSandbox Runtimeを統合する．

本Checkpointの主要目的は，

```text
MREAL
+
Sandbox Runtime
+
Core Contents
+
Debug Tools
```

を一つのUnity Scene上で結合し，

```text
Human Speech
↓
Sandbox Runtime
↓
AIR Manager
↓
AI Actor Action
↓
Verification
↓
Human Evaluation
↓
Experience
```

までのHuman-AI Interaction Loopを，
MREAL環境上でEnd-to-Endに動作させることである．

CHECKPOINT-8ではSandbox Runtimeそのものを成立させた．

CHECKPOINT-9では，
Sandbox RuntimeをMR Environmentへ接続し，
AIとMRを統合した実行環境を成立させる．

---

# 2. Basic Implementation Policy

本Checkpointでは，
Sandbox RuntimeとScene固有要素を分離し，
再利用可能なUnity Componentとして構成する．

基本構成は以下とする．

```text
MREAL Template
│
├─ MREAL / XR Environment
│
├─ SandboxRuntime
│
├─ CoreContents
│
└─ DebugTools
```

各Componentの責務を以下のように分離する．

```text
MREAL Template
= MR表示・Tracking・Device依存環境

SandboxRuntime
= Human-AI Interaction Runtime

CoreContents
= 最小のEnvironmentおよびEntity

DebugTools
= 開発・確認・デバッグ支援
```

この分離によって，
Sandbox Runtimeそのものを変更せずに，
異なるUnity / XR Environmentへ導入できる構造を目指す．

---

# 3. SandboxRuntime Prefab

CHECKPOINT-8で構築したSandbox Runtimeを，
一つのPrefabとして整理した．

構成：

```text
SandboxRuntime
├─ SpeechReceiver
├─ Permission
├─ Verification
├─ HumanEvaluation
├─ Experience
└─ AIRSender
```

各Componentは
`SandboxRuntime` 直下の兄弟Nodeとして配置する．

Hierarchyは所有・構成関係を示し，
処理上の依存関係はComponent Referenceによって定義する．

主な参照関係：

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
= 所有・構成関係

Reference
= 処理・依存関係

Protocol
= 情報授受の意味・条件・規則
```

として区別する．

---

# 4. SandboxRuntime Package

`SandboxRuntime.prefab` を単独で再利用可能にするため，

```text
SandboxRuntime.unitypackage
```

としてExportした．

Export時には，

```text
Include dependencies = ON
Include all scripts   = OFF
```

とした．

これにより，
Sandbox Runtimeが直接依存するPrefabおよびScriptのみを
可能な限り切り出す．

`SandboxRuntime.unitypackage` は
Sandbox Runtime単体を再利用するための
最小Packageとして保持する．

---

# 5. CoreContents Prefab

Sandbox Runtimeとは別に，
最小限の試験用ContentsをPrefab化した．

本Prefabは，
将来作成する実験・体験固有のContentsと区別するため，

```text
CoreContents.prefab
```

と命名した．

構成例：

```text
CoreContents
├─ Environment
│   ├─ Floor
│   ├─ Directional Light
│   └─ Scene Objects
│
└─ Entities
    ├─ Human_1
    └─ AI_1
```

`CoreContents` は，
Sandbox Runtimeの動作確認に必要な
最小EnvironmentとEntityを提供する．

`Directional Light` は
SceneのEnvironmentを構成する要素として
`Environment` 内に配置する．

---

# 6. DebugTools Prefab

Sandbox RuntimeおよびContents本体とは別に，
開発・動作確認に必要な機能を
`DebugTools.prefab` としてまとめた．

構成：

```text
DebugTools
├─ DebugCanvas
│   └─ SpeechText
│
└─ EscQuit
    └─ EscQuit.cs
```

`DebugCanvas` は，
音声認識結果等を画面表示するために使用する．

`EscQuit.cs` は，
BuildしたStandalone Applicationを
ESC Keyで終了するための補助機能である．

実装例：

```csharp
using UnityEngine;

public class EscQuit : MonoBehaviour
{
    void Update()
    {
        if (Input.GetKeyDown(KeyCode.Escape))
        {
            Application.Quit();
        }
    }
}
```

`Application.Quit()` は
Unity Editor上ではなく，
BuildされたApplication上で動作確認した．

DebugToolsはSandbox Runtime本体の機能ではなく，
開発・確認用の補助機能として分離する．

Unity標準の`EventSystem`は，
MREAL Template等のScene側に存在する可能性があるため，
DebugTools Prefabには含めない．

---

# 7. SandboxDev Package

MREAL TemplateへSandbox開発環境をまとめて導入するため，

```text
SandboxDev.unitypackage
```

を作成した．

構成：

```text
SandboxDev.unitypackage
├─ SandboxRuntime.prefab
├─ DebugTools.prefab
└─ CoreContents.prefab
```

役割：

```text
SandboxRuntime.prefab
= Human-AI Interaction Runtime

DebugTools.prefab
= 開発・確認支援

CoreContents.prefab
= 最小のEnvironment / Entity
```

これにより，
MREAL Template側でSandboxを一から構築する必要をなくし，
Package Importによって再利用できる構成とした．

---

# 8. MREAL Template

CHECKPOINT-9では，
2026年10月2日に作成した
MREAL Unity Templateを使用した．

このTemplateには，
MREAL Environmentに加えて，
3D Systems HapticsDirectを用いた
Haptic Device連携用の基本構成が組み込まれている．

したがって，
本Templateは将来的に，

```text
MR
+
AI
+
Haptics
+
External Tracking
```

を統合するための基盤として利用できる．

CHECKPOINT-9では，
まずMREALとSandbox Runtimeの結合を優先する．

---

# 9. Import SandboxDev into MREAL Template

MREAL Templateを開き，

```text
SandboxDev.unitypackage
```

をImportした．

Import後，
MREAL Template側の既存構造は変更せず，
Sandbox側のAssetを追加する．

Import時，
3D Systems HapticsDirect側から以下のWarningが表示された．

```text
Assets\3DSystems\HapticsDirect\HapticScripts\HapticPlugin.cs(125,18):
warning CS0414:
フィールド 'HapticPlugin.enablef' が割り当てられていますが、
値は使用されていません
```

これはHapticsDirect既存Script由来のWarningであり，
SandboxDev側のCompile Errorではない．

Vendor PackageのScriptは変更せず，
Consoleに赤色のCompile Errorがないことを確認して
作業を継続した．

---

# 10. Prefab Placement in MREAL Scene

Package Import後，
以下の3つのPrefabを
MREAL SceneのHierarchyへ配置した．

```text
MREAL Scene
├─ MREAL / XR Components
│
├─ SandboxRuntime
│
├─ CoreContents
│
└─ DebugTools
```

各Prefabの内部構成：

```text
SandboxRuntime
├─ SpeechReceiver
├─ Permission
├─ Verification
├─ HumanEvaluation
├─ Experience
└─ AIRSender
```

```text
CoreContents
├─ Environment
└─ Entities
    ├─ Human_1
    └─ AI_1
```

```text
DebugTools
├─ DebugCanvas
│   └─ SpeechText
└─ EscQuit
```

MREAL側既存GameObjectは，
この段階では可能な限り変更しない．

---

# 11. External Reference Reconnection

Prefab内部Referenceは保持したまま，
Scene依存Referenceを
MREAL Scene上で再接続した．

代表例：

```text
SpeechReceiver
 ├─ Human Transform
 │      → CoreContents / Entities / Human_1
 │
 ├─ AI Transform
 │      → CoreContents / Entities / AI_1
 │
 └─ Speech Text
        → DebugTools / DebugCanvas / SpeechText
```

同様に，

```text
AIRSender
Verification
HumanEvaluation
```

等についても，
必要なScene外部Referenceを接続する．

この方式によって，

```text
Prefab内部
= 再利用可能なRuntime Logic

Scene側
= Environment固有Reference
```

という分離を維持する．

---

# 12. End-to-End Test

MREAL Template上で，
Sandbox Runtimeを導入した状態で
End-to-End動作を確認した．

現在の処理経路：

```text
Human Speech
↓
Python / faster-whisper
↓
SpeechReceiver
↓
Action Request
↓
Permission
↓
Human_1 State
↓
AIRSender
↓
C++ AIR Manager
↓
Body-Centered Spatial Mapping
↓
Target Position
↓
Unity / MREAL Scene
↓
AI_1 Movement
↓
Verification
↓
Human Evaluation
↓
Experience
↓
experience.jsonl
```

これにより，
CHECKPOINT-8で成立したSandbox Runtimeが，
MREAL Template上でも
End-to-Endに動作することを確認した．

---

# 13. Current Limitation: Human Reference

CHECKPOINT-9終了時点では，
`Human_1` はCoreContents内の
固定またはProxy Entityとして使用している．

したがって，

```text
Human_1
↓
AIR Manager
↓
right / left / forward
```

という相対移動は動作するが，
MREALで実際にHead TrackingされているUserに対して
リアルタイムに相対移動する構成には
まだ接続していない．

次Checkpointでは，

```text
MREAL Head Tracking
↓
Human_1 Position / Orientation
↓
AIR
↓
AI_1 Target Position
```

へ接続する．

これはSandbox Architectureそのものの変更ではなく，
Human EntityのPosition / Orientation入力元を
MREAL Trackingへ接続する実装修正として扱う．

---

# 14. MREAL Coordinate Reference Marker

MREALでは，
VICON等の外部Motion Capture Systemを使用しなくても，
基準座標系マーカを用いて
MR空間の基準座標系を構成できる．

したがって，
VICONなしの状態でも，

```text
MREAL基準座標系マーカ
↓
MREAL / Unity Coordinate System
↓
Human / AI / Contents
↓
Sandbox Runtime
↓
AIR
```

という空間的対応を試験できる．

このため，
VICONはAI-MR Sandboxを成立させるための必須要素ではなく，
外部からより高精度な身体計測を追加する
拡張Systemとして位置づけることができる．

基本構成：

```text
MREAL
+
Sandbox
```

拡張構成：

```text
MREAL
+
Sandbox
+
VICON
```

---

# 15. Planned Physical-space Connection

次Checkpointでは，
MREALのHead Trackingを
Human_1へ接続する．

第一段階では，
MREAL基準座標系マーカによるTrackingを使用する．

```text
MREAL Marker Tracking
↓
MREAL Head Tracking
↓
Human_1
↓
SandboxRuntime
↓
AIR Manager
↓
AI_1
```

第二段階では，
Tracking SourceをVICONへ切り替える．

```text
VICON
↓
MREAL Head Tracking
↓
Human_1
↓
SandboxRuntime
↓
AIR Manager
↓
AI_1
```

MREAL側では両Tracking方式が統合されているため，
Sandbox Runtime側では同一のHead Pose Interfaceを
利用できることが期待される．

---

# 16. Role of Haptics

今回使用したMREAL Templateには，
HapticsDirectによる
Haptic Device用基本構成が含まれている．

CHECKPOINT-9では
HapticsそのものをSandbox Runtimeへ統合することを
主要目的とはしない．

しかし将来的には，

```text
MREAL
= 視覚・MR空間

Haptics
= 物理的作用・触覚

VICON
= 外部身体計測

Sandbox
= Human-AI Interaction

AIR
= 意味的・空間的中間表現
```

という統合構成へ展開できる．

---

# 17. Unity Content Development Guideline

CHECKPOINT-9を通して，
AI-MR Sandbox Projectにおける
Unity Content Developmentの基本構造を整理した．

```text
Device / XR Environment
        ↕
CoreContents
        ↕
SandboxRuntime
        ↕
External Runtime
```

さらに開発支援機能を，

```text
DebugTools
```

として独立させる．

基本原則：

> Scene固有のEnvironmentおよびEntityと，
> Human-AI Interactionを実行するSandbox Runtimeを分離する．
> 両者は最小限のReferenceおよびProtocolによって接続する．

これにより，

```text
MREAL
Meta Quest
XV Arena
VICON-linked Environment
Desktop Unity Scene
```

等へ，
同一Sandbox Runtimeを再利用できる構造を目指す．

---

# 18. CHECKPOINT-9 Achievement

CHECKPOINT-9では，

```text
Sandbox Prototype
↓
Sandbox Prefab
↓
Sandbox Package
↓
MREAL Template Import
↓
MR Environment Integration
↓
End-to-End Operation
```

までを実現した．

特に，

```text
SandboxRuntime.prefab
CoreContents.prefab
DebugTools.prefab
```

という三つの再利用単位を定義し，

```text
SandboxDev.unitypackage
```

としてMREAL Templateへ導入した．

その結果，
Sandbox Runtimeを
MR Environment固有実装から分離した状態で，
MREAL上へ導入できることを確認した．

---

# 19. Significance

CHECKPOINT-8までの実装では，
Human-AI Interaction Loopと
独立AIR Managerが成立していた．

CHECKPOINT-9では，
そのSandbox Runtimeを
実際のMR PlatformであるMREALへ導入した．

したがって本Checkpointは，

> AI側のSandbox Architectureと，
> MR側の実行Environmentが
> 初めて一つのEnd-to-End Systemとして接続された段階

と位置づけることができる．

これにより，

```text
AI
+
MR
```

が結合された
AI-MR Meta Body Sphere Sandboxの
最小実装基盤が成立した．

次段階では，

```text
MREAL Head Tracking
↓
Human Entity

MREAL Coordinate Reference Marker
↓
Spatial Reference

VICON
↓
External Body Measurement

Haptics
↓
Physical Interaction
```

を段階的に接続することで，
Sandboxを実空間・身体・物理的作用へ拡張する．

---

# 20. CHECKPOINT-9 Status

```text
SandboxRuntime Prefab        DONE
CoreContents Prefab          DONE
DebugTools Prefab            DONE
SandboxRuntime.unitypackage  DONE
SandboxDev.unitypackage      DONE
MREAL Template Import        DONE
Prefab Placement             DONE
Reference Reconnection       DONE
End-to-End Runtime Test      DONE

MREAL Head Tracking Link     NEXT
MREAL Marker Spatial Test    NEXT
VICON Integration            PENDING
Haptics Integration          FUTURE
```

CHECKPOINT-9の基本統合は成立した．

次段階では，
MREAL Head Trackingおよび
実空間座標との接続を進める．
```

この版なら，**CP9の終了地点と，その後CP10で実際に達成した内容が混ざりません**．

流れとしても，

**CP8：Sandboxを成立させる  
→ CP9：SandboxをMREALへ導入してAI＋MRを成立させる  
→ CP10：実空間のHumanを接続する**

と，非常に明瞭になっています．