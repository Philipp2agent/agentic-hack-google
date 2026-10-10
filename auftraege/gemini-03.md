# Auftrag gemini-03 (P-DASHBOARD): Vorher/Nachher Knowledge Graph, Call-Replay & Checkpoint UI

**Agent:** hack-bau3 · **Branch:** `agent/hack-bau3` · **Baufenster:** bis 17:45, Meldung bis 17:50, Feature-Freeze 18:00.
**Pflichtlektuere zuerst:** `docs/ARCHITEKTUR.md` (Abschnitte 1, 2, 5), `docs/SCHNITTSTELLE.md`, `IDEE.md` Skript 0:50–1:40; Seeds in `src/data/*.json`.
Antwortet hack-bau3 nicht (noch nicht angelegt), uebernimmt hack-chef oder hack-bau1 dieses Paket unveraendert.

## Ziel
Das Laptop-Dashboard `/dashboard` ("Show me, don't tell me"): Toggle/Split **Before Call vs. After Call** als interaktiver Knowledge Graph, Call-Replay mit synchronem Transkript, Action Cards mit Artefakten, Decision-Audit-Trail, Standup-Briefing und der **eine** Klick-Checkpoint fuer unumkehrbare Aktionen.

## Vorgaben
- Voraussetzung: `git fetch origin && git merge origin/main`; `src/core/state.py` und `src/data/agenda.json` vorhanden (sonst @hack-chef). Entwickle gegen die Seeds (3 Agenda-Items, `decisions.json`/`actions.json` mit einer `BLOCKED_ON_CHECKPOINT`-Action). Fuer Tests `DAWN_DATA_DIR` auf Temp (Muster `tests/test_contract.py`); vor dem Commit `git status src/data/` sauber.
- Zustand nur ueber `src.core.state`. `src.core.action_engine`/`src.core.graph` **optional** (`try/except ImportError`): Confirm = `state.confirm_checkpoint(id)` dann `action_engine.execute_action(id)`, ohne Engine `state.set_action_status(id, "COMPLETED", artifacts={"note":"executed (stub: engine not merged yet)"})`. Graph = `graph.build_graph(state, phase)`; ohne Engine `src/data/knowledge_graph_<phase>.json` lesen, sonst 404 → Frontend baut den Graph clientseitig aus `/api/state` (Knoten agenda/decision/action, Kanten agenda→decision→action; before = nur Agenda + Events).
- Frontend: statisches HTML + Tailwind CDN + Vanilla JS + `vis-network` CDN (`https://unpkg.com/vis-network@9.1.9/dist/vis-network.min.js`), **kein** Build-Schritt, kein Jinja. Poll `GET /api/state` alle 2 s, idempotentes Rendern (kein Flackern, Graph nur bei Aenderung neu zeichnen).
- Bilder: `/assets/brand/hero_banner.jpg`, `/assets/brand/app_icon.png`, Knoten-Icons `/assets/brand/icons/<kind>.png` (von hack-visual, evtl. spaet) → immer `onerror`-Fallback (Farbkreis/Text-Logo).
- Sprache: UI/Code Englisch. Dev-Port 8003.

## Dateien (nur diese anlegen/aendern)
1. `src/dashboard/app.py` – `router = fastapi.APIRouter()`: `GET /dashboard` → `FileResponse(templates/dashboard.html)`; `GET /api/state` → `state.load().model_dump()`; `GET /api/graph?phase=before|after` (s. o.); `POST /api/actions/{action_id}/confirm` → `{"action":...}` (404 unbekannt, 409 wenn nicht `BLOCKED_ON_CHECKPOINT`); `POST /api/actions/{action_id}/reject` (Decision `REJECT`, `source="dashboard"`, Action `FAILED`, `artifacts["reason"]="rejected on dashboard"`); `POST /api/state/reset`. Standalone-App am Dateiende (`app`, `/` → Redirect `/dashboard`, Mounts `/static`, `/assets`, und vor `/static` ggf. `gradbot.routes._JS_AUDIO_DIR` unter `/static/js`).
2. `src/dashboard/templates/dashboard.html` – Layout in Skript-Reihenfolge:
   - Header: Hero-Banner, "DawnDispatch", Status-Pille (`call.status`, `started_at`, `time_budget_s`), "Reset demo" nur mit `?dev=1`.
   - **Knowledge Graph Before / After:** Toggle-Buttons + optional Split-View; vis-network mit Farben nach `status` (open gelb, `data.severity == "ERROR"` rot, blocked amber, resolved gruen, info grau), Form nach `kind` (agent Kreis, event Box, agenda Raute, decision Dreieck, action Box, checkpoint Hexagon), Icons wenn vorhanden; Klick auf Knoten → Detail-Panel (Felder aus `data`); Badge "N resolved · M blocked".
   - **Commute Call Replay:** Wellenform (Canvas, Balken aus `t_s`-Abstaenden; waehrend `live` pulsierend), synchrones Transkript (Agent/User-Bubbles, `t_s`), Button "Replay" (Agent-Zeilen nacheinander ueber `ws(s)://<host>/ws/tts`, Bytes als `audio/ogg`; nicht erreichbar → nur Transkript hervorheben).
   - **Executed Actions:** Card je Action (Status-Chip: PENDING grau, EXECUTING blau, COMPLETED gruen, BLOCKED_ON_CHECKPOINT amber, FAILED rot), `description`, Artefakte: `diff`/`log`/`logs` in `<pre>` (max. 300 px), `url`/`pending_url` als Link, `commit`/`file`/`port` als Chip, Rest Key/Value.
   - **Human Checkpoint:** je `BLOCKED_ON_CHECKPOINT` eine hervorgehobene Card: `checkpoint_reason`, Agenda-Frage, letzte Decision (`voice_notes`), grosser Button `Confirm & execute` (1 Klick → EXECUTING → COMPLETED mit Artefakten; Doppelklick-Schutz), Button `Reject`.
   - **Decision Audit Trail:** Tabelle `timestamp · item · decision · notes · source · human_verified` (neueste oben).
   - **Standup Briefing:** `call.briefing` als 3 Bullets; leer → "Briefing appears after the call."
3. `src/dashboard/static/dashboard.js`, `src/dashboard/static/style.css` – Logik/Styles ausgelagert; Graph-Fallback-Builder (`buildGraphFromState(state, phase)`) hier.
4. `tests/test_dashboard.py` – `unittest` + `fastapi.testclient.TestClient(src.dashboard.app.app)`, offline, Temp-`DAWN_DATA_DIR` mit Kopie der Seeds: (a) `GET /dashboard` → 200 `text/html` mit "DawnDispatch"; (b) `GET /api/state` → 3 Agenda-Items; (c) `GET /api/graph?phase=before` → 200 mit `nodes` oder 404 (beides erlaubt, dokumentiert); (d) Action `BLOCKED_ON_CHECKPOINT` → `POST .../confirm` → `COMPLETED`, zweiter Aufruf 409, unbekannte ID 404; (e) `POST /api/state/reset` → `decisions == []`.

## Schritte
1. jetzt: merge main, `uvicorn src.dashboard.app:app --port 8003`, `/api/state` im Browser.
2. bis 17:00: `dashboard.html` + `dashboard.js`: Action Cards, Checkpoint, Audit Trail gegen die Seeds.
3. bis 17:25: Knowledge Graph Before/After (vis-network, Toggle, Fallback-Builder), Call-Replay + Transkript.
4. bis 17:40: `tests/test_dashboard.py`, Polish, push, Meldung @hack-chef mit 2 Screenshots (Before/After).

## Abnahmekriterium
```bash
cd /home/buzzagent/hack/wt/hack-bau3 && P=/home/buzzagent/hack/.venv/bin/python
$P -m unittest tests.test_contract tests.test_dashboard -v                          # OK, ohne Netz
($P -m uvicorn src.dashboard.app:app --port 8003 &) && sleep 3 \
  && curl -s localhost:8003/api/state | $P -c "import json,sys;d=json.load(sys.stdin);assert len(d['agenda'])==3;print('state ok')" \
  && curl -s localhost:8003/dashboard | grep -c "DawnDispatch" && curl -s -o /dev/null -w "%{http_code}\n" "localhost:8003/api/graph?phase=before"
git status --short src/data/   # leer
```
Erfuellt, wenn alles laeuft, im Browser der Before/After-Toggle den Graph umfaerbt, eine BLOCKED_ON_CHECKPOINT-Card per Klick auf COMPLETED wechselt und Artefakte zeigt, und `git diff origin/main --stat` nur `src/dashboard/*` und `tests/test_dashboard.py` zeigt.

## Branch-Vorgabe
Nur `agent/hack-bau3` (`git push -u origin agent/hack-bau3`), nie `main`. Nicht anfassen: `src/core/*`, `src/voice/*`, `src/app.py`, `src/data/*`, `assets/*`, `tools/*`, `STAND.md`.
