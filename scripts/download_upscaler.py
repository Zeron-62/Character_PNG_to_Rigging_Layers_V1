"""Download the official Real-ESRGAN anime 6B x4 weights on explicit request."""
from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "models" / "upscaler"
MODEL_PATH = MODEL_DIR / "RealESRGAN_x4plus_anime_6B.pth"
MODEL_URL = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/RealESRGAN_x4plus_anime_6B.pth"


def main() -> int:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    if MODEL_PATH.is_file() and MODEL_PATH.stat().st_size > 1_000_000:
        print(f"Upscaler model already exists: {MODEL_PATH}")
        return 0
    temporary = MODEL_PATH.with_suffix(MODEL_PATH.suffix + ".download")
    request = urllib.request.Request(MODEL_URL, headers={"User-Agent": "AnimeLayerStudio/2.0"})
    try:
        print("Downloading Real-ESRGAN x4plus anime 6B weights (~17 MB)...", flush=True)
        with urllib.request.urlopen(request, timeout=60) as response, temporary.open("wb") as target:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                target.write(chunk)
        if temporary.stat().st_size < 1_000_000:
            raise RuntimeError("Downloaded file is unexpectedly small; refusing to install it as model weights.")
        temporary.replace(MODEL_PATH)
        print(f"Model downloaded: {MODEL_PATH}", flush=True)
        print("Review Real-ESRGAN and model licensing before redistribution.", flush=True)
        return 0
    except Exception as exc:
        temporary.unlink(missing_ok=True)
        print(f"ERROR downloading upscaler model: {exc}", file=sys.stderr, flush=True)
        print("Retry from DOWNLOAD_MODELS.bat when your connection is stable.", file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
