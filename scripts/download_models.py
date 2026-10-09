"""Download public See-through V3 weights into Anime Layer Studio's local model folder.

This script deliberately downloads weights only when explicitly launched by the user.
It never downloads models during app startup or an inference job.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
HUB_DIR = ROOT / "models" / "huggingface" / "hub"

# The Blockswap pair is the default mode in the app. Repository sizes are approximate
# and can change as upstream maintainers update files.
BASE_MODELS: tuple[tuple[str, str], ...] = (
    (
        "layerdifforg/seethroughv0.0.2_layerdiff3d",
        "seethroughv0.0.2_layerdiff3d",
    ),
    (
        "layerdifforg/seethroughv0.0.1_marigold",
        "seethroughv0.0.1_marigold",
    ),
)

NF4_MODELS: tuple[tuple[str, str], ...] = (
    (
        "24yearsold/seethroughv0.0.2_layerdiff3d_nf4",
        "seethroughv0.0.2_layerdiff3d_nf4",
    ),
    (
        "24yearsold/seethroughv0.0.1_marigold_nf4",
        "seethroughv0.0.1_marigold_nf4",
    ),
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--include-nf4",
        action="store_true",
        help="also download the optional NF4 models for the experimental quantized mode",
    )
    return parser.parse_args(argv)


def _get_snapshot_download():
    import subprocess

    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        print("huggingface_hub is missing; installing it into this Python environment...", flush=True)
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--upgrade", "huggingface_hub"]
        )
        from huggingface_hub import snapshot_download

    # Newer Hugging Face repositories use Xet-backed storage. Install its optional
    # downloader when absent; if that add-on cannot be installed, Hub may still use
    # its HTTP fallback depending on the repository/client version.
    try:
        import hf_xet  # noqa: F401
    except ImportError:
        print("Installing the optional Hugging Face Xet downloader...", flush=True)
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "hf_xet"])
        except subprocess.CalledProcessError:
            print("Warning: hf_xet could not be installed; continuing with the available Hub downloader.", flush=True)

    return snapshot_download


def download_models(models: Iterable[tuple[str, str]]) -> None:
    snapshot_download = _get_snapshot_download()
    HUB_DIR.mkdir(parents=True, exist_ok=True)

    for repo_id, folder_name in models:
        local_dir = HUB_DIR / folder_name
        local_dir.mkdir(parents=True, exist_ok=True)
        print("\n" + "=" * 72, flush=True)
        print(f"Source:      https://huggingface.co/{repo_id}", flush=True)
        print(f"Destination: {local_dir}", flush=True)
        print("If interrupted, run this downloader again to resume/retry.", flush=True)
        print("=" * 72, flush=True)
        snapshot_download(
            repo_id=repo_id,
            local_dir=str(local_dir),
        )
        if not (local_dir / "model_index.json").is_file():
            raise RuntimeError(
                f"Download finished but model_index.json is missing from {local_dir}. "
                "Check the Hugging Face repository and retry."
            )
        print(f"Verified model folder: {folder_name}", flush=True)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    models = list(BASE_MODELS)
    if args.include_nf4:
        models.extend(NF4_MODELS)

    print("Anime Layer Studio model downloader", flush=True)
    print(f"Project folder: {ROOT}", flush=True)
    print(f"Model destination: {HUB_DIR}", flush=True)
    print("Model weights are ignored by Git and will not be uploaded to GitHub.", flush=True)
    print("Use only model files whose licenses/terms you have reviewed.", flush=True)

    try:
        download_models(models)
    except KeyboardInterrupt:
        print("\nDownload cancelled. Run DOWNLOAD_MODELS.bat again to retry.", flush=True)
        return 130
    except Exception as exc:
        print(f"\nERROR: {exc}", file=sys.stderr, flush=True)
        print("Fix the network/storage issue and rerun DOWNLOAD_MODELS.bat.", file=sys.stderr, flush=True)
        return 1

    print("\nAll requested model folders were downloaded and verified.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
