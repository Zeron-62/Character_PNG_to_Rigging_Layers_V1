from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config.json"

DEFAULTS = {
    "see_through_repo": "third_party/see-through",
    "python_executable": "python",
    "hf_home": "models/huggingface",
    "workspace": "workspace",
    "max_jobs": 1,
    "memory_manager": {"inventory_cache_seconds": 30, "gpu_reserve_mb": 1536, "ram_reserve_gb": 6},
}

def load_config():
    if not CONFIG_PATH.exists():
        return DEFAULTS.copy()
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig"))
        out = DEFAULTS.copy(); out.update(data); return out
    except Exception:
        return DEFAULTS.copy()

def abs_path(value: str) -> Path:
    p = Path(value)
    return p if p.is_absolute() else ROOT / p
