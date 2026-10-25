@echo off
setlocal
set PYTHONUTF8=1
cd /d "%~dp0"
if not exist ".gui_packages" mkdir ".gui_packages"
set "TEMP=%~dp0.pip_temp"
set "TMP=%TEMP%"
if not exist ".pip_temp" mkdir ".pip_temp"
"C:\AI_venvs\AI_MR_Sandbox\Scripts\python.exe" -m pip install --upgrade --target ".gui_packages" -r requirements-gui-lock.txt
if errorlevel 1 (
  echo.
  echo Dependency installation failed.
  pause
  exit /b 1
)
echo.
echo GUI dependencies installed in .gui_packages.
pause
endlocal
