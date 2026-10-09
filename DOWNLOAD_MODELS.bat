@echo off
setlocal
cd /d "%~dp0"
title Download Anime Layer Studio models

echo ========================================================
echo  Anime Layer Studio - Model downloader
echo ========================================================
echo.
echo Required Blockswap models: approximately 13.5 GB total.
echo Recommended free disk space: at least 20 GB.
echo Downloads are public Hugging Face model files and are not added to Git.
echo Review each model's license and terms before using it.
echo.
if not exist ".venv\Scripts\python.exe" (
  echo ERROR: The project environment is missing.
  echo First double-click INSTALL_ANIME_LAYER_STUDIO.bat and let it finish.
  pause
  exit /b 1
)
choice /C YN /M "Also download optional experimental NF4 models? They need about 5 GB extra"
if errorlevel 2 goto standard_only
".venv\Scripts\python.exe" "scripts\download_models.py" --include-nf4
goto done
:standard_only
".venv\Scripts\python.exe" "scripts\download_models.py"
:done
if errorlevel 1 (
  echo.
  echo A download failed. Run DOWNLOAD_MODELS.bat again to resume/retry.
  pause
  exit /b 1
)
echo.
echo Model download completed. You can now double-click RUN_ANIME_LAYER_STUDIO.bat.
pause
