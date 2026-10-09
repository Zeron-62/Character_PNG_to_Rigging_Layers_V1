# Anime Layer Studio

Anime Layer Studio is a local Windows application for AI-assisted anime-character layer decomposition. It runs the See-through V3 inference pipeline, lets you inspect the resulting PSD layers, and exports each layer as a full-canvas transparent PNG or ZIP archive.

> **This repository does not include the upscaler.** The model weights are downloaded separately and are never committed to Git.

## Features

- See-through V3 character decomposition with **Blockswap** (the default; intended for lower-VRAM systems) and optional experimental NF4 mode.
- Controls for inference resolution, step count, depth resolution, and seed.
- Job progress and local pipeline logs.
- PSD layer inspector, previews, and bounding-box details.
- Transparent full-canvas PNG export and one-click ZIP export.
- Local-only web server at `127.0.0.1`; it is not designed to be exposed directly to the public internet.

## Quick start (Windows 10/11)

### Requirements

- 64-bit Windows 10/11.
- **64-bit Python 3.12** and the Python Launcher (`py`). Download it from [python.org](https://www.python.org/downloads/windows/) and enable the launcher during setup.
- [Git for Windows](https://git-scm.com/download/win), used to fetch the upstream See-through source.
- An NVIDIA GPU with a working driver. Blockswap is the recommended starting mode on an 8 GB VRAM GPU, but memory use varies with input size and settings.
- A reliable internet connection for installation and model downloads.
- At least **20 GB of free disk space** for the default models and working files. The standard model download is approximately **13.5 GB**; the actual size may change upstream.

### 1. Install the application

1. Download this repository as a ZIP from GitHub and extract the whole folder to a permanent location, such as `D:\AI Projects\AnimeLayerStudio`. Do not run it from inside the ZIP.
2. Double-click **`INSTALL_ANIME_LAYER_STUDIO.bat`** in the project root.
3. Let the terminal finish. The installer creates a project-local `.venv`, installs CUDA-enabled PyTorch and the See-through inference dependencies, clones the upstream source under `third_party/see-through`, and creates local folders/configuration.
4. If Windows asks for network access or Python installation permission, review the prompt and allow it as appropriate. An internet connection is required.

The installer uses a project-local virtual environment to avoid replacing Python packages in other projects. It installs the PyTorch CUDA 12.8 wheel set currently specified by the upstream See-through setup. A compatible NVIDIA driver is still required for GPU inference.

### 2. Download model weights

1. Double-click **`DOWNLOAD_MODELS.bat`** in the project root.
2. The downloader fetches the two standard Blockswap models from Hugging Face into `models/huggingface/hub/` and verifies that each has a `model_index.json`.
3. It asks whether to also download the optional NF4 models. Choose `N` for the default Blockswap workflow. Choose `Y` only when you want the experimental quantized mode; NF4 adds roughly another 5 GB and has additional dependency requirements.

The download is explicit and separate from app startup: the application will not silently download multi-gigabyte files when you launch it or submit an inference job. If a download is interrupted, run `DOWNLOAD_MODELS.bat` again to retry/resume.

### 3. Run Anime Layer Studio

Double-click **`RUN_ANIME_LAYER_STUDIO.bat`** in the project root. Keep its terminal window open, then open this address in your browser:

**http://127.0.0.1:7860**

Upload a PNG, JPEG, or WebP character image, leave the mode set to **Blockswap** for the first run, choose your settings, and start decomposition. After the job finishes, inspect the PSD layers and export the PSD or ZIP of transparent PNG layers.

To stop the local server, focus the terminal and press `Ctrl+C`.

## Model files and licenses

### Standard Blockswap models

`DOWNLOAD_MODELS.bat` downloads the following public repositories and saves them into the exact folders used by this application:

| Purpose | Hugging Face repository | Local folder |
|---|---|---|
| Layer generation | [layerdifforg/seethroughv0.0.2_layerdiff3d](https://huggingface.co/layerdifforg/seethroughv0.0.2_layerdiff3d) | `models/huggingface/hub/seethroughv0.0.2_layerdiff3d/` |
| Anime depth estimation | [layerdifforg/seethroughv0.0.1_marigold](https://huggingface.co/layerdifforg/seethroughv0.0.1_marigold) | `models/huggingface/hub/seethroughv0.0.1_marigold/` |

The folders must contain a `model_index.json` file. Do not rename the folders after downloading them.

### Optional NF4 models

The optional experimental quantized mode uses these additional repositories:

- [24yearsold/seethroughv0.0.2_layerdiff3d_nf4](https://huggingface.co/24yearsold/seethroughv0.0.2_layerdiff3d_nf4)
- [24yearsold/seethroughv0.0.1_marigold_nf4](https://huggingface.co/24yearsold/seethroughv0.0.1_marigold_nf4)

To use NF4 after downloading its weights, install the upstream NF4 dependencies from the project root in PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip install -r .\third_party\see-through\requirements-inference-bnb.txt
```

Then launch the app and select the experimental NF4 mode. If dependency installation fails on your Windows/Python combination, use Blockswap instead.

### Important license note

The root `LICENSE` file is the MIT license for original Anime Layer Studio project files only. It does **not** relicense third-party code, model weights, or dependencies. Review the licenses, `README`, `LICENSE`, and `NOTICE` files supplied by the [upstream See-through code repository](https://github.com/shitagaki-lab/see-through) and each model repository before using, modifying, or redistributing them. Model weights can carry terms inherited from the models they are derived from. Do not upload model weights to your GitHub repository unless you have verified that redistribution is permitted.

## GitHub Desktop workflow

1. Extract the downloaded project ZIP into a permanent folder.
2. Open GitHub Desktop and select **File → Add Local Repository**. Select the project folder. If GitHub Desktop says it is not a repository yet, choose the option to create a repository in that folder.
3. Review the files, enter a first commit message such as `Prepare Anime Layer Studio project`, and click **Commit to main**.
4. Click **Publish repository** and choose Private or Public.

Before publishing, confirm that `models/`, `third_party/`, `workspace/`, `.venv/`, and `config.json` are not staged. The `.gitignore` excludes these local directories/files.

## Files and folders

| Path | Purpose | Commit to Git? |
|---|---|---|
| `app/` | FastAPI backend, job manager, PSD export | Yes |
| `frontend/` | Local browser UI | Yes |
| `scripts/` | Installer, model downloader, and launcher | Yes |
| `INSTALL_ANIME_LAYER_STUDIO.bat` | Root-level one-click installer | Yes |
| `DOWNLOAD_MODELS.bat` | Root-level one-click model downloader | Yes |
| `RUN_ANIME_LAYER_STUDIO.bat` | Root-level one-click app launcher | Yes |
| `LICENSE` | MIT license for original project files, with third-party scope note | Yes |
| `config.json` | Local path/settings overrides | No |
| `models/` | Model weights | No |
| `third_party/` | Upstream See-through checkout | No |
| `workspace/` | Input files, job logs, intermediate outputs | No |
| `.venv/` | Project-local Python environment | No |

## Troubleshooting

**The installer cannot find Python 3.12.** Install 64-bit Python 3.12 from [python.org](https://www.python.org/downloads/windows/), enable the Python Launcher, and run the installer again.

**The installer fails while installing Python packages.** Check the full error shown in the terminal and verify internet access. Some upstream Python packages may change their Windows support; the error may need to be handled according to the upstream See-through installation notes. Re-running the installer is safe for an existing `.venv` in most cases.

**The installer reports CUDA unavailable.** Update/install your NVIDIA driver and re-run `INSTALL_ANIME_LAYER_STUDIO.bat`. The UI may start without CUDA, but AI inference needs a supported NVIDIA GPU and CUDA-enabled PyTorch.

**The app says a model is missing.** Run `DOWNLOAD_MODELS.bat` and wait for it to verify both model folders. Confirm each expected folder contains `model_index.json`.

**The model download stops or fails.** Check your disk space and internet connection, then run `DOWNLOAD_MODELS.bat` again. Keep the destination folders in place so the downloader can reuse completed files.

**CUDA runs out of memory.** Keep Blockswap selected, lower the inference resolution, close other GPU-heavy applications, and process one image at a time.

**The browser cannot connect.** Keep the launcher terminal open and visit `http://127.0.0.1:7860`. The app binds to localhost only.

## Development checks

Use the project's environment after installation:

```powershell
.\.venv\Scripts\python.exe -m compileall -q app scripts tests
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The lightweight tests do not run GPU inference or download model weights.
