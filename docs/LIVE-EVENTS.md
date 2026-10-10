# Live events: voice session to live screen (contract for claude-03 and claude-04)

## Transport
- In-process pub/sub in src/live/bus.py (built by claude-04): async def publish(event: dict) and an async subscriber API.
- The voice side imports it with try-import: from src.live.bus import publish (if missing: no-op).
- Browser: WebSocket /ws/events (one JSON object per message). Reload state: GET /api/live/state.
- Replay fallback: POST /api/live/replay plays the last recorded session again (for video takes). Reset: POST /api/live/reset.

## Event format
{"type": "<type>", "ts": "<ISO time>", "data": {...}}

## Types
- call_started {opening}
- time_budget {seconds}
- speed_changed {speed, reason}
- agenda_item {item_id, title, index, total}
- user_said {text}                      (final transcript line, short)
- decision {item_id, decision, summary} (decision: APPROVE, REJECT, HOLD, AMEND)
- checkpoint {item_id, action, reason}  (irreversible, waits for a click on the laptop)
- checkpoint_resolved {item_id, approved}
- v2_idea {id, title, linked_to}
- participants_scaled {count, label}
- call_ended {duration_s}
- brief_ready {}

## Demo agenda (English, the agent leads, the user answers freely)
1. Opening (fixed): "Good morning Philipp. Overnight your agents kept building DawnDispatch. I have four things for you. How much time do you have?"
2. Status Version 1: one sentence on what was built today (from context/hackathon-day and the repo), then "Anything you want me to flag?"
3. Decision Version 2: options A real phone or WhatsApp calling, B night shift starts the call automatically, C the users cloned voice. The user picks freely; emit decision and v2_idea.
4. Irreversible: "Shall I make the repo public and submit?" Emit checkpoint; it waits for the click on the laptop.
5. Scale: "Should I offer this morning call to every other team at the hackathon?" Emit participants_scaled.
6. Close: when the user ends the call by voice, emit call_ended, run post-call processing, emit brief_ready and say "Your dashboard is ready."
Speed: if the user signals hurry (no fixed keyword), call set_speaking_speed and emit speed_changed.

## Implemented: live screen and bus (claude-04, src/live/)
- Screen: GET /live (dark, one accent, big type; works in a normal browser window). Static files under /live/static/. No library, no LLM in the rendering path.
- Bus: src/live/bus.py with async def publish(event), sync emit(event) (safe from worker threads), subscribe()/unsubscribe()/events(), state(), reset(), replay().
- Recording: every published event is appended to src/data/live_session.jsonl (DAWN_DATA_DIR overrides the folder; git-ignored). reset keeps the file until the next live event; a call_started after a call_ended starts a new session on its own.
- HTTP: GET /api/live/state · GET /api/live/graph?stage=before|after · POST /api/live/event (one event or a list) · POST /api/live/checkpoint/{item_id} {"approved": true|false} -> publishes checkpoint_resolved · POST /api/live/replay?speed=1&max_gap=6 · POST /api/live/reset.
- WebSocket /ws/events: first message {"type":"snapshot","data":{...state}}, then one event per message; control messages reset, replay_started, replay_finished are not recorded.
- Mount in src/app.py (claude-03): `from src.live.router import router as live_router; app.include_router(live_router)` inside try/except. Standalone: `uvicorn src.live.app:app --port 8000`.
- Demo without a call: `python3 tools/live_demo_events.py [--fast | --instant] [--base-url http://127.0.0.1:8000]` sends the demo agenda above as events and waits for the click on the laptop at the checkpoint.
- Screen behaviour per event: agenda_item -> question big in the middle, graph dims; user_said -> answer under the question and in the sidebar; decision -> verdict big, node turns green; checkpoint -> pulsing node and APPROVE button; v2_idea -> violet node grows out of linked_to; participants_scaled -> ring of nodes around the project and a count-up; call_ended + brief_ready -> "What the call delivered", three before -> after rows (brief_ready.data.rows [{before, after}] overrides the derived ones).
