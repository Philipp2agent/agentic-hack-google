# DawnDispatch

> **Autonomous Commute Voice Dispatcher & Knowledge Graph Dashboard**  
> *"The agent owns the code and the human."*

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![Google DeepMind Gemini](https://img.shields.io/badge/Gemini-3.8_Flash-4285F4.svg)](https://deepmind.google/technologies/gemini/)
[![Gradium Voice](https://img.shields.io/badge/Gradium-Realtime_Voice-FF5722.svg)](https://gradium.ai)
[![Tests](https://img.shields.io/badge/Tests-41%2F41_Passing-success.svg)](tests/)
[![Hackathon](https://img.shields.io/badge/Hackathon-{Tech:_Europe}_Zürich_2026-blueviolet.svg)](HACKATHON.md)

![DawnDispatch Hero Banner](assets/titelbild-v2.jpg)

---

## 🌅 The Problem

Autonomous software agent swarms build code while developers sleep. Overnight, dozens of commits land, branches diverge, background pull requests open, and CI pipelines finish.

When a technical lead or founding engineer heads to the office in the morning, they face a wall of unread logs and pull request alerts. Reading raw git commit diffs on a smartphone while walking across a crowded city street is cumbersome, distracting, and unsafe. Traditional notifications fail because they demand constant eyes-down screen interaction.

## ⚡ The Solution: DawnDispatch

**DawnDispatch** turns the morning commute into an effortless, hands-free decision sprint:

1. **Voice Front Door via Meta Ray-Ban Smart Glasses (`/call`):**  
   A mobile web incoming call simulator (`/call`) rings on the user's phone. Audio streams directly over Bluetooth to open-ear Meta Ray-Ban smart glasses using Web Audio and WebSocket streaming.
2. **60-Second Rapid Quick-Fire Standup:**  
   The agent greets the lead with *"Good morning Philipp. How much time do you have?"* Upon hearing *"Got 60 seconds. Keep it fast"*, the system automatically accelerates speaking rate (Gradium TTS speed scaling) and fires concise Yes/No triage questions synthesized from overnight repository activity.
3. **Desk Reveal: Before/After Knowledge Graph (`/dashboard`):**  
   Arriving at the desk, the engineer opens the laptop dashboard. Instead of dry text, an interactive Before/After Knowledge Graph ("Show me, don't tell me") demonstrates how the 60-second voice standup resolved open blocker nodes into concrete, dispatched actions.
4. **Human Checkpoint Safeguard:**  
   Irreversible actions (such as publishing a repository, migrating production databases, or triggering production deployments) cannot execute autonomously. They pause in a `BLOCKED_ON_CHECKPOINT` state, displaying visual diff previews and awaiting a verified 1-click confirmation on the desktop dashboard.

---

## 🤝 Partner Technologies & DeepMind Alignment

### 1. Google DeepMind Gemini
* **Gemini 3.8 Flash (`gemini-3.8-flash`):** Drives conversational quickfire triage dialog with tool execution (`set_time_budget`, `log_decision`, `mark_irreversible_checkpoint`).
* **Interactions API (`google-genai`):** Synthesizes overnight repository events into a crisp 3-to-4 item agenda, infers knowledge graph relationships, and extracts post-call executive briefings.
* **Gemini Nano Banana (`gemini-3.1-flash-image` / `gemini-2.5-flash-image`):** Generated brand assets, logos, and hero visuals in `assets/`.
* **DeepMind Agentic Principles Fulfilled:**
  1. **Acts Autonomously:** Continuously aggregates repository events, plans morning agendas, and dispatches follow-up agent tasks.
  2. **Serves a Real Human:** Built for a named technical lead (Philipp) walking to his office in Zürich.
  3. **Human Retains Control:** Irreversible operations require explicit 1-click desk checkpoints.
  4. **Live Execution:** Fully tested with 85 real repository events extracted from live git history.

### 2. Gradium Voice AI
* **Low-Latency Speech-to-Text & Text-to-Speech:** Real-time bi-directional audio streaming over WebSockets powered by the `gradbot` framework.
* **Dynamic Cadence & Speed Scaling:** Accelerates speech playback from 1.0x to 1.35x when the user indicates time pressure.
* **Acoustics Optimized for Smart Glasses:** Open-ear audio tuning ensuring clear intelligibility in urban outdoor environments.

### 3. Meta Ray-Ban Smart Glasses
* Open-ear spatial speakers and beamforming directional microphones enable true eyes-up, hands-free commute triage.

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    subgraph Commute["A. Voice Front Door (Handy + Meta Ray-Bans)"]
        RB["Meta Ray-Ban Smart Glasses<br/>Bluetooth mic + speaker"] <--> MC["Mobile Browser (/call)<br/>Incoming Call UI · Web Audio"]
    end

    subgraph VoiceEngine["B. Voice Streaming & Dialog"]
        MC <-- "WebSocket /ws/chat" --> VS["src/voice/app.py<br/>gradbot handle_session"]
        VS <--> GR["Gradium AI<br/>Realtime STT / TTS · Speed Scaling"]
        VS <-- "Tool Calls" --> GM["Gemini 3.8 Flash<br/>Rapid Quick-Fire Dialog"]
    end

    subgraph Core["C. Orchestration, Reasoning & State"]
        GH[("GitHub Repository<br/>Git Commits · PRs · Branches")] --> RE["src/core/repo_events.py<br/>85 Live Overnight Events"]
        RE --> AE["src/core/action_engine.py<br/>Gemini Interactions API"]
        AE --> KG["src/core/graph.py<br/>Knowledge Graph Engine"]
        AE <--> ST[("Atomic State Store (src/data/)<br/>events · agenda · decisions · actions")]
    end

    subgraph Desktop["D. Desk Reveal Dashboard"]
        ST --> DB["src/dashboard/app.py<br/>Dashboard API (/dashboard)"]
        DB --> UI["dashboard.html (vis-network)<br/>Before/After Graph Toggle<br/>Synchronized Call Transcript<br/>1-Click Checkpoint Confirm Card"]
        UI -- "1-Click Confirm" --> DB --> AE
    end

    VS -- "log_decision / mark_checkpoint" --> ST
```

### Repository Structure
```
agentic-hack-google/
├── assets/                    # Brand assets, logos & hero images generated via Nano Banana
├── docs/
│   ├── ARCHITEKTUR.md         # Detailed system architecture & component interfaces
│   ├── SCHNITTSTELLE.md       # Canonical data schemas & contracts
│   ├── LIVE-EVENTS.md         # Real-time event streaming protocol
│   ├── VIDEO_SCRIPT.md        # 2-Minute video & demo walkthrough script
│   └── META.md                # Autonomous swarm development story & metrics
├── src/
│   ├── app.py                 # Unified FastAPI entry point (mounts voice & dashboard)
│   ├── core/                  # Event aggregator, Gemini client, agenda & graph engine
│   │   ├── action_engine.py   # Decision execution & irreversible checkpoint logic
│   │   ├── agenda.py          # Quick-fire triage catalog & v1->v2 roadmap
│   │   ├── gemini_client.py   # Interactions API & fallback client helper
│   │   ├── graph.py           # Knowledge graph generation (Before / After)
│   │   ├── models.py          # Pydantic v2 data models
│   │   ├── repo_events.py     # Live git log, branch & Stand aggregator
│   │   └── state.py           # RLock thread-safe atomic JSON state store
│   ├── dashboard/             # Desktop dashboard UI & API
│   │   ├── app.py             # Dashboard routes, actions & checkpoint endpoints
│   │   └── static/            # Dashboard HTML, CSS, and vis-network graph UI
│   ├── voice/                 # Mobile call simulator & Gradium voice client
│   │   ├── app.py             # Mobile call routes (/call) & transcript export
│   │   ├── gradium_client.py  # System prompt generator & decision extractor
│   │   └── static/            # Realistic iOS/Android incoming call screen
│   └── data/                  # Committed seed data & live state JSON files
├── tests/                     # 41 automated unit & integration tests (100% offline)
└── tools/
    ├── bild.py                # Nano Banana image generation tool
    ├── live_demo_events.py    # Live demo event generator for /live screen
    └── ton.py                 # Gemini audio generation tool
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites
* Python 3.10 or higher
* Git

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/Philipp2agent/agentic-hack-google.git
cd agentic-hack-google

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install required dependencies
pip install fastapi uvicorn google-genai pydantic starlette httpx
```

### 3. Environment Configuration
Create a `.env` file (see `.env.example`):
```bash
GEMINI_API_KEY=your_google_gemini_api_key
GRADIUM_API_KEY=your_gradium_api_key
```
*Note: The entire test suite and deterministic core engines run offline without external API keys.*

### 4. Running the Application
Launch the unified FastAPI server:
```bash
uvicorn src.app:app --host 0.0.0.0 --port 8000 --reload
```

Open the key interfaces in your browser:
* **Mobile Call Screen (Phone / Ray-Ban):** [`http://localhost:8000/call`](http://localhost:8000/call)
* **Desktop Command Dashboard (Laptop):** [`http://localhost:8000/dashboard`](http://localhost:8000/dashboard)
* **API Health Check:** [`http://localhost:8000/api/health`](http://localhost:8000/api/health)

### 5. Running the Automated Test Suite
Run all 41 test cases across contracts, core models, dashboard API, voice pipeline, and live event schemas:
```bash
python -m unittest discover -s tests -v
```
All tests run in isolated temporary environments and pass 100% offline.

---

## 🎬 2-Minute Demo Flow

1. **Mobile Incoming Call (`/call`):** Simulated incoming call rings with Web Audio chime; hands-free audio streams to Meta Ray-Bans.
2. **Rapid Quick-Fire Standup:** 60-second dialog covers 4 key overnight items:
   * **Item 1 (Status v1):** Baseline lock-in of mobile call screen and audio engine -> `APPROVE`.
   * **Item 2 (Decision v2):** Selection of Version 2 priority candidate (Option A: Real WhatsApp / Telephony) -> `APPROVE`, auto-dispatched to swarm build queue.
   * **Item 3 (Irreversible Checkpoint):** Public repository submission and autonomous write access -> `APPROVE with Checkpoint`, held in `BLOCKED_ON_CHECKPOINT`.
   * **Item 4 (Scale Network):** Expansion of commute triage network to all 42 hackathon teams -> `APPROVE`.
3. **Desk Reveal (`/dashboard`):**
   * Before/After Knowledge Graph visually transitions from unresolved red/yellow clusters to green completed nodes.
   * Amber pulsing Checkpoint Card shows git commit preview for hackathon submission.
   * Lead clicks **"1-Click Confirm Checkpoint"** -> Action turns `COMPLETED`.

See [`docs/VIDEO_SCRIPT.md`](docs/VIDEO_SCRIPT.md) for the second-by-second video recording storyboard.

---

## 🐝 The Meta Story: Built by an Autonomous Swarm

DawnDispatch was conceived, architected, and built in **2.5 hours** by an autonomous agent swarm collaborating in real-time on a Linux VPS:

* **76+ Git Commits** across parallel worktrees (`hack-chef`, `hack-bau1`, `hack-bau2`, `hack-bau3`, `hack-visual`, `Claude-Cloud`).
* **4,200+ Lines of Code** across backend inference, voice streaming, and interactive graph visualizations.
* **Zero Merge Conflicts** achieved through strict schema contracts (`docs/SCHNITTSTELLE.md`).

Read the full development narrative and swarm metrics in [`docs/META.md`](docs/META.md).

---

## 📜 License & Acknowledgments

Built at the **{Tech: Europe} Agentic AI Hackathon Zürich (10.10.2026)**.  
Sponsored by Google DeepMind and Gradium.

## Run locally (claude-03)

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
| `http://127.0.0.1:8090/call` | phone page (redirects to `/voice/`, the proven `dawn/` client): round call button, Dawn speaks first (mic needs HTTPS on a phone, see tunnel) |
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

`src/voice/server.py` is `dawn/main.py` (the proven gradbot simple_chat base: init_logging, config, make_config, handle_session, routes.setup, client `dawn/static/index.html`) plus tools and live events. The app is mounted at `/voice` like the gradbot demos launcher; `/ws/chat` and `/api/call/*` are also served at the root. Gemini (`LLM_MODEL`
over `LLM_BASE_URL`) leads the dialog from `src/voice/prompt.py`; Gradium does STT and TTS. Tools the agent calls:

| Tool | Effect |
|---|---|
| `log_decision(item_id, decision, notes, option?)` | `src/data/decisions.json` + `actions.json` via `src/core`; events `decision`, `v2_idea`, `participants_scaled` |
| `mark_irreversible_checkpoint(item_id, reason)` | action `BLOCKED_ON_CHECKPOINT`, waits for the dashboard click; event `checkpoint` |
| `end_call(summary)` | post-call: `knowledge_graph_after.json`, `actions.json`, `transcript.json`, briefing; events `call_ended`, `brief_ready` |

Every event follows `docs/LIVE-EVENTS.md` and goes to `src.live.bus.publish` (try-import, no-op if absent) and to the
phone page. Data contract: `docs/SCHNITTSTELLE.md`, architecture: `docs/ARCHITEKTUR.md`, video tools: `tools/video/README.md`.
