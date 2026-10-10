Modell: Fable (sonst Opus)

# Auftrag claude-03: Lauffaehiges MVP Ende-zu-Ende Backend, Integration & Video-Tools

## Ziel
Baue das vollstaendige, lauffaehige DawnDispatch MVP Ende-zu-Ende als Python-Backend in `src/voice`, `src/dashboard` und `src/main` (und `src/app.py`):
1. **Voice-Backend (`src/voice`):**
   - Echter gradbot-Anruf mit Prompt-Me & Schnellfeuer-Modus ("Good morning Philipp. Swarm overnight triage is ready. How much time do you have?").
   - 3 Agenda-Punkte im Schnellfeuer abfragen, Entscheidungen aufnehmen via `src.core.state.add_decision` (APPROVE, REJECT, HOLD, AMEND).
   - Audio Replay / Stream Uebertragung ueber WebSocket `/ws/chat` mit Gradium / gradbot integration.
2. **Dashboard-Backend (`src/dashboard`):**
   - Endpunkte fuer Vorher-Nachher-Graph (`/api/graph?phase=before|after` oder `/api/graph/before`, `/api/graph/after`).
   - Checkpoint-Freigaben: 1-Klick-Confirmation fuer unumkehrbare Aktionen (`BLOCKED_ON_CHECKPOINT`) via `POST /api/actions/{action_id}/confirm`, setzt Status auf `COMPLETED` und synchronisiert den Graph auf `AFTER`.
   - Endpunkte fuer Transcript (`/api/transcript`) und Aktionen (`/api/actions`).
3. **Gemeinsamer Einstiegspunkt (`src/main.py` & `src/app.py`):**
   - `python -m src.main` bzw. `uvicorn src.main:app --port 8000` startet das Gesamtsystem in einem einzigen Prozess.
   - Routen `/call` (Mobile Call Screen) und `/dashboard` (Desktop Web Dashboard), `/` redirect auf `/dashboard`.
   - Bindet die statischen UI-Dateien der Bauer ein (`src/voice/static/` und `src/dashboard/static/`), ohne ihre HTML/CSS/JS-Dateien zu ueberschreiben.
4. **Video-Tools (`tools/video`):**
   - Video-Generierungsskripte fuer Google Veo und Omni (z.B. `veo_generate.py`, `omni_generate.py` oder einheitliches CLI `tools/video/generate.py`) zur Erstellung von Promo-/Demo-Videoclips mit klarem Prompt-Interface, API-Anbindung (google-genai / Vertex) und robustem Dry-Run-/Mock-Modus bei fehlenden Keys.

## Betroffene Dateien
- `src/voice/` (insb. `app.py`, `server.py`, `gradium_client.py`, `prompt.py`)
- `src/dashboard/` (insb. `app.py`)
- `src/main.py` und `src/app.py`
- `tools/video/` (`generate.py`, `README.md`)
- `tests/` (Testabdeckung fuer alle neuen Endpunkte und Integrationspfade)
- *Achtung:* Die statischen Dateien in `src/voice/static/` und `src/dashboard/static/` sowie die Daten-Seeds in `src/data/` gehoeren den Gemini-Bauern – nicht ueberschreiben!

## Abnahmekriterien
1. **Ende-zu-Ende Lauffaehigkeit:** `uvicorn src.main:app --host 0.0.0.0 --port 8000` startet fehlerfrei.
2. **Mobile Call Screen:** `GET /call` liefert die mobile Anrufoberflaeche aus `src/voice/static/call.html`. Der Anruf-Flow startet, fragt das Zeitbudget ab und fuehrt den Schnellfeuer-Dialog ueber die 3 Agenda-Items.
3. **Decisions & Graph Transition:** Nach dem Anruf sind Entscheidungen in `src.core.state` hinterlegt. `GET /api/graph?phase=after` liefert den aktualisierten Graph.
4. **1-Klick Checkpoint:** `POST /api/actions/{action_id}/confirm` bestaetigt eine blockierte unumkehrbare Aktion (`act-102`), setzt Status auf `COMPLETED` und laesst den Graphen als `resolved` rendern.
5. **Video-Tools:** `python -m tools.video.generate --help` und Ausfuehrung im Mock/Dry-run-Modus funktionieren und erzeugen strukturierte Video-Prompts/Assets fuer Veo und Omni.
6. **Tests:** `python -m unittest discover tests` laeuft gruen durch.
