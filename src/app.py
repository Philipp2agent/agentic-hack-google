"""DawnDispatch combined entry point (owned by claude-02 / hack-chef).

Mounts whatever has been merged so far; each package is optional, so the app
starts with any subset of src/voice, src/dashboard and src/core present.

Run:  uvicorn src.app:app --host 0.0.0.0 --port 8000
Routes: /call (voice, hack-bau2) · /dashboard (hack-bau3) · / -> /dashboard
"""
from __future__ import annotations

import logging
import pathlib

import fastapi
import fastapi.responses
import fastapi.staticfiles

log = logging.getLogger("dawndispatch")
REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]

app = fastapi.FastAPI(title="DawnDispatch")


@app.get("/api/health")
async def health():
    return {"status": "ok", "app": "DawnDispatch"}


@app.get("/")
async def index():
    return fastapi.responses.RedirectResponse("/dashboard")


# --- voice (hack-bau2): /call, /ws/chat, /ws/tts, /api/voices, /api/audio-config ---
try:
    from src.voice.server import router as voice_router  # noqa: E402

    app.include_router(voice_router)
    log.info("voice router mounted")
except Exception as exc:  # module missing until agent/hack-bau2 is merged
    log.warning("voice router not mounted: %s", exc)

# --- dashboard (hack-bau3): /dashboard, /api/state, /api/graph, /api/actions/{id}/confirm ---
try:
    from src.dashboard.app import router as dashboard_router  # noqa: E402

    app.include_router(dashboard_router)
    log.info("dashboard router mounted")
except Exception as exc:  # module missing until agent/hack-bau3 is merged
    log.warning("dashboard router not mounted: %s", exc)

# --- static files: gradbot's bundled audio JS first (more specific prefix wins) ---
try:
    import gradbot.routes  # noqa: E402

    app.mount("/static/js", fastapi.staticfiles.StaticFiles(directory=gradbot.routes._JS_AUDIO_DIR), name="bundled_js")
except Exception as exc:
    log.warning("gradbot js not mounted: %s", exc)

for prefix, folder in (
    ("/static/voice", REPO_ROOT / "src" / "voice" / "static"),
    ("/static", REPO_ROOT / "src" / "dashboard" / "static"),
    ("/assets", REPO_ROOT / "assets"),
):
    if folder.is_dir():
        app.mount(prefix, fastapi.staticfiles.StaticFiles(directory=folder), name=prefix.strip("/").replace("/", "_"))

_audio = REPO_ROOT / "src" / "data" / "audio"
_audio.mkdir(parents=True, exist_ok=True)
app.mount("/data/audio", fastapi.staticfiles.StaticFiles(directory=_audio), name="audio")
