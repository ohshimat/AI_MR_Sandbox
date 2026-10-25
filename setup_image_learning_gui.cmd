@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_image_learning_gui.ps1"
if errorlevel 1 (
  echo.
  echo Image learning GUI setup failed. Review the message above.
  pause
  exit /b 1
)
echo.
echo Image learning GUI setup completed successfully.
pause
endlocal
