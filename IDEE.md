# IDEE: DawnDispatch – Autonomous Morning Commute Voice Dispatcher & Action Dashboard

> **Core in one sentence:** An autonomous morning voice agent that connects via mobile web audio hands-free over Meta Ray-Ban smart glasses during your morning walk, conducts an agenda-driven triage over overnight agent outputs from this repo, and reveals completed, personalized work and irreversible checkpoints on your laptop dashboard ("Show me, don't tell me").

---

## 1. User & Problem (Persona)
**User:** Philipp, Tech Lead / Founding Engineer in Zurich walking to the office.  
**The Problem:**
- While commuting (walking through Zurich streets), overnight autonomous agent runs, test alerts, PRs, and decisions pile up in the repo.
- Typing on a phone while walking is clumsy, slow, and dangerous; reading dense pull requests or dashboard logs on mobile screens is painful.
- Critical blockers sit idle until the engineer sits down at their desk, delaying team standup and blocking morning deployments.

**The Solution:**
- During the morning walk, Philipp opens the mobile web page on his phone.
- Audio streams seamlessly hands-free over **Meta Ray-Ban smart glasses** via Bluetooth (no Twilio, no WhatsApp).
- Powered by **gradbot + Gradium Voice** (low-latency STT/TTS, custom voice design) and **Gemini 3.8 Flash**, the agent leads an agenda-driven standup triage over the overnight agent swarm activity in `Philipp2agent/agentic-hack-google`.
- In under 90 seconds of hands-free conversation, Philipp makes 2–3 high-leverage decisions.
- **"Show me, don't tell me":** When Philipp sits down at his laptop, the Web Dashboard immediately displays the fully executed, personalized work—live action cards, generated PR diffs, and irreversible actions waiting for his explicit checkpoint click.

---

## 2. 2-Minute Demo Script (Video & Live Jury Presentation)

| Time | Actor / Scene | Interaction / Action | Visible / Audible Output |
|---|---|---|---|
| **0:00 - 0:25** | Hands-free Commute Audio Link | Philipp is walking to work with Meta Ray-Ban glasses on. He starts the web voice call on mobile. Audio connects via Bluetooth. | **Gradium Voice (custom voice, natural audio streaming):**<br>*"Good morning Philipp. Overnight agent swarm triage in agentic-hack-google completed. 3 items require your decision before standup: 1) PR #4 schema migration, 2) Visual asset approval for DawnDispatch, 3) Compute budget allocation for Gemini 3.8. Item 1: hack-bau1 completed the schema migration, but requires approval to deploy to staging. Approve or hold?"* |
| **0:25 - 0:55** | Hands-free Voice Decisions | Philipp speaks naturally via Ray-Ban glasses microphone.<br>Agent extracts decisions, notes checkpoints, and executes downstream tasks. | **Philipp:** *"Approve staging deployment, and dispatch hack-bau2 to run smoke tests."*<br>**Agent:** *"Confirmed. Staging deployment triggered, smoke tests dispatched. Item 2: hack-visual generated 3 hero banners. Two are finalized; one irreversible publishing step awaits your laptop click. Item 3: Gemini 3.8 budget headroom is at 85%. Requesting 50k token buffer."*<br>**Philipp:** *"Granted for today's hackathon."*<br>**Agent:** *"Recorded. All decisions processed. See you at your desk."* |
| **0:55 - 1:35** | Laptop Reveal: "Show me, don't tell me" | Philipp arrives at office desk, opens laptop, shares Web Dashboard screen. | **Dashboard instantly displays live executed state:**<br>1. **Commute Voice Call Card:** Audio waveform playback & synced transcript of the Ray-Ban conversation.<br>2. **Personalized Executed Actions:** Live status of staging deploy, smoke test results, token quota update.<br>3. **Human Checkpoint (Irreversible Action):** Distinct action card waiting for Philipp's click: `[Publish Hero Asset to Public Repo]` with instant visual diff.<br>4. **Standup Briefing:** 3-bullet personalized summary ready for 09:00 team standup. |
| **1:35 - 2:00** | DeepMind Criteria & Architecture Pitch | Presenter recaps the solution against hackathon criteria. | Highlights: (1) **Autonomous Action:** overnight triage + automated task dispatch, (2) **Real Persona:** solves commute bottleneck with Ray-Ban glasses, (3) **Human Checkpoint:** irreversible actions strictly gated on laptop click, (4) **Live Tech:** gradbot + Gradium Voice + Gemini 3.8 Flash Interactions API + FastAPI Dashboard. |

---

## 3. System Components & Tech Stack
- **Voice Front Door (Web Audio & Dialog):**
  - **gradbot Framework & Gradium:** Minimal FastAPI + WebSocket voice chat (`simple_chat` baseline running on VPS), ultra-low latency STT, semantic end-of-turn pause detection, Gradium TTS audio streaming with custom voice design.
  - **Meta Ray-Ban Glasses:** Bluetooth audio endpoint (mic & open-ear speakers) connected to mobile web browser. Direct web audio—no third-party telephony services (no Twilio, no WhatsApp).
- **Orchestration & Reasoning:**
  - **Gemini 3.8 Flash (Google Interactions API):**
    - Overnight Agent Activity Aggregator: synthesizes raw agent logs and git events from `Philipp2agent/agentic-hack-google` into a prioritized 3-item voice agenda.
    - Real-time conversational agent driving the voice call.
    - Post-call interaction processor: extracts structured decisions and downstream tool dispatches.
- **Action Engine & Human Checkpoint:**
  - Fast execution for reversible actions (dispatching tests, updating status).
  - Explicit Human Checkpoint gating for irreversible actions (e.g. production/public publish, deletions, permanent deployments).
- **Web Dashboard ("Show me, don't tell me"):**
  - FastAPI + modern Tailwind/HTML frontend.
  - Displays audio replay, live decision audit trail, and interactive checkpoint buttons.

---

## 4. DeepMind & Hackathon Criteria Matrix

| Criterion | Implementation in DawnDispatch |
|---|---|
| **Acts autonomously** | Swarm agents run overnight in repo; Morning agent synthesizes agenda and triggers actions immediately upon voice input. |
| **Solves a real problem for a real person** | Philipp commutes hands-free with Meta Ray-Ban glasses; unblocks team before arriving at the office without looking at a screen. |
| **Human in control (Checkpoints)** | High-leverage choices decided by voice; irreversible actions held for explicit laptop confirmation. |
| **Runs live with real inputs** | Live Gradium Web Audio + live Gemini 3.8 Flash + real repo events from `Philipp2agent/agentic-hack-google`. |
| **Partner Technologies** | **Google Gemini 3.8 Flash** (Interactions API / Reasoning) + **Gradium** (gradbot, STT, TTS, Custom Voice Design). |
