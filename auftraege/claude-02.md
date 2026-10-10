Modell: Fable (sonst Opus)

# Auftrag claude-02: Architektur, Schnittstellen & Parallele Arbeitspakete fuer DawnDispatch

## Ziel
Entwirf die vollstaendige technische Systemarchitektur fuer das Hackathon-Produkt **DawnDispatch (Autonomous Morning Commute Voice Dispatcher & Action Dashboard)** und erstelle vier praezise, unabhaengige und parallel umsetzbare Arbeitspakete als `auftraege/gemini-01.md` bis `auftraege/gemini-04.md` fuer die vier Gemini-Bauer-Agenten (`hack-bau1`, `hack-bau2`, `hack-bau3`, `hack-visual`) fuer das Baufenster **16:15–18:00 (CEST)**.

Grundlage sind:
- `IDEE.md`: Morning Commute Web-Voice-Call via Smartphone & Meta Ray-Ban (Bluetooth), Agenda-Triage ueber naechtliche Repo-Agenten-Ergebnisse, Web-Dashboard ("Show me, don't tell me") mit Klick-Checkpoint fuer Unumkehrbares.
- **Wichtigste Randbedingungen:**
  - **KEIN Twilio, KEIN WhatsApp!** Der Voice-Call laeuft direkt ueber eine mobile Web-Seite mit Web Audio / WebSocket auf das Handy, Audio-Aus-/Eingabe per Bluetooth ueber Meta-Ray-Ban-Brille.
  - **Basis-Code:** Die existierende gradbot-Demo `simple_chat` auf dem VPS (`/home/buzzagent/hack/vendor/gradbot/demos/simple_chat`) dient als Referenz und Fundament fuer FastAPI + WebSocket + Gradium.
  - **Demo-Daten & Kontext:** Genau dieses Hack-Team und sein Repo (`Philipp2agent/agentic-hack-google`) mit den aktiven Agenten (`hack-chef`, `hack-bau1`, `hack-bau2`, `hack-bau3`, `hack-visual`).
  - **Technologie-Stack:** Google Gemini 3.8 Flash (Interactions API / Reasoning / Tool-Calling), Gradium (gradbot, STT, TTS mit Custom Voice Design), FastAPI + HTML/Tailwind, alles in englischer Sprache fuer Code, Prompts und UI.
  - **Feature-Freeze ist 18:00 (CEST)**. Abgabe 19:00 (CEST).

---

## 1. Zu erstellende Architektur-Dokumentation: `docs/ARCHITEKTUR.md`
Erstelle `docs/ARCHITEKTUR.md` mit folgenden klaren Abschnitten:
1. **Systemuebersicht & Komponenten-Diagramm (ASCII / Mermaid):**
   - **Voice Front Door:** Mobile Web Browser -> WebSocket `/ws/chat` -> `gradbot` + Gradium STT/TTS (Custom Voice) -> Meta Ray-Ban Audio.
   - **Orchestration & Reasoning:** Gemini 3.8 Flash (Google Interactions API) fuer (a) Agenda-Synthese aus Repo-Events, (b) Real-Time Voice Dialog, (c) Post-Call Decision Extraction.
   - **Data Store & State Engine:** Overnight Swarm Events aus `Philipp2agent/agentic-hack-google`, Action Queue, Human Checkpoints.
   - **Laptop Web Dashboard:** FastAPI-Endpoints + HTML/Tailwind ("Show me, don't tell me", Live Audio Replay, Action Cards, One-Click Confirmation fuer unumkehrbare Aktionen).
2. **Datenmodelle & Schnittstellen (Pydantic / JSON Schemas):**
   - `OvernightEvent`: `id`, `source` (git commit/PR/agent log), `agent_id`, `title`, `details`, `severity`, `proposed_action`.
   - `AgendaItem`: `item_id`, `topic`, `question_for_lead`, `recommended_action`, `is_irreversible`.
   - `DecisionRecord`: `item_id`, `decision_type` (APPROVE / REJECT / HOLD / AMEND), `voice_notes`, `timestamp`, `human_verified`.
   - `ActionExecution`: `action_id`, `item_id`, `action_type`, `status` (PENDING, EXECUTING, COMPLETED, BLOCKED_ON_CHECKPOINT), `artifacts` (diffs, commit links, logs).
3. **Voice Dialog & Tool-Calling Spezifikation:**
   - Prompt-Design fuer den morgendlichen Anruf (knapp, agenda-getrieben, max. 90 Sekunden Dialog).
   - Gemini Tools: `log_decision(item_id, decision, notes)`, `mark_irreversible_checkpoint(item_id, reason)`.
4. **Verzeichnis- & Dateistruktur fuer das Repo:**
   - Klare Aufteilung unter `src/`:
     - `src/voice/` (gradbot Web-Socket Handler, Gradium Integration, Audio Streaming)
     - `src/core/` (Datenmodelle, State Engine, Gemini Interactions API Client, Repo Event Aggregator)
     - `src/dashboard/` (FastAPI Routes, HTML/Templates, Static Web Assets)
     - `src/data/` (Seed-Daten aus `agentic-hack-google`, persistenter JSON State)

---

## 2. Zu erstellende Arbeitspakete (`auftraege/gemini-01.md` bis `gemini-04.md`)

Schneide exakt 4 unabhaengige, parallele Pakete fuer die Bauzeit **16:15–18:00**:

### `auftraege/gemini-01.md`: Data Models, Repo Event Aggregator & Action Engine
- **Verantwortlicher Agent:** `hack-bau1`
- **Branch:** `agent/hack-bau1`
- **Umfang:**
  - Pydantic-Modelle (`src/core/models.py`)
  - Repo Event Aggregator & Seed Data aus `agentic-hack-google` (`src/core/repo_events.py`, `src/data/overnight_events.json`)
  - Action Engine & Post-Call Processor mit Gemini 3.8 Flash (`src/core/action_engine.py`)
  - Ausfuehrbarer Unit-/Integrations-Test.

### `auftraege/gemini-02.md`: Voice Dialog Pipeline & Web-Audio Backend
- **Verantwortlicher Agent:** `hack-bau2`
- **Branch:** `agent/hack-bau2`
- **Umfang:**
  - Adaption von `gradbot/demos/simple_chat` fuer DawnDispatch (`src/voice/server.py`, `src/voice/prompt.py`)
  - Gradium STT/TTS Konfiguration mit Custom Voice ID & deutscher/englischer Audiofuehrung
  - Tool-Calling Integration mit Gemini 3.8 Flash waehrend des Web-Voice-Calls zur Extraktion von Beschluessen in Echtzeit.
  - Test-Skript zur Simulation einer Voice-Session.

### `auftraege/gemini-03.md`: Web Dashboard & Checkpoint UI ("Show me, don't tell me")
- **Verantwortlicher Agent:** `hack-bau3`
- **Branch:** `agent/hack-bau3`
- **Umfang:**
  - FastAPI Web Dashboard (`src/dashboard/app.py`, `src/dashboard/templates/index.html`)
  - Live Action Cards, Decision Audit Trail, Audio Waveform & Transkript-Replay
  - Interaktives Checkpoint-Element fuer unumkehrbare Aktionen (1-Click Ausfuehrung)
  - Mobile-optimierte Start-Seite fuer den Web-Voice-Call (fuer das Handy mit Ray-Ban Verbindung).

### `auftraege/gemini-04.md`: Visual Identity, Hero Banners & Dashboard Assets
- **Verantwortlicher Agent:** `hack-visual`
- **Branch:** `agent/hack-visual`
- **Umfang:**
  - Erstellung der visuellen Assets mit `tools/bild.py` (Gemini Nano Banana):
    - DawnDispatch Hero Banner / Logo fuer Dashboard (`assets/hero_banner.jpg`)
    - Architektur- / Flow-Visualisierung fuer Pitch & Video (`assets/system_flow.jpg`)
    - Icon / Favicon fuer Web-Dashboard und Mobile App (`assets/app_icon.png`)
  - Einbindung der generierten Assets in `assets/` und Dokumentation in `docs/VISUALS.md`.

Jedes `auftraege/gemini-NN.md` MUSS zwingend enthalten:
1. **Ziel** (1-3 Saetze)
2. **Dateien** (exakte Pfade, die erstellt oder modifiziert werden)
3. **Abnahmekriterium** (inklusive ausfuehrbarem Test- bzw. Verifizierungsbefehl)
4. **Branch-Vorgabe**

---

## 3. Abnahmekriterien fuer claude-02
1. `docs/ARCHITEKTUR.md` ist vollstaendig, praezise und adressiert die Web-Voice-Loesung ohne Twilio.
2. Alle vier Pakete `auftraege/gemini-01.md`, `auftraege/gemini-02.md`, `auftraege/gemini-03.md` und `auftraege/gemini-04.md` sind vollstaendig angelegt, disjunkt und konfliktfrei fuer paralleles Arbeiten.
3. Keine API-Keys, Tokens oder Secrets im Code oder in der Dokumentation.
