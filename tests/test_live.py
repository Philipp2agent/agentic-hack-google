"""Tests for src/live: event bus, router (/live, /api/live/*, /ws/events) and the demo script.

Recording goes to a temp DAWN_DATA_DIR so the committed seeds in src/data stay untouched.
"""
from __future__ import annotations

import asyncio
import json
import os
import pathlib
import shutil
import socket
import subprocess
import sys
import time
import urllib.request

import pytest
from fastapi.testclient import TestClient

from src.live import bus as live_bus
from src.live.app import app

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def isolated_data_dir(tmp_path, monkeypatch):
    """Point the recording at a temp folder (with the graph seed copied in) and start from an empty bus."""
    shutil.copy(REPO_ROOT / "src" / "data" / "knowledge_graph_before.json", tmp_path / "knowledge_graph_before.json")
    monkeypatch.setenv("DAWN_DATA_DIR", str(tmp_path))
    live_bus.bus.reset()
    yield tmp_path
    live_bus.bus.reset()


def _lines(path: pathlib.Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


# ---------------------------------------------------------------- bus
def test_publish_normalizes_and_records(isolated_data_dir):
    ev = asyncio.run(live_bus.publish({"type": "time_budget", "data": {"seconds": 60}}))
    assert ev["type"] == "time_budget" and ev["seq"] == 1 and ev["ts"].endswith("Z")
    st = live_bus.state()
    assert st["count"] == 1 and st["events"][0]["data"] == {"seconds": 60}
    assert _lines(isolated_data_dir / "live_session.jsonl") == st["events"]


def test_publish_rejects_bad_events():
    with pytest.raises(ValueError):
        live_bus.emit({"data": {}})
    with pytest.raises(ValueError):
        live_bus.emit({"type": "decision", "data": "APPROVE"})
    with pytest.raises(ValueError):
        live_bus.emit("call_started")


def test_subscriber_receives_events():
    async def run():
        queue = live_bus.subscribe()
        try:
            await live_bus.publish({"type": "user_said", "data": {"text": "yes"}})
            got = await asyncio.wait_for(queue.get(), 1)
        finally:
            live_bus.unsubscribe(queue)
        return got

    got = asyncio.run(run())
    assert got["type"] == "user_said" and got["data"]["text"] == "yes"
    assert live_bus.bus.subscriber_count == 0


def test_emit_from_worker_thread_reaches_loop_subscriber():
    async def run():
        queue = live_bus.subscribe()
        try:
            await asyncio.to_thread(live_bus.emit, {"type": "brief_ready", "data": {}})
            got = await asyncio.wait_for(queue.get(), 1)
        finally:
            live_bus.unsubscribe(queue)
        return got

    assert asyncio.run(run())["type"] == "brief_ready"


def test_reset_clears_state_but_keeps_recording_until_next_event(isolated_data_dir):
    rec = isolated_data_dir / "live_session.jsonl"
    live_bus.emit({"type": "call_started", "data": {"opening": "hi"}})
    live_bus.emit({"type": "user_said", "data": {"text": "60 seconds"}})
    assert len(_lines(rec)) == 2
    assert live_bus.reset() == 2
    assert live_bus.state()["count"] == 0
    assert len(_lines(rec)) == 2, "recording survives reset so replay still works"
    live_bus.emit({"type": "call_started", "data": {"opening": "take two"}})
    assert [e["type"] for e in _lines(rec)] == ["call_started"]
    assert live_bus.state()["events"][0]["seq"] == 1


def test_new_call_after_call_ended_starts_new_session(isolated_data_dir):
    rec = isolated_data_dir / "live_session.jsonl"
    live_bus.emit({"type": "call_started", "data": {}})
    live_bus.emit({"type": "call_ended", "data": {"duration_s": 3}})
    live_bus.emit({"type": "call_started", "data": {}})
    assert [e["type"] for e in live_bus.state()["events"]] == ["call_started"]
    assert [e["type"] for e in _lines(rec)] == ["call_started"]


def test_replay_republishes_recording_in_order(isolated_data_dir):
    rec = isolated_data_dir / "live_session.jsonl"
    for t in ("call_started", "time_budget", "decision"):
        live_bus.emit({"type": t, "data": {"x": t}})
    live_bus.reset()

    async def run():
        queue = live_bus.subscribe()
        try:
            n = await live_bus.replay(speed=1000, wait=True)
            msgs = []
            while not queue.empty():
                msgs.append(queue.get_nowait())
        finally:
            live_bus.unsubscribe(queue)
        return n, msgs

    n, msgs = asyncio.run(run())
    assert n == 3
    assert [m["type"] for m in msgs] == ["reset", "replay_started", "call_started", "time_budget", "decision", "replay_finished"]
    replayed = [m for m in msgs if m.get("replay")]
    assert [m["data"]["x"] for m in replayed] == ["call_started", "time_budget", "decision"]
    assert [e["type"] for e in live_bus.state()["events"]] == ["call_started", "time_budget", "decision"]
    assert len(_lines(rec)) == 3, "replay must not append to the recording"


def test_replay_without_recording_is_a_noop():
    assert asyncio.run(live_bus.replay(wait=True)) == 0


# ---------------------------------------------------------------- router
@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_live_page_and_static(client):
    r = client.get("/live")
    assert r.status_code == 200 and "text/html" in r.headers["content-type"]
    assert "MISSION CONTROL" in r.text and "/ws/events" in client.get("/live/static/live.js").text
    assert client.get("/live/static/live.css").status_code == 200
    assert client.get("/live/static/../router.py").status_code in (404, 422)
    assert client.get("/", follow_redirects=False).headers["location"] == "/live"


def test_graph_endpoint_serves_seed(client):
    r = client.get("/api/live/graph")
    assert r.status_code == 200
    body = r.json()
    assert body["stage"] == "BEFORE" and any(n["type"] == "agenda" for n in body["nodes"])
    assert client.get("/api/live/graph?stage=after").status_code == 404  # not copied into the temp dir
    assert client.get("/api/live/graph?stage=nope").status_code == 422


def test_event_endpoint_accepts_single_and_list(client):
    r = client.post("/api/live/event", json={"type": "call_started", "data": {"opening": "hi"}})
    assert r.status_code == 202 and r.json()["accepted"] == 1
    r = client.post("/api/live/event", json=[{"type": "time_budget", "data": {"seconds": 45}}, {"type": "mystery"}])
    assert r.status_code == 202 and r.json()["accepted"] == 2 and r.json()["unknown_types"] == ["mystery"]
    assert client.post("/api/live/event", json={"data": {}}).status_code == 422
    assert client.post("/api/live/event", json=[]).status_code == 422
    st = client.get("/api/live/state").json()
    assert st["count"] == 3 and [e["seq"] for e in st["events"]] == [1, 2, 3]


def test_checkpoint_click_publishes_checkpoint_resolved(client):
    r = client.post("/api/live/checkpoint/agenda-03", json={"approved": False})
    assert r.status_code == 200
    ev = r.json()["event"]
    assert ev["type"] == "checkpoint_resolved" and ev["data"] == {"item_id": "agenda-03", "approved": False}
    r = client.post("/api/live/checkpoint/agenda-03")
    assert r.json()["event"]["data"]["approved"] is True


def test_reset_and_replay_endpoints(client):
    client.post("/api/live/event", json={"type": "call_started", "data": {}})
    r = client.post("/api/live/reset")
    assert r.json() == {"status": "reset", "cleared": 1}
    assert client.get("/api/live/state").json()["count"] == 0
    r = client.post("/api/live/replay?speed=1000")
    assert r.status_code == 200 and r.json()["status"] == "replaying" and r.json()["events"] == 1
    client.post("/api/live/reset")
    assert client.post("/api/live/replay").json()["status"] == "replaying"  # recording still there
    assert client.post("/api/live/replay?speed=0").status_code == 422


def test_websocket_snapshot_then_stream(client):
    client.post("/api/live/event", json={"type": "call_started", "data": {"opening": "hi"}})
    with client.websocket_connect("/ws/events") as ws:
        snap = ws.receive_json()
        assert snap["type"] == "snapshot" and [e["type"] for e in snap["data"]["events"]] == ["call_started"]
        client.post("/api/live/event", json={"type": "decision", "data": {"item_id": "agenda-01", "decision": "APPROVE"}})
        ev = ws.receive_json()
        assert ev["type"] == "decision" and ev["seq"] == 2
        client.post("/api/live/checkpoint/agenda-02")
        assert ws.receive_json()["type"] == "checkpoint_resolved"
        client.post("/api/live/reset")
        assert ws.receive_json()["type"] == "reset"
    assert live_bus.bus.subscriber_count == 0


# ---------------------------------------------------------------- demo script against a real server
def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_demo_script_runs_through_all_event_types(isolated_data_dir):
    port = _free_port()
    env = dict(os.environ, DAWN_DATA_DIR=str(isolated_data_dir))
    server = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "src.live.app:app", "--host", "127.0.0.1", "--port", str(port), "--log-level", "warning"],
        cwd=REPO_ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT,
    )
    base = f"http://127.0.0.1:{port}"
    try:
        for _ in range(100):
            try:
                urllib.request.urlopen(base + "/api/health", timeout=1)
                break
            except Exception:
                time.sleep(0.1)
        else:
            pytest.fail("live server did not start")
        run = subprocess.run(
            [sys.executable, "-I", "tools/live_demo_events.py", "--base-url", base, "--instant", "--wait-click", "0"],
            cwd=REPO_ROOT, env=env, capture_output=True, text=True, timeout=60,
        )
        assert run.returncode == 0, run.stdout + run.stderr
        state = json.load(urllib.request.urlopen(base + "/api/live/state", timeout=5))
        types = {e["type"] for e in state["events"]}
        assert types == set(live_bus.EVENT_TYPES), f"missing: {set(live_bus.EVENT_TYPES) - types}"
        assert [e["type"] for e in state["events"]][0] == "call_started"
        assert [e["type"] for e in state["events"]][-1] == "brief_ready"
        recorded = _lines(isolated_data_dir / "live_session.jsonl")
        assert len(recorded) == state["count"]
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
