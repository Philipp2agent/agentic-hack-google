"""Project call agent + decision board (based on the gradbot simple_chat demo)."""
import json, pathlib, subprocess, tempfile, threading, time
import fastapi
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import gradbot

HERE = pathlib.Path(__file__).parent
SYSTEM_PROMPT = (HERE / "prompt.txt").read_text()
STATE = HERE / "board_state.json"
APPROVALS = HERE / "approvals.json"
IMG = HERE / "board_img"
IMG.mkdir(exist_ok=True)
LOCK = threading.Lock()

gradbot.init_logging()
app = fastapi.FastAPI(title="DawnDispatch")
cfg = gradbot.config.from_env()
DEFAULT_VOICE_ID = "cLONiZ4hQ8VpQ4Sz"  # fest eingestellt


def make_config(msg: dict) -> gradbot.SessionConfig:
    return gradbot.SessionConfig(
        voice_id=DEFAULT_VOICE_ID,
        language=gradbot.LANGUAGES.get("en"),
        instructions=SYSTEM_PROMPT,
        **({"assistant_speaks_first": True} | cfg.session_kwargs),
    )


@app.websocket("/ws/chat")
async def ws_chat(websocket: fastapi.WebSocket):
    await gradbot.websocket.handle_session(websocket, config=cfg, on_start=make_config)


def _load(path, default):
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


@app.get("/board", response_class=HTMLResponse)
def board():
    return (HERE / "board.html").read_text()


@app.get("/api/board/state")
def board_state():
    s = _load(STATE, {"status": "waiting", "decisions": {}, "transcript": [], "config": {}})
    for k, v in _load(APPROVALS, {}).items():
        if k in s.get("decisions", {}):
            s["decisions"][k].update(v)
    return JSONResponse(s, headers={"Cache-Control": "no-store"})


def _set_approval(key, value):
    with LOCK:
        a = _load(APPROVALS, {})
        a[key] = value
        APPROVALS.write_text(json.dumps(a))


def _dispatch(key, d):
    try:
        repo = tempfile.mkdtemp() + "/r"
        subprocess.run(["git", "clone", "-q", __import__("os").environ.get("DAWN_DISPATCH_REMOTE", ".."), repo], check=True, timeout=90)
        name = "auftraege/nachtschicht-%s-%s.md" % (time.strftime("%H%M"), key)
        pathlib.Path(repo, name).write_text(
            "# Night shift task %s (approved by Philipp on the call)\n\n" % key
            + "Philipp said: %s\n\nUnderstood as: %s\n\nTask: %s\n\n" % (d.get("said", ""), d.get("understood", ""), d.get("task", ""))
            + "hack-chef: assign this to an agent for the night shift and report in STAND.md.\n")
        subprocess.run(["git", "-C", repo, "add", name], check=True)
        subprocess.run(["git", "-C", repo, "commit", "-qm", "nachtschicht: " + (d.get("task") or key)[:60]], check=True)
        subprocess.run(["git", "-C", repo, "push", "-q"], check=True, timeout=90)
        h = subprocess.run(["git", "-C", repo, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
        _set_approval(key, {"approved": True, "dispatch": "queued for the night shift (%s)" % h})
    except Exception as e:
        print("Dispatch fehlgeschlagen:", e, flush=True)
        _set_approval(key, {"approved": True, "dispatch": "approved (queue offline)"})


@app.post("/api/board/approve/{key}")
def approve(key: str):
    d = _load(STATE, {}).get("decisions", {}).get(key)
    if not d:
        return JSONResponse({"ok": False}, status_code=404)
    _set_approval(key, {"approved": True, "dispatch": "sending to your agents ..."})
    threading.Thread(target=_dispatch, args=(key, d), daemon=True).start()
    return {"ok": True}



def _context():
    raw = ""
    try:
        raw = subprocess.run(["git", "-C", __import__("os").environ.get("DAWN_REPO", ".."), "show", "origin/main:src/data/overnight_events.json"], capture_output=True, text=True, timeout=20).stdout
    except Exception:
        pass
    try:
        data = json.loads(raw)
    except Exception:
        data = []
    if isinstance(data, dict):
        data = next((v for v in data.values() if isinstance(v, list)), [])
    items, agents = [], set()
    for e in data:
        if isinstance(e, dict):
            t = e.get("title") or e.get("summary") or e.get("details") or ""
            a = e.get("agent_id") or e.get("agent") or e.get("source") or ""
            items.append({"title": str(t)[:90], "agent": str(a)[:24]})
            if a:
                agents.add(str(a))
    return {"events": len(items), "agents": sorted(agents)[:12], "recent": items[-12:]}


CONTEXT = _context()


@app.get("/api/board/context")
def board_context():
    return CONTEXT


app.mount("/board-img", StaticFiles(directory=str(IMG)), name="board_img")
gradbot.routes.setup(app, config=cfg, static_dir=HERE / "static", with_voices=True)
