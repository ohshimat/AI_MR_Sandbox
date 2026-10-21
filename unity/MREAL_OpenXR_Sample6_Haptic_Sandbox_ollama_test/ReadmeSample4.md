# MREAL Unity Sample 4 — HapticsDirect 統合

## 目的

MREAL + Unity + OpenXR 環境に、3D Systems Touch を用いたハプティック機能を追加する。

Sample 4 では、まず **HapticsDirect for Unity V1** を既存の MREAL Unity プロジェクトへ導入し、
Touch 用 Haptic Actor を Scene に配置するところまでを行う。

最終的には、MREAL 上の仮想オブジェクトに対して、
Touch デバイスによる触覚・力覚フィードバックを付加することを目標とする。

---

## 前提

- MREAL Platform 2025
- Unity + OpenXR
- URP (Universal Render Pipeline)
- HapticsDirect for Unity V1
- 3D Systems Touch
- Windows 環境

Sample 1〜3 までで、MREAL + Unity + OpenXR の基本動作、
Hand Tracking、Target Tracking 等の検証を進めている。

Sample 4 では、これに Haptics を追加する。

---

## Step 0 — HapticsDirect for Unity V1 の導入

Unity Asset Store から **HapticsDirect for Unity V1** を入手し、
My Assets に登録した。

Unity Editor の Package Manager から対象プロジェクトへインポートした。

---

## Step 1 — Project Settings の設定

HapticsDirect のマニュアルに従い、以下を設定した。

### Player

`Edit > Project Settings > Player`

#### Api Compatibility Level

```text
.NET Framework
```

に設定。

### Physics

`Edit > Project Settings > Physics`

以下を設定。

#### Enable Adaptive Force

```text
ON
```

#### Default Contact Offset

```text
0.001
```

#### Default Solver Iterations

```text
12
```

#### Default Solver Velocity Iterations

```text
2
```

ここまでで、HapticsDirect プラグイン導入後の基本的な Project Settings は完了。

---

## Step 2 — TouchActor Prefab を Scene に配置

Project ウィンドウから、HapticsDirect の Prefabs フォルダを開く。

使用デバイスは **3D Systems Touch** のため、
Touch 用の Prefab を Scene に配置した。

今回配置した Prefab：

```text
TouchActor
```

TouchActor Prefab には、Haptic Actor に加えて、
Virtual Stylus / On Screen Stylus 等の構成が含まれている。

---

## Step 3 — TouchActor の Device Setup を確認

Hierarchy で `TouchActor` を選択し、
Inspector の Haptic Plugin / Device Setup を確認。

以下の設定になっていることを確認した。

### Device Identifier

```text
Default Device
```

### Connect On Start

```text
ON
```

実機側で作成した Device Configuration 名と
Device Identifier は一致している必要がある。

今回はデフォルト設定の `Default Device` を使用する。

---

## Step 4 — 実機なしで Scene 起動確認

この時点では、3D Systems Touch 実機は実験室にあり、
作業場所には無いため、実機接続確認は未実施。

Unity の Play Mode を起動すると、
Touch デバイスの CG モデル自体は表示された。

したがって、

```text
HapticsDirect Plugin
    ↓
TouchActor Prefab
    ↓
Unity Scene
```

までの導入は確認できた。

---

## Step 5 — Touch CG モデルのマゼンタ表示への対応

Play Mode で Touch デバイスの CG モデルが表示されたが、
モデル全体が陰影のないマゼンタ色で表示された。

Unity でマゼンタ表示になる場合、
Material が現在の Render Pipeline に対応していない可能性が高い。

Touch モデルの Material を確認したところ、
Shader が以下になっていた。

```text
Standard
```

現在の MREAL Unity Sample 4 は URP を使用しているため、
Built-in Render Pipeline 用の Standard Shader と互換性がなく、
マゼンタ表示になっていたと判断した。

対応として、Touch モデルの Material の Shader を

```text
Universal Render Pipeline/Lit
```

へ変更する。

複数の Material が使用されている場合は、
マゼンタ表示となっている Material を同様に確認・変更する。

※ プロジェクト全体を一括変換するのではなく、
まず TouchActor に関連する Material のみを個別に変更する。

---

## Step 6 — Haptic Collider と Haptic Material の確認

`TouchActor` Prefab の子オブジェクトを確認したところ、
Virtual Stylus 側にはすでに `Haptic Collider` コンポーネントが設定済みであることを確認した。

そのため、Haptic Collider は新規に作成せず、Prefab に含まれる設定をそのまま使用する。

触覚確認用オブジェクトとして、既存の Cube ではなく **Sphere** を使用する。

Sphere には作成時点で `Sphere Collider` が付いているため、以下を追加した。

1. `Rigidbody`
2. `Haptic Material` (`HapticMaterial.cs`)

### Sphere の Haptic Material 初期設定

現時点では以下の値を使用する。

```text
Stiffness         = 0.2
Damping           = 0
Static Friction   = 0
Dynamic Friction  = 0
```

この設定では、

- `Stiffness = 0.2`：触覚効果は有効
- `Damping = 0`：減衰なし
- `Static Friction = 0`：静止摩擦なし
- `Dynamic Friction = 0`：動摩擦なし

となる。

Sample 4 の最初の実機確認では、材質感を複雑に作り込まず、
**Sphere に接触したときに基本的な反力が得られるか**を確認するため、
まずこの単純な設定のまま使用する。

実機で動作確認した後、必要に応じて Stiffness / Damping / Friction を変更し、
材質感の違いを評価する。

---

## 現在地

現時点で完了している内容：

- HapticsDirect for Unity V1 のインポート
- HapticsDirect 用 Project Settings
- TouchActor Prefab の Scene 配置
- Device Identifier = `Default Device`
- Connect On Start = ON
- 実機なしで Touch CG モデルの表示を確認
- Standard Shader と URP の不一致を確認
- URP/Lit へ変更する方針を確認
- TouchActor 内に Haptic Collider が設定済みであることを確認
- Sphere に Rigidbody を追加
- Sphere に Haptic Material を追加
- Sphere の Haptic Material 初期値を確認
  - Stiffness = 0.2
  - Damping = 0
  - Static Friction = 0
  - Dynamic Friction = 0

---

## 未着手

以下はまだ実施していない。

- Touch 実機との接続確認
- Virtual Stylus の実機追従確認
- Sphere への触覚フィードバック実機確認
- MREAL 空間と Haptics workspace の座標整合
- OpenXR / MREAL と Haptics の同時動作確認

---

## 次の Step

次は実験室で Touch 実機を接続し、

```text
Touch Device
      ↓
TouchActor / Virtual Stylus
      ↓
Haptic Collider
      ↓
Sphere + Haptic Material
```

という最小構成で実機動作を確認する。

目標は、

> Touch デバイスのスタイラスで Unity 上の Sphere に接触したとき、
> 力覚・触覚フィードバックを得る。

こと。

その後、

```text
MREAL / OpenXR
      +
Unity
      +
HapticsDirect
      +
3D Systems Touch
```

を統合し、MREAL の MR 空間内で視覚提示とハプティック提示を同時に成立させる。

---

## 備考

Sample 1〜3 までは Canon の MREAL / OpenXR 関連マニュアルを主に参照した。

Sample 4 は、
MREAL + Unity + OpenXR に HapticsDirect を追加する統合検証であり、
Canon の MREAL チュートリアルの範囲を超えるため、
本 README を作業記録および引き継ぎ資料として使用する。
