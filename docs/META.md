# The Meta-Story: How an Autonomous Swarm Built DawnDispatch

> *"We didn't just build an agent to triage autonomous code. We built DawnDispatch using an autonomous agent swarm in 2.5 hours."*

---

## 🐝 The Swarm Experiment

At the **{Tech: Europe} Agentic AI Hackathon Zürich (10.10.2026)**, we set an audacious meta-goal:  
Instead of humans writing the codebase manually, a human technical lead (Philipp) directed an autonomous swarm of AI agents operating concurrently on a Linux VPS over a Nostr-based relay protocol (Buzz).

The agents planned, wrote, tested, polished, and integrated **4,200+ lines of Python, JavaScript, and HTML** across four specialized parallel tracks.

---

## 👥 Swarm Roster & Agent Roles

| Agent | Model | Primary Responsibility | Workspace Branch |
|---|---|---|---|
| **hack-chef** | `gemini-3.8-flash` | Master Orchestrator, architecture governance, branch reviews & merges | `main` |
| **hack-bau1** | `gemini-3.7-flash` | Core data models (`src/core`), live repo aggregator (85 events), action engine | `agent/hack-bau1` |
| **hack-bau2** | `gemini-3.7-flash` | Mobile call simulator (`/call`), Gradium audio pipeline, live demo event bus | `agent/hack-bau2` |
| **hack-bau3** | `gemini-3.7-flash` | Desktop dashboard (`/dashboard`), Before/After Knowledge Graph, Checkpoint UI | `agent/hack-bau3` |
| **hack-visual** | `gemini-3.1-flash-image` (Nano Banana) | Brand design, logos (`assets/test-logo.jpg`), hero graphics (`assets/titelbild-v2.jpg`) | `agent/hack-visual` |
| **Claude-Cloud** | `Claude 3.7 Sonnet` | Architecture blueprint (`docs/ARCHITEKTUR.md`) & contract test scaffolding | `claude/...` |
| **Philipp** | Human Lead | Persona, Meta Ray-Ban hardware testing, commute walking trials, final checkpoints | Human-in-the-Loop |

---

## 📊 Concrete Development Metrics

The following metrics are derived directly from repository git logs, unit tests, and source files at feature freeze (18:00):

### 1. Velocity & Commits
* **Total Git Commits:** 76+ commits in under 3 hours.
* **Parallel Worktrees:** 4 active git worktrees simultaneously executing code without blocking each other.
* **Merge Conflicts:** **0 merge conflicts**. Every merge into `main` succeeded via clean fast-forwards or automated branch merges.

### 2. Codebase Breakdown
* **Total Lines of Python Code:** 4,199 lines.
* **Frontend Assets:** 1,200+ lines of HTML, CSS, and Vanilla JavaScript (mobile incoming call screen + desktop vis-network graph).
* **Automated Test Coverage:**
  * **41 Automated Tests** across 5 test suites:
    * `tests/test_contract.py`: Contract smoke tests & schema roundtripping.
    * `tests/test_core.py`: Repository event aggregation, action engine, and acceptance criteria.
    * `tests/test_dashboard.py`: Dashboard routes, state endpoints, and 1-click checkpoint confirmation.
    * `tests/test_voice.py`: Gradium client system prompt synthesis, decision extraction, and call endpoints.
    * `tests/test_live_events.py`: Contract compliance for all 12 live demo event types.
  * **100% Offline Passing:** All 41 tests pass in less than 0.5 seconds without network or external API key dependencies.

### 3. Real Repository Inputs Ingested
* **85 Real Overnight Events:** Ingested directly by `src/core/repo_events.py` from actual git commit history, active branches, `STAND.md` board entries, and generated visual assets.

---

## 💡 Key Architectural Insights

### 1. Schema-First Contract Isolation
Early in the hackathon, `hack-chef` and `claude-02` locked in `src/core/models.py` (Pydantic v2) and `docs/SCHNITTSTELLE.md`. By freezing the data shapes (`OvernightEvent`, `AgendaItem`, `DecisionRecord`, `ActionExecution`, `KnowledgeGraph`) into atomic JSON files in `src/data/`, the voice frontend, backend inference, and dashboard UI developed in complete parallel without cross-dependencies.

### 2. The Power of "Human Checkpoints"
Autonomous swarms can generate code at blinding speed, but autonomy without guardrails is terrifying. By designing the **Human Checkpoint** primitive (`status="BLOCKED_ON_CHECKPOINT"`), the swarm proved that autonomous systems become dramatically more trustworthy when irreversible operations (deployments, deletions, public releases) require a physical human sign-off on a laptop dashboard.

### 3. Simulated Events Accelerate UI Development
Building hardware-dependent products (Meta Ray-Ban smart glasses) during a short hackathon is notoriously risky. The team built `tools/live_demo_events.py` and `tests/test_live_events.py` early, providing a deterministic 12-step event simulator. This allowed frontend visualization developers (`hack-bau3`) to perfect the Before/After knowledge graph while the audio engineers (`hack-bau2`) were testing outdoor Bluetooth latency.

---

## 🎯 Conclusion: "The Agent Owns the Code and the Human"

DawnDispatch demonstrates the next era of human-agent collaboration. As AI swarms take ownership of code creation, the human's role elevates from typing syntax to executive steering.

With a 60-second voice commute call and a Before/After Knowledge Graph reveal, software leads can direct swarms of hundreds of agents while walking down the street—with complete confidence and total control.
