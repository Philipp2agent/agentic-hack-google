# IDEE: DawnDispatch – Autonomous Morning Commute Voice Dispatcher & Action Dashboard

> **Core in one sentence:** An autonomous morning voice agent that calls your phone via Twilio and Gradium while you walk to work, lets you take the call hands-free on Meta Ray-Ban smart glasses to decide on overnight agent results, and reveals completed, personalized work on your laptop dashboard when you arrive ("Show me, don't tell me").

---

## 1. User & Problem (Persona)
**User:** Philipp (or Alex), Tech Lead / Founding Engineer in Zurich walking to the office.  
**The Problem:**
- While commuting (walking through Zurich streets), overnight autonomous agent runs, test alerts, and customer incidents pile up.
- Typing on a phone while walking is clumsy, slow, and dangerous; reading dense pull requests or dashboard logs on mobile screens is painful.
- Critical blockers sit idle until the engineer sits down at their desk, delaying team standup and blocking morning deployments.

**The Solution:**
- During the morning walk, the phone rings via **Twilio Voice**.
- Philipp answers hands-free via his **Meta Ray-Ban smart glasses**.
- Powered by **Gradium Voice** (low-latency STT/TTS) and **Gemini 3.8 Flash**, the agent delivers a razor-sharp, 3-item agenda synthesized from the night's autonomous work.
- In under 90 seconds of hands-free conversation, Philipp makes 2–3 high-leverage decisions (approve hotfix dispatch, hold release, approve overtime/SLA escalation).
- **"Show me, don't tell me":** When Philipp sits down at his laptop, the Web Dashboard immediately displays the fully executed, personalized work—live action cards, held release flags, generated hotfix PR diffs, and an auditable decision trail.

---

## 2. 2-Minute Demo Script (Video & Live Jury Presentation)

| Time | Actor / Scene | Interaction / Action | Visible / Audible Output |
|---|---|---|---|
| **0:00 - 0:25** | Phone Rings on the Commute | Philipp is walking to work with Meta Ray-Ban glasses on. Phone rings via Twilio. He taps the glasses temple to answer hands-free. | **Gradium Voice (natural audio streaming):**<br>*"Good morning Philipp. Overnight agent triage completed. 3 items require your decision before standup: 1) Staging test failure, 2) Emergency SLA escalation, 3) Compute quota alert. Item 1: Billing migration failed validation tests. Should we hold the 9 AM release and dispatch a hotfix bot?"* |
| **0:25 - 0:55** | Hands-free Voice Decisions | Philipp speaks naturally via Ray-Ban glasses microphone.<br>Agent asks for Human Checkpoints before irreversible actions. | **Philipp:** *"Hold the release, and dispatch the hotfix bot to isolate the schema diff."*<br>**Agent:** *"Confirmed. Release held, hotfix agent dispatched. Item 2: Enterprise customer Acme requests emergency SLA fix. Senior engineer requests 2 hours overtime approval. Approve?"*<br>**Philipp:** *"Approved up to 3 hours."*<br>**Agent:** *"Recorded: approved with 3-hour ceiling. All 3 decisions processed and executing. See you at your desk."* (Hangs up) |
| **0:55 - 1:35** | Laptop Reveal: "Show me, don't tell me" | Philipp arrives at office desk, opens laptop, shares Web Dashboard screen. | **Dashboard instantly displays live executed state:**<br>1. **Commute Call Card:** Audio waveform playback & synced transcript of the Ray-Ban call.<br>2. **Executed Action 1:** Release banner `RELEASE HELD VIA VOICE @ 07:32`; Hotfix PR generated with visual schema diff.<br>3. **Executed Action 2:** Signed Overtime Approval card with 3-hour limit and audit trail.<br>4. **Executive Standup Briefing:** 3-bullet personalized summary ready for 09:00 team standup. |
| **1:35 - 2:00** | DeepMind Criteria & Architecture Pitch | Presenter recaps the solution against hackathon criteria. | Highlights: (1) **Autonomous Action:** overnight triage + automated hotfix execution, (2) **Real Persona:** solves commute bottleneck, (3) **Human Checkpoint:** voice approval required for irreversible actions, (4) **Live Tech:** Twilio + Gradium + Gemini 3.8 Flash + Web Dashboard. |

---

## 3. System Components & Tech Stack
- **Voice Front Door (Telephony & Dialog):**
  - **Twilio Voice Webhook:** Inbound / Outbound call connection to cellphone.
  - **Meta Ray-Ban Glasses:** Bluetooth audio endpoint (microphone/speaker) for true hands-free interaction.
  - **gradbot Framework & Gradium:** Ultra-low latency STT, semantic end-of-turn pause detection, Gradium TTS audio streaming.
- **Orchestration & Reasoning:**
  - **Gemini 3.8 Flash:**
    - Tool calling during the phone call (`record_decision`, `dispatch_action`).
    - Overnight briefing synthesizer (synthesizes overnight mock runs into 3 structured decisions).
    - Post-call execution agent (turns approvals into concrete mock git PRs, held release flags, audit logs).
- **Backend & Storage:**
  - **FastAPI / uvicorn (Python):** REST & WebSocket server on VPS, exposed via cloudflared tunnel.
  - **State Store (JSON / SQLite):** Overnight events, Call state, Recorded decisions, Executed artifacts.
- **Web Dashboard:**
  - Responsive, modern dashboard (HTML/Tailwind/FastAPI).
  - Shows Call Audio Player & Transcript, Live Action Cards ("Show me, don't tell me"), Executed Diff Artifacts.
- **Language:** All prompts, UI, voice dialog, and logs are in **English**.

---

## 4. Scope: Must-have vs. Nice-to-have (Feature Freeze 18:00 CEST)

### Must-have (Core for 18:00 Freeze)
- [x] **Working Voice Flow:** Twilio phone call connection to gradbot/Gradium + Gemini 3.8 Flash dialog loop (with browser voice fallback).
- [x] **Structured Morning Agenda:** Overnight events prioritized into 3 concise decisions.
- [x] **Human Checkpoint Enforcement:** Explicit voice confirmation required before irreversible mock actions execute.
- [x] **"Show Me" Web Dashboard:** Responsive UI displaying:
  1. Overnight alerts & summary.
  2. Transcript & decision audit log from the phone call.
  3. Action result artifacts (Held release banner, Hotfix PR diff, Signed audit log).
- [x] **Deterministic Demo Seed:** Seed data demonstrating the full walk-to-desk workflow reliably.

### Nice-to-have (If time allows)
- [ ] Outbound auto-dial trigger from a "Trigger Morning Call" button on the web dashboard.
- [ ] Visual asset generated with Gemini Nano Banana (`tools/bild.py`) as part of the overnight incident report.
- [ ] WhatsApp / SMS follow-up summary link sent via Twilio right after call ends.

---

## 5. Risks & Countermeasures
1. **Telephony / Audio Latency on Conference Wi-Fi:**
   - *Countermeasure:* Gradbot supports local browser-audio fallback (`gradbot` web client) if mobile signal drops during live presentation; recorded audio backup of the real Twilio call available.
2. **Ambiguous Speech Recognition over Phone Line:**
   - *Countermeasure:* Constrained dialogue state; agent prompts with clear binary options ("Should I hold the release, or proceed?"); confirmation repetitions for high-risk actions.
3. **Tight Timeline (Feature Freeze at 18:00 CEST):**
   - *Countermeasure:* Parallel execution: Claude-Cloud designs modular architecture and writes Gemini worker specs (`auftraege/gemini-NN.md`); Gemini workers implement backend, voice flow, and UI in parallel branches.

---

## 6. 3 Decisions for Philipp (1A/1B)
1. **Call-Trigger:**
   - **1A: Outbound Call (Triggered via Web-Button or Scheduled)** *(Empfehlung)* – Handy klingelt "von selbst", perfekte Story für "Ich gehe zur Arbeit und mein Handy klingelt".
   - **1B: Inbound Call (Philipp ruft Twilio-Nummer an)** – Technisch einfacher (kein Twilio Outbound API Call nötig), aber weniger magisch.
2. **Szenario-Domäne:**
   - **2A: Tech Lead / DevOps (Staging Failure, Hotfix Dispatch, Overtime Approval)** *(Empfehlung)* – Höchste Relevanz und Glaubwürdigkeit vor einer Tech- und AI-Jury.
   - **2B: Product / Ops Executive (Budget overrun, Vendor contract sign-off, Customer escalation)** – Breiter verständlich, aber weniger technisch greifbar.
3. **Dashboard "Show Me"-Fokus:**
   - **3A: Action & Execution Cards (Visual Diff, Triage Artifact, Signed Audit Trail)** *(Empfehlung)* – Maximale Demonstration von autonomem Agenten-Handeln ("Show me, don't tell me").
   - **3B: Executive Briefing & Audio Recap (Visual Timeline + Podcast Player)** – Fokus auf Informationsverdichtung statt Aktionsausführung.
