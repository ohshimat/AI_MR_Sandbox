@echo off
setlocal
set PYTHONUTF8=1
cd /d "%~dp0"
if not defined AI_MR_COMMON_ROOT set "AI_MR_COMMON_ROOT=C:\AI_MR_Sandbox"
if not defined AI_MR_IMAGE_PYTHON set "AI_MR_IMAGE_PYTHON=C:\AI_venvs\AI_MR_Sandbox\Scripts\python.exe"
if not defined AI_MR_TRAINING_PACKAGES set "AI_MR_TRAINING_PACKAGES=%AI_MR_COMMON_ROOT%\runtime\image_training_packages"
if not exist "%AI_MR_IMAGE_PYTHON%" (
  echo Image AI Python was not found: %AI_MR_IMAGE_PYTHON%
  pause
  exit /b 1
)
if not exist "%AI_MR_TRAINING_PACKAGES%" mkdir "%AI_MR_TRAINING_PACKAGES%"
set "TEMP=%AI_MR_COMMON_ROOT%\temp\pip"
set "TMP=%TEMP%"
if not exist "%TEMP%" mkdir "%TEMP%"
"%AI_MR_IMAGE_PYTHON%" -m pip install --upgrade --target "%AI_MR_TRAINING_PACKAGES%" -r requirements-training-lock.txt
if errorlevel 1 (
  echo.
  echo Training dependency installation failed.
  pause
  exit /b 1
)
echo.
echo Training dependencies installed in %AI_MR_TRAINING_PACKAGES%.
pause
endlocal
