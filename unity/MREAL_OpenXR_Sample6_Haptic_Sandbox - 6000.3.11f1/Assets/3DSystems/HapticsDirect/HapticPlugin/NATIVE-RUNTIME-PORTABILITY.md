# Haptic native runtime portability

## Bundled Windows x64 native dependencies

The project now carries `PhantomIoLib42.dll` (2023.10.11.1213), `msvcr120.dll` and `msvcp120.dll` (12.0.40664.0) beside the existing `HapticsDirect.dll` and `hd.dll`.

- The VC++ 2013 runtime files are unchanged Microsoft-signed files from the official redistributable. See `VC2013-RUNTIME-MANIFEST.json`.
- The Phantom DLL is unchanged from the root x64 entry of the vendor-signed `Touch_Device_Driver_2023.10.11.exe`, obtained from the vendor's S3 distribution linked by the Japanese supplier. The DLL itself is unsigned; the signed source package and file hashes are recorded in `PHANTOM-RUNTIME-MANIFEST.json`.
- All five DLLs are enabled for the Windows x64 Editor and Windows x64 Player; Android and other platforms are excluded. Keep `.meta` files with their DLLs. These are native plug-ins, not `Resources.Load` assets.
- Existing `HapticsDirect.dll` and `hd.dll` binaries and GUIDs were retained. Only their platform/preload settings changed. Preload is disabled; normal native calls load them when required.

## Validated on 2026-11-13

- Existing `hd.dll` imports 76 Phantom functions; all 76 are exported by the bundled x64 Phantom DLL.
- An isolated process loaded the five staged native libraries without installing the Touch device driver.
- Unity Editor 6000.3.11f1 entered and exited Play with `TouchActor` active and no haptic hardware attached. The Haptic version log reported PluginVersion=1.0, PluginBuild=Oct 27 2021, OpenHapticsVersion=3.50.0.
- No Haptic DLL exceptions occurred during this run or shutdown. Module paths showed HapticsDirect, hd, PhantomIoLib42, MSVCP120 and MSVCR120 loading from this project's HapticPlugin folder, including the VC++ 2013 dependencies despite the central runtime installation.
- Scene and XR startup settings were not changed. Hand Tracking's missing-subsystem warning and TcpSpeechReceiver's shutdown SocketException remain separate issues.

## Remaining environment requirements and validation

- The current Editor uses `MSVCP140.dll` and `VCRUNTIME140.dll` from Windows System32. VC++ 14 and Universal CRT/Windows libraries remain prerequisites; this change does not make the entire application independent of the operating system or all installed runtimes.
- No clean-PC or Windows Player build test was performed. Windows Player compatibility flags alone do not prove successful build inclusion or loading; validate both on the target environment.
- Physical Touch/Phantom operation, calibration, USB/Ethernet access and vendor driver requirements are not validated. No Touch driver was installed in this task.
- Real OpenXR tracking separately requires its intended tracking source and runtime. Native haptic DLL bundling does not provide hand tracking.
- Public/third-party redistribution permissions for the vendor runtime have not been established by this technical validation. Preserve the source information and confirm applicable vendor terms before distributing the project outside its authorized use. Microsoft's redistribution terms also apply to the VC++ files.
- Locally bundled runtimes must be maintained and updated with the project; Windows Update does not replace these project copies.

## Git and rollback

The Unity 6 project was untracked in its parent Git repository at the time of this work. No Git add, commit, reset or global configuration change was performed. The work report under `documents/log/20261113_Haptic-Phantom依存DLL同梱.md` records the changed files. The Phantom manifest also preserves the original HapticsDirect/hd importer metadata for rollback. Restoring the earlier import settings disables Editor loading again; it is not a fix for the original issue.
