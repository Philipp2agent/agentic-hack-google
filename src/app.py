"""DawnDispatch combined entry point (owned by claude-02 / hack-chef).

Mounts whatever has been merged so far; each package is optional, so the app
starts with any subset of src/voice, src/dashboard and src/core present.

Run:  uvicorn src.app:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import logging
import pathlib

import fastapi
import fastapi.staticfiles

log = logging.getLogger("dawndispatch")
REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]

app = fastapi.FastAPI(title="DawnDispatch")


@app.get("/api/health")
async def health():
    return {"status": "ok", "app": "DawnDispatch"}


# --- voice (hack-bau2): /ws/chat, /ws/tts, /api/voices, /api/audio-config ---
try:
    from src.voice.server import router as voice_router  # noqa: E402

    app.include_router(voice_router)
    log.info("voice router mounted")
except Exception as exc:  # module missing until agent/hack-bau2 is merged
    log.warning("voice router not mounted: %s", exc)

# --- dashboard (hack-bau3): /, /call, /api/state, /api/actions/{id}/confirm ---
try:
    from src.dashboard.app import router as dashboard_router  # noqa: E402

    app.include_router(dashboard_router)
    log.info("dashboard router mounted")
except Exception as exc:  # module missing until agent/hack-bau3 is merged
    log.warning("dashboard router not mounted: %s", exc)

# --- static files: gradbot's bundled audio JS first (more specific prefix) ---
try:
    import gradbot.routes  # noqa: E402

    app.mount("/static/js", fastapi.staticfiles.StaticFiles(directory=gradbot.routes._JS_AUDIO_DIR), name="bundled_js")
except Exception as exc:
    log.warning("gradbot js not mounted: %s", exc)

_dash_static = REPO_ROOT / "src" / "dashboard" / "static"
if _dash_static.is_dir():
    app.mount("/static", fastapi.staticfiles.StaticFiles(directory=_dash_static), name="static")

_assets = REPO_ROOT / "assets"
if _assets.is_dir():
    app.mount("/assets", fastapi.staticfiles.StaticFiles(directory=_assets), name="assets")

_audio = REPO_ROOT / "src" / "data" / "audio"
_audio.mkdir(parents=True, exist_ok=True)
app.mount("/data/audio", fastapi.staticfiles.StaticFiles(directory=_audio), name="audio")
