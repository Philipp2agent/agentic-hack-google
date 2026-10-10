"""DawnDispatch voice app (claude-03), built 1:1 on gradbot demos/simple_chat/main.py.

Taken unchanged from simple_chat: gradbot.init_logging(), cfg = gradbot.config.from_env(), make_config() shape,
handle_session(websocket, config=cfg, on_start=make_config), gradbot.routes.setup(app, config=cfg, static_dir, with_voices=True)
and the client JS in static/index.html (audio path + message format). Added on top: the instructions (demo agenda from
docs/LIVE-EVENTS.md, agent speaks first), the tools, LIVE-EVENTS publishing and the post-call processing.

Mounted by src/app.py at /voice like the official demos launcher (demos/app.py); /call redirects there and the
root also exposes /ws/chat, /api/audio-config and /api/call/*.

Keys only from the environment: GRADIUM_API_KEY, LLM_API_KEY, LLM_BASE_URL (no trailing slash), LLM_MODEL;
optional DAWN_VOICE_ID, DAWN_SPEED, DAWN_LANGUAGE, DAWN_TEAM_COUNT, DAWN_DATA_DIR, DAWN_HIDE_ERRORS=1.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import pathlib
import time
from typing import Any

import fastapi
import fastapi.responses
import gradbot

from src.core import state
from src.core.action_engine import on_decision
from src.core.models import AgendaItem, DecisionRecord, TranscriptTurn, now_iso
from src.voice import postcall, prompt

log = logging.getLogger("dawndispatch.voice")
if not logging.getLogger().handlers:  # uvicorn leaves the root logger unconfigured
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

# --- exactly as in demos/simple_chat/main.py ------------------------------------------------------------
if os.environ.get("LLM_BASE_URL", "").endswith("/"):  # a trailing slash gave a 404 on the VPS this afternoon
    os.environ["LLM_BASE_URL"] = os.environ["LLM_BASE_URL"].rstrip("/")

gradbot.init_logging()
app = fastapi.FastAPI(title="DawnDispatch Voice")
cfg = gradbot.config.from_env()
if os.environ.get("DAWN_HIDE_ERRORS") != "1":
    cfg.debug = True  # the phone page shows the real error text instead of "An error occurred"

DEFAULT_VOICE_ID = "cLONiZ4hQ8VpQ4Sz"  # Skyler
STATIC_DIR = pathlib.Path(__file__).resolve().parent / "static"
CLOSE_GRACE_S = float(os.environ.get("DAWN_CLOSE_GRACE_S", "15"))


def make_config(msg: dict, padding_bonus: float | None = None) -> gradbot.SessionConfig:
    """simple_chat's make_config + instructions/tools; DAWN_VOICE_ID (if set) wins over the page's voice picker."""
    voice_id = os.environ.get("DAWN_VOICE_ID") or msg.get("voice_id") or DEFAULT_VOICE_ID
    language = msg.get("language") or os.environ.get("DAWN_LANGUAGE") or "en"
    extra: dict[str, Any] = {} if padding_bonus is None else {"padding_bonus": padding_bonus}
    return gradbot.SessionConfig(
        voice_id=voice_id,
        language=gradbot.LANGUAGES.get(language) if language else None,
        instructions=prompt.build_instructions(),
        tools=prompt.gradbot_tools(),
        **({"assistant_speaks_first": True} | cfg.session_kwargs | extra),
    )


# --- live events bus (claude-04), optional ---------------------------------------------------------------
try:  # pragma: no cover - depends on the sibling package
    from src.live.bus import publish as _bus_publish  # type: ignore
except Exception:  # module missing until claude-04 is merged
    _bus_publish = None


def make_event(event_type: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"type": event_type, "ts": now_iso(), "data": data or {}}


async def publish(event_type: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    """Publish one LIVE-EVENTS event; no-op when src.live.bus is absent."""
    event = make_event(event_type, data)
    if _bus_publish is not None:
        try:
            result = _bus_publish(event)
            if asyncio.iscoroutine(result):
                await result
        except Exception:  # never let the live screen break the call
            log.exception("live bus publish failed for %s", event_type)
    return event


# --- helpers ---------------------------------------------------------------------------------------------
def voice_id() -> str:
    return os.environ.get("DAWN_VOICE_ID") or DEFAULT_VOICE_ID


def default_speed() -> float:
    try:
        return float(os.environ.get("DAWN_SPEED", "1.0"))
    except ValueError:
        return 1.0


def speed_to_padding(speed: float) -> float:
    """gradbot cadence knob: padding_bonus -4..4, negative = faster (hotel demo mapping)."""
    return max(-4.0, min(4.0, -4.0 * (speed - 1.0)))


def clamp_speed(speed: float) -> float:
    return max(0.6, min(1.8, float(speed)))


def team_count() -> int:
    try:
        return int(os.environ.get("DAWN_TEAM_COUNT", "24"))
    except ValueError:
        return 24


def _read_json(name: str, default: Any) -> Any:
    path = state.data_dir() / name
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default
    except Exception:
        return default


def participants_payload() -> dict[str, Any]:
    """participants_scaled data: src/data/participants.json (hack-bau1) first, DAWN_TEAM_COUNT as fallback."""
    data = _read_json("participants.json", {})
    count = data.get("total_count") if isinstance(data, dict) else None
    if not isinstance(count, int) or count <= 0:
        return {"count": team_count(), "label": "teams at the hackathon"}
    return {"count": count, "label": data.get("label") or "teams at the hackathon"}


def v2_idea_payload(option: str, notes: str, item_id: str) -> dict[str, Any]:
    """v2_idea data: ids/titles from src/data/v2_options.json when present, else prompt.V2_OPTIONS."""
    for raw in _read_json("v2_options.json", []) or []:
        if isinstance(raw, dict) and str(raw.get("key", "")).upper() == option:
            linked = raw.get("linked_to") or item_id
            return {"id": raw.get("id") or f"v2-opt-{option.lower()}", "title": raw.get("title") or prompt.V2_OPTIONS.get(option, notes),
                    "linked_to": linked if isinstance(linked, list) else [linked, prompt.V1_ITEM_ID]}
    title = prompt.V2_OPTIONS.get(option) or (notes or "a custom Version 2")
    return {"id": f"v2-opt-{option.lower()}", "title": title, "linked_to": [item_id, prompt.V1_ITEM_ID]}


# --- per-call state: agenda progress, speed, tools, events ---------------------------------------------
CURRENT: dict[str, "CallSession | None"] = {"session": None}


class CallSession:
    """Tool handlers and LIVE-EVENTS for one call. Does not touch the audio path."""

    def __init__(self, websocket: Any, start_msg: dict | None = None):
        self.websocket = websocket
        self.start_msg = dict(start_msg or {})
        self.language = (self.start_msg.get("language") or os.environ.get("DAWN_LANGUAGE") or "en").lower()
        self.agenda: list[AgendaItem] = postcall.ensure_demo_agenda()
        self.speed = default_speed()
        self.time_budget_s: int | None = None
        self.started_at = time.monotonic()
        self.current_index = 0  # 0 = opening, 1..n = agenda items
        self.checkpointed: set[str] = set()
        self.ended = False
        self.post_call: dict[str, Any] | None = None
        self.input_handle: Any = None
        self.events: list[dict[str, Any]] = []
        self.turns: dict[tuple[str, int | None], str] = {}
        self._close_task: asyncio.Task | None = None
        self.ready = asyncio.Event()  # set once start() reset the state; tools and turns wait for it

    # -- helpers ------------------------------------------------------------------------------
    def item(self, item_id: str) -> AgendaItem | None:
        return next((it for it in self.agenda if it.item_id == item_id), None)

    def item_index(self, item_id: str) -> int:
        return next((i for i, it in enumerate(self.agenda, start=1) if it.item_id == item_id), 0)

    def duration_s(self) -> int:
        return int(time.monotonic() - self.started_at)

    async def send_client(self, payload: dict[str, Any]) -> None:
        try:
            await self.websocket.send_json(payload)
        except Exception:
            log.debug("client send failed (%s)", payload.get("type"))

    async def emit(self, event_type: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        event = await publish(event_type, data)
        self.events.append(event)
        await self.send_client(event)
        return event

    # -- transcript (posted by the page from SyncedAudioPlayer.onText, see static/index.html) -------
    async def record_turn(self, role: str, turn_idx: int | None, text: str, t_s: float | None = None) -> bool:
        await self.wait_ready()
        key = (role, turn_idx)
        is_new = key not in self.turns
        self.turns[key] = text
        await asyncio.to_thread(self._persist_turn, role, turn_idx, text, t_s)
        if role == "user" and is_new:
            await self.emit("user_said", {"text": text[:160]})
        return is_new

    @staticmethod
    def _persist_turn(role: str, turn_idx: int | None, text: str, t_s: float | None) -> None:
        def _do(st):
            for t in st.call.transcript:
                if t.role == role and t.turn_idx == turn_idx:
                    t.text = text
                    t.t_s = t_s if t_s is not None else t.t_s
                    return
            st.call.transcript.append(TranscriptTurn(role=role, text=text, t_s=t_s, turn_idx=turn_idx))  # type: ignore[arg-type]
        state.update(_do)

    # -- agenda progression -------------------------------------------------------------------
    async def advance_to(self, index: int) -> AgendaItem | None:
        if index < 1 or index > len(self.agenda):
            return None
        if index <= self.current_index:
            return self.agenda[index - 1]
        self.current_index = index
        it = self.agenda[index - 1]
        await self.emit("agenda_item", {"item_id": it.item_id, "title": it.topic, "index": index, "total": len(self.agenda)})
        return it

    # -- session lifecycle --------------------------------------------------------------------
    async def start(self) -> None:
        """Bookkeeping at call start; runs as a background task so it never delays gradbot.run."""
        try:
            await asyncio.to_thread(self._start_state)
        except Exception:
            log.exception("call start bookkeeping failed (the voice session continues)")
        self.ready.set()
        await self.send_client(prompt.agenda_payload(self.agenda))
        await self.emit("call_started", {"opening": prompt.OPENING})
        log.info("call started: voice=%s agenda=%d items", self.start_msg.get("voice_id") or voice_id(), len(self.agenda))

    async def wait_ready(self) -> None:
        """Never let a tool or a transcript line race the state reset at call start."""
        try:
            await asyncio.wait_for(self.ready.wait(), timeout=10)
        except asyncio.TimeoutError:
            log.warning("call start bookkeeping still pending; continuing")

    def _start_state(self) -> None:
        state.reset()  # fresh decisions/actions/call/meta for every call; events + agenda stay
        state.start_call(language=self.language, voice_id=voice_id())
        if not postcall.paths()["graph_before"].exists():
            postcall.refresh_graph_before()

    async def finish(self, summary: str | None = None, reason: str = "end_call") -> dict[str, Any]:
        """call_ended -> post-call processing -> brief_ready. Idempotent."""
        if self.ended:
            return self.post_call or {}
        self.ended = True
        duration = self.duration_s()
        await self.emit("call_ended", {"duration_s": duration, "reason": reason})
        try:
            self.post_call = await asyncio.to_thread(postcall.process_post_call, summary, duration)
        except Exception as exc:
            log.exception("post-call processing failed")
            self.post_call = {"error": str(exc)}
        await self.emit("brief_ready", {"briefing": (self.post_call or {}).get("briefing", [])})
        return self.post_call

    def schedule_close(self) -> None:
        """Fallback: close the socket a few seconds after end_call if the page does not send stop."""
        if self._close_task is not None:
            return

        async def _close():
            await asyncio.sleep(CLOSE_GRACE_S)
            try:
                await self.websocket.close()
            except Exception:
                pass

        self._close_task = asyncio.create_task(_close())

    # -- tools --------------------------------------------------------------------------------
    async def on_tool_call(self, handle: Any, input_handle: Any, websocket: Any) -> None:
        self.input_handle = input_handle
        name, args = handle.name, handle.args or {}
        log.info("tool %s %s", name, args)
        await self.wait_ready()
        try:
            if name == "set_time_budget":
                await self._tool_set_time_budget(handle, args)
            elif name == "log_decision":
                await self._tool_log_decision(handle, args)
            elif name == "mark_irreversible_checkpoint":
                await self._tool_mark_checkpoint(handle, args)
            elif name == "set_speaking_speed":
                await self._tool_set_speed(handle, args)
            elif name == "end_call":
                await self._tool_end_call(handle, args)
            else:
                await handle.send_error(f"Unknown tool: {name}")
        except Exception as exc:
            log.exception("tool %s failed", name)
            await handle.send_error(f"{name} failed: {exc}")

    async def _tool_set_time_budget(self, handle, args) -> None:
        seconds = max(10, min(900, int(args.get("seconds") or 60)))
        self.time_budget_s = seconds
        await asyncio.to_thread(state.set_time_budget, seconds)
        await self.emit("time_budget", {"seconds": seconds})
        first = await self.advance_to(1)
        await handle.send_json({
            "ok": True,
            "seconds": seconds,
            "items_to_cover": len(self.agenda) if seconds >= 45 else 2,
            "next_item_id": first.item_id if first else None,
            "next_question": first.question_for_lead if first else None,
        })

    async def _tool_log_decision(self, handle, args) -> None:
        item_id = str(args.get("item_id") or "").strip()
        it = self.item(item_id)
        if it is None:
            await handle.send_error(f"unknown item_id {item_id!r}; valid: {[a.item_id for a in self.agenda]}")
            return
        decision = str(args.get("decision") or "").strip().upper()
        if decision not in ("APPROVE", "REJECT", "HOLD", "AMEND"):
            await handle.send_error("decision must be one of APPROVE, REJECT, HOLD, AMEND")
            return
        notes = str(args.get("notes") or "").strip()
        rec = DecisionRecord(item_id=item_id, decision_type=decision, voice_notes=notes, source="voice_tool")  # type: ignore[arg-type]
        await asyncio.to_thread(state.add_decision, rec)
        # core seam (src/core/action_engine.on_decision): reversible -> executed now, irreversible -> BLOCKED_ON_CHECKPOINT
        await asyncio.to_thread(on_decision, rec)
        await self.emit("decision", {"item_id": item_id, "decision": decision, "summary": notes[:160]})

        if item_id == prompt.V2_ITEM_ID:
            option = str(args.get("option") or "OTHER").strip().upper()
            if option not in prompt.V2_OPTIONS and option != "OTHER":
                option = "OTHER"
            await asyncio.to_thread(state.set_meta, "v2_option", option)
            await self.emit("v2_idea", v2_idea_payload(option, notes, item_id))
        if it.is_irreversible and decision == "APPROVE":
            await self._checkpoint(item_id, "Irreversible: makes the repository public and submits. Needs your click on the laptop.")
        if item_id == prompt.SCALE_ITEM_ID and decision == "APPROVE":
            await self.emit("participants_scaled", participants_payload())

        idx = self.item_index(item_id)
        nxt = await self.advance_to(idx + 1)
        result: dict[str, Any] = {"ok": True, "item_id": item_id, "recorded": decision, "next_item_id": nxt.item_id if nxt else None}
        if nxt is not None:
            result["next_question"] = nxt.question_for_lead
        else:
            result["note"] = "All agenda items are recorded. Ask if there is anything else, then end_call when the lead wraps up."
        if it.is_irreversible and decision == "APPROVE":
            result["checkpoint"] = "BLOCKED_ON_CHECKPOINT"
            result["say"] = "Noted. That one waits for your click on the laptop."
        await handle.send_json(result)

    async def _checkpoint(self, item_id: str, reason: str) -> dict[str, Any]:
        it = self.item(item_id)
        action = await asyncio.to_thread(postcall.set_checkpoint_reason, item_id, reason)
        if item_id not in self.checkpointed:
            self.checkpointed.add(item_id)
            await self.emit("checkpoint", {"item_id": item_id, "action": it.topic if it else action.get("action_type"), "reason": reason})
        return action

    async def _tool_mark_checkpoint(self, handle, args) -> None:
        item_id = str(args.get("item_id") or "").strip()
        if self.item(item_id) is None:
            await handle.send_error(f"unknown item_id {item_id!r}")
            return
        reason = str(args.get("reason") or "Irreversible action, needs a click on the laptop.").strip()
        await self._checkpoint(item_id, reason)
        await handle.send_json({"ok": True, "item_id": item_id, "checkpoint": "BLOCKED_ON_CHECKPOINT"})

    async def _tool_set_speed(self, handle, args) -> None:
        speed = clamp_speed(float(args.get("speed") or 1.0))
        reason = str(args.get("reason") or "").strip()
        self.speed = speed
        if self.input_handle is not None:  # same config as at start, only the cadence changes
            await self.input_handle.send_config(make_config(self.start_msg, padding_bonus=speed_to_padding(speed)))
        await self.emit("speed_changed", {"speed": speed, "reason": reason[:160]})
        await handle.send_json({"ok": True, "speed": speed})

    async def _tool_end_call(self, handle, args) -> None:
        summary = str(args.get("summary") or "").strip()
        result = await self.finish(summary, reason="end_call")
        self.schedule_close()
        await handle.send_json({"ok": True, "say": prompt.CLOSING_LINE, "briefing": result.get("briefing", [])})


# --- WebSocket: as in simple_chat, plus on_tool_call ---------------------------------------------------
@app.websocket("/ws/chat")
async def ws_chat(websocket: fastapi.WebSocket):
    session: CallSession | None = None
    bookkeeping: list[asyncio.Task] = []
    log.info("ws/chat: client connected (model=%s base_url=%s keys: gradium=%s llm=%s)",
             cfg.llm.model, cfg.llm.base_url, bool(cfg.gradium.api_key), bool(cfg.llm.api_key))

    def on_start(msg: dict) -> gradbot.SessionConfig:
        nonlocal session
        session = CallSession(websocket, msg)
        CURRENT["session"] = session
        log.info("ws/chat: start received %s -> gradbot.run", {k: msg.get(k) for k in ("type", "voice_name", "voice_id", "language")})
        bookkeeping.append(asyncio.create_task(session.start()))
        return make_config(msg)

    async def on_tool_call(handle, input_handle, ws):
        if session is not None:
            await session.on_tool_call(handle, input_handle, ws)

    try:
        await gradbot.websocket.handle_session(
            websocket,
            config=cfg,
            on_start=on_start,
            on_tool_call=on_tool_call,
        )
    finally:
        log.info("ws/chat: session closed")
        if bookkeeping:
            try:
                await asyncio.wait_for(asyncio.gather(*bookkeeping, return_exceptions=True), timeout=10)
            except Exception:
                log.exception("call start bookkeeping did not finish")
        if session is not None:
            try:
                await session.finish(None, reason="hangup")
            except Exception:
                log.exception("post-call after hangup failed")


# --- DawnDispatch API (served under /voice and at the root) ---------------------------------------------
api_router = fastapi.APIRouter()
AVATAR = pathlib.Path(__file__).resolve().parents[2] / "assets" / "brand" / "call_avatar.png"


@api_router.get("/api/call/agenda")
async def call_agenda():
    payload = prompt.agenda_payload(postcall.ensure_demo_agenda())
    payload["avatar_url"] = "/assets/brand/call_avatar.png" if AVATAR.exists() else None
    payload["voice_id_env"] = bool(os.environ.get("DAWN_VOICE_ID"))
    return payload


@api_router.get("/api/call/state")
async def call_state():
    st = state.load()
    return {
        "call": st.call.model_dump(),
        "decisions": [d.model_dump() for d in st.decisions],
        "actions": [a.model_dump() for a in st.actions],
        "meta": st.meta,
        "voice_ready": bool(cfg.gradium.api_key and cfg.llm.api_key),
    }


@api_router.post("/api/call/turn")
async def call_turn(payload: dict[str, Any]):
    """The page posts finished transcript lines (SyncedAudioPlayer.onText) so the dashboard and user_said get them."""
    role = "user" if payload.get("is_user") or payload.get("role") == "user" else "agent"
    text = str(payload.get("text") or "").strip()
    turn_idx = payload.get("turn_idx")
    if not text:
        return {"ok": False}
    session = CURRENT["session"]
    if session is not None and not session.ended:
        is_new = await session.record_turn(role, turn_idx, text, payload.get("t_s"))
    else:
        await asyncio.to_thread(CallSession._persist_turn, role, turn_idx, text, payload.get("t_s"))
        is_new = True
    return {"ok": True, "new": is_new}


@api_router.post("/api/call/postcall")
async def call_postcall():
    """Manual trigger (demo safety net): rebuild actions, graph after, transcript from the recorded state."""
    return await asyncio.to_thread(postcall.process_post_call, None, None)


app.include_router(api_router)

# --- exactly as in demos/simple_chat/main.py: /, /static, /static/js, /api/audio-config, /api/voices ----
gradbot.routes.setup(
    app,
    config=cfg,
    static_dir=STATIC_DIR,
    with_voices=True,
)
