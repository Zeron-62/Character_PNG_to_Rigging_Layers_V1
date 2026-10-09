from __future__ import annotations
import json, os, shutil, subprocess, threading, time, uuid, sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional
from .config import ROOT, load_config, abs_path

@dataclass
class Job:
    id: str
    input_path: Path
    workdir: Path
    status: str = "queued"
    progress: float = 0.0
    stage: str = "Queued"
    message: str = ""
    return_code: Optional[int] = None
    output_psd: Optional[Path] = None
    output_dir: Optional[Path] = None
    log_path: Optional[Path] = None
    started_at: Optional[float] = None
    finished_at: Optional[float] = None
    thread: Optional[threading.Thread] = field(default=None, repr=False)

class JobManager:
    def __init__(self):
        self.jobs: Dict[str, Job] = {}
        self.lock = threading.Lock()
        self.cfg = load_config()
        self.active = 0

    def create(self, input_bytes: bytes, filename: str, resolution: int, steps: int, depth_resolution: int, seed: int, mode: str):
        with self.lock:
            if self.active >= int(self.cfg.get("max_jobs", 1)):
                raise RuntimeError("Another job is already running. This 8GB profile intentionally allows one GPU job at a time.")
            jid = uuid.uuid4().hex[:12]
            workdir = abs_path(self.cfg["workspace"]) / jid
            workdir.mkdir(parents=True, exist_ok=True)
            inp = workdir / "input.png"
            inp.write_bytes(input_bytes)
            job = Job(jid, inp, workdir, log_path=workdir / "pipeline.log")
            self.jobs[jid] = job
            self.active += 1
            t = threading.Thread(target=self._run, args=(job,resolution,steps,depth_resolution,seed,mode), daemon=True)
            job.thread = t; t.start()
            return job

    def _write(self, job, text):
        job.log_path.parent.mkdir(parents=True, exist_ok=True)
        with job.log_path.open("a", encoding="utf-8", errors="replace") as f:
            f.write(text)

    @staticmethod
    def _script_flags(script: Path) -> str:
        """Read the installed See-through script without importing it."""
        try:
            return script.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return ""

    def _local_model(self, kind: str) -> Path | None:
        """Resolve manually extracted See-through models without contacting Hugging Face."""
        hub = abs_path(self.cfg.get("hf_home", "models/huggingface")) / "hub"
        candidates = {
            "layerdiff_nf4": [hub / "seethroughv0.0.2_layerdiff3d_nf4"],
            "depth_nf4": [hub / "seethroughv0.0.1_marigold_nf4"],
            "layerdiff_bf16": [
                hub / "seethroughv0.0.2_layerdiff3d",
                hub / "models--layerdifforg--seethroughv0.0.2_layerdiff3d" / "snapshots",
            ],
            "depth_bf16": [
                hub / "seethroughv0.0.1_marigold",
                hub / "models--layerdifforg--seethroughv0.0.1_marigold" / "snapshots",
            ],
        }
        for candidate in candidates.get(kind, []):
            if candidate.is_dir() and (candidate / "model_index.json").exists():
                return candidate
            if candidate.name == "snapshots" and candidate.is_dir():
                for snap in candidate.iterdir():
                    if snap.is_dir() and (snap / "model_index.json").exists():
                        return snap
        return None

    def _require_local_models(self, mode: str):
        """Return local model paths; never download anything implicitly."""
        if mode == "quantized":
            ld = self._local_model("layerdiff_nf4")
            depth = self._local_model("depth_nf4")
            if not ld or not depth:
                missing=[]
                if not ld: missing.append("seethroughv0.0.2_layerdiff3d_nf4")
                if not depth: missing.append("seethroughv0.0.1_marigold_nf4")
                raise FileNotFoundError("Missing local model(s): " + ", ".join(missing) + ". Put the extracted folders under models\\huggingface\\hub\\ and retry.")
            return ld, depth
        ld = self._local_model("layerdiff_bf16")
        if not ld:
            raise FileNotFoundError("Missing local BF16 LayerDiff model. Expected models\\huggingface\\hub\\seethroughv0.0.2_layerdiff3d or a cached layerdifforg snapshot.")
        depth = self._local_model("depth_bf16")
        if not depth:
            raise FileNotFoundError("Missing local BF16 Marigold model. Blockswap requires models\\huggingface\\hub\\seethroughv0.0.1_marigold (or a cached models--layerdifforg-style snapshot). The NF4 Marigold folder cannot be passed to the BF16 Blockswap depth loader.")
        return ld, depth

    def _make_local_blockswap_script(self, source: Path, layerdiff: Path, depth: Path, workdir: Path) -> Path:
        """Create a syntax-safe per-job Blockswap wrapper using only local model paths.

        The previous implementation injected assignments after ``parse_args()``
        without preserving the script's indentation, which produced an
        ``IndentationError`` before inference could even start. This version
        changes only existing default/string literals and never injects
        top-level statements into the official main block.
        """
        text = source.read_text(encoding="utf-8", errors="ignore")
        ld = str(layerdiff).replace("\\", "/")
        dp = str(depth).replace("\\", "/")

        # The wrapper runs from a per-job workspace. The official script imports
        # sibling helpers from inference/scripts and package modules from
        # inference/modules, so add both directories before imports execute.
        scripts_dir = str(source.parent).replace("\\", "/")
        inference_dir = str(source.parent.parent).replace("\\", "/")
        repo_dir = str(source.parent.parent.parent).replace("\\", "/")
        common_dir = str((source.parent.parent.parent / "common")).replace("\\", "/")
        # The current See-through checkout keeps `modules` and `utils` under
        # <repo>/common, while its inference scripts import `modules.*` and
        # `utils.*` as top-level packages. Add all required roots explicitly.
        bootstrap = (
            "import sys as _sys\n"
            f"_sys.path.insert(0, {scripts_dir!r})\n"
            f"_sys.path.insert(0, {inference_dir!r})\n"
            f"_sys.path.insert(0, {common_dir!r})\n"
        )
        if "_sys.path.insert(0" not in text:
            text = bootstrap + text

        # The official Blockswap script already exposes --repo_id_layerdiff.
        # Replace its default with the verified local absolute model path.
        import re
        text, n = re.subn(
            r"(parser\.add_argument\(\s*['\"]--repo_id_layerdiff['\"],\s*type=str,\s*default=)['\"][^'\"]*['\"]",
            lambda m: m.group(1) + repr(ld),
            text, count=1, flags=re.S,
        )
        if n == 0:
            raise RuntimeError("Could not locate --repo_id_layerdiff in the installed See-through Blockswap script.")

        # Current official Blockswap has the Marigold repo hard-coded in its
        # Namespace. Replace only that literal, preserving the surrounding
        # indentation and syntax.
        text, n = re.subn(
            r"(repo_id_depth\s*=\s*)['\"]24yearsold/seethroughv0\.0\.1_marigold['\"]",
            lambda m: m.group(1) + repr(dp),
            text, count=1, flags=re.S,
        )
        if n == 0:
            raise RuntimeError("Could not locate the Marigold repo_id_depth in the installed See-through Blockswap script.")

        out = workdir / "inference_psd_blockswap_local.py"
        out.write_text(text, encoding="utf-8", newline="\n")

        # Validate syntax before the GPU process is started.
        import ast
        try:
            ast.parse(text, filename=str(out))
        except SyntaxError as exc:
            raise RuntimeError(f"Generated Blockswap wrapper has invalid Python syntax: {exc}") from exc
        return out

    def _run_process(self, job, cmd, env, stage_prefix=""):
        self._write(job, "\n$ " + " ".join(cmd) + "\n\n")
        p=subprocess.Popen(
            cmd, cwd=str(abs_path(self.cfg["see_through_repo"])),
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1, env=env
        )
        for line in p.stdout:
            self._write(job,line)
            s=line.lower()
            if "building blockswap" in s or "building quantized" in s or "building layerdiff3d" in s:
                job.stage="Loading See-through models"; job.progress=max(job.progress,8)
            elif "running layerdiff" in s:
                job.stage="LayerDiff 3D decomposition"; job.progress=20
            elif "running marigold" in s:
                job.stage="Anime depth estimation"; job.progress=65
            elif "running psd assembly" in s:
                job.stage="Assembling semantic layers"; job.progress=82
            elif "layerdiff3d done" in s:
                job.progress=max(job.progress,60)
            elif "marigold done" in s:
                job.progress=max(job.progress,80)
            elif "psd assembly done" in s:
                job.progress=max(job.progress,95)
        rc=p.wait()
        return rc

    def _run(self, job, resolution, steps, depth_resolution, seed, mode):
        job.status="running"; job.started_at=time.time()
        try:
            repo = abs_path(self.cfg["see_through_repo"])
            scripts = repo / "inference" / "scripts"
            quant_script = scripts / "inference_psd_quantized.py"
            block_script = scripts / "inference_psd_blockswap.py"
            if not scripts.exists():
                raise FileNotFoundError(f"See-through repository not found: {repo}. Run scripts\\install_windows.ps1 first.")
            script = block_script if mode == "blockswap" else quant_script
            if not script.exists():
                raise FileNotFoundError(f"Required See-through script not found: {script}")

            # Resolve manually downloaded models before launching the heavy process.
            # This guarantees zero surprise Hugging Face downloads.
            local_ld, local_depth = self._require_local_models(mode)

            out = job.workdir / "see_through_output"; out.mkdir(exist_ok=True)
            job.output_dir = out
            configured_python = str(self.cfg.get("python_executable", "python")).strip()
            # `python` can resolve to a different Windows installation than the
            # one running FastAPI. Use the current interpreter unless an explicit
            # executable path was configured.
            if not configured_python or Path(configured_python).name.lower() in {"python", "python.exe"}:
                configured_python = sys.executable
            base = [
                configured_python, str(script),
                "--srcp", str(job.input_path), "--save_dir", str(out),
                "--resolution", str(resolution),
                "--num_inference_steps", str(steps),
                "--resolution_depth", str(depth_resolution),
                "--seed", str(seed), "--save_to_psd"
            ]

            source = self._script_flags(script)
            env=os.environ.copy()
            env["HF_HOME"]=str(abs_path(self.cfg["hf_home"]))
            env.setdefault("HF_HUB_DISABLE_XET","1")
            # Safety: never let a decomposition job silently download multi-GB models.
            # Downloads are explicitly opt-in from the UI.
            # Local-model mode: repository paths are absolute local directories.
            # Keep HF offline even if the UI toggle is enabled; this build never
            # silently falls back to network downloads.
            env["HF_HUB_OFFLINE"] = "1"
            job.message = "Local models locked: Hugging Face downloads disabled"
            # Do not force PYTORCH_CUDA_ALLOC_CONF on Windows: some installed
            # PyTorch builds report expandable_segments as unsupported.

            # See-through's current NF4 path uses group offload to lower peak VRAM.
            # Add only flags actually supported by the installed script, so older checkouts
            # remain compatible.
            cmd=list(base)
            if mode == "quantized":
                cmd += ["--repo_id_layerdiff", str(local_ld), "--repo_id_depth", str(local_depth)]
            else:
                # Use a temporary copy so the official third-party checkout remains untouched.
                script = self._make_local_blockswap_script(block_script, local_ld, local_depth, job.workdir)
                base[1] = str(script)
                cmd = list(base)
                source = self._script_flags(block_script)
            if "--group_offload" in source:
                cmd.append("--group_offload")
                job.message="8GB mode: group offload enabled"
            elif mode == "quantized":
                job.message="NF4 mode: installed script has no group-offload flag; using compatibility mode"

            rc=self._run_process(job, cmd, env)
            job.return_code=rc

            # IMPORTANT: See-through NF4 + --cpu_offload is not a safe retry path on
            # this Windows/8GB configuration. The quantized script caches CLIP tag
            # embeddings before inference, and the CPU-offload hooks can leave the
            # token indices on CPU while the quantized CLIP embedding weights are on
            # CUDA. That produces the device-mismatch failure seen in v0.3.1.
            #
            # If NF4 hits a CUDA allocation failure, retry with the official bf16
            # block-swap pipeline in a fresh process. Block-swap is explicitly
            # documented by See-through as an ~8GB path and is much safer here.
            log_text=job.log_path.read_text(encoding="utf-8", errors="replace")
            alloc_failure = any(x in log_text for x in (
                "CUBLAS_STATUS_ALLOC_FAILED", "CUDA out of memory", "CUDA error: out of memory"
            ))
            if rc != 0 and mode == "quantized" and alloc_failure and block_script.exists():
                job.stage="Retrying with Blockswap (8GB safe mode)"; job.progress=6
                local_block = self._make_local_blockswap_script(block_script, self._local_model("layerdiff_bf16") or local_ld, self._local_model("depth_bf16") or local_depth, job.workdir)
                retry=list(base)
                retry[1] = str(local_block)
                retry_source=self._script_flags(block_script)
                # The retry also uses only local model paths.
                self._write(job, "\nLOW-VRAM RETRY: NF4 failed during CUDA allocation; switching to official bf16 blockswap with local models.\n")
                self._write(job, "BLOCKSWAP RETRY: CPU-offload NF4 is intentionally skipped because it caused a device mismatch in CLIP.\n")
                rc=self._run_process(job, retry, env, stage_prefix="blockswap-retry")
                job.return_code=rc

            if rc != 0:
                raise RuntimeError(f"See-through exited with code {rc}. See {job.log_path}")
            candidates=list(out.rglob("*.psd"))
            if not candidates:
                raise RuntimeError("See-through completed but no PSD was found.")
            job.output_psd=candidates[0]
            job.status="completed"; job.stage="Ready"; job.progress=100; job.message=str(job.output_psd)
        except Exception as e:
            job.status="failed"; job.stage="Failed"; job.message=str(e); self._write(job,"\nERROR: "+repr(e)+"\n")
        finally:
            job.finished_at=time.time()
            with self.lock: self.active=max(0,self.active-1)

    def get(self,jid): return self.jobs.get(jid)

manager=JobManager()
