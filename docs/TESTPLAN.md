# DawnDispatch: E2E Testplan & Verification Protocol

> **Event:** {Tech: Europe} Agentic AI Hackathon Zürich (10.10.2026)  
> **Target Run:** 17:15 CEST Walkthrough with Meta Ray-Ban Smart Glasses  
> **Tester & Presenter:** Philipp (Human Lead / Founding Engineer)  
> **Feature Freeze:** 18:00 CEST | **Video Recording:** 18:15 CEST | **Submission:** 19:00 CEST  

---

## 1. Test Scope & Pre-Flight Prerequisites

### Hardware & Environment
- **Smartphone:** Modern mobile browser (Chrome / Safari) connected to Meta Ray-Ban glasses via Bluetooth.
- **Meta Ray-Ban Smart Glasses:** Fully charged (> 50%), Bluetooth audio output verified, microphone permission enabled.
- **Laptop:** Desktop browser (Chrome / Brave) opened at [`http://localhost:8000/dashboard`](http://localhost:8000/dashboard).
- **Backend Host (VPS):** FastAPI unified application running on port 8000 (accessible locally or via cloudflared HTTPS tunnel).

### Pre-Flight Automated Check
Run the automated pre-flight test script before heading outdoors:
```bash
/home/buzzagent/hack/.venv/bin/python scripts/validate_demo.py
```
*Expected Result:* All 40+ system checks return `[PASS]`, exit code `0`.

---

## 2. Step-by-Step Test Scenarios (TC-01 through TC-07)

### TC-01: Automated Seed & Contract Integrity
* **Objective:** Ensure all committed seed files in `src/data/` adhere to Pydantic v2 schemas and contain live repo data.
* **Procedure:**
  1. Execute `/home/buzzagent/hack/.venv/bin/python -m unittest discover -s tests -v`.
  2. Verify all 41 test cases pass cleanly offline.
* **Pass Criteria:**
  - `overnight_events.json` contains ≥ 5 valid events (current seed: 85 events).
  - `agenda.json` contains exactly 1 irreversible item (`agenda-03`).
  - No network errors, 100% offline passing.

---

### TC-02: Mobile Incoming Call Screen & Web Audio Ring (`/call`)
* **Objective:** Verify mobile incoming call simulator and hands-free answering ergonomics.
* **Procedure:**
  1. Open [`http://localhost:8000/call`](http://localhost:8000/call) on the smartphone.
  2. Confirm incoming call ring chime sounds through Meta Ray-Ban open-ear speakers.
  3. Visual check: Screen displays **"Incoming Call: DawnDispatch Agent"** with caller avatar and pulsing green Accept button.
  4. Tap the Accept button (or tap Ray-Ban temple touch-pad).
* **Pass Criteria:**
  - Transition from `screen-incoming` to `screen-active` in < 200 ms.
  - Active call timer starts counting from `00:00`.
  - Audio waveform animates smoothly in response to agent speech.

---

### TC-03: Rapid Quick-Fire Triage & Cadence Match
* **Objective:** Test speech-to-text accuracy, dynamic speed scaling, and multi-turn rapid standup.
* **Procedure:**
  1. **Greeting:** Agent speaks: *"Good morning Philipp. Overnight your autonomous agents kept building DawnDispatch. I have four things for you. How much time do you have?"*
  2. **Cadence Trigger:** Philipp answers: *"Morning! I have about 60 seconds walking down to the office. Keep it fast."*
  3. **Speed Scaling:** Agent acknowledges with speed acceleration (1.25x TTS playback): *"Speed adjusted to 1.25x. Rapid fire starting now."*
  4. **Turn 1 (Status v1):**
     - Agent: *"Item 1: Version 1 baseline was built today — simulated web call on Ray-Bans, low-latency audio, before/after graph. Anything you want me to flag?"*
     - Lead: *"No, Version 1 baseline looks solid. Let's proceed."*
     - Agent logs `APPROVE` on `agenda-01`.
  5. **Turn 2 (Decision v2):**
     - Agent: *"Item 2: Which Version 2 feature should the autonomous build pipeline prioritize — Option A: WhatsApp Calling, Option B: Night Shift, or Option C: Cloned Voice?"*
     - Lead: *"Option A: real WhatsApp and phone calling."*
     - Agent logs `APPROVE` on `agenda-02` and dispatches build task to swarm queue.
* **Pass Criteria:**
  - End-to-end conversational turn latency < 600 ms.
  - No dropped turns or audio clipping.

---

### TC-04: Irreversible Human Checkpoint Safeguard
* **Objective:** Verify that high-impact destructive or release actions cannot execute via voice alone.
* **Procedure:**
  1. **Turn 3 (Irreversible Checkpoint):**
     - Agent: *"Item 3: Shall I make the repository public and submit the hackathon entry for 19:00 deadline?"*
     - Lead: *"Yes, approve submission, but hold execution until I confirm on my laptop."*
  2. Agent logs decision as `APPROVE` with human checkpoint requirement.
  3. State store transitions action `act-103` (`agenda-03`) to `BLOCKED_ON_CHECKPOINT`.
  4. Agent confirms: *"Designated as irreversible. Checkpoint held for desk confirmation."*
* **Pass Criteria:**
  - Action `act-103` remains unexecuted (`BLOCKED_ON_CHECKPOINT`).
  - Artifact `pending_url` points to `/dashboard#act-103`.
  - Voice agent does not perform the public release autonomously.

---

### TC-05: Scale Hackathon Swarm & Call Termination
* **Objective:** Verify participant network scaling and clean call teardown.
* **Procedure:**
  1. **Turn 4 (Network Scaling):**
     - Agent: *"Item 4: Should I scale the autonomous morning commute call to every other team at the hackathon?"*
     - Lead: *"Yes, offer it to all 42 teams!"*
     - Agent logs `APPROVE`, updates participant budget to 42 teams.
  2. **Termination:** Agent concludes: *"Captured. 42 teams onboarded. Knowledge graph updated. See you at your desk."*
  3. Call terminates with audio handoff chime; screen transitions to `screen-ended`.
* **Pass Criteria:**
  - Total call duration between 45 and 60 seconds.
  - `src/data/transcript.json` saved with full multi-turn dialog history.

---

### TC-06: Desktop Reveal — Before/After Knowledge Graph (`/dashboard`)
* **Objective:** Verify desktop laptop visualization and 1-click checkpoint confirmation.
* **Procedure:**
  1. Philipp sits at laptop and opens [`http://localhost:8000/dashboard`](http://localhost:8000/dashboard).
  2. **Toggle Before Graph:** Verify 85 overnight repository events rendered with open warning/error nodes (yellow/red).
  3. **Toggle After Graph:** Verify resolved nodes turn green, decision edges link to dispatched action cards (`src/data/dispatch/hack-bau1.md`).
  4. **Call Replay Card:** Verify audio player loads and synchronized transcript highlights matching turns.
  5. **1-Click Checkpoint Confirmation:**
     - Locate amber pulsing card: `[CHECKPOINT ACTION act-103: PUBLIC_RELEASE_AND_SUBMIT]`.
     - Inspect git commit preview.
     - Click `[1-Click Confirm Checkpoint]`.
* **Pass Criteria:**
  - Card status transitions from `BLOCKED_ON_CHECKPOINT` to `COMPLETED`.
  - Action node in knowledge graph updates from amber/blocked to green/resolved.
  - HTTP `POST /api/actions/{action_id}/confirm` returns `200 OK` with updated state.

---

### TC-07: Resilience & Outdoor Replay Fallback
* **Objective:** Ensure video recording can proceed flawlessly even if cellular connectivity drops outdoors.
* **Procedure:**
  1. In case of mobile network drops outdoor, trigger the pre-recorded event replay:
     ```bash
     curl -X POST http://localhost:8000/api/live/replay
     ```
  2. Verify that `/live` and `/dashboard` reflect the full demo sequence deterministically.
* **Pass Criteria:**
  - Demo visuals and graph transitions operate 100% reliably in replay mode.

---

## 3. Sign-off Matrix & Schedule

| Checkpoint | Time (CEST) | Responsible | Status Criteria | Sign-off |
|---|---|---|---|---|
| **P-REVIEW Automated Checks** | 15:20 | `hack-bau1` | `scripts/validate_demo.py` all green | [x] PASSED |
| **claude-03 E2E Integration** | 16:45 | `hack-chef` | Merged into `main`, unified app running | [ ] Pending |
| **17:15 Ray-Ban Walkthrough** | 17:15 - 17:35 | Philipp | Live call on glasses, desk reveal verified | [ ] Pending |
| **Feature Freeze** | 18:00 | All | No further code commits, documentation locked | [ ] Pending |
| **2-Minute Video Take** | 18:15 - 18:40 | Philipp | Loom / MP4 recording completed | [ ] Pending |
| **Final Submission** | 18:50 | Philipp | GitHub Repo public, Video link submitted | [ ] Pending |
