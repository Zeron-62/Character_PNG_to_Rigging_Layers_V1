"""Phase 1: read-only memory telemetry and placement planning.

This module deliberately does not change See-through's model loader. It reports
system headroom, inventories existing local model files, and produces a safe
placement recommendation for the next streaming-engine phase.
"""
from __future__ import annotations

import os
import platform
import shutil
import subprocess
import threading
import time
from pathlib import Path
from typing import Any

from .config import abs_path, load_config


MODEL_SPECS = (
    ("layerdiff_bf16", "LayerDiff V3 (Blockswap/BF16)", "seethroughv0.0.2_layerdiff3d"),
    ("depth_bf16", "Marigold depth (BF16)", "seethroughv0.0.1_marigold"),
    ("layerdiff_nf4", "LayerDiff V3 (NF4)", "seethroughv0.0.2_layerdiff3d_nf4"),
    ("depth_nf4", "Marigold depth (NF4)", "seethroughv0.0.1_marigold_nf4"),
)


def _directory_size(path: Path) -> int:
    total = 0
    for root, _dirs, files in os.walk(path, followlinks=False):
        for name in files:
            try:
                total += (Path(root) / name).stat().st_size
            except (OSError, PermissionError):
                continue
    return total


def _memory_bytes() -> dict[str, int | None]:
    try:
        import psutil
        vm = psutil.virtual_memory()
        return {
            "total": int(vm.total),
            "available": int(vm.available),
            "used": int(vm.used),
            "percent": int(vm.percent),
        }
    except Exception:
        # Windows fallback keeps the diagnostic endpoint useful if psutil is
        # temporarily unavailable; psutil is included in requirements.txt.
        if os.name == "nt":
            try:
                import ctypes
                from ctypes import wintypes

                class MEMORYSTATUSEX(ctypes.Structure):
                    _fields_ = [
                        ("dwLength", wintypes.DWORD),
                        ("dwMemoryLoad", wintypes.DWORD),
                        ("ullTotalPhys", ctypes.c_ulonglong),
                        ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong),
                        ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong),
                        ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                    ]

                status = MEMORYSTATUSEX()
                status.dwLength = ctypes.sizeof(status)
                if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                    used = int(status.ullTotalPhys - status.ullAvailPhys)
                    total = int(status.ullTotalPhys)
                    return {
                        "total": total,
                        "available": int(status.ullAvailPhys),
                        "used": used,
                        "percent": round(used / total * 100) if total else 0,
                    }
            except Exception:
                pass
        return {"total": None, "available": None, "used": None, "percent": None}


def _gpu_memory() -> dict[str, Any]:
    """Read NVIDIA memory telemetry without importing torch into the web server."""
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total,memory.used,memory.free,utilization.gpu",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            rows = []
            for line in result.stdout.strip().splitlines():
                parts = [part.strip() for part in line.split(",")]
                if len(parts) < 5:
                    continue
                try:
                    rows.append({
                        "name": parts[0],
                        "total_mb": int(parts[1]),
                        "used_mb": int(parts[2]),
                        "free_mb": int(parts[3]),
                        "utilization_percent": int(parts[4]),
                    })
                except ValueError:
                    continue
            if rows:
                return {"available": True, "devices": rows, "source": "nvidia-smi"}
    except (OSError, subprocess.SubprocessError):
        pass
    return {
        "available": False,
        "devices": [],
        "source": None,
        "note": "nvidia-smi was unavailable; GPU memory could not be measured.",
    }


class MemoryManager:
    """System telemetry, local model inventory, and conservative placement plans."""

    def __init__(self) -> None:
        self.cfg = load_config()
        self._lock = threading.Lock()
        self._inventory_cache: dict[str, Any] | None = None
        self._inventory_at = 0.0

    def _model_hub(self) -> Path:
        return abs_path(str(self.cfg.get("hf_home", "models/huggingface"))) / "hub"

    def _find_model(self, expected_name: str) -> Path | None:
        hub = self._model_hub()
        if not hub.is_dir():
            return None
        direct = hub / expected_name
        if (direct / "model_index.json").is_file():
            return direct
        # Hugging Face's normal cache layout uses a repository directory with
        # a snapshots/<revision> child. Search only likely matching repo dirs.
        normalized = expected_name.lower().replace(".", "")
        try:
            candidates = [
                child for child in hub.iterdir()
                if child.is_dir() and expected_name.lower() in child.name.lower()
            ]
        except OSError:
            candidates = []
        for candidate in candidates:
            if (candidate / "model_index.json").is_file():
                return candidate
            snapshots = candidate / "snapshots"
            if snapshots.is_dir():
                try:
                    for snapshot in snapshots.iterdir():
                        if (snapshot / "model_index.json").is_file():
                            return snapshot
                except OSError:
                    continue
        # Some manual caches use the model name without a repository prefix.
        try:
            for child in hub.iterdir():
                if not child.is_dir() or normalized not in child.name.lower().replace(".", ""):
                    continue
                if (child / "model_index.json").is_file():
                    return child
        except OSError:
            pass
        return None

    def model_inventory(self, force: bool = False) -> dict[str, Any]:
        now = time.monotonic()
        with self._lock:
            cache_seconds = max(5, int(self.cfg.get("memory_manager", {}).get("inventory_cache_seconds", 30)))
            if not force and self._inventory_cache and now - self._inventory_at < cache_seconds:
                return self._inventory_cache
            models = []
            for model_id, label, folder in MODEL_SPECS:
                path = self._find_model(folder)
                present = path is not None
                size = _directory_size(path) if path else 0
                models.append({
                    "id": model_id,
                    "label": label,
                    "present": present,
                    "path": str(path) if path else None,
                    "size_bytes": size,
                    "size_gb": round(size / (1024 ** 3), 2),
                    "load_state": "on_disk" if present else "missing",
                    "note": "Inventory only; this phase does not load or unload model weights.",
                })
            hub = self._model_hub()
            try:
                free = shutil.disk_usage(hub if hub.exists() else hub.parent).free
            except OSError:
                free = None
            payload = {
                "model_root": str(hub),
                "disk_free_bytes": free,
                "disk_free_gb": round(free / (1024 ** 3), 2) if free is not None else None,
                "models": models,
                "scanned_at_unix": time.time(),
                "cache_seconds": cache_seconds,
            }
            self._inventory_cache = payload
            self._inventory_at = now
            return payload

    def snapshot(self) -> dict[str, Any]:
        ram = _memory_bytes()
        gpu = _gpu_memory()
        hub = self._model_hub()
        disk_path = hub if hub.exists() else hub.parent
        try:
            disk = shutil.disk_usage(disk_path)
            disk_data = {
                "path": str(disk_path),
                "total_bytes": disk.total,
                "free_bytes": disk.free,
                "used_bytes": disk.used,
                "free_gb": round(disk.free / (1024 ** 3), 2),
            }
        except OSError:
            disk_data = {"path": str(disk_path), "total_bytes": None, "free_bytes": None, "used_bytes": None, "free_gb": None}
        return {
            "phase": 1,
            "mode": "observe_and_plan",
            "algorithm_changed": False,
            "platform": platform.platform(),
            "ram": {
                **ram,
                "total_gb": round(ram["total"] / (1024 ** 3), 2) if ram["total"] is not None else None,
                "available_gb": round(ram["available"] / (1024 ** 3), 2) if ram["available"] is not None else None,
            },
            "gpu": gpu,
            "model_disk": disk_data,
            "recommendation": self._recommend(ram, gpu, disk_data),
            "timestamp_unix": time.time(),
        }

    def _recommend(self, ram: dict[str, Any], gpu: dict[str, Any], disk: dict[str, Any]) -> dict[str, Any]:
        available_ram_gb = (ram.get("available") or 0) / (1024 ** 3)
        devices = gpu.get("devices") or []
        free_vram_mb = devices[0].get("free_mb") if devices else None
        gpu_name = devices[0].get("name") if devices else None
        free_disk_gb = disk.get("free_gb")
        notes = [
            "Phase 1 only observes memory and plans placement; it does not change See-through inference.",
            "Keep Blockswap as the default for the 8 GB GPU. The backend remains responsible for actual tensor/block placement.",
            "Model files remain in the configured Hugging Face cache; no weights are downloaded or moved by this manager.",
        ]
        settings = self.cfg.get("memory_manager", {})
        gpu_reserve_mb = max(512, int(settings.get("gpu_reserve_mb", 1536)))
        ram_reserve_gb = max(2, float(settings.get("ram_reserve_gb", 6)))
        if free_vram_mb is not None and free_vram_mb < gpu_reserve_mb:
            action = "close_gpu_apps"
            summary = "Very little GPU memory is free. Close GPU-heavy apps before starting a decomposition job."
        elif available_ram_gb and available_ram_gb < ram_reserve_gb:
            action = "free_ram"
            summary = "System RAM is low. Close memory-heavy applications before starting a job."
        elif free_disk_gb is not None and free_disk_gb < 20:
            action = "free_disk"
            summary = "Less than 20 GB is free on the model/cache volume. Free disk space before additional model work."
        else:
            action = "ready_for_test"
            summary = "Memory headroom looks adequate for a controlled Blockswap test, subject to the actual inference workload."
        return {
            "action": action,
            "summary": summary,
            "gpu_name": gpu_name,
            "free_vram_mb": free_vram_mb,
            "available_ram_gb": round(available_ram_gb, 2),
            "free_disk_gb": free_disk_gb,
            "notes": notes,
        }

    def placement_plan(self, stage: str = "layer_decomposition", mode: str = "blockswap") -> dict[str, Any]:
        if mode not in {"blockswap", "quantized"}:
            mode = "blockswap"
        inventory = self.model_inventory()
        snapshot = self.snapshot()
        required_ids = (
            ["layerdiff_bf16", "depth_bf16"]
            if mode == "blockswap"
            else ["layerdiff_nf4", "depth_nf4"]
        )
        by_id = {item["id"]: item for item in inventory["models"]}
        required = [by_id[item] for item in required_ids]
        missing = [item["label"] for item in required if not item["present"]]
        plan = [
            {"tier": "SSD", "purpose": "Persistent source of truth for all model weights", "action": "keep_existing_files_in_place"},
            {"tier": "RAM", "purpose": "OS file cache and runtime working set", "action": "allow_os_cache; reserve_memory_for_windows"},
            {"tier": "GPU", "purpose": "See-through block execution", "action": "use_existing_backend_blockswap"},
        ]
        return {
            "phase": 1,
            "stage": stage,
            "requested_mode": mode,
            "recommended_mode": "blockswap",
            "streaming_enabled": False,
            "planning_only": True,
            "required_models": required,
            "missing_models": missing,
            "ready_to_run": not missing,
            "tiers": plan,
            "system": snapshot,
            "limitations": [
                "This is a placement plan, not a Colibrì-compatible tensor streamer.",
                "True SSD-backed block prefetch and cache eviction will be implemented only after measuring the current See-through loader boundaries.",
                "No model files are moved, deleted, downloaded, or re-quantized.",
            ],
        }


manager = MemoryManager()
