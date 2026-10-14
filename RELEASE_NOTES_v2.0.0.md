# Anime Layer Studio v2.0.0 — 4x Anime Upscaling

Version 2 adds a separate Real-ESRGAN anime upscaling stage to the v1 character decomposition workflow.

## What's new

- 4x upscaling of exported transparent PNG layers using RealESRGAN_x4plus_anime_6B.
- Tile-based inference (default tile 128, configurable in backend) to reduce peak VRAM use.
- Alpha channel is scaled separately using bicubic interpolation to preserve transparent layer edges.
- Batch processing of each layer PNG, producing a separate upscaled folder and ZIP download.
- One-click download of the upscaler weights from `DOWNLOAD_MODELS.bat`.
- The upscaler runs only after decomposition is complete; it does not run concurrently with the See-through model subprocess.

## Upgrade / installation

1. Download and extract the v2.0.0 source ZIP.
2. Run `INSTALL_ANIME_LAYER_STUDIO.bat` to install the additional upscaler dependencies into the project-local environment.
3. Run `DOWNLOAD_MODELS.bat` and choose to download the Real-ESRGAN anime upscaler model.
4. Run `RUN_ANIME_LAYER_STUDIO.bat`.
5. Complete decomposition, then use **Upscale exported layers 4x** and download the resulting ZIP.

The official model weights are downloaded separately and are not included in this source package. The default tile size is 128 to reduce VRAM pressure; if CUDA out-of-memory occurs, close other GPU applications and retry.

## Compatibility and licensing

- This release uses the upstream Real-ESRGAN x4plus anime 6B model and project. See [Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN) for upstream licensing and model information.
- The root MIT license applies only to original Anime Layer Studio project files; it does not override third-party licenses or model terms.
- The release workflow tests Python compilation and unit tests. A fresh end-to-end GPU inference run is not performed by GitHub Actions.
