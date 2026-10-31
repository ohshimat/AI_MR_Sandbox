はい．**CP10の中核である「実ユーザの頭部位置・姿勢をSandboxへ接続する」ことは成立しました．**  
ただし，VICON切替の実機確認はまだなので，ドキュメントでは **Stage 1完了，Stage 2は同一インタフェースでの確認待ち** としておくのが正確です．

以下を `CHECKPOINT-10.md` 案とします．

```markdown
# CHECKPOINT-10
# Connection to Physical Space
## MREAL Head Tracking Integration

## 1. Purpose

CHECKPOINT-10では，
CHECKPOINT-9でMREALと統合したAI-MR Sandboxを，
実空間内のユーザの位置・姿勢へ接続する．

CHECKPOINT-9までのHuman_1は，
CoreContents内の固定Proxy Entityであった．

CHECKPOINT-10では，
MREALによってTrackingされる実ユーザのHead Poseを
Human_1へ反映し，

```text
Physical Human
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

という実空間接続を成立させる．

---

# 2. Tracking Architecture

MREALでは，
以下の二種類のTracking方式を利用できる．

```text
1. MREAL Marker Tracking
2. VICON Tracking
```

両方式はMREAL側で統合されており，
Tracking Sourceを切り替えて利用できる．

Sandbox側ではTracking方式そのものを参照せず，
MREALがUnityへ提供するHead Transformを参照する．

したがって基本構造は，

```text
Marker Tracking
      │
      ├──→ MREAL Head Tracking
      │
VICON Tracking
      │
      └──→ MREAL Head Tracking
                    ↓
             Main Camera Transform
                    ↓
                 Human_1
                    ↓
              SandboxRuntime
```

となる．

この構造により，
Marker TrackingとVICON Trackingを切り替えても，
Sandbox側のProgram変更を必要としないことを目指す．

---

# 3. MREAL Head Tracking Object

MREAL TemplateのHierarchyを調査した結果，
Head TrackingされるCameraを以下に確認した．

```text
main
└─ XR Interaction Hands Setup
    └─ XR Origin
        └─ Camera Offset
            └─ Main Camera
```

Play ModeでMREALを使用し，
頭部を移動・回転させたところ，

```text
Main Camera
├─ Position
└─ Rotation
```

が実際の頭部運動に追従することを確認した．

したがって，

```text
Main Camera Transform
```

をSandboxにおける
実ユーザHead Poseの入力点として採用した．

---

# 4. Human Entity Tracking

`Human_1` はMain Cameraの子Objectとはせず，
Sandbox側の独立Entityとして維持する．

Main CameraのTransformを追従するため，

```text
HeadTrackingFollower.cs
```

をHuman_1へ追加した．

実装例：

```csharp
using UnityEngine;

public class HeadTrackingFollower : MonoBehaviour
{
    public Transform headTransform;

    void LateUpdate()
    {
        if (headTransform == null)
            return;

        transform.position = headTransform.position;

        float yaw = headTransform.eulerAngles.y;
        transform.rotation = Quaternion.Euler(0f, yaw, 0f);
    }
}
```

Inspectorでは，

```text
Human_1
└─ HeadTrackingFollower
     └─ Head Transform
          → Main Camera
```

として接続する．

---

# 5. Yaw-only Orientation

Human_1のRotationには，
Main CameraのRotation全体をコピーせず，
Y軸回転（Yaw）のみを使用する．

```text
Head Pitch / Roll
     ↓
Human_1には反映しない

Head Yaw
     ↓
Human_1 Orientation
```

これは，
AIR Managerで扱う

```text
right
left
forward
```

を水平面上の身体基準方向として
安定して利用するためである．

---

# 6. Marker Tracking Test

MREALのMarker Trackingを使用し，
Head TrackingによるHuman_1追従を確認した．

動作経路：

```text
MREAL基準座標系マーカ
↓
MREAL Tracking
↓
Main Camera
↓
HeadTrackingFollower
↓
Human_1 Position / Yaw
↓
AIRSender
↓
AIR Manager
↓
AI_1
```

実際にユーザが頭部を移動・回転すると，
Human_1がそのPositionおよびYawへ追従することを確認した．

これにより，
固定ProxyであったHuman_1を，
実空間のユーザ位置・姿勢へ接続することができた．

---

# 7. Sandbox Integration

既存のSandboxRuntime側では，
AIRSenderがHuman_1のTransformを参照している．

そのため，
Human_1の入力元をMain Camera Trackingへ変更するだけで，

```text
Physical Human
↓
MREAL Head Tracking
↓
Human_1
↓
AIRSender
↓
AIR Manager
↓
Body-Centered Spatial Mapping
↓
AI_1 Target Position
```

という処理へ移行できた．

AIR Managerおよび既存のSandbox Runtimeについて，
基本的なArchitecture変更は必要なかった．

---

# 8. Significance

CHECKPOINT-9では，

```text
AI
+
MR Environment
```

をEnd-to-Endで接続した．

CHECKPOINT-10では，
さらに，

```text
Physical Human
+
MR Environment
+
AI Sandbox
```

を接続した．

これにより，
Humanの実空間におけるPosition / Orientationを基準として，
AI Actorの空間的Actionを計算する構成が成立した．

すなわち，

```text
実空間
↓
MR
↓
AIR
↓
AI
```

というAI-MR Meta Body Sphere Sandboxの
基本的な空間接続経路が成立した．

---

# 9. Tracking-source Independence

本実装の重要な特徴は，
Sandbox RuntimeがTracking Sourceそのものに
依存しないことである．

Sandboxが参照するのは，

```text
Main Camera Transform
```

のみである．

MREAL側で，

```text
Marker Tracking
↕
VICON Tracking
```

を切り替えても，
MREALが同一のHead Pose Interfaceを提供する限り，
Sandbox側のScript変更は不要である．

これは，

```text
Tracking implementation
≠
Sandbox logic
```

という責務分離を実現する．

---

# 10. VICON Tracking

次段階では，
MREAL側のTracking Sourceを
Marker TrackingからVICON Trackingへ切り替える．

想定経路：

```text
VICON
↓
MREAL Tracking
↓
Main Camera Transform
↓
Human_1
↓
SandboxRuntime
↓
AIR Manager
↓
AI_1
```

Sandbox側のProgramは変更せず，
同じHeadTrackingFollowerおよびRuntimeを使用する．

VICON環境で，
Marker Tracking時と同一のSandbox動作が得られることを
確認する予定である．

---

# 11. CHECKPOINT-10 Achievement

CHECKPOINT-10では，

```text
MREAL Head Tracking
↓
Main Camera
↓
Human_1
↓
SandboxRuntime
↓
AIR Manager
```

という実空間接続を実装した．

Marker Tracking環境において，
Human_1が実ユーザの頭部PositionおよびYawへ
追従することを確認した．

これにより，
固定Proxy Entityを用いたSandboxから，
実ユーザの身体位置を基準とする
AI-MR Sandboxへ移行した．

---

# 12. Current Status

```text
MREAL Main Camera identification        DONE
Head Transform tracking confirmation   DONE
HeadTrackingFollower implementation    DONE
Human_1 position tracking              DONE
Human_1 yaw tracking                   DONE
Marker Tracking integration            DONE

VICON Tracking switching test          PENDING
VICON environment validation           PENDING
```

CHECKPOINT-10の中核となる
実空間Head Tracking接続は成立した．

VICONについては，
同一のMREAL Head Tracking Interfaceを使用した
Tracking Source切替の実機確認を残す．
```

今回のCP10で重要なのは，**新しい大規模機能を追加したというより，CP8・CP9で意図的に分離してきた構造が実際に効いた**ことです．

つまり，

```text
CP8  Sandboxを作る
CP9  MRへSandboxを入れる
CP10 実空間のHumanをSandboxへ入れる
```

と，非常にきれいにつながりました．

特に **MREAL側でMarker/VICONを吸収し，Sandboxは `Main Camera Transform` だけを見ればよい**という点は，第二論文の実装設計上かなり重要な成果になると思います．