# DawnDispatch: 2-Minute Video & Demo Script

> **Video Duration:** Exactly 2:00 (120 seconds)  
> **Target Audience:** Hackathon Jury, Google DeepMind & Gradium Evaluators  
> **Presenter:** Philipp (Lead Engineer / Founder)  
> **Hardware:** Smartphone, Meta Ray-Ban Smart Glasses (Bluetooth audio), Laptop  

---

## Storyboard Overview

| Timestamp | Scene | Location | Visual Focus | Key Audio / Dialog |
|---|---|---|---|---|
| **0:00 - 0:20** | **The Commute Walk & Call** | Outside on the sidewalk | Philipp walking with Meta Ray-Bans; phone rings hands-free | Incoming Call Chime; *"Good morning Philipp. How much time do you have?"* |
| **0:20 - 0:55** | **Rapid Quick-Fire Standup** | Walking towards office | Close-up on Ray-Bans + phone audio waveform | 4 Yes/No triage items; speed scales to 1.25x; irreversible item held |
| **0:55 - 1:40** | **The Desk Reveal: Before/After** | Office desk / Laptop | `/dashboard` Knowledge Graph toggle & 1-Click Checkpoint confirm | Split-view graph reveal; live checkpoint confirmation click |
| **1:40 - 2:00** | **Partner Tech & Conclusion** | Laptop + Camera to Philipp | Architecture diagram & partner tech logos | Summary of DeepMind Gemini 3.8 Flash, Gradium Voice, and Meta Ray-Bans |

---

## Second-by-Second Script

### 🎬 Scene 1: The Commute Walk & Hands-Free Incoming Call (0:00 - 0:20)
* **Camera Angle:** Tracking over-shoulder shot following Philipp walking outside in Zürich wearing Meta Ray-Ban smart glasses.
* **Audio Atmosphere:** Subtle ambient outdoor street sounds, suddenly interrupted by a distinctive phone ring chime.
* **Action:** Philipp reaches for his phone. The screen displays the realistic incoming call interface (`/call`):  
  **"Incoming Call: DawnDispatch Agent"** with active green Accept button.  
  Philipp taps the side touch-pad of his Meta Ray-Ban smart glasses. The screen shifts to active call with live audio waveforms.

* **Dialog (0:08 - 0:20):**
  * **DawnDispatch Agent (Gradium Voice, clear and natural):**  
    *"Good morning Philipp. Overnight your autonomous agents kept building DawnDispatch. I have four things for you. How much time do you have?"*
  * **Philipp (speaking naturally through Ray-Ban glasses mic):**  
    *"Morning! I have about 60 seconds walking down to the office. Keep it fast."*
  * **DawnDispatch Agent:**  
    *"Speed adjusted to 1.25x. Rapid fire starting now."*

---

### 🎬 Scene 2: Rapid Quick-Fire Triage (0:20 - 0:55)
* **Camera Angle:** Cut between close-up of Philipp's face/glasses and screen recording of the mobile phone showing live transcript turns.
* **Pacing:** Crisp, rapid turn-taking (average 7 seconds per item).

* **Turn 1 — Status Version 1 (0:20 - 0:28):**
  * **Agent:** *"Item 1: Version 1 baseline was built today — simulated web call on Ray-Bans, low-latency audio, before/after graph. Anything you want me to flag?"*
  * **Philipp:** *"No, Version 1 baseline looks solid. Let's proceed."*
  * **Agent:** *"Locked in."*

* **Turn 2 — Decision Version 2 Roadmap (0:28 - 0:38):**
  * **Agent:** *"Item 2: Which Version 2 feature should the autonomous build pipeline prioritize — Option A: WhatsApp Calling, Option B: Night Shift, or Option C: Cloned Voice?"*
  * **Philipp:** *"Option A: real WhatsApp and phone calling."*
  * **Agent:** *"Selected Option A. Dispatched to autonomous build queue."*

* **Turn 3 — Irreversible Human Checkpoint (0:38 - 0:47):**
  * **Agent:** *"Item 3: Shall I make the repository public and submit the hackathon entry for 19:00 deadline?"*
  * **Philipp:** *"Yes, approve submission, but hold execution until I confirm on my laptop."*
  * **Agent:** *"Designated as irreversible. Checkpoint held for desk confirmation."*

* **Turn 4 — Hackathon Scale & Close (0:47 - 0:55):**
  * **Agent:** *"Item 4: Should I scale the autonomous morning commute call to every other team at the hackathon?"*
  * **Philipp:** *"Yes, offer it to all 42 teams!"*
  * **Agent:** *"Captured. 42 teams onboarded. Knowledge graph updated. See you at your desk."*  
  *(Call ends with clean handoff chime).*

---

### 🎬 Scene 3: The Desk Reveal — Before/After Knowledge Graph (0:55 - 1:40)
* **Camera Angle:** Medium shot transitioning to a high-definition direct screen capture of Philipp's laptop screen running [`http://localhost:8000/dashboard`](http://localhost:8000/dashboard).
* **Action:** Philipp sits down at his desk, opens his laptop, and the camera zooms into the dashboard.

* **Narration / Voiceover by Philipp (0:55 - 1:15):**
  *"I just arrived at my desk. Instead of wading through 85 commits and endless pull requests, DawnDispatch reveals the state of my repository through an interactive Before/After Knowledge Graph."*

* **Visual Demonstration on Screen (1:00 - 1:25):**
  1. **Before Call View:**  
     Philipp toggles the **"Before Call"** view.  
     The screen displays an intricate network of 85 overnight repository events clustered around unresolved yellow warning nodes and red unreviewed code branches.
  2. **After Call View:**  
     Philipp toggles the **"After Call"** view.  
     In real time, the resolved nodes transition to crisp green. The decisions made during the 60-second walk are linked directly to generated action cards (`src/data/dispatch/hack-bau1.md`).
  3. **Call Audio & Synchronized Transcript:**  
     Philipp points to the audio replay card showing the 52-second recorded commute conversation with word-for-word transcript synchronization.

* **The Human Checkpoint Interaction (1:25 - 1:40):**
  * **Visual:** An amber pulsing card highlights:  
    `[CHECKPOINT ACTION act-103: PUBLIC_RELEASE_AND_SUBMIT]`  
    *Reason: Irreversible repository public release & hackathon submission requires 1-click confirmation.*
  * **Action:** Philipp reviews the git diff preview on the card and clicks the bold green button:  
    `[1-Click Confirm Checkpoint]`.
  * **Result:** The card immediately updates to `COMPLETED`, the node in the knowledge graph flashes green, and the official release tag `v1.0.0-hackathon` is committed.
  * **Philipp:** *"The human stays in the loop. The agent owns the code, but the human signs off on the irreversible."*

---

### 🎬 Scene 4: Partner Technology & Conclusion (1:40 - 2:00)
* **Camera Angle:** Picture-in-picture with architectural diagram on screen and Philipp addressing the camera directly.

* **Philipp (1:40 - 2:00):**
  *"To build DawnDispatch, we integrated three cutting-edge technologies:*
  * *First, **Google DeepMind Gemini 3.8 Flash** via the Interactions API — performing real-time rapid triage dialog and autonomous knowledge graph inference.*
  * *Second, **Gradium Voice AI** — delivering ultra-low latency speech-to-text and streaming speech with dynamic speed adaptation.*
  * *And third, **Meta Ray-Ban Smart Glasses** — turning audio into a seamless, hands-free interface for commuting developers.*
  
  *DawnDispatch proves that when autonomous agent swarms write code faster than humans can read logs, voice-first triage is how engineers will stay in control. Thank you!"*

---

## Production & Filming Checklist for Philipp

- [ ] **Hardware Setup:** Meta Ray-Ban glasses paired via Bluetooth to smartphone; phone microphone verified on mobile browser.
- [ ] **Screen Recording:** OBS or QuickTime recording laptop screen at 1080p60 on `/dashboard`.
- [ ] **Lighting:** Natural outdoor light for the 20-second walk; clean office desk light for the reveal.
- [ ] **Audio Monitoring:** Ensure Gradium voice playback routes to Ray-Ban open-ear speakers with clear microphone pickup.
- [ ] **Replay Fallback:** If cellular network has interference outdoors, `/api/live/replay` is pre-seeded with the exact demo event sequence.
