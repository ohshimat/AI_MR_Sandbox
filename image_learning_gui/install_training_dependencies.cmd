@echo off
setlocal
set PYTHONUTF8=1
cd /d "%~dp0"
if not exist ".training_packages" mkdir ".training_packages"
set "TEMP=%~dp0.pip_temp"
set "TMP=%TEMP%"
if not exist ".pip_temp" mkdir ".pip_temp"
"C:\AI_venvs\AI_MR_Sandbox\Scripts\python.exe" -m pip install --upgrade --target ".training_packages" -r requirements-training-lock.txt
if errorlevel 1 (
  echo.
  echo Training dependency installation failed.
  pause
  exit /b 1
)
echo.
echo Training dependencies installed in .training_packages.
pause
endlocal
