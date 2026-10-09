$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root

Write-Host "Installing Anime Layer Studio v0.4.7 (no upscaler)" -ForegroundColor Cyan
Write-Host "A local .venv will be used so your other Python projects are not modified." -ForegroundColor Gray

$pyLauncher = Get-Command py -ErrorAction SilentlyContinue
if (-not $pyLauncher) {
    throw "The Python launcher (py) was not found. Install 64-bit Python 3.12 from https://www.python.org/downloads/windows/ and enable the Python Launcher option."
}
$pythonExe = (& py -3.12 -c "import sys; print(sys.executable)" 2>$null | Select-Object -Last 1)
if ($LASTEXITCODE -ne 0 -or -not $pythonExe) {
    throw "Python 3.12 64-bit was not found. Install it from https://www.python.org/downloads/windows/ and rerun this installer."
}
$pythonExe = $pythonExe.Trim()
Write-Host "Base Python: $pythonExe" -ForegroundColor Green

$venvPython = Join-Path $root ".venv\Scripts\python.exe"
if (!(Test-Path $venvPython)) {
    Write-Host "Creating project virtual environment..." -ForegroundColor Cyan
    & $pythonExe -m venv (Join-Path $root ".venv")
    if ($LASTEXITCODE -ne 0) { throw "Could not create .venv." }
}

Write-Host "Updating pip in .venv..." -ForegroundColor Cyan
& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "Could not update pip." }

Write-Host "Installing the CUDA-enabled PyTorch build used by See-through..." -ForegroundColor Cyan
& $venvPython -m pip install "torch==2.8.0+cu128" "torchvision==0.23.0+cu128" "torchaudio==2.8.0+cu128" --index-url "https://download.pytorch.org/whl/cu128"
if ($LASTEXITCODE -ne 0) { throw "PyTorch installation failed. Check your internet connection and supported Windows/Python version, then retry." }

$seeThrough = Join-Path $root "third_party\see-through"
if (!(Test-Path (Join-Path $seeThrough "requirements.txt"))) {
    if (Test-Path $seeThrough) {
        throw "third_party\see-through exists but does not contain requirements.txt. Back it up or remove that incomplete folder, then rerun setup."
    }
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        throw "Git for Windows was not found. Install it from https://git-scm.com/download/win and rerun setup."
    }
    New-Item -ItemType Directory -Force (Join-Path $root "third_party") | Out-Null
    git clone --depth 1 https://github.com/shitagaki-lab/see-through.git $seeThrough
    if ($LASTEXITCODE -ne 0) { throw "Could not clone the upstream See-through repository." }
}

Write-Host "Installing the upstream See-through inference dependencies..." -ForegroundColor Cyan
Push-Location $seeThrough
try {
    & $venvPython -m pip install -r "requirements.txt"
    if ($LASTEXITCODE -ne 0) { throw "See-through dependencies failed to install. See the error above; review the upstream requirements before retrying." }
} finally {
    Pop-Location
}

Write-Host "Installing Anime Layer Studio backend dependencies..." -ForegroundColor Cyan
& $venvPython -m pip install -r (Join-Path $root "requirements.txt")
if ($LASTEXITCODE -ne 0) { throw "Anime Layer Studio backend dependencies failed to install." }

if (!(Test-Path (Join-Path $root "config.json"))) {
    Copy-Item (Join-Path $root "config.example.json") (Join-Path $root "config.json")
}
New-Item -ItemType Directory -Force (Join-Path $root "models\huggingface\hub"), (Join-Path $root "workspace") | Out-Null

Write-Host "Checking Python dependencies..." -ForegroundColor Cyan
& $venvPython -c "import torch, diffusers, transformers, huggingface_hub, uvicorn, fastapi, psd_tools; print('PyTorch:', torch.__version__); print('CUDA build:', torch.version.cuda); print('CUDA available:', torch.cuda.is_available())"
if ($LASTEXITCODE -ne 0) { throw "A required Python dependency could not be imported. See the error above." }

& $venvPython -c "import torch; raise SystemExit(0 if torch.cuda.is_available() else 2)"
if ($LASTEXITCODE -ne 0) {
    Write-Warning "PyTorch installed, but CUDA is not available. The web UI may start, but AI inference needs a compatible NVIDIA driver/GPU and CUDA-enabled PyTorch. See the README troubleshooting section."
}

Write-Host "Setup complete." -ForegroundColor Green
Write-Host "Next: double-click DOWNLOAD_MODELS.bat (about 13.5 GB for the default models)." -ForegroundColor Green
Write-Host "Then: double-click RUN_ANIME_LAYER_STUDIO.bat." -ForegroundColor Green
