"""DawnDispatch entry point (claude-03): ONE process serves the phone call, the dashboard and the live screen.

Run:   uvicorn src.app:app --host 127.0.0.1 --port 8090      (or: python -m src.main)
Routes:
  /call        phone start page -> WebSocket /ws/chat (gradbot: Gradium STT/TTS + Gemini)   src/voice/server.py
  /call/sim    hack-bau2's static incoming-call simulation (no backend audio)
  /dashboard   before/after knowledge graph, transcript, human checkpoints                 src/dashboard/app.py
  /live        mission-control screen fed by the live event bus (claude-04, optional)      src/live/router.py
  /api/health  {"status": "ok", "mounted": {...}}
Each package is optional: the app starts with whatever is importable and says so in /api/health.
"""
from __future__ import annotations

import logging
import pathlib

import fastapi
import fastapi.responses
import fastapi.staticfiles
from fastapi.routing import APIRoute, APIWebSocketRoute

log = logging.getLogger("dawndispatch")
REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]

app = fastapi.FastAPI(title="DawnDispatch", version="1.0.0")
MOUNTED: dict[str, bool] = {}


@app.get("/api/health")
async def health():
    return {"status": "ok", "app": "DawnDispatch", "mounted": MOUNTED}


@app.get("/", include_in_schema=False)
async def index():
    return fastapi.responses.RedirectResponse("/dashboard")


def _existing_paths() -> set[str]:
    """Paths already served, including routers FastAPI >= 0.143 keeps nested after include_router."""
    paths: set[str] = set()
    for r in app.routes:
        inner = getattr(r, "original_router", None)
        for sub in (inner.routes if inner is not None else [r]):
            if getattr(sub, "path", None):
                paths.add(sub.path)
    return paths


# --- voice (claude-03): /call, /call/sim, /ws/chat, /api/audio-config, /api/call/* -------------
try:
    from src.voice.server import router as voice_router

    app.include_router(voice_router)
    MOUNTED["voice"] = True
except Exception as exc:  # pragma: no cover
    log.warning("voice router not mounted: %s", exc)
    MOUNTED["voice"] = False

# --- dashboard (hack-bau3): its FastAPI app's API routes, skipping duplicates and its static mounts ---
try:
    from src.dashboard.app import app as dashboard_app

    taken = _existing_paths()
    for route in dashboard_app.routes:
        if isinstance(route, (APIRoute, APIWebSocketRoute)) and route.path not in taken:
            app.router.routes.append(route)
    MOUNTED["dashboard"] = True
except Exception as exc:  # pragma: no cover
    log.warning("dashboard routes not mounted: %s", exc)
    MOUNTED["dashboard"] = False

# --- live screen (claude-04): /live, /ws/events, /api/live/* -----------------------------------
try:
    from src.live.router import router as live_router

    app.include_router(live_router)
    MOUNTED["live"] = True
except Exception as exc:
    log.info("live router not mounted (%s)", exc)
    MOUNTED["live"] = False

# --- static files: gradbot's bundled audio JS first (more specific prefix wins) --------------
try:
    import gradbot.routes

    app.mount("/static/js", fastapi.staticfiles.StaticFiles(directory=gradbot.routes._JS_AUDIO_DIR), name="bundled_js")
    MOUNTED["gradbot_js"] = True
except Exception as exc:  # pragma: no cover
    log.warning("gradbot js not mounted: %s", exc)
    MOUNTED["gradbot_js"] = False

for prefix, folder in (
    ("/static/voice", REPO_ROOT / "src" / "voice" / "static"),
    ("/static/live", REPO_ROOT / "src" / "live" / "static"),
    ("/static", REPO_ROOT / "src" / "dashboard" / "static"),
    ("/assets", REPO_ROOT / "assets"),
):
    if folder.is_dir():
        app.mount(prefix, fastapi.staticfiles.StaticFiles(directory=folder), name=prefix.strip("/").replace("/", "_"))

_audio = REPO_ROOT / "src" / "data" / "audio"
_audio.mkdir(parents=True, exist_ok=True)
app.mount("/data/audio", fastapi.staticfiles.StaticFiles(directory=_audio), name="audio")
