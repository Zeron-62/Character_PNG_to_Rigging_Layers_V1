"""Tile-based 4x anime PNG upscaling using Real-ESRGAN x4plus anime 6B.

The upscaler is invoked only after decomposition finishes. It processes one PNG at a time
with tiling to limit VRAM use and preserves transparent alpha using bicubic alpha scaling.
"""
from __future__ import annotations

import gc
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "models" / "upscaler" / "RealESRGAN_x4plus_anime_6B.pth"
MODEL_URL = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/RealESRGAN_x4plus_anime_6B.pth"
UPSCALE_FACTOR = 4
DEFAULT_TILE = 128


def _load_upscaler(tile: int = DEFAULT_TILE):
    try:
        import torch
        # BasicSR 1.4.x references a torchvision module removed in newer torchvision.
        # Alias the supported functional module before importing BasicSR/Real-ESRGAN.
        import torchvision.transforms.functional as tv_functional
        sys.modules.setdefault("torchvision.transforms.functional_tensor", tv_functional)
        from basicsr.archs.rrdbnet_arch import RRDBNet
        from realesrgan import RealESRGANer
    except Exception as exc:
        raise RuntimeError(
            "Real-ESRGAN dependencies are missing or incompatible. Run "
            "INSTALL_ANIME_LAYER_STUDIO.bat again to install the upscaler requirements."
        ) from exc

    if not MODEL_PATH.is_file():
        raise FileNotFoundError(
            f"Upscaler model is missing: {MODEL_PATH}. Run DOWNLOAD_MODELS.bat and select the upscaler download."
        )
    if not 64 <= int(tile) <= 256:
        raise ValueError("Tile size must be between 64 and 256.")

    model = RRDBNet(
        num_in_ch=3, num_out_ch=3, num_feat=64,
        num_block=6, num_grow_ch=32, scale=4,
    )
    engine = RealESRGANer(
        scale=UPSCALE_FACTOR,
        model_path=str(MODEL_PATH),
        model=model,
        tile=int(tile),
        tile_pad=10,
        pre_pad=0,
        half=bool(torch.cuda.is_available()),
        gpu_id=0 if torch.cuda.is_available() else None,
    )
    return engine, torch


def upscale_png_directory(input_dir: Path, output_dir: Path, tile: int = DEFAULT_TILE) -> list[Path]:
    """Upscale PNG layers 4x one at a time; input PNGs are never overwritten."""
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("OpenCV is missing. Re-run the project installer.") from exc

    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    if not input_dir.is_dir():
        raise FileNotFoundError(f"Layer PNG directory does not exist: {input_dir}")
    files = sorted(p for p in input_dir.glob("*.png") if p.is_file())
    if not files:
        raise FileNotFoundError("No PNG layers found. Export the PSD layers before upscaling.")

    engine, torch = _load_upscaler(tile=tile)
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    try:
        for source in files:
            image = cv2.imread(str(source), cv2.IMREAD_UNCHANGED)
            if image is None:
                raise RuntimeError(f"Could not read layer PNG: {source.name}")
            try:
                result, _ = engine.enhance(image, outscale=UPSCALE_FACTOR, alpha_upsampler="bicubic")
            except Exception as exc:
                raise RuntimeError(
                    f"Upscaling {source.name} failed. Close GPU-heavy apps and retry; "
                    "tile-based inference is configured for lower VRAM."
                ) from exc
            destination = output_dir / source.name
            if not cv2.imwrite(str(destination), result):
                raise RuntimeError(f"Could not save upscaled PNG: {destination}")
            written.append(destination)
            del image, result
    finally:
        del engine
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    return written


def zip_upscaled_layers(files: list[Path], destination: Path) -> Path:
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file in files:
            archive.write(file, arcname=file.name)
    return destination
