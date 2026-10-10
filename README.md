# Anime Layer Studio

**AI-assisted anime character decomposition for layered 2D animation workflows.**  
Turn a single character image into an editable layer stack, inspect the generated PSD, and export every layer as a transparent PNG.

> **Version 1.0.0 · Initial release**  
[Download the v1.0.0 source package](https://github.com/Zeron-62/Character_PNG_to_Rigging_Layers_V1/releases/tag/v1.0.0) (after the release is published).  
> Windows 10/11 · NVIDIA GPU · Python 3.12  
> **The upscaler is not included.** Model weights are downloaded separately and are not committed to this repository.

<p align="center">
  <strong>Decompose → Inspect → Export → Animate</strong>
</p>

## What it does

Anime Layer Studio provides a local web interface around the See-through V3 inference pipeline. It is designed to support anime character artwork preparation for manual rigging and 2D animation.

- **Character layer decomposition** using See-through V3.
- **Blockswap mode** as the recommended starting point for lower-VRAM systems.
- **Experimental NF4 mode** for users who install the additional dependencies and models.
- **Inference controls** for resolution, sampling steps, depth resolution, and seed.
- **Live job status and logs** for monitoring processing.
- **PSD layer inspector** with layer previews, dimensions, visibility, and bounds.
- **Transparent PNG export** with full-canvas alignment.
- **One-click ZIP export** of the decomposed PNG layers.
- **Local-first interface** bound to `127.0.0.1`.

## Quick start

The easiest way to install on Windows is with the three launcher files at the repository root.

### 1. Requirements

- Windows 10 or Windows 11, 64-bit.
- Python **3.12 (64-bit)** with the Python Launcher (`py`).
- Git for Windows.
- NVIDIA GPU with a compatible driver.
- Internet access for setup and model downloads.
- At least **20 GB of free disk space** recommended for default model downloads, Python packages, and working files.

### 2. Install

1. Download the repository using **Code → Download ZIP**, then extract it to a permanent folder such as `D:\\AI Projects\\AnimeLayerStudio`. Do not run it from inside the ZIP.
2. Double-click **`INSTALL_ANIME_LAYER_STUDIO.bat`**.
3. Wait for the terminal to report setup complete. The installer creates a project-local `.venv`, installs the Python dependencies, obtains the upstream See-through source, and prepares local folders.

This setup uses its own virtual environment; it should not replace packages in other Python projects. Installation and model retrieval need an internet connection.

### 3. Download models

1. Double-click **`DOWNLOAD_MODELS.bat`**.
2. Choose the default **Blockswap** models first. The standard pair is approximately **13.5 GB** (upstream sizes may change).
3. The downloader verifies the downloaded model folders before it exits. If interrupted, run the same file again to retry.

Optional NF4 models add approximately 5 GB and require additional dependencies. Use the NF4 option only if you intend to run the experimental quantized mode.

### 4. Launch

1. Double-click **`RUN_ANIME_LAYER_STUDIO.bat`**.
2. Keep the terminal window open.
3. Open **http://127.0.0.1:7860** in your browser.

Upload a PNG, JPEG, or WebP character image, start with **Blockswap**, and run decomposition. When processing finishes, inspect the PSD layers and download the PSD or a ZIP containing transparent layer PNGs. To stop the app, focus the terminal and press `Ctrl+C`.

## One-click files

| File | Purpose |
|---|---|
| `INSTALL_ANIME_LAYER_STUDIO.bat` | Creates the local Python environment and installs dependencies |
| `DOWNLOAD_MODELS.bat` | Downloads the standard models and offers optional NF4 models |
| `RUN_ANIME_LAYER_STUDIO.bat` | Starts the local web interface |

If a launcher fails, keep its terminal window open and read the error message before closing it.

## Models

Model files are intentionally not stored in GitHub. The model downloader places them under `models/huggingface/hub/`.

| Purpose | Model repository | Local folder |
|---|---|---|
| Layer generation | [layerdifforg/seethroughv0.0.2_layerdiff3d](https://huggingface.co/layerdifforg/seethroughv0.0.2_layerdiff3d) | `seethroughv0.0.2_layerdiff3d/` |
| Depth estimation | [layerdifforg/seethroughv0.0.1_marigold](https://huggingface.co/layerdifforg/seethroughv0.0.1_marigold) | `seethroughv0.0.1_marigold/` |

Experimental NF4 models:

- [24yearsold/seethroughv0.0.2_layerdiff3d_nf4](https://huggingface.co/24yearsold/seethroughv0.0.2_layerdiff3d_nf4)
- [24yearsold/seethroughv0.0.1_marigold_nf4](https://huggingface.co/24yearsold/seethroughv0.0.1_marigold_nf4)

The folders must contain `model_index.json`. Do not rename them after downloading.

## Example workflow

1. Prepare a clean character image with the character visible against a suitable background.
2. Run decomposition with Blockswap.
3. Inspect generated PSD layers and layer previews.
4. Export all layers to transparent PNG files.
5. Bring those PNGs into your preferred rigging or animation software and adjust the layer stack manually.

The application exports layers; it does not automatically create a fully rigged, production-ready puppet. Layer quality varies with the input image and model result.

## License and third-party models

The root [MIT License](LICENSE) applies to the original Anime Layer Studio project files only. It does not relicense the upstream [See-through source](https://github.com/shitagaki-lab/see-through), model weights, dependencies, or any third-party assets. Review the license and usage terms of each upstream repository before use or redistribution. Do not commit model weights or third-party files to this repository unless their terms explicitly permit it.

## Privacy and safety

- The app binds to `127.0.0.1` and is intended for local use.
- Do not expose the local server to the public internet.
- Your model files, uploaded images, jobs, logs, and outputs are local files; keep them out of Git commits.
- The upscaler and its dependencies are not part of this release.

## Troubleshooting

**Python 3.12 is not found**  
Install 64-bit Python 3.12 from [python.org](https://www.python.org/downloads/windows/) and enable the Python Launcher, then run the installer again.

**Git is not found**  
Install [Git for Windows](https://git-scm.com/download/win), then rerun the installer.

**Model missing**  
Run `DOWNLOAD_MODELS.bat` again and confirm the expected local model folder includes `model_index.json`.

**CUDA is unavailable**  
Update your NVIDIA driver and reinstall using `INSTALL_ANIME_LAYER_STUDIO.bat`. The interface may start without CUDA, but inference requires a compatible NVIDIA GPU and CUDA-enabled PyTorch.

**GPU out of memory**  
Use Blockswap, reduce resolution, close other GPU-heavy applications, and process one image at a time. Actual VRAM use varies by input and settings.

**The browser cannot connect**  
Keep the launcher terminal open and visit http://127.0.0.1:7860.

## Developer checks

After installing the project environment, run:

```powershell
.\.venv\Scripts\python.exe -m compileall -q app scripts tests
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

These checks do not perform a full GPU inference run or download model weights.

## Repository layout

```text
app/                         FastAPI backend and PSD export
frontend/                    Local web interface
scripts/                     Installer, downloader, and launcher scripts
tests/                       Lightweight project tests
INSTALL_ANIME_LAYER_STUDIO.bat
DOWNLOAD_MODELS.bat
RUN_ANIME_LAYER_STUDIO.bat
LICENSE                      License for original project files
```

---

**Anime Layer Studio v1.0.0** · Built for local anime-art workflows.


## Phase 1: memory telemetry and placement planning

The Phase 1 branch adds a read-only **Memory & model placement** panel and three local API endpoints:

- `GET /api/system/memory` — system RAM, NVIDIA VRAM (via `nvidia-smi`), model-volume free space, and conservative next-step advice.
- `GET /api/system/models` — inventory of existing BF16/Blockswap and optional NF4 model folders. Inventory metadata is cached briefly.
- `GET /api/system/streaming-plan?stage=layer_decomposition&mode=blockswap` — a proposed SSD/RAM/GPU placement plan for the selected pipeline stage.

This phase is deliberately **observability and planning only**. It does not implement Colibrì-style SSD tensor streaming, load or unload model weights, move cache files, download models, or alter the existing See-through inference algorithm. The next phase should use measurements from this panel and inspect the upstream loader boundaries before introducing prefetch or eviction. The manager honours the configured `hf_home` path, so existing D: drive caches remain in place.

The manager uses `psutil` for RAM telemetry and `nvidia-smi` for GPU memory reporting. If GPU telemetry is unavailable, the app continues to work and displays that limitation.
