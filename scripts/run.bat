@echo off
setlocal
cd /d "%~dp0.."
title Anime Layer Studio

echo ========================================================
echo  Anime Layer Studio v0.4.7 - no upscaler
echo ========================================================
echo.

set "PY=%~dp0..\.venv\Scripts\python.exe"
if not exist "%PY%" (
  echo ERROR: The project Python environment is missing.
  echo Double-click INSTALL_ANIME_LAYER_STUDIO.bat first.
  pause
  exit /b 1
)

"%PY%" -c "import uvicorn, fastapi, psd_tools; print('Backend dependencies OK')" >nul 2>&1
if errorlevel 1 (
  echo ERROR: Required backend dependencies are missing.
  echo Double-click INSTALL_ANIME_LAYER_STUDIO.bat again.
  pause
  exit /b 1
)

echo Starting Anime Layer Studio at http://127.0.0.1:7860 ...
echo Keep this terminal window open while using the app.
echo Press Ctrl+C here to stop the server.
echo.
"%PY%" -m uvicorn app.main:app --host 127.0.0.1 --port 7860
pause
