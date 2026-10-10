# Video 2 Script (120 Sekunden / 2 Minuten): Hands-Free Repo Triage

> **Titel:** PromptMe / DawnDispatch — The Agent Prompts the Human  
> **Laufzeit:** Exakt 120 Sekunden (0:00 – 2:00)  
> **Drehtermin:** 18:30 CEST Sprint Video 2  
> **Hauptdarsteller:** Philipp (Tech Lead / Founder)  
> **Hardware:** Meta Ray-Ban Smart Glasses (Open-Ear Audio), Smartphone, Laptop (MacBook)  
> **Web-UIs:** Live-Ansicht (`/live`), Web-Call (`/call` bzw. `dawn/main.py`), Terminal (`setup.sh`, `start.sh`)  
> **Subline / Call-to-Action:** *"Try it on your own repo in 3 minutes."*

---

## Übersicht & Phasen-Storyboard

| Timecode | Phase | Szene & Location | Visueller Fokus | Kern-Audio / Dialog |
|---|---|---|---|---|
| **0:00 – 0:25** | **1. Gang & Ausgangslage** | Straße / Außenbereich Zürich | Verfolgerkamera; Philipp geht zügig mit Meta Ray-Ban Brille; Hände in den Taschen | Gehgeräusche, Straßengeräusche; kein Handy in der Hand; Klingelton im Brillen-Lautsprecher |
| **0:25 – 0:55** | **2. Eingehender Anruf & Triage** | Gehweg Richtung Büro | Nahaufnahme Ray-Bans + Smartphone-Waveform; Touch-Tap am Brillenbügel | 3 Quickfire-Entscheidungen (Roadmap V2, Checkpoint, Skalierung); Latenz <700ms |
| **0:55 – 1:40** | **3. Laptop-Live-Ansicht & Reveal** | Bürotisch / Schreibtisch | Laptop `/live` mit Nachher-Ansicht: *"Das hat das Gespräch gebracht"*; 1-Click Checkpoint | Split-Screen / Over-Shoulder: 3 Vorher->Nachher Karten + Bestätigungsklick |
| **1:40 – 2:00** | **4. Plug-and-Play Abschluss** | Studio / Schreibtisch | Screencast Terminal: `./setup.sh` -> `./start.sh` + Titelkarte | *"Try it on your own repo in 3 minutes"* + URL & Hackathon-Credits |

---

## Detailliertes 120s-Drehbuch mit Regieanweisungen

### Phase 1: Gang mit Meta Ray-Ban Brille (0:00 – 0:25)

* **0:00 – 0:10 | Die Ausgangslage**
  * **Kamera:** Dynamische Steadicam-Halbtotale, folgt Philipp von schräg vorne auf dem Gehweg in Zürich. Philipp trägt die Meta Ray-Ban Smart Glasses, geht mit schnellem Schritt zur Arbeit. Seine Hände sind frei, kein Smartphone vor den Augen.
  * **Atmosphäre:** Dezente urbane Hintergrundgeräusche (Schritte, entfernter Verkehr).
  * **Philipp (Off/On-Kamera, direkt ins Brillen-Mikrofon sprechend):**
    *"Every morning, dozens of autonomous agents keep building our repo overnight. Pull requests, commit diffs, failing checks. I don't want to stare at a phone screen while walking across Zürich."*
  * **Regie:** Blickkontakt zur Kamera im Gehen, souverän, fokussiert.

* **0:10 – 0:25 | Der eingehende Anruf**
  * **Kamera:** Schnitt auf Nahaufnahme von Philipps Profil: Meta Ray-Ban Brillenbügel mit diskreter LED/Touchfläche.
  * **Audio:** Ein prägnanter, futuristischer Rufton erklingt direkt aus den Open-Ear Lautsprechern der Ray-Ban Brille.
  * **Smartphone (Bild-in-Bild unten links):** Auf dem Smartphone in Philipps Jackentasche/Hand leuchtet der Anrufbildschirm: `Incoming Call: DawnDispatch (Reverse Triage)`.
  * **Aktion:** Philipp tippt mit dem Zeigefinger kurz an den rechten Bügel der Ray-Ban Brille. Der Klingelton stoppt sofort.
  * **Philipp:** *"Hey. What's the state of the repo?"*

---

### Phase 2: Eingehender Anruf & Hands-Free Triage (0:25 – 0:55)

* **0:25 – 0:33 | Begrüßung & Speed-Budgetierung**
  * **Kamera:** Dynamischer Wechsel zwischen Nahaufnahme Philipp (Gehbewegung) und Telefondisplay mit Live-Transkription.
  * **Agent (Gradium Realtime Voice, extrem klar und ohne Roboter-Vibe, <700ms Latenz):**
    *"Good morning Philipp! Overnight your swarm merged PR #4 and deployed the live dashboard. You have three open threads. How much time do you have?"*
  * **Philipp:** *"About 40 seconds while walking to my desk. Keep it tight."*
  * **Agent:** *"Got it. Speed set to 1.25x. Three rapid-fire questions."*

* **0:33 – 0:40 | Triage Turn 1: Roadmap Version 2**
  * **Agent:** *"Item 1: Roadmap decision for Version 2. Option A: Real WhatsApp and phone calling, or Option B: Autonomous Night Shift?"*
  * **Philipp:** *"Option A. Real WhatsApp calling."*
  * **Agent:** *"Locked in. Dispatched to hack-bau1."*

* **0:40 – 0:48 | Triage Turn 2: Irreversibler Checkpoint (Sicherheitsanker)**
  * **Agent:** *"Item 2: Checkpoint. PR #4 is green. Make repository public and submit hackathon entry?"*
  * **Philipp:** *"Approve submission, but hold execution until I confirm on my laptop."*
  * **Agent:** *"Holding for laptop one-click confirmation. Marked blocked on checkpoint."*

* **0:48 – 0:55 | Triage Turn 3: Skalierung & Call Wrap-Up**
  * **Agent:** *"Item 3: Hackathon network expansion. Scale the morning dispatch queue to all 42 teams?"*
  * **Philipp:** *"Yes. Scale it up."*
  * **Agent:** *"Done. All decisions logged. It's all waiting on your laptop when you sit down. Have a good walk!"*
  * **Audio:** Leiser Chime beim Auflegen. Philipp lächelt kurz in die Kamera.

---

### Phase 3: Laptop-Live-Ansicht `/live` & Nachher-Ansicht (0:55 – 1:40)

* **0:55 – 1:05 | Ankunft am Schreibtisch & Laptop Reveal**
  * **Kamera:** Weicher Schnitt. Philipp betritt das Büro, setzt sich an seinen Schreibtisch und klappt das MacBook auf.
  * **Kamera-Perspektive:** Over-Shoulder-Einstellung direkt auf den 16-Zoll Bildschirm mit dem Browserfenster auf `localhost:8000/live` (bzw. Cloudflared HTTPS-Tunnel).
  * **Philipp:** *"Fifty seconds later, I arrive at my desk. Let's see what the conversation actually accomplished."*

* **1:05 – 1:25 | Die Nachher-Ansicht: "Das hat das Gespräch gebracht"**
  * **Kamera:** Vollbild-Screencast der `/live` Ansicht mit Bild-in-Bild von Philipp am Laptop.
  * **Visueller Ablauf im Web-UI:**
    * Der Live-Graphenbereich blendet weich ab, das Zentrum fokussiert die Nachher-Karte:
      **Header:** `Das hat das Gespräch gebracht`
      **Subline:** `52s Fußweg · 3 Entscheidungen getroffen · Version 2 steht`
    * **Karte 1 (Roadmap V2):**
      `[VORHER] 3 unentschiedene Optionen (A/B/C)` &rarr; `[NACHHER] Option A gewählt: Real WhatsApp calling dispatched to hack-bau1`
    * **Karte 2 (Release Checkpoint):**
      `[VORHER] Blockierter Checkpoint (Make repo public)` &rarr; `[NACHHER] Freigegeben durch Voice, wartet auf 1-Klick-Bestätigung`
    * **Karte 3 (Hackathon Skalierung):**
      `[VORHER] Team-Status isoliert` &rarr; `[NACHHER] Dispatch-Netzwerk auf alle 42 Teams skaliert`

* **1:25 – 1:40 | Der 1-Klick-Checkpoint & Abschluss am Laptop**
  * **Kamera:** Nahaufnahme auf die Maushand und den Screen.
  * **Aktion:** Philipp bewegt den Cursor auf den leuchtenden Button: `[Confirm Submission & Deploy]`.
  * **Klick:** Ein Klick &mdash; grüner Haken erscheint sofort (`Status: SUBMITTED & LIVE`).
  * **Philipp:** *"Irreversible actions never deploy without human eyes. One click on the laptop, and the overnight work is live."*

---

### Phase 4: Abschluss: "Try it on your own repo in 3 minutes" (1:40 – 2:00)

* **1:40 – 1:52 | Plug-and-Play Demo im Terminal**
  * **Kamera:** Split-Screen: Links Philipp im Studio/Büro frontal zur Kamera, rechts gestochen scharfes Terminal.
  * **Philipp:** *"The best part? You don't need our project. You can run this on YOUR own codebase right now."*
  * **Terminal-Ablauf (Replay im Zeitraffer):**
    ```bash
    git clone https://github.com/Philipp2agent/agentic-hack-google.git
    cd agentic-hack-google
    ./setup.sh    # Fragt nach Ziel-Repo & API-Keys
    ./start.sh    # Startet Voice-Server & Live-Ansicht
    ```
  * **Text-Callout im Screencast:** *"Point it at any repo &rarr; Gemini synthesizes the briefing &rarr; Gradium calls your phone."*

* **1:52 – 2:00 | Titelkarte & Abspann**
  * **Visuell:** Großformatige Titelkarte mit minimalistischem, futuristischem Design:
    * **Logo & Name:** `PromptMe / DawnDispatch`
    * **Subline:** *"Try it on your own repo in 3 minutes."*
    * **GitHub-Link:** `github.com/Philipp2agent/agentic-hack-google`
    * **Footer:** `Built in one afternoon by 8 Gemini agents + Claude`
  * **Philipp (Off-Stimme):** *"Clone it, grab your keys, and let your agents prompt you on your walk to work. Link in the description."*
  * **Fade to Black bei genau 02:00.**

---

## Technische Regieanweisungen & Checkliste für den Dreh (18:30)

1. **Meta Ray-Ban Smart Glasses:**
   * Vorher per Bluetooth mit dem Smartphone koppeln.
   * Lautstärke auf 85% für saubere Abnahme am Brillenbügel-Mikrofon.
2. **Audio-Routing:**
   * Handymikrofon und Brillenmikrofon separat pegeln.
   * Gradium TTS Voice-Latenz auf <700ms voreinstellen (`dawn/main.py`).
3. **Laptop & Live-UI:**
   * `/live` im Browser im Vollbildmodus (1080p oder 4K Skalierung).
   * Nachher-Ansicht mit `brief_ready` Event vorbereiten (per WebSocket oder `tools/live_demo_events.py`).
4. **Terminal Screencast:**
   * Sauberes Terminalfenster mit hoher Schriftgröße (20pt+, Nerd Font) für die Befehle `./setup.sh` und `./start.sh`.
