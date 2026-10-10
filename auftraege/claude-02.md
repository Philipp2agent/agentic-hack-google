Modell: Fable (sonst Opus)

# Auftrag claude-02: Architektur & Arbeitspakete fuer Morgen-Anruf-Agent (DawnDispatch)

## Ziel
Entwirf die vollstaendige technische Architektur fuer das Hackathon-Produkt **DawnDispatch (Morgen-Anruf-Agent)** und zerlege die Umsetzung in praezise, unabhaengige Arbeitspakete als `auftraege/gemini-NN.md` fuer die Gemini-Bauer-Agenten.

Grundlage sind:
- `IDEE.md`: Morning Commute Phone Call via Twilio + Gradium + Gemini 3.8 Flash, gefolgt vom Web-Dashboard ("Show me, don't tell me").
- `HACKATHON.md`: Partner-Technologien Google Gemini (Interactions API / OpenAI-compat) und Gradium (gradbot, STT/TTS). Alles in Englisch.
- `docs/SETUP.md`: Python-Laufzeit am VPS (`/home/buzzagent/hack/.venv`), Secrets in `secrets.env` (nie committen!), Twilio + cloudflared Tunnel.

## Vorgaben & Architektur-Umfang
Erstelle `docs/ARCHITEKTUR.md` mit folgenden Abschnitten:
1. **Systemuebersicht & Komponenten-Diagramm (ASCII oder Mermaid):**
   - Telephony / Voice Front Door (`gradbot` + Gradium STT/TTS + Twilio Webhook)
   - Core Agent (`gemini-3.8-flash` ueber OpenAI-compat/Google-API mit Tool-Calling)
   - State & Action Engine (Overnight Seed-Daten, Call-State, Executed Actions)
   - Web Dashboard (FastAPI + HTML/Tailwind)
2. **Datenmodelle & Schnittstellen (JSON-Schemas):**
   - `OvernightEvent`: ID, Titel, Dringlichkeit, Kontext, Vorgeschlagene Aktion.
   - `DecisionItem`: Agenda-Punkt, Optionen, benoetigter Checkpoint.
   - `ExecutedAction`: Status (PENDING, APPROVED, REJECTED, EXECUTED), Timestamp, Audit-Log, generierte Artefakte.
3. **Voice-Dialog & Tool-Calling Spezifikation:**
   - System-Prompt fuer Gradium/Gemini waehrend des Anrufs.
   - Definierte Werkzeuge: `record_decision(item_id, decision, notes)`, `request_human_checkpoint(item_id, prompt)`.
4. **Verzeichnis- & Dateistruktur:**
   - `src/` Layout (z. B. `src/backend/`, `src/voice/`, `src/dashboard/`, `src/data/`).

## Zu erstellende Arbeitspakete (auftraege/gemini-NN.md)
Schneide mindestens 3 unabhaengige, parallele Arbeitspakete mit je:
- **Ziel:** Was genau soll gebaut werden?
- **Dateien:** Welche Pfade werden neu angelegt oder geaendert?
- **Abnahmekriterium:** Wie wird die Funktion ueberprueft (inkl. ausfuehrbarem Test-Befehl)?
- **Zugewiesener Branch:** `agent/hack-bau1`, `agent/hack-bau2`, etc.

Empfohlene Aufteilung:
- `auftraege/gemini-01.md`: Data Store & Action Engine (Mock Overnight Events, State Machine, Action Execution Runners).
- `auftraege/gemini-02.md`: Voice Dialog Pipeline (`gradbot` Integration mit Gradium STT/TTS, Twilio Webhook Handler, Gemini Tool-Calling).
- `auftraege/gemini-03.md`: Web Dashboard ("Show me, don't tell me" UI mit Live Status, Transcript View, Action Execution Artifacts).

## Dateien
- `docs/ARCHITEKTUR.md` (neu)
- `auftraege/gemini-01.md` (neu)
- `auftraege/gemini-02.md` (neu)
- `auftraege/gemini-03.md` (neu)

## Abnahmekriterien
1. `docs/ARCHITEKTUR.md` ist vollstaendig, praezise und deckt das Zusammenspiel von gradbot, Twilio, Gemini 3.8 Flash und FastAPI ab.
2. Alle Arbeitspakete `auftraege/gemini-01.md` bis `gemini-03.md` sind vollstaendig definiert, disjunkt und enthalten pruefbare Abnahmekriterien.
3. Keine Secrets, keine Schluessel im Code oder in Beispielen.
