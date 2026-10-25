@echo off
setlocal
cd /d "%TEMP%"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0update_gui_on_pc.ps1"
if errorlevel 1 (
  echo.
  echo GUI update failed. The previous operational GUI was preserved or restored.
  echo Close the GUI and its command window, then run the updater from Documents\Codex.
  echo If access to C:\AI_MR_Sandbox was denied, run this file as administrator.
  pause
  exit /b 1
)
echo.
echo GUI update completed successfully.
pause
endlocal
