# IDEE: DawnDispatch – Autonomous Morning Commute Voice Dispatcher & Action Dashboard

> **Core in one sentence:** An autonomous morning agent that calls your phone via Twilio and Gradium Voice while you walk to work, walks you through critical overnight decisions from night-shift agent runs, and reveals completed, personalized work on your laptop dashboard when you arrive ("Show me, don't tell me").

---

## 1. User & Problem (Persona)
**User:** Alex (or Philipp), Tech Lead / Product Founder in Zurich.  
**The Problem:**
- While commuting to work (walking, bus, train), dozens of overnight notifications, test runs, customer escalations, and PRs flood in.
- Typing on a smartphone while walking is clumsy, slow, and unsafe; reading complex dashboards on mobile is painful.
- Often, key blockers sit idle until the engineer sits down at their laptop at 08:30, delaying the entire team's morning.

**The Solution:**
- At 07:30, the phone rings via Twilio.
- Powered by **Gradium Voice** and **Gemini 3.8 Flash**, the agent greets Alex with a prioritized 3-item morning agenda synthesized from overnight runs.
- In under 90 seconds of hands-free conversation, Alex makes 2–3 high-leverage decisions (hold/proceed with release, authorize emergency overtime, trigger hotfix).
- **"Show me, don't tell me":** Upon opening the laptop at the office, the Web Dashboard displays the fully executed actions—not just meeting notes, but held releases, deployed fixes, updated triage tickets, and an audit trail.

---

## 2. 2-Minute Demo Script (Video & Live Jury Presentation)

| Time | Actor | Interaction / Action | Visible / Audible Output |
|---|---|---|---|
| **0:00 - 0:25** | Phone Rings (Commute) | Philipp is walking to work. Phone rings via Twilio. He answers on speaker / headset. | Gradium Voice (natural audio): *"Good morning Philipp. Your overnight triage is ready. 3 items require your call: 1) Staging test failure, 2) Emergency SLA ticket, 3) Compute quota alert. Let's start with item 1: The billing migration failed validation tests. Should we hold the 9 AM release and dispatch a hotfix bot?"* |
| **0:25 - 0:55** | Voice Dialogue & Decisions | Philipp (hands-free): *"Hold the release, and dispatch the hotfix bot to isolate the schema diff."*<br>Agent: *"Confirmed. Release held. Item 2: Enterprise customer Acme requests emergency SLA fix. Senior engineer asks for 2h overtime approval. Approve?"*<br>Philipp: *"Approved up to 3 hours."*<br>Agent: *"Approved. All decisions recorded and queued for execution. See you at your desk."* | Live speech-to-text and tool-calling on backend. Agent commits human-checkpoint approvals with signed audit logs. Agent hangs up. |
| **0:55 - 1:35** | Laptop Reveal: "Show me, don't tell me" | Philipp arrives at laptop, switches screen share to Web Dashboard (`localhost` / tunnel). | **Dashboard displays live executed state:**<br>1. **Audio & Call Card:** Waveform/transcript of the commute call.<br>2. **Executed Action 1:** Release banner `HELD BY VOICE @ 07:32`; hotfix branch created with diff.<br>3. **Executed Action 2:** Overtime approval logged in audit trail with timestamp & budget ceiling.<br>4. **Executive Standup Card:** Auto-generated 3-bullet summary ready for 09:00 standup. |
| **1:35 - 2:00** | DeepMind Criteria & Architecture | Presenter recaps against jury criteria. | Highlights: (1) Acts autonomously (triage + execution), (2) Solves real human commute bottleneck, (3) Human checkpoint (voice approval before irreversible deployment), (4) Live working stack (Gradium + Gemini 3.8 Flash + Twilio). |

---

## 3. System Components & Tech Stack
- **Voice Front Door (Telephony & Dialog):**
  - **Twilio Voice Webhook:** Inbound / Outbound phone call management.
  - **gradbot Framework & Gradium:** Low-latency STT (Speech-to-Text), semantic end-of-turn pause detection, and Gradium TTS voice streaming.
- **Orchestration & LLM:**
  - **Gemini 3.8 Flash:**
    - Tool calling during the phone call (invoking decision-logging tools).
    - Overnight briefing synthesizer (summarizes mock inbox/alerts into structured agenda).
    - Post-call execution agent (translates approvals into executed mock-system actions).
- **Backend & Storage:**
  - **FastAPI / uvicorn (Python):** REST & WebSocket server running on VPS, exposed via cloudflared.
  - **State Store (JSON / SQLite):** Overnight events, Call state, Recorded decisions, Executed artifacts.
- **Web Dashboard:**
  - Modern, responsive web interface (HTML/Tailwind/FastAPI).
  - Displays Morning Agenda, Audio playback / Transcript, Live Action Cards ("Show me, don't tell me").
- **Language:** All prompts, UI, voice dialog, and logs are in **English**.

---

## 4. Scope: Must-have vs. Nice-to-have (Feature Freeze 18:00 CEST)

### Must-have (Core for 18:00 Freeze)
- [x] **Working Voice Flow:** Twilio phone call connection to gradbot/Gradium + Gemini 3.8 Flash dialog loop (with browser voice fallback).
- [x] **Structured Morning Agenda:** Overnight events loaded, prioritized into 3 concise decisions.
- [x] **Human Checkpoint Enforcement:** Explicit voice confirmation required before irreversible mock actions execute.
- [x] **"Show Me" Web Dashboard:** Responsive UI displaying:
  1. Overnight alerts & summary.
  2. Transcript & decision audit log from the phone call.
  3. Action result artifacts (e.g. Held release notice, Triage ticket, Audit trail).
- [x] **Reproducible Demo Scenario:** Deterministic seed data demonstrating the complete workflow reliably.

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
   - *Countermeasure:* Parallel execution: Claude-Cloud designs the modular architecture and writes Gemini worker specs (`auftraege/gemini-NN.md`); Gemini workers implement backend, voice flow, and UI in parallel branches.

---

## 6. 3 Decisions for Philipp (1A/1B)
1. **Call Trigger:**
   - **1A: Outbound Call (Triggered via Web-Button or Scheduled)** *(Empfehlung)* – Handy klingelt "von selbst", perfekte Story für "Ich gehe zur Arbeit und mein Handy klingelt".
   - **1B: Inbound Call (Philipp ruft Twilio-Nummer an)** – Technisch einfacher (kein Twilio Outbound API Call nötig), aber weniger magisch.
2. **Szenario-Domäne:**
   - **2A: Tech Lead / DevOps (Staging Failure, Hotfix Dispatch, Overtime Approval)** *(Empfehlung)* – Höchste Relevanz und Glaubwürdigkeit vor einer Tech- und AI-Jury.
   - **2B: Product / Ops Executive (Budget overrun, Vendor contract sign-off, Customer escalation)** – Breiter verständlich, aber weniger technisch greifbar.
3. **Dashboard "Show Me"-Fokus:**
   - **3A: Action & Execution Cards (Visual Diff, Triage Artifact, Signed Audit Trail)** *(Empfehlung)* – Maximale Demonstration von autonomem Agenten-Handeln ("Show me, don't tell me").
   - **3B: Executive Briefing & Audio Recap (Visual Timeline + Podcast Player)** – Fokus auf Informationsverdichtung statt Aktionsausführung.
