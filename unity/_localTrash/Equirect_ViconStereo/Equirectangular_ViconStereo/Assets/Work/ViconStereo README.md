# ViconStereo / Equirectangular Capture System

Unity上で、VICON Trackerから取得した頭部の位置・回転を用いて、左右眼位置からリアルタイムにEquirectangular形式の360°映像を生成する研究用システム。

Mono出力およびSide-by-Side Stereo出力に対応する。

---

## 1. 基準開発環境

- Unity: 2020.3.62f3
- Vicon Unity Plugin: VIcon_Unity_Plugin-1.3.1.131291h
- VICON DataStream Port: 801
- Windows環境で使用
- Unity 6000系でもVicon Unity Plugin 1.3.1の動作実績あり
  - CVIC環境では別途「互換性」を確認すること

---

## 2. 基本構成

### Mono

`CaptureMono`

UnityシーンからMono Equirectangular映像をリアルタイム生成する。

内部スクリプト:

`EquirectMono.cs`

出力:

`EquirectRT`

基本解像度:

`4096 x 2048`

---

### Stereo

`CaptureStereo`

左右眼位置から2系統のEquirectangular映像を生成し、Side-by-Side形式に結合する。

基本構造:

```text
CaptureStereo
├─ Head
│  ├─ LeftEye
│  └─ RightEye
└─ CaptureCamera
   └─ Equirect Stereo (Script)
```

内部スクリプト:

`EquirectStereo.cs`

出力:

- `EquirectRT_Left`
- `EquirectRT_Right`
- `EquirectRT_SBS`

基本解像度:

- Left: 4096 x 2048
- Right: 4096 x 2048
- SBS: 8192 x 2048

---

## 3. Head座標系

`Head` は頭部の「ローカル座標系」を表す。

標準の左右眼位置:

```text
LeftEye
Position = (-0.032, 0, 0)

RightEye
Position = (+0.032, 0, 0)
```

これはIPD 64 mmを仮定した設定。

`Head` の位置・回転を変更すると、`LeftEye` / `RightEye` の「ワールド位置」が変化する。

重要:

`Head` の回転は左右眼位置の計算に使用するが、Equirectangular映像の方位そのものはワールド座標に固定する。

したがって、

- 頭部が移動 → 左右眼の撮影位置が移動
- 頭部が回転 → 左右眼の位置関係が回転
- バーチャル世界 → 絶対座標に固定
- Equirectangular映像の東西南北 → 固定

という設計になっている。

---

## 4. EquirectStereo.cs の基本処理

左右眼それぞれの「ワールド位置」に `CaptureCamera` を移動して360° Cubemapを生成する。

Cubemapの6面すべてを描画するため、

```csharp
0x3F
```

を「ビットマスク」として使用する。

`0x3F = 00111111b = 63`

左右眼の撮影にはUnity内部の `stereoSeparation` を使用せず、`LeftEye` / `RightEye` のTransformを直接使用する。

そのため、研究用途で任意の頭部座標系やモーションキャプチャ座標系と接続しやすい。

---

## 5. VICON接続

VICON対応版では以下の構成を使用する。

```text
ViconStereo
├─ ViconDataStreamPrefab
├─ ViconHead
│  └─ CaptureStereo
│     ├─ Head
│     │  ├─ LeftEye
│     │  └─ RightEye
│     └─ CaptureCamera
└─ EquirectStereoDisplay
```

役割:

- `ViconDataStreamPrefab`
  - VICON DataStreamとの「通信」

- `ViconHead`
  - VICON Trackerで定義した剛体Objectの位置・回転を受ける

- `CaptureStereo`
  - 左右眼位置からStereo Equirectangular映像を生成する

- `EquirectStereoDisplay`
  - SBS映像をGame画面に表示する

---

## 6. VICON設定

`ViconDataStreamPrefab` の設定:

```text
Host Name = VICON Tracker PC のIPアドレス
Port      = 801
```

Host Nameは使用場所のネットワーク環境に応じて設定する。

`ViconHead` には `RBScript` を使用する。

`RBScript` の設定:

```text
Client      = ViconDataStreamPrefab
Object Name = VICON Tracker側で定義したObject名
```

`Object Name` はVICON Tracker側とUnity側で完全に一致させる。

---

## 7. VICON座標とStereo Captureの関係

VICONから取得したTransformは `ViconHead` に適用する。

```text
VICON Tracker
      ↓
ViconDataStreamPrefab
      ↓
RBScript
      ↓
ViconHead
      ↓
CaptureStereo
      ↓
Head
├─ LeftEye
└─ RightEye
      ↓
Stereo Equirectangular
```

`CaptureStereo` の「ローカル座標」は原則として以下とする。

```text
Position = (0, 0, 0)
Rotation = (0, 0, 0)
Scale    = (1, 1, 1)
```

これにより `ViconHead` と頭部座標系を一致させる。

---

## 8. 表示用Prefab

### EquirectDisplay

Mono表示用。

`Raw Image` の Texture:

`EquirectRT`

推奨Game View「アスペクト比」:

`2:1`

---

### EquirectStereoDisplay

Side-by-Side Stereo表示用。

`Raw Image` の Texture:

`EquirectRT_SBS`

推奨Game View「アスペクト比」:

`4:1`

---

## 9. フルスクリーン

Windows Buildでは、

`Project Settings → Player → Resolution and Presentation`

の `Fullscreen Mode` を

`Fullscreen Window`

に設定する。

注意:

Player SettingsはPrefabの「依存関係」としてunitypackageに含まれない場合があるため、移植後に確認すること。

---

## 10. アプリ終了

`EscapeQuit.cs` を使用。

Windows Buildしたアプリでは、

`Esc`

キーで終了する。

Unity Editor内のPlayでは `Application.Quit()` による終了は通常行われない。

---

## 11. Workフォルダ

自作リソースは原則として `Assets/Work` 以下で管理する。

例:

```text
Assets
└─ Work
   ├─ Prefabs
   │  ├─ CaptureMono
   │  ├─ CaptureStereo
   │  ├─ EquirectDisplay
   │  ├─ EquirectStereoDisplay
   │  └─ ViconStereo
   │
   ├─ Scripts
   │  ├─ EquirectMono.cs
   │  ├─ EquirectStereo.cs
   │  └─ EscapeQuit.cs
   │
   ├─ RenderTextures
   │  ├─ CubeRT
   │  ├─ CubeRT_Left
   │  ├─ CubeRT_Right
   │  ├─ EquirectRT
   │  ├─ EquirectRT_Left
   │  ├─ EquirectRT_Right
   │  └─ EquirectRT_SBS
   │
   └─ README.md
```

---

## 12. 研究用パッケージ作成

研究用・引き継ぎ用では、「再現性」を優先し、必要なVICON Pluginも含めたワンパックとして保存する。

基本手順:

1. `Work` フォルダを選択
2. VICON Plugin関連フォルダも選択
3. アセット → パッケージをエクスポート…
4. 依存関係を含める を有効
5. `.unitypackage` として保存

推奨ファイル名例:

`ViconEquirectStereo_YYYYMMDD.unitypackage`

---

## 13. 現地導入時チェック

CVIC等のVICON環境で以下を確認する。

- Unityバージョン
- Vicon Unity Pluginバージョン
- VICON Tracker起動
- Tracker PCのIPアドレス
- Port = 801
- `Object Name`
- UnityとVICON Tracker間のDataStream接続
- `ViconHead` の位置変化
- `ViconHead` の回転変化
- LeftEye / RightEyeの「ワールド位置」
- SBS Equirectangular出力
- フルスクリーン表示
- Escによる終了

---

## 14. 設計方針

本システムは、研究開発用の「小さく動く単位」として構築する。

個々のPrefab / Scriptを単独で動作確認し、その後組み合わせる。

基本的な「役割分担」:

```text
VICON
  = Tracking

ViconHead
  = Head Transform

CaptureMono / CaptureStereo
  = Equirectangular Generation

EquirectDisplay / EquirectStereoDisplay
  = Display
```

バーチャル世界の絶対座標系と頭部の「ローカル座標系」を分離し、将来的にVICON以外のTracking、XRデバイス、OSC等とも接続可能な構造を維持する。