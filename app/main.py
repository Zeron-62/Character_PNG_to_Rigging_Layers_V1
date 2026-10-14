from pathlib import Path
import io

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse

from .job_manager import manager
from .psd_export import export_layers, export_zip, inspect_psd, render_layer
from .upscaler import upscale_png_directory, zip_upscaled_layers

ROOT = Path(__file__).resolve().parents[1]
APP_VERSION = "2.0.0"
app = FastAPI(title="Anime Layer Studio", version=APP_VERSION, description="Local-first AI-assisted anime character layer decomposition, PSD inspection, transparent PNG export, and 4x Real-ESRGAN anime upscaling.")


@app.get("/", response_class=HTMLResponse)
def index():
    return (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")


@app.get("/api/health")
def health():
    return {
        "ok": True,
        "version": APP_VERSION,
        "active_jobs": manager.active,
        "backend": "FastAPI + See-through V3",
        "model_downloads": "disabled; local model files required",
    }


@app.post("/api/jobs")
async def create_job(
    file: UploadFile = File(...),
    resolution: int = 1024,
    steps: int = 24,
    depth_resolution: int = 720,
    seed: int = 42,
    mode: str = "blockswap",
):
    filename = file.filename or ""
    if not filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
        raise HTTPException(400, "Input must be PNG/JPEG/WebP")
    if mode not in {"blockswap", "quantized"}:
        raise HTTPException(400, "Mode must be blockswap or quantized")
    if resolution not in {768, 1024, 1280}:
        raise HTTPException(400, "Resolution must be 768, 1024, or 1280")
    if not 10 <= steps <= 40:
        raise HTTPException(400, "Steps must be between 10 and 40")
    if not 384 <= depth_resolution <= 768:
        raise HTTPException(400, "Depth resolution must be between 384 and 768")

    try:
        job = manager.create(
            await file.read(), filename, resolution, steps, depth_resolution, seed, mode
        )
        return {"id": job.id, "status": job.status}
    except Exception as exc:
        raise HTTPException(409, str(exc)) from exc


@app.get("/api/jobs/{jid}")
def job_status(jid: str):
    job = manager.get(jid)
    if not job:
        raise HTTPException(404, "Job not found")
    return {
        "id": job.id,
        "status": job.status,
        "progress": job.progress,
        "stage": job.stage,
        "message": job.message,
        "log": f"/api/jobs/{jid}/log",
    }


@app.get("/api/jobs/{jid}/log", response_class=HTMLResponse)
def job_log(jid: str):
    job = manager.get(jid)
    if not job or not job.log_path:
        raise HTTPException(404, "Job not found")
    content = (
        job.log_path.read_text(encoding="utf-8", errors="replace")
        if job.log_path.exists()
        else ""
    )
    escaped = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return '<html><body><pre style="white-space:pre-wrap;font-family:monospace">' + escaped + "</pre></body></html>"


@app.get("/api/jobs/{jid}/psd")
def download_psd(jid: str):
    job = manager.get(jid)
    if not job or not job.output_psd:
        raise HTTPException(404, "PSD not ready")
    return FileResponse(job.output_psd, media_type="application/psd", filename=job.output_psd.name)


@app.get("/api/jobs/{jid}/inspect")
def inspect_job_psd(jid: str):
    job = manager.get(jid)
    if not job or not job.output_psd:
        raise HTTPException(404, "PSD not ready")
    try:
        return inspect_psd(job.output_psd)
    except Exception as exc:
        raise HTTPException(500, f"PSD inspection failed: {exc}") from exc


@app.get("/api/jobs/{jid}/layer/{layer_id}/preview")
def layer_preview(jid: str, layer_id: int):
    job = manager.get(jid)
    if not job or not job.output_psd:
        raise HTTPException(404, "PSD not ready")
    try:
        image = render_layer(job.output_psd, layer_id)
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        return StreamingResponse(buffer, media_type="image/png")
    except Exception as exc:
        raise HTTPException(400, f"Layer preview failed: {exc}") from exc


@app.post("/api/jobs/{jid}/export")
def export_job_layers(jid: str):
    job = manager.get(jid)
    if not job or job.status != "completed" or not job.output_psd:
        raise HTTPException(409, "Job is not complete")
    output_dir = job.workdir / "layers_png"
    files = export_layers(job.output_psd, output_dir)
    return {"count": len(files), "files": [path.name for path in files]}


@app.get("/api/jobs/{jid}/export_zip")
def export_job_layers_zip(jid: str):
    job = manager.get(jid)
    if not job or not job.output_psd:
        raise HTTPException(409, "PSD is not ready")
    output_dir = job.workdir / "layers_png"
    zip_path, _files = export_zip(job.output_psd, output_dir)
    return FileResponse(zip_path, media_type="application/zip", filename="anime_layers.zip")


@app.post("/api/jobs/{jid}/upscale")
def upscale_job_layers(jid: str, tile: int = 128):
    """Upscale exported PSD layers 4x after the decomposition subprocess has finished."""
    job = manager.get(jid)
    if not job or job.status != "completed" or not job.output_psd:
        raise HTTPException(409, "Decomposition must be complete before upscaling")
    layer_dir = job.workdir / "layers_png"
    try:
        if not layer_dir.is_dir() or not any(layer_dir.glob("*.png")):
            export_layers(job.output_psd, layer_dir)
        output_dir = job.workdir / "layers_png_4x"
        if output_dir.exists():
            import shutil
            shutil.rmtree(output_dir)
        files = upscale_png_directory(layer_dir, output_dir, tile=tile)
        archive = zip_upscaled_layers(files, job.workdir / "anime_layers_4x.zip")
        return {"count": len(files), "scale": 4, "tile": tile, "download": f"/api/jobs/{jid}/upscale_zip", "archive": archive.name}
    except FileNotFoundError as exc:
        raise HTTPException(409, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, f"Upscaling failed: {exc}") from exc


@app.get("/api/jobs/{jid}/upscale_zip")
def download_upscaled_layers(jid: str):
    job = manager.get(jid)
    archive = job.workdir / "anime_layers_4x.zip" if job else None
    if not job or not archive or not archive.is_file():
        raise HTTPException(404, "Upscaled layer ZIP is not ready. Run upscaling first.")
    return FileResponse(archive, media_type="application/zip", filename="anime_layers_4x.zip")
