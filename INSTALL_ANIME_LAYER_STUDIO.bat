@echo off
setlocal
cd /d "%~dp0"
title Install Anime Layer Studio

echo ========================================================
echo  Anime Layer Studio - One-click setup
echo ========================================================
echo.
echo This setup uses a project-local .venv so it will not replace
necho packages in your other Python projects.
echo It installs PyTorch CUDA 12.8 and the See-through dependencies.
echo A working internet connection and several GB of downloads are required.
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\install_windows.ps1"
if errorlevel 1 (
  echo.
  echo Setup did not complete. Read the error above and the Troubleshooting
  echo section in README.md, then run this file again after fixing it.
  pause
  exit /b 1
)
echo.
echo Setup finished. Next, double-click DOWNLOAD_MODELS.bat.
echo When the models finish downloading, double-click RUN_ANIME_LAYER_STUDIO.bat.
pause
