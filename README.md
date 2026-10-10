# agentic-hack-google
**DawnDispatch** - the morning call that owns the code and the human. Your agents build overnight; on the way to the office
Dawn calls you through your smart glasses, asks "How much time do you have?", runs four decisions in rapid fire, and when you
sit down the dashboard already shows the knowledge graph before and after the call, with a human checkpoint for anything
irreversible. Partner tech: **Gradium** (gradbot STT/TTS voice loop) and **Google Gemini** (voice dialog via the
OpenAI-compatible endpoint; agenda synthesis and media tools via google-genai).

## Run locally

Requirements: Python 3.12+, keys in the environment (never in the repo, see `.env.example`).

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt

# keys: on the VPS
set -a; . /home/buzzagent/hack/secrets.env; set +a
# or by hand (LLM_BASE_URL without a trailing slash, otherwise 404)
export GRADIUM_API_KEY=... LLM_API_KEY=... LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai LLM_MODEL=gemini-3.8-flash
export GEMINI_API_KEY=...            # optional: agenda synthesis + tools/
export DAWN_VOICE_ID=...             # optional: custom Gradium voice

python -m src.core.state --reset                        # fresh demo state (keeps events + agenda)
uvicorn src.app:app --host 127.0.0.1 --port 8090        # or: python -m src.main
```

Then open:

| URL | What |
|---|---|
| `http://127.0.0.1:8090/call` | phone page (redirects to `/voice/`): big round call button, the agent speaks first (mic needs HTTPS on a phone, see tunnel) |
| `http://127.0.0.1:8090/dashboard` | laptop: knowledge graph before/after, transcript, human checkpoints |
| `http://127.0.0.1:8090/live` | laptop: live mission-control screen (when `src/live` is merged) |
| `http://127.0.0.1:8090/call/sim` | static call simulation without backend audio (hack-bau2) |
| `http://127.0.0.1:8090/api/health` | what is mounted |

Phone over the internet (microphone requires HTTPS): `cloudflared tunnel --url http://127.0.0.1:8090` and open
`https://<tunnel>/call` on the phone; audio routes through the connected glasses or headset.

Tests (no network, no keys, seeds are restored afterwards):

```bash
python -m pytest -q
```

## How the call works

`src/voice/server.py` is gradbot `demos/simple_chat/main.py` (init_logging, config, make_config, handle_session, routes.setup) plus instructions and tools; the page `src/voice/static/index.html` is simple_chat's with the agenda panel added. The app is mounted at `/voice` like the gradbot demos launcher; `/ws/chat` and `/api/call/*` are also served at the root. Gemini (`LLM_MODEL`
over `LLM_BASE_URL`) leads the dialog from `src/voice/prompt.py`; Gradium does STT and TTS. Tools the agent calls:

| Tool | Effect |
|---|---|
| `set_time_budget(seconds)` | `call.json` time budget; event `time_budget` |
| `log_decision(item_id, decision, notes, option?)` | `src/data/decisions.json` + `actions.json` via `src/core`; events `decision`, `v2_idea`, `participants_scaled` |
| `mark_irreversible_checkpoint(item_id, reason)` | action `BLOCKED_ON_CHECKPOINT`, waits for the dashboard click; event `checkpoint` |
| `set_speaking_speed(speed, reason)` | Gradium cadence mid-call via `send_config`; event `speed_changed` |
| `end_call(summary)` | post-call: `knowledge_graph_after.json`, `actions.json`, `transcript.json`, briefing; events `call_ended`, `brief_ready` |

Every event follows `docs/LIVE-EVENTS.md` and goes to `src.live.bus.publish` (try-import, no-op if absent) and to the
phone page. Data contract: `docs/SCHNITTSTELLE.md`, architecture: `docs/ARCHITEKTUR.md`, video tools: `tools/video/README.md`.
