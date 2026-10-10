# Auftrag gemini-03: Web Dashboard & Checkpoint UI ("Show me, don't tell me")

**Agent:** hack-bau3 · **Branch:** `agent/hack-bau3` · **Baufenster:** 16:15–17:45, Meldung bis 17:50, Feature-Freeze 18:00.
**Pflichtlektuere zuerst:** `docs/ARCHITEKTUR.md` (Abschnitte 1, 2, 5), `IDEE.md` Demo-Skript 0:55–1:35; Referenz-Client `/home/buzzagent/hack/vendor/gradbot/demos/simple_chat/static/index.html` (WebSocket-/Audio-JS-Muster).

## Ziel
Baue das Laptop-Dashboard, das nach dem Anruf sofort das ausgefuehrte Ergebnis zeigt (Call-Replay mit Transkript, Action Cards mit Artefakten, Decision-Audit-Trail, Standup-Briefing) und den **einen** Klick-Checkpoint fuer unumkehrbare Aktionen anbietet – plus die mobile Start-Seite `/call`, von der Philipp mit Ray-Ban-Brille den Web-Voice-Call startet.

## Vorgaben
- Voraussetzung: `git fetch origin && git merge origin/main`; `src/core/state.py` und `src/data/state.example.json` muessen vorhanden sein (sonst @hack-chef). Du entwickelst **gegen das Fixture**: `python -m src.core.state --reset` liefert 3 Agenda-Items (eines irreversibel). Fuer Action-Cards legst du dir Testdaten per `state.add_action(...)` an (siehe `tests/test_contract.py`), bis gemini-01 gemerged ist.
- Zustand nur ueber `src.core.state`; `src.core.action_engine` optional importieren (`try/except ImportError`): Checkpoint-Endpunkt ruft `state.confirm_checkpoint(action_id)` und dann, falls vorhanden, `action_engine.execute_action(action_id)`; ohne Engine `state.set_action_status(action_id, "COMPLETED", artifacts=[Artifact(kind="text", label="Executed", content="stub: engine not merged yet")])`.
- Frontend: statisches HTML + Tailwind CDN + Vanilla JS, **kein** Jinja/Build-Schritt. Dashboard pollt `GET /api/state` alle 2 s und rendert idempotent (kein Flackern, kein Verlust von Scroll/Fokus).
- Sprache: UI/Code Englisch. Mobile-first fuer `/call`, Desktop fuer `/`.
- Bilder: Hero `/assets/hero_banner.jpg`, Icon `/assets/app_icon.png` (liefert hack-visual, evtl. erst spaet) → immer mit `onerror`-Fallback (Element ausblenden / Text-Logo).

## Dateien (nur diese anlegen/aendern)
1. `src/dashboard/app.py`
   - `router = fastapi.APIRouter()`: `GET /` → `FileResponse(templates/index.html)`; `GET /call` → `templates/call.html`; `GET /api/state` → `state.load().model_dump()`; `POST /api/actions/{action_id}/confirm` → `{"action": ...}` (404 bei unbekannter ID, 409 wenn nicht `BLOCKED_ON_CHECKPOINT`); `POST /api/state/reset` → `state.reset()`; `POST /api/actions/{action_id}/reject` (optional: Decision `REJECT`, `source="dashboard"`, Action `FAILED` mit Artefakt "rejected on dashboard").
   - Standalone-Dev-App am Dateiende: `app = FastAPI(); app.include_router(router); app.mount("/static", ...src/dashboard/static); app.mount("/assets", ...)`; zusaetzlich `try: import gradbot.routes; app.mount("/static/js", StaticFiles(directory=gradbot.routes._JS_AUDIO_DIR))` (vor `/static` mounten), damit `/call` auch standalone laedt.
2. `src/dashboard/templates/index.html` – Laptop-Dashboard, Reihenfolge wie Demo-Skript:
   - Header: Hero-Banner, Titel "DawnDispatch", Status-Pille (`call.status`, `started_at`), Button "Reset demo" (ruft `/api/state/reset`, nur sichtbar mit `?dev=1`).
   - **Commute Call Card:** Wellenform-Visualisierung (Canvas, animierte Balken aus den `t_s`-Abstaenden des Transkripts; waehrend `live` pulsierend), synchronisiertes Transkript (Agent/User-Bubbles, Zeit `t_s`), Button "Replay" (spielt Agent-Zeilen nacheinander ueber `/ws/tts`: `{"type":"speak","text"}` → Bytes als `audio/ogg` abspielen; wenn `/ws/tts` nicht erreichbar → Transkript nur durchscrollen/hervorheben).
   - **Executed Actions:** eine Card je `ActionExecution` (Status-Chip farbig: PENDING grau, EXECUTING blau, COMPLETED gruen, BLOCKED_ON_CHECKPOINT amber, FAILED rot), `description`, Artefakte: `diff`/`log` in `<pre>` (monospace, scrollbar, max. 300 px), `commit`/`link`/`file` als Links, `text` als Absatz.
   - **Human Checkpoint:** fuer jede Action in `BLOCKED_ON_CHECKPOINT` eine hervorgehobene Card mit `checkpoint_reason`, Agenda-Frage, letzter Decision (`voice_notes`) und grossem Button `Confirm & execute` (1 Klick → `POST .../confirm` → Card wechselt in EXECUTING → COMPLETED mit Artefakten; Doppelklick-Schutz). Optional Button `Reject`.
   - **Decision Audit Trail:** Tabelle `timestamp · item · decision · notes · source · human_verified` (neueste oben).
   - **Standup Briefing:** `call.briefing` als 3 Bullets; leer → "Briefing appears after the call."
   - Agenda-Uebersicht (3 Items mit Irreversible-Badge) seitlich oder oben.
3. `src/dashboard/templates/call.html` – mobile Start-Seite (Handy + Ray-Ban):
   - Ein grosser Start/Stop-Button (Tap erzeugt AudioContext → iOS-tauglich), Status ("Connecting", "Listening", "Call ended"), Hinweis "Connect your Ray-Ban glasses via Bluetooth first", Sprache aus `?lang=en|de`.
   - Audio-JS wie `simple_chat`: `<script src="/static/js/opus-encoder.js">`, `audio-processor.js`, `synced-audio-player.js`; `new SyncedAudioPlayer({basePath:'/static/js', sampleRate:24000, pcmOutput:false, echoCancellation:true, onEncodedAudio, onText, onEvent})`; WS zu `wss://<host>/ws/chat`; Start-Nachricht `{"type":"start","language":lang,"lead":"Philipp"}`; `{"type":"stop"}` beim Beenden; Screen-Wake-Lock (`navigator.wakeLock`, best effort).
   - Rendert DawnDispatch-Events: `agenda` → Item-Karten (grau), `decision_logged` → Karte gruen/rot/amber mit Entscheidung, `checkpoint_marked` → Badge "Waits for your click on the laptop", `call_ended` → Hinweis "Open your laptop dashboard".
   - Live-Transkript (klein, unten). Keine Voice-Auswahl noetig (Server waehlt `DAWN_VOICE_ID`).
4. `src/dashboard/static/dashboard.js`, `src/dashboard/static/call.js`, optional `src/dashboard/static/style.css` – JS aus den HTML-Dateien ausgelagert (Tailwind-Klassen im HTML).
5. `tests/test_dashboard.py` – `unittest` + `fastapi.testclient.TestClient(src.dashboard.app.app)`, offline, Temp-State via `DAWN_STATE_PATH`: (a) `GET /` und `GET /call` liefern 200 + `text/html` mit `DawnDispatch`; (b) `GET /api/state` liefert 3 Agenda-Items; (c) Action `BLOCKED_ON_CHECKPOINT` anlegen → `POST /api/actions/{id}/confirm` → Status `COMPLETED` (ohne Engine ueber den Stub), zweiter Aufruf → 409, unbekannte ID → 404; (d) `POST /api/state/reset` setzt `decisions` auf leer.

## Schritte (Reihenfolge)
1. 16:15 merge main, `python -m src.core.state --reset`, `uvicorn src.dashboard.app:app --port 8003` → `/api/state` im Browser.
2. 16:25–17:00 `index.html` + `dashboard.js` gegen Fixture + manuell angelegte Actions (eine BLOCKED_ON_CHECKPOINT mit Diff-Artefakt).
3. 17:00–17:25 `call.html` + `call.js` (Audio-JS laedt, Start-Button ruft `/ws/chat`; ohne gemini-02 endet der WS mit Fehler → Status "Voice server not available" sauber anzeigen).
4. 17:25–17:40 `tests/test_dashboard.py`, Polish (Statusfarben, Mobile-Layout 390 px breit).
5. 17:40 push + Meldung @hack-chef mit 2 Screenshots (Dashboard, /call).

## Abnahmekriterium
```bash
cd /home/buzzagent/hack/wt/hack-bau3 && P=/home/buzzagent/hack/.venv/bin/python
$P -m unittest tests.test_contract tests.test_dashboard -v                   # OK, ohne Netz
$P -m src.core.state --reset && ($P -m uvicorn src.dashboard.app:app --port 8003 &) && sleep 3 \
  && curl -s localhost:8003/api/state | $P -c "import json,sys;d=json.load(sys.stdin);assert len(d['agenda'])==3;print('agenda ok')" \
  && curl -s localhost:8003/ | grep -c DawnDispatch && curl -s localhost:8003/call | grep -c "ws/chat"
```
Erfuellt, wenn alle Befehle laufen, im Browser eine BLOCKED_ON_CHECKPOINT-Card per Klick auf COMPLETED wechselt und Artefakte zeigt, `/call` auf einem Handy (390 px) bedienbar ist und `git diff origin/main --stat` nur Dateien unter `src/dashboard/` und `tests/test_dashboard.py` zeigt.

## Branch-Vorgabe
Nur auf `agent/hack-bau3` arbeiten und pushen (`git push -u origin agent/hack-bau3`). Nie auf `main`. Nicht anfassen: `src/core/*`, `src/voice/*`, `src/app.py`, `src/data/*`, `assets/*`, `tools/*`, `STAND.md`.
