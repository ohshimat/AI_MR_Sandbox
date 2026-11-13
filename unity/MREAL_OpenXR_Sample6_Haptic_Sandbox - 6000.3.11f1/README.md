設定～サンプル１

✓ MRP2025 OpenXR Runtime 有効
✓ Unity 2022.3.62f3 / 3D URP プロジェクト作成
✓ OpenXR Plugin 導入
✓ New Input System 有効化
✓ Depth Submission Mode = 24 Bit
✓ Run In Background 有効
✓ Main Camera → XR Rig 変換
✓ MREAL向けCamera設定
✓ Cube配置
✓ Unity Editor再生からMREAL実機表示成功

## Unity 6 hardware verification

Open this project with Unity **6000.3.11f1**. This folder is the Unity 6 copy; preserve the separate Unity 2022.3 project.

Windows x64 Haptic native dependencies are bundled under `Assets/3DSystems/HapticsDirect/HapticPlugin/`. Editor Play start/stop without a haptic device was validated on 2026-11-13, with TouchActor active and no Haptic DLL exceptions. Physical device operation and a Windows Player build still require validation.

Read `../../documents/log/20261113_Unity6実機確認送付準備.md` for the hardware handoff steps and known issues. See the HapticPlugin manifests and `NATIVE-RUNTIME-PORTABILITY.md` for dependency origins, hashes, remaining requirements and applicable redistribution terms. Generated Library/Temp/Built outputs are not source files and are excluded from Git.
