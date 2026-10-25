@echo off
setlocal
set PYTHONUTF8=1
set GRADIO_ANALYTICS_ENABLED=False
set HF_HUB_OFFLINE=1
set TRANSFORMERS_OFFLINE=1
set HF_DATASETS_OFFLINE=1
cd /d "%~dp0"
if not defined AI_MR_COMMON_ROOT set "AI_MR_COMMON_ROOT=C:\AI_MR_Sandbox"
if not defined AI_MR_IMAGE_PYTHON set "AI_MR_IMAGE_PYTHON=C:\AI_venvs\AI_MR_Sandbox\Scripts\python.exe"
if not defined AI_MR_IMAGE_ACCELERATE set "AI_MR_IMAGE_ACCELERATE=C:\AI_venvs\AI_MR_Sandbox\Scripts\accelerate.exe"
if not defined AI_MR_WORKSPACE set "AI_MR_WORKSPACE=%USERPROFILE%\AI_MR_Workspace"
if not defined AI_MR_GUI_PACKAGES set "AI_MR_GUI_PACKAGES=%AI_MR_COMMON_ROOT%\runtime\image_gui_packages"
if not defined AI_MR_TRAINING_PACKAGES set "AI_MR_TRAINING_PACKAGES=%AI_MR_COMMON_ROOT%\runtime\image_training_packages"
if not exist "%AI_MR_GUI_PACKAGES%\gradio" if exist "%AI_MR_COMMON_ROOT%\image_learning_gui\.gui_packages\gradio" set "AI_MR_GUI_PACKAGES=%AI_MR_COMMON_ROOT%\image_learning_gui\.gui_packages"
if not exist "%AI_MR_TRAINING_PACKAGES%\datasets" if exist "%AI_MR_COMMON_ROOT%\image_learning_gui\.training_packages\datasets" set "AI_MR_TRAINING_PACKAGES=%AI_MR_COMMON_ROOT%\image_learning_gui\.training_packages"
if not exist "%AI_MR_IMAGE_PYTHON%" (
  echo Image AI Python was not found: %AI_MR_IMAGE_PYTHON%
  echo Run setup_image_learning_gui.cmd from the repository root.
  pause
  exit /b 1
)
if not exist "%AI_MR_GUI_PACKAGES%\gradio" (
  echo Gradio dependencies were not found.
  echo Run setup_image_learning_gui.cmd from the repository root.
  pause
  exit /b 1
)
set "PYTHONPATH=%AI_MR_GUI_PACKAGES%"
"%AI_MR_IMAGE_PYTHON%" app.py
if errorlevel 1 (
  echo.
  echo GUI could not start. Review the message above.
  pause
)
endlocal
