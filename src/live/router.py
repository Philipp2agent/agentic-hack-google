"""FastAPI router for the live mission-control screen (contract: docs/LIVE-EVENTS.md).

Mounted from src/app.py with ``from src.live.router import router`` (try-import).

Routes
  GET  /live                               the screen (dark, 16:9, filmed through the glasses)
  GET  /live/static/{file}                 its css/js
  WS   /ws/events                          first message {"type":"snapshot","data":{...state}}, then one event per message
  GET  /api/live/state                     current session (events so far) for reloads
  GET  /api/live/graph?stage=before|after  knowledge graph seed for the screen
  POST /api/live/event                     publish one event or a list (used by tools/live_demo_events.py)
  POST /api/live/checkpoint/{item_id}      laptop click -> publishes checkpoint_resolved {item_id, approved}
  POST /api/live/replay?speed=1&max_gap=6  play the last recorded session again (video takes)
  POST /api/live/reset                     clear state for the next take
"""
from __future__ import annotations

import asyncio
import json
import pathlib
from typing import Any

from fastapi import APIRouter, Body, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse

from src.live import bus as live_bus

router = APIRouter(tags=["live"])

STATIC_DIR = pathlib.Path(__file__).resolve().parent / "static"
GRAPH_FILES = {"before": "knowledge_graph_before.json", "after": "knowledge_graph_after.json"}
MEDIA_TYPES = {".js": "application/javascript", ".css": "text/css", ".html": "text/html", ".svg": "image/svg+xml"}


@router.get("/live", response_class=HTMLResponse, include_in_schema=False)
async def live_page():
    return FileResponse(STATIC_DIR / "index.html", media_type="text/html")


@router.get("/live/static/{filename}", include_in_schema=False)
async def live_static(filename: str):
    path = STATIC_DIR / pathlib.Path(filename).name  # no sub-folders, no traversal
    if not path.is_file():
        raise HTTPException(status_code=404, detail="not found")
    return FileResponse(path, media_type=MEDIA_TYPES.get(path.suffix, "application/octet-stream"))


@router.get("/api/live/state")
async def live_state():
    return live_bus.state()


@router.get("/api/live/graph")
async def live_graph(stage: str = Query("before", pattern="^(before|after)$")):
    path = live_bus.data_dir() / GRAPH_FILES[stage]
    if not path.is_file():
        raise HTTPException(status_code=404, detail=f"{path.name} not found")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


@router.post("/api/live/event", status_code=202)
async def live_event(payload: Any = Body(...)):
    items = payload if isinstance(payload, list) else [payload]
    if not items:
        raise HTTPException(status_code=422, detail="empty event list")
    accepted: list[dict[str, Any]] = []
    try:
        for item in items:
            accepted.append(await live_bus.publish(item))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    unknown = sorted({e["type"] for e in accepted if e["type"] not in live_bus.EVENT_TYPES})
    return {"accepted": len(accepted), "unknown_types": unknown, "events": accepted}


@router.post("/api/live/checkpoint/{item_id}")
async def live_checkpoint(item_id: str, payload: dict[str, Any] | None = Body(None)):
    approved = bool((payload or {}).get("approved", True))
    event = await live_bus.publish({"type": "checkpoint_resolved", "data": {"item_id": item_id, "approved": approved}})
    return {"status": "ok", "event": event}


@router.post("/api/live/replay")
async def live_replay(speed: float = Query(1.0, gt=0), max_gap: float = Query(6.0, ge=0)):
    count = await live_bus.replay(speed=speed, max_gap_s=max_gap)
    return {"status": "replaying" if count else "empty", "events": count, "speed": speed, "max_gap_s": max_gap}


@router.post("/api/live/reset")
async def live_reset():
    cleared = live_bus.reset()
    return {"status": "reset", "cleared": cleared}


@router.websocket("/ws/events")
async def live_events_socket(websocket: WebSocket):
    await websocket.accept()
    queue = live_bus.subscribe()
    get_task: asyncio.Task | None = None
    recv_task: asyncio.Task | None = None
    try:
        await websocket.send_json({"type": "snapshot", "ts": live_bus.now_iso(), "data": live_bus.state()})
        get_task = asyncio.create_task(queue.get())
        recv_task = asyncio.create_task(websocket.receive_text())
        while True:
            done, _ = await asyncio.wait({get_task, recv_task}, return_when=asyncio.FIRST_COMPLETED)
            if get_task in done:
                await websocket.send_json(get_task.result())
                get_task = asyncio.create_task(queue.get())
            if recv_task in done:
                try:
                    recv_task.result()  # client text (pings) is ignored
                except (WebSocketDisconnect, RuntimeError):
                    break
                recv_task = asyncio.create_task(websocket.receive_text())
    except (WebSocketDisconnect, RuntimeError, ConnectionError):
        pass
    finally:
        for task in (get_task, recv_task):
            if task and not task.done():
                task.cancel()
        live_bus.unsubscribe(queue)
