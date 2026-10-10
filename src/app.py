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


# --- voice (claude-03): simple_chat-style app mounted at /voice like gradbot's demos/app.py ------------
try:
    from src.voice.server import api_router as voice_api_router
    from src.voice.server import app as voice_app
    from src.voice.server import cfg as voice_cfg
    from src.voice.server import ws_chat as voice_ws_chat

    @app.get("/call", include_in_schema=False)
    async def call_redirect():
        """The phone opens /call; the page itself lives at /voice/ (relative paths exactly as in simple_chat)."""
        return fastapi.responses.RedirectResponse("/voice/")

    @app.websocket("/ws/chat")
    async def ws_chat_root(websocket: fastapi.WebSocket):
        await voice_ws_chat(websocket)

    @app.get("/api/audio-config")
    async def audio_config_root():
        return {"pcm": bool(voice_cfg.use_pcm)}

    app.include_router(voice_api_router)  # /api/call/* at the root too (dashboard, live placeholder)

    _SIM_PAGE = REPO_ROOT / "src" / "voice" / "static" / "call.html"

    @app.get("/call/sim", include_in_schema=False)
    async def call_simulation_page():
        """hack-bau2's static incoming-call simulation (no backend audio), asset paths rewritten for this app."""
        if not _SIM_PAGE.exists():
            return fastapi.responses.JSONResponse({"error": "call.html not found"}, status_code=404)
        html = _SIM_PAGE.read_text(encoding="utf-8").replace('"/static/call.', '"/static/voice/call.')
        return fastapi.responses.HTMLResponse(html)

    MOUNTED["voice"] = True
except Exception as exc:  # pragma: no cover
    log.warning("voice app not mounted: %s", exc)
    voice_app = None
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

# --- legacy text simulation (hack-bau2, src/voice/app.py): /ws/call + /api/end_call for /call/sim ---
try:
    from src.voice.app import app as voice_sim_app

    taken = _existing_paths()
    for route in voice_sim_app.routes:
        if isinstance(route, (APIRoute, APIWebSocketRoute)) and route.path not in taken:
            app.router.routes.append(route)
    MOUNTED["voice_sim"] = True
except Exception as exc:  # pragma: no cover
    log.warning("voice simulation routes not mounted: %s", exc)
    MOUNTED["voice_sim"] = False

# --- live screen (claude-04): /live, /ws/events, /api/live/* -----------------------------------
try:
    from src.live.router import router as live_router

    app.include_router(live_router)
    MOUNTED["live"] = True
except Exception as exc:
    log.info("live router not mounted (%s)", exc)
    MOUNTED["live"] = False

if "/live" not in _existing_paths():
    _LIVE_PLACEHOLDER = REPO_ROOT / "src" / "voice" / "static" / "live_placeholder.html"

    @app.get("/live", include_in_schema=False)
    async def live_placeholder():
        """Stand-in until src/live (claude-04) is merged: shows the recorded call state instead of 404."""
        if _LIVE_PLACEHOLDER.exists():
            return fastapi.responses.FileResponse(_LIVE_PLACEHOLDER, media_type="text/html")
        return fastapi.responses.HTMLResponse("<h1>DawnDispatch live screen</h1><p>src/live not merged yet.</p>")

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

# hack-bau3's templates/index.html has relative fallbacks (graph.js, style.css) that resolve to the site root
@app.get("/graph.js", include_in_schema=False)
async def _dashboard_graph_js_alias():
    return fastapi.responses.RedirectResponse("/static/graph.js")


@app.get("/style.css", include_in_schema=False)
async def _dashboard_style_alias():
    return fastapi.responses.RedirectResponse("/static/style.css")


if voice_app is not None:
    app.mount("/voice", voice_app, name="voice")  # /voice/ page, /voice/ws/chat, /voice/static/js, /voice/api/voices

_audio = REPO_ROOT / "src" / "data" / "audio"
_audio.mkdir(parents=True, exist_ok=True)
app.mount("/data/audio", fastapi.staticfiles.StaticFiles(directory=_audio), name="audio")
