@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0deploy_gui_to_pc.ps1"
if errorlevel 1 (
  echo.
  echo GUI deployment failed. No existing target was overwritten.
  echo If access to C:\AI_MR_Sandbox was denied, run this file as administrator.
  pause
  exit /b 1
)
echo.
echo GUI deployment completed successfully.
pause
endlocal
