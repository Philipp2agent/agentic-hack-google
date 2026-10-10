"""DawnDispatch voice server (claude-03): /call page and the gradbot session on /ws/chat.

Pattern: gradbot demos/simple_chat (FastAPI + gradbot.websocket.handle_session + Gradium STT/TTS,
Gemini through the OpenAI-compatible endpoint from LLM_BASE_URL / LLM_MODEL).

Keys only from the environment: GRADIUM_API_KEY, LLM_API_KEY, LLM_BASE_URL (no trailing slash),
LLM_MODEL; optional DAWN_VOICE_ID, DAWN_SPEED, DAWN_LANGUAGE, DAWN_TEAM_COUNT, DAWN_DATA_DIR.

Tools the agent can call (see prompt.TOOL_SPECS): set_time_budget, log_decision,
mark_irreversible_checkpoint, set_speaking_speed, end_call. Every agenda step and tool publishes an
event per docs/LIVE-EVENTS.md through ``src.live.bus.publish`` (try-import, otherwise no-op) and
mirrors it to the phone page over the same WebSocket.
"""
from __future__ import annotations

import asyncio
import logging
import os
import pathlib
import time
from typing import Any

import fastapi
import fastapi.responses

from src.core import state
from src.core.action_engine import log_decision as core_log_decision
from src.core.action_engine import process_decisions
from src.core.models import AgendaItem, TranscriptTurn, now_iso
from src.voice import postcall, prompt

log = logging.getLogger("dawndispatch.voice")

STATIC_DIR = pathlib.Path(__file__).resolve().parent / "static"
LIVE_PAGE = STATIC_DIR / "call_live.html"
SIM_PAGE = STATIC_DIR / "call.html"  # hack-bau2's static simulation, kept reachable at /call/sim

DEFAULT_VOICE_ID = "cLONiZ4hQ8VpQ4Sz"  # Gradium flagship "Skyler" (English, US)
CLOSE_GRACE_S = float(os.environ.get("DAWN_CLOSE_GRACE_S", "15"))

# --- live events bus (claude-04), optional ---------------------------------------------------
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


# --- gradbot config ----------------------------------------------------------------------------
def gradbot_config():
    """gradbot Config from the environment (LLM_BASE_URL normalised: no trailing slash -> no 404)."""
    base = os.environ.get("LLM_BASE_URL")
    if base and base.endswith("/"):
        os.environ["LLM_BASE_URL"] = base.rstrip("/")
    import gradbot

    return gradbot.config.from_env()


def voice_id() -> str:
    return os.environ.get("DAWN_VOICE_ID") or DEFAULT_VOICE_ID


def default_speed() -> float:
    try:
        return float(os.environ.get("DAWN_SPEED", "1.1"))
    except ValueError:
        return 1.1


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


# --- transcript buffering ----------------------------------------------------------------------
class _TurnBuffer:
    """Collects the incremental user_text / agent_text chunks gradbot sends."""

    def __init__(self, role: str):
        self.role = role
        self.turn_idx: int | None = None
        self.parts: list[str] = []
        self.t_s: float | None = None

    def add(self, text: str, turn_idx: int | None, t_s: float | None) -> None:
        if turn_idx is not None and self.turn_idx is not None and turn_idx != self.turn_idx and self.parts:
            # caller flushes on turn change; keep the newest turn
            self.parts = []
        self.turn_idx = turn_idx if turn_idx is not None else self.turn_idx
        self.parts.append(text.strip())
        self.t_s = t_s if t_s is not None else self.t_s

    def pop(self) -> tuple[str, int | None, float | None]:
        text = " ".join(p for p in self.parts if p).strip()
        turn_idx, t_s = self.turn_idx, self.t_s
        self.parts, self.turn_idx, self.t_s = [], None, None
        return text, turn_idx, t_s


class CallSession:
    """Per-WebSocket state: agenda progress, speed, time budget, transcript, events."""

    def __init__(self, websocket: fastapi.WebSocket, language: str = "en"):
        self.websocket = websocket
        self.language = language
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
        self._user = _TurnBuffer("user")
        self._agent = _TurnBuffer("agent")
        self._close_task: asyncio.Task | None = None

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

    def make_config(self):
        import gradbot

        cfg = gradbot_config()
        lang = gradbot.LANGUAGES.get(self.language, gradbot.Lang.En)
        kwargs = {
            "assistant_speaks_first": True,
            "silence_timeout_s": float(os.environ.get("DAWN_SILENCE_TIMEOUT_S", "0")),
            "padding_bonus": speed_to_padding(self.speed),
            "rewrite_rules": lang.rewrite_rules,
            "flush_duration_s": 0.5,
        } | cfg.session_kwargs
        kwargs["padding_bonus"] = speed_to_padding(self.speed)  # the tool decides, not the yaml
        return gradbot.SessionConfig(
            voice_id=voice_id(),
            instructions=prompt.build_instructions(self.agenda),
            language=lang,
            tools=prompt.gradbot_tools(),
            **kwargs,
        )

    # -- transcript ---------------------------------------------------------------------------
    def on_user_text(self, msg: dict[str, Any]) -> None:
        self._user.add(msg.get("text", ""), msg.get("turn_idx"), msg.get("stop_s"))

    def on_agent_text(self, msg: dict[str, Any]) -> None:
        turn_idx = msg.get("turn_idx")
        if self._agent.parts and turn_idx is not None and self._agent.turn_idx not in (None, turn_idx):
            self.flush_agent()
        self._agent.add(msg.get("text", ""), turn_idx, msg.get("stop_s"))

    def flush_agent(self) -> str:
        text, turn_idx, t_s = self._agent.pop()
        if text:
            state.append_turn(TranscriptTurn(role="agent", text=text, t_s=t_s, turn_idx=turn_idx))
        return text

    async def flush_user(self) -> str:
        text, turn_idx, t_s = self._user.pop()
        if text:
            state.append_turn(TranscriptTurn(role="user", text=text, t_s=t_s, turn_idx=turn_idx))
            await self.emit("user_said", {"text": text[:160]})
        return text

    # -- agenda progression -------------------------------------------------------------------
    async def advance_to(self, index: int) -> AgendaItem | None:
        """Announce agenda item `index` (1-based) once; returns the item or None when done."""
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
        state.reset()  # fresh decisions/actions/call/meta for every call; events + agenda stay
        state.start_call(language=self.language, voice_id=voice_id())
        try:
            postcall.refresh_graph_before()
        except Exception:
            log.exception("could not refresh knowledge_graph_before.json")
        await self.send_client(prompt.agenda_payload(self.agenda))
        await self.emit("call_started", {"opening": prompt.OPENING})

    async def finish(self, summary: str | None = None, reason: str = "end_call") -> dict[str, Any]:
        """call_ended -> post-call processing -> brief_ready. Idempotent."""
        if self.ended:
            return self.post_call or {}
        self.ended = True
        await self.flush_user()
        self.flush_agent()
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
        """Fallback: close the socket a few seconds after end_call if the client does not stop."""
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
        await self.flush_user()
        self.flush_agent()
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
        seconds = int(args.get("seconds") or 60)
        seconds = max(10, min(900, seconds))
        self.time_budget_s = seconds
        state.set_time_budget(seconds)
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
        p = postcall.paths()
        core_log_decision(item_id, decision, notes, file_path=p["decisions"])
        process_decisions(p["agenda"], p["decisions"], p["actions"])
        await self.emit("decision", {"item_id": item_id, "decision": decision, "summary": notes[:160]})

        if item_id == prompt.V2_ITEM_ID:
            option = str(args.get("option") or "OTHER").strip().upper()
            if option not in prompt.V2_OPTIONS and option != "OTHER":
                option = "OTHER"
            state.set_meta("v2_option", option)
            title = prompt.V2_OPTIONS.get(option) or (notes or "a custom Version 2")
            await self.emit("v2_idea", {"id": f"v2-{option.lower()}", "title": title, "linked_to": [item_id, prompt.V1_ITEM_ID]})
        if it.is_irreversible and decision == "APPROVE":
            await self._checkpoint(item_id, "Irreversible: makes the repository public and submits. Needs your click on the laptop.")
        if item_id == prompt.SCALE_ITEM_ID and decision == "APPROVE":
            await self.emit("participants_scaled", {"count": team_count(), "label": "teams at the hackathon"})

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
        if self.input_handle is not None:
            await self.input_handle.send_config(self.make_config())
        await self.emit("speed_changed", {"speed": speed, "reason": reason[:160]})
        await handle.send_json({"ok": True, "speed": speed})

    async def _tool_end_call(self, handle, args) -> None:
        summary = str(args.get("summary") or "").strip()
        result = await self.finish(summary, reason="end_call")
        self.schedule_close()
        await handle.send_json({"ok": True, "say": prompt.CLOSING_LINE, "briefing": result.get("briefing", [])})


class _TranscriptProxy:
    """Wraps the FastAPI WebSocket so gradbot's user_text / agent_text frames are captured."""

    def __init__(self, websocket: fastapi.WebSocket, session: CallSession):
        self._ws = websocket
        self._session = session

    def __getattr__(self, name: str) -> Any:
        return getattr(self._ws, name)

    async def send_json(self, payload: Any, *args: Any, **kwargs: Any) -> None:
        if isinstance(payload, dict):
            t = payload.get("type")
            if t == "user_text":
                self._session.on_user_text(payload)
            elif t == "agent_text":
                self._session.on_agent_text(payload)
        await self._ws.send_json(payload, *args, **kwargs)


# --- routes --------------------------------------------------------------------------------------
router = fastapi.APIRouter()


@router.get("/call", include_in_schema=False)
async def call_page():
    if LIVE_PAGE.exists():
        return fastapi.responses.FileResponse(LIVE_PAGE, media_type="text/html")
    return fastapi.responses.JSONResponse({"error": "call_live.html not found"}, status_code=404)


@router.get("/call/sim", include_in_schema=False)
async def call_simulation_page():
    """hack-bau2's static incoming-call simulation (no backend audio), paths rewritten for src.app."""
    if not SIM_PAGE.exists():
        return fastapi.responses.JSONResponse({"error": "call.html not found"}, status_code=404)
    html = SIM_PAGE.read_text(encoding="utf-8").replace('"/static/call.', '"/static/voice/call.')
    return fastapi.responses.HTMLResponse(html)


@router.get("/api/audio-config")
async def audio_config():
    try:
        return {"pcm": bool(gradbot_config().use_pcm)}
    except Exception:
        return {"pcm": False}


@router.get("/api/call/agenda")
async def call_agenda():
    return prompt.agenda_payload(postcall.ensure_demo_agenda())


@router.get("/api/call/state")
async def call_state():
    st = state.load()
    return {
        "call": st.call.model_dump(),
        "decisions": [d.model_dump() for d in st.decisions],
        "actions": [a.model_dump() for a in st.actions],
        "meta": st.meta,
        "voice_ready": bool(os.environ.get("GRADIUM_API_KEY") and os.environ.get("LLM_API_KEY")),
    }


@router.post("/api/call/postcall")
async def call_postcall():
    """Manual trigger (demo safety net): rebuild actions, graph after, transcript from the recorded state."""
    return await asyncio.to_thread(postcall.process_post_call, None, None)


@router.websocket("/ws/chat")
async def ws_chat(websocket: fastapi.WebSocket):
    import gradbot

    session: CallSession | None = None
    proxy_holder: dict[str, Any] = {}

    async def on_start(msg: dict) -> Any:
        nonlocal session
        language = (msg.get("language") or os.environ.get("DAWN_LANGUAGE") or "en").lower()
        if language not in gradbot.LANGUAGES:
            language = "en"
        session = CallSession(proxy_holder["ws"], language=language)
        await session.start()
        return session.make_config()

    async def on_tool_call(handle, input_handle, ws):
        if session is not None:
            await session.on_tool_call(handle, input_handle, ws)

    # the proxy needs the session, the session needs the socket: resolve lazily
    class _LateProxy(_TranscriptProxy):
        def __init__(self, ws):
            self._ws = ws

        @property
        def _session(self):  # type: ignore[override]
            return session

        async def send_json(self, payload: Any, *args: Any, **kwargs: Any) -> None:
            if session is not None and isinstance(payload, dict):
                t = payload.get("type")
                if t == "user_text":
                    session.on_user_text(payload)
                elif t == "agent_text":
                    session.on_agent_text(payload)
            await self._ws.send_json(payload, *args, **kwargs)

    proxy = _LateProxy(websocket)
    proxy_holder["ws"] = proxy
    cfg = gradbot_config()
    try:
        await gradbot.websocket.handle_session(
            proxy,  # type: ignore[arg-type]
            config=cfg,
            on_start=on_start,
            on_tool_call=on_tool_call,
        )
    finally:
        if session is not None:
            try:
                await session.finish(None, reason="hangup")
            except Exception:
                log.exception("post-call after hangup failed")
