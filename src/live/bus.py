"""In-process pub/sub for the live screen (contract: docs/LIVE-EVENTS.md).

Voice side (claude-03)::

    try:
        from src.live.bus import publish          # async def publish(event: dict) -> dict
    except ImportError:
        async def publish(event): return event    # no-op when src/live is missing

    await publish({"type": "decision", "data": {"item_id": "agenda-02", "decision": "APPROVE", "summary": "..."}})

``emit(event)`` is the synchronous twin and is safe from worker threads (``asyncio.to_thread``).
Browser sockets use ``subscribe()`` / ``unsubscribe()`` or the ``events()`` async iterator.

Every published event is appended to ``src/data/live_session.jsonl`` (one JSON object per line,
``DAWN_DATA_DIR`` overrides the folder like src/core/state.py). ``reset()`` clears the in-memory
session; the recording is kept until the next live event arrives, so ``replay()`` can play the
last take again with its original timing. A ``call_started`` after a ``call_ended`` also starts a
fresh session, so a second live take needs no explicit reset.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import pathlib
import threading
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Callable

log = logging.getLogger("dawndispatch.live")

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
RECORDING_NAME = "live_session.jsonl"

# Event types from docs/LIVE-EVENTS.md. Unknown types are accepted (the browser ignores them).
EVENT_TYPES = frozenset(
    {
        "call_started",
        "time_budget",
        "speed_changed",
        "agenda_item",
        "user_said",
        "decision",
        "checkpoint",
        "checkpoint_resolved",
        "v2_idea",
        "participants_scaled",
        "call_ended",
        "brief_ready",
    }
)
# Control messages the bus sends to browsers but never records.
CONTROL_TYPES = frozenset({"reset", "snapshot", "replay_started", "replay_finished"})


def now_iso() -> str:
    """ISO 8601 UTC with milliseconds, e.g. 2026-10-10T16:42:01.250Z."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def parse_iso(ts: str) -> float | None:
    """ISO timestamp -> unix seconds; None when it cannot be parsed."""
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00")).timestamp()
    except (TypeError, ValueError):
        return None


def data_dir() -> pathlib.Path:
    return pathlib.Path(os.environ.get("DAWN_DATA_DIR") or (REPO_ROOT / "src" / "data"))


def recording_path() -> pathlib.Path:
    return data_dir() / RECORDING_NAME


def normalize(event: Any) -> dict[str, Any]:
    """Validate and complete an event: type (str), ts (ISO, filled), data (dict, filled)."""
    if not isinstance(event, dict):
        raise ValueError("event must be a JSON object")
    etype = event.get("type")
    if not isinstance(etype, str) or not etype.strip():
        raise ValueError("event.type must be a non-empty string")
    data = event.get("data")
    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise ValueError("event.data must be a JSON object")
    ts = event.get("ts")
    if not isinstance(ts, str) or parse_iso(ts) is None:
        ts = now_iso()
    out = {k: v for k, v in event.items() if k not in ("type", "ts", "data", "seq")}
    out.update({"type": etype.strip(), "ts": ts, "data": dict(data)})
    return out


class LiveBus:
    """Session state + fan-out + JSONL recording. One instance per process (``bus``)."""

    def __init__(self, path_factory: Callable[[], pathlib.Path] = recording_path) -> None:
        self._lock = threading.RLock()
        self._events: list[dict[str, Any]] = []
        self._seq = 0
        self._session_started: str | None = None
        self._new_recording = True  # next recorded event truncates the file
        self._subscribers: dict[asyncio.Queue, asyncio.AbstractEventLoop] = {}
        self._path_factory = path_factory
        self._replay_task: asyncio.Task | None = None

    # ------------------------------------------------------------------ publish
    def emit(self, event: dict[str, Any], *, record: bool = True) -> dict[str, Any]:
        """Synchronous publish: update state, record, fan out. Thread-safe."""
        ev = normalize(event)
        with self._lock:
            if ev["type"] == "call_started" and any(e["type"] == "call_ended" for e in self._events):
                # new take without an explicit reset
                self._events.clear()
                self._seq = 0
                self._session_started = None
                self._new_recording = True
            self._seq += 1
            ev["seq"] = self._seq
            if self._session_started is None:
                self._session_started = ev["ts"]
            self._events.append(ev)
            if record:
                self._write(ev)
        self._fanout(ev)
        return ev

    async def publish(self, event: dict[str, Any]) -> dict[str, Any]:
        return self.emit(event)

    def _write(self, ev: dict[str, Any]) -> None:
        try:
            path = self._path_factory()
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w" if self._new_recording else "a", encoding="utf-8") as fh:
                fh.write(json.dumps(ev, ensure_ascii=False) + "\n")
            self._new_recording = False
        except OSError as exc:  # recording must never break the call
            log.warning("live recording failed: %s", exc)

    # ---------------------------------------------------------------- subscribe
    def subscribe(self, maxsize: int = 512) -> asyncio.Queue:
        """Register a subscriber queue bound to the current running loop."""
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue = asyncio.Queue(maxsize=maxsize)
        with self._lock:
            self._subscribers[queue] = loop
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        with self._lock:
            self._subscribers.pop(queue, None)

    async def events(self) -> AsyncIterator[dict[str, Any]]:
        queue = self.subscribe()
        try:
            while True:
                yield await queue.get()
        finally:
            self.unsubscribe(queue)

    @property
    def subscriber_count(self) -> int:
        return len(self._subscribers)

    def _fanout(self, message: dict[str, Any]) -> None:
        try:
            running = asyncio.get_running_loop()
        except RuntimeError:
            running = None
        with self._lock:
            targets = list(self._subscribers.items())
        for queue, loop in targets:
            if loop.is_closed():
                self.unsubscribe(queue)
                continue
            if loop is running:
                self._put(queue, message)
            else:
                try:
                    loop.call_soon_threadsafe(self._put, queue, message)
                except RuntimeError:
                    self.unsubscribe(queue)

    @staticmethod
    def _put(queue: asyncio.Queue, message: dict[str, Any]) -> None:
        try:
            queue.put_nowait(message)
        except asyncio.QueueFull:
            log.warning("live subscriber queue full; dropping %s", message.get("type"))

    # -------------------------------------------------------------------- state
    def state(self) -> dict[str, Any]:
        with self._lock:
            events = [dict(e) for e in self._events]
            started = self._session_started
        return {
            "session_started_at": started,
            "count": len(events),
            "recording": str(self._path_factory()),
            "replaying": bool(self._replay_task and not self._replay_task.done()),
            "events": events,
        }

    def reset(self) -> int:
        """Clear the session (browsers get a ``reset`` control message). Keeps the recording."""
        self.stop_replay()
        with self._lock:
            cleared = len(self._events)
            self._events.clear()
            self._seq = 0
            self._session_started = None
            self._new_recording = True
        self._fanout({"type": "reset", "ts": now_iso(), "data": {"cleared": cleared}})
        return cleared

    # ------------------------------------------------------------------- replay
    def recorded(self) -> list[dict[str, Any]]:
        """Events of the last recorded session (empty when there is none)."""
        path = self._path_factory()
        if not path.is_file():
            return []
        out: list[dict[str, Any]] = []
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(normalize(json.loads(line)))
                except (ValueError, TypeError):
                    continue
        return out

    def stop_replay(self) -> bool:
        task = self._replay_task
        if task and not task.done():
            task.cancel()
            return True
        return False

    async def replay(self, speed: float = 1.0, max_gap_s: float = 6.0, wait: bool = False) -> int:
        """Play the last recorded session again with its original timing (gaps capped at max_gap_s / speed)."""
        events = self.recorded()
        if not events:
            return 0
        self.stop_replay()
        with self._lock:
            self._events.clear()
            self._seq = 0
            self._session_started = None
        self._fanout({"type": "reset", "ts": now_iso(), "data": {"replay": True}})
        speed = max(float(speed), 0.01)
        self._replay_task = asyncio.get_running_loop().create_task(self._run_replay(events, speed, max(float(max_gap_s), 0.0)))
        if wait:
            await self._replay_task
        return len(events)

    async def _run_replay(self, events: list[dict[str, Any]], speed: float, max_gap_s: float) -> None:
        self._fanout({"type": "replay_started", "ts": now_iso(), "data": {"count": len(events), "speed": speed}})
        prev: float | None = None
        try:
            for ev in events:
                t = parse_iso(ev["ts"])
                if prev is not None and t is not None:
                    gap = min(max(t - prev, 0.0), max_gap_s) / speed
                    if gap > 0:
                        await asyncio.sleep(gap)
                prev = t if t is not None else prev
                copy = dict(ev)
                copy["replay"] = True
                self.emit(copy, record=False)
        finally:
            self._fanout({"type": "replay_finished", "ts": now_iso(), "data": {}})


bus = LiveBus()


# Module-level API (the contract names ``publish``; the rest mirrors the instance).
async def publish(event: dict[str, Any]) -> dict[str, Any]:
    return bus.emit(event)


def emit(event: dict[str, Any]) -> dict[str, Any]:
    return bus.emit(event)


def subscribe(maxsize: int = 512) -> asyncio.Queue:
    return bus.subscribe(maxsize)


def unsubscribe(queue: asyncio.Queue) -> None:
    bus.unsubscribe(queue)


def events() -> AsyncIterator[dict[str, Any]]:
    return bus.events()


def state() -> dict[str, Any]:
    return bus.state()


def reset() -> int:
    return bus.reset()


def recorded() -> list[dict[str, Any]]:
    return bus.recorded()


async def replay(speed: float = 1.0, max_gap_s: float = 6.0, wait: bool = False) -> int:
    return await bus.replay(speed=speed, max_gap_s=max_gap_s, wait=wait)
