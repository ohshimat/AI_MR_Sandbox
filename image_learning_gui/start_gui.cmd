@echo off
setlocal
set PYTHONUTF8=1
cd /d "%~dp0"
set "PYTHONPATH=%~dp0.gui_packages"
"C:\AI_venvs\AI_MR_Sandbox\Scripts\python.exe" app.py
if errorlevel 1 (
  echo.
  echo GUI could not start. Review the message above.
  pause
)
endlocal
