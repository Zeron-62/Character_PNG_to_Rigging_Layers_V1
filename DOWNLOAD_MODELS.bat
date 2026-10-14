@echo off
setlocal
cd /d "%~dp0"
title Download Anime Layer Studio models

echo ========================================================
echo  Anime Layer Studio v2.0.0 - Model downloader
echo ========================================================
echo.
echo Required Blockswap models: approximately 13.5 GB total.
echo Optional NF4 models: approximately 5 GB extra.
echo Optional Real-ESRGAN anime upscaler weights: approximately 17 MB.
echo Model weights are stored locally and are never added to Git.
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
if errorlevel 1 goto download_failed
goto ask_upscaler
:standard_only
".venv\Scripts\python.exe" "scripts\download_models.py"
if errorlevel 1 goto download_failed
:ask_upscaler
choice /C YN /M "Download Real-ESRGAN anime 6B upscaler weights (~17 MB)?"
if errorlevel 2 goto done
".venv\Scripts\python.exe" "scripts\download_upscaler.py"
if errorlevel 1 goto download_failed
:done
echo.
echo Downloads completed. Run RUN_ANIME_LAYER_STUDIO.bat.
pause
exit /b 0
:download_failed
echo.
echo A download failed. Fix the reported issue and run DOWNLOAD_MODELS.bat again.
pause
exit /b 1
