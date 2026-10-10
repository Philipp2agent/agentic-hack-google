"""DawnDispatch Desktop Web Dashboard FastAPI Application.

Provides the interactive Knowledge Graph dashboard, Call Transcript playback,
and Human Checkpoint 1-click confirmation interface.
"""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from src.core.action_engine import confirm_checkpoint
from src.core.graph_engine import generate_and_save_graph_after
from src.core.models import (
    load_actions,
    load_agenda,
    load_decisions,
    load_knowledge_graph,
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "src" / "data"
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
STATIC_DIR = Path(__file__).resolve().parent / "static"
ASSETS_DIR = BASE_DIR / "assets"

app = FastAPI(
    title="DawnDispatch Dashboard",
    description="Autonomous Commute Voice Dispatcher & Knowledge Graph Dashboard",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

if ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")


def _read_json_file(file_path: Path, default_factory: Any = None) -> Any:
    if not file_path.exists():
        if default_factory is not None:
            return default_factory()
        return {}
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


@app.get("/", include_in_schema=False)
def root_redirect():
    """Redirect root path to /dashboard."""
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_view():
    """Render main DawnDispatch dashboard interface."""
    index_path = TEMPLATES_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Dashboard template not found")
    return FileResponse(index_path, media_type="text/html")


@app.get("/dashboard/checkpoint/{item_id}", response_class=HTMLResponse)
def dashboard_checkpoint_view(item_id: str):
    """Render dashboard focused on a specific irreversible human checkpoint."""
    index_path = TEMPLATES_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Dashboard template not found")
    return FileResponse(index_path, media_type="text/html")


@app.get("/api/graph/before")
def get_graph_before():
    """Return pre-call knowledge graph (unresolved overnight state)."""
    graph_path = DATA_DIR / "knowledge_graph_before.json"
    if not graph_path.exists():
        raise HTTPException(status_code=404, detail="knowledge_graph_before.json not found")
    return _read_json_file(graph_path, dict)


@app.get("/api/graph/after")
def get_graph_after():
    """Return post-call knowledge graph (resolved state with decisions & actions)."""
    graph_path = DATA_DIR / "knowledge_graph_after.json"
    if not graph_path.exists():
        raise HTTPException(status_code=404, detail="knowledge_graph_after.json not found")
    return _read_json_file(graph_path, dict)


@app.get("/api/transcript")
def get_transcript():
    """Return the 60-second commute call transcript between lead and DawnDispatch."""
    transcript_path = DATA_DIR / "transcript.json"
    if transcript_path.exists():
        return _read_json_file(transcript_path)

    # Fallback default transcript
    return {
        "call_id": "call-20261010-0830",
        "lead": "Philipp",
        "agent": "DawnDispatch",
        "duration_seconds": 60,
        "turns": [
            {
                "index": 1,
                "time": "00:03",
                "speaker": "DawnDispatch",
                "text": "Good morning Philipp. Swarm overnight triage ready. How much time do you have?",
                "tag": "Opening",
            },
            {
                "index": 2,
                "time": "00:08",
                "speaker": "Philipp",
                "text": "Got 60 seconds walking down to the office.",
                "tag": "Cadence Match",
            },
            {
                "index": 3,
                "time": "00:15",
                "speaker": "DawnDispatch",
                "text": "Rapid fire. Item 1: PR #4 auth schema refactor — approve staging migration?",
                "tag": "Rapid Fire #1",
            },
            {
                "index": 4,
                "time": "00:22",
                "speaker": "Philipp",
                "text": "Yes, approve staging.",
                "tag": "Decision: APPROVE",
            },
        ],
    }


@app.get("/api/actions")
def get_actions():
    """Return current action execution records and checkpoint statuses."""
    actions_path = DATA_DIR / "actions.json"
    return _read_json_file(actions_path, list)


@app.get("/api/agenda")
def get_agenda():
    """Return synthesized morning agenda items."""
    agenda_path = DATA_DIR / "agenda.json"
    return _read_json_file(agenda_path, list)


@app.post("/api/actions/{action_id}/confirm")
def confirm_action_checkpoint(action_id: str):
    """Confirm an irreversible human checkpoint for a given action ID."""
    actions_path = DATA_DIR / "actions.json"
    try:
        updated_action = confirm_checkpoint(
            action_id_or_item_id=action_id,
            actions_path=actions_path,
            confirmed_by="Philipp (Lead Web Dashboard 1-Click)",
        )
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Action or item '{action_id}' not found",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to confirm checkpoint: {e}",
        )

    # Sync and regenerate post-call knowledge graph after checkpoint approval
    try:
        generate_and_save_graph_after(
            graph_before_path=DATA_DIR / "knowledge_graph_before.json",
            decisions_path=DATA_DIR / "decisions.json",
            actions_path=actions_path,
            output_path=DATA_DIR / "knowledge_graph_after.json",
        )
    except Exception:
        pass

    return {
        "status": "success",
        "action_id": updated_action.action_id,
        "item_id": updated_action.item_id,
        "action": updated_action.model_dump(),
        "all_actions": _read_json_file(actions_path, list),
    }


@app.post("/api/checkpoint/{item_id}/confirm")
def confirm_checkpoint_by_item(item_id: str):
    """Confirm an irreversible checkpoint by its referenced agenda item ID."""
    return confirm_action_checkpoint(action_id=item_id)


@app.get("/api/health")
def health_check():
    """Dashboard health check."""
    return {
        "status": "ok",
        "service": "DawnDispatch Dashboard",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def main():
    """CLI entry point for running the dashboard."""
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    host = os.environ.get("HOST", "0.0.0.0")
    uvicorn.run("src.dashboard.app:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
