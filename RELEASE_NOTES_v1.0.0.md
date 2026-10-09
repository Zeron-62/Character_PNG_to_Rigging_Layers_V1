# Anime Layer Studio v1.0.0 — Initial Release

Anime Layer Studio is a local Windows application for AI-assisted anime character layer decomposition. This first release packages the current See-through V3 workflow with PSD inspection and transparent PNG export.

## Included

- See-through V3 decomposition workflow with Blockswap as the recommended default.
- Optional experimental NF4 mode.
- Inference controls for resolution, steps, depth resolution, and seed.
- Job progress and local pipeline logs.
- PSD layer inspector and per-layer previews.
- Full-canvas transparent PNG export and ZIP export.
- Windows one-click installer, model downloader, and app launcher.

## Install on Windows

1. Download the source ZIP from the repository's **Code → Download ZIP** menu and extract it.
2. Install 64-bit Python 3.12 and Git for Windows.
3. Double-click `INSTALL_ANIME_LAYER_STUDIO.bat`.
4. Double-click `DOWNLOAD_MODELS.bat` and wait for the standard model downloads to complete (about 13.5 GB).
5. Double-click `RUN_ANIME_LAYER_STUDIO.bat`.
6. Open http://127.0.0.1:7860 in your browser.

Use Blockswap first. The optional NF4 models add approximately 5 GB and need additional dependencies.

## Important notes

- **The upscaler is not included.**
- Model weights, the upstream See-through checkout, cache, and generated user data are not bundled in Git.
- A compatible NVIDIA GPU and driver are required for AI inference. Results and memory use vary with input images/settings.
- The root MIT license applies only to original Anime Layer Studio project files. Upstream code, model weights, and dependencies retain their own licenses and usage terms.
- This first release has not been fully validated by a fresh end-to-end GPU inference test in the release environment.

