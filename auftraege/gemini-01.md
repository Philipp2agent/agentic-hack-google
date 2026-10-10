# Auftrag gemini-01: Data Models, Repo Event Aggregator & Action Engine

**Agent:** hack-bau1 · **Branch:** `agent/hack-bau1` · **Baufenster:** 16:15–17:45, Meldung bis 17:50, Feature-Freeze 18:00.
**Pflichtlektuere zuerst:** `docs/ARCHITEKTUR.md` (Abschnitte 2, 3 Interactions-API, 4, 6), `IDEE.md`.

## Ziel
Baue den Kern von DawnDispatch: den Repo-Event-Aggregator, der echte Ereignisse aus `Philipp2agent/agentic-hack-google` sammelt, und die Action Engine, die daraus mit Gemini 3.8 Flash (Interactions API) eine 3-Punkte-Agenda synthetisiert, Entscheidungen in Aktionen umsetzt (Reversibles sofort, Unumkehrbares als Checkpoint) und nach dem Anruf Beschluesse + Briefing extrahiert.

## Vorgaben
- `src/core/models.py` und `src/core/state.py` liegen bereits auf `main` (eingefrorener Vertrag). Du darfst Felder/Methoden **ergaenzen**, nie umbenennen oder entfernen. Alle Schreibzugriffe auf den Zustand nur ueber `src.core.state`.
- Voraussetzung: `git fetch origin && git merge origin/main`; danach muss `test -f src/core/models.py` wahr sein. Falls nicht: hack-chef hat claude-02 noch nicht gemerged → im Thread melden und warten.
- Schluessel nur aus der Umgebung (`GEMINI_API_KEY`); nie ausgeben, nie in Dateien. Tests laufen **ohne** Netz/Schluessel; Live-Aufrufe nur hinter `--live`/`--refresh`.
- Sprache: Code, Prompts, Strings Englisch. Nur Standardbibliothek + bereits installierte Pakete (`google-genai`, `pydantic`).
- Gemini sparsam: Agenda-Synthese = 1 Aufruf, Post-Call = 1 Aufruf. Keine Schleifen.

## Dateien (nur diese anlegen/aendern)
1. `src/core/repo_events.py` – `collect_events(repo_root: Path, since_hours: int = 24) -> list[OvernightEvent]`
   - Quellen: `git log --since` (Autor/Commit-Message → `agent_id` aus Praefix `feat(assets)`/`merge: ... von agent/<name>`/`claude`), `STAND.md`-Tabelle (Zeilen mit Status ≠ fertig → `board`), `assets/*` (Bilder → `asset`), `AGENTEN.md` (Agentenliste), optional GitHub PRs via `https://api.github.com/repos/Philipp2agent/agentic-hack-google/pulls?state=all` (urllib, Timeout 5 s, Fehler → ignorieren).
   - `severity` nach Heuristik (blockiert/wartet → high, merge → medium, sonst info/low); `proposed_action` kurz, Englisch.
   - CLI: `python -m src.core.repo_events --out src/data/overnight_events.json` (schreibt, druckt Anzahl).
2. `src/data/overnight_events.json` – committeter Seed aus dem echten Repo (≥ 8 Events).
3. `src/core/gemini_client.py` – `gemini_json(system: str, user: str, schema: dict, previous_interaction_id: str | None = None) -> tuple[dict, str | None]`
   - Primaer `client.interactions.create(...)` mit `response_format={"type":"text","mime_type":"application/json","schema":...}` (Snippet in ARCHITEKTUR 3); bei Fehler Fallback `client.models.generate_content(..., config={"response_mime_type":"application/json","response_schema":schema})`. Rueckgabe: geparstes JSON + `interaction.id` (oder None).
   - Ohne `GEMINI_API_KEY` → `RuntimeError("GEMINI_API_KEY not set")`.
4. `src/core/action_engine.py` – die vier Naht-Funktionen aus ARCHITEKTUR 2 **mit exakt diesen Namen und Signaturen**:
   - `synthesize_agenda(events, refresh=False) -> list[AgendaItem]`: ohne `refresh` und mit vorhandener `src/data/agenda.json` → Cache laden; sonst Gemini; max. 3 Items, genau 1 davon `is_irreversible` wenn ein unumkehrbarer Kandidat existiert; `is_irreversible == action_type in IRREVERSIBLE_ACTION_TYPES` erzwingen; `meta["agenda_interaction_id"]` setzen.
   - `on_decision(record) -> list[ActionExecution]`: APPROVE/AMEND → Action anlegen; reversibel → sofort `execute_action`; unumkehrbar → `status=BLOCKED_ON_CHECKPOINT`, `checkpoint_reason` gefuellt. REJECT/HOLD → keine Action, nur `NOTE`-Action `COMPLETED` mit Artefakt-Text. Idempotent pro `decision_id`.
   - `execute_action(action_id) -> ActionExecution`: `EXECUTING` → `COMPLETED|FAILED` mit echten Artefakten: `MERGE_BRANCH` → `git diff --stat main...origin/<branch>` + `git log --oneline -5` (kind=diff/commit; **kein** echter Merge, nur Vorschau); `DISPATCH_AGENT` → Datei `src/data/dispatch/<agent>.md` (kind=file); `RUN_TESTS` → `python -m unittest tests.test_contract` Ausgabe (kind=log); `UPDATE_BUDGET` → `meta["budget:<key>"]` (kind=text); `DELETE_FILES` (nur nach Checkpoint) → `git rm` + Commit auf neuem Branch `dawn/exec-<action_id>` (kind=commit, nie auf main pushen); `TAG_RELEASE`/`PUBLISH_ASSET` → simuliert mit Artefakt-Text `would run: ...`. Jeder Unterprozess mit Timeout 20 s, Fehler → `FAILED` + Log.
   - `process_post_call() -> CallRecord`: Items ohne `voice_tool`-Entscheidung aus dem Transkript extrahieren (Gemini, `source="post_call"`, danach `on_decision`), Briefing (3 Bullets, Englisch) schreiben via `state.end_call(briefing=...)`; ohne Transkript oder ohne Schluessel → Briefing deterministisch aus Entscheidungen bauen (kein Fehler).
   - CLI: `python -m src.core.action_engine --seed [--refresh]` (collect → synthesize → `state.reset()` + events/agenda einsetzen → `src/data/agenda.json` schreiben), `--execute <action_id>`, `--process-call`, `--decide <item_id> <APPROVE|REJECT|HOLD|AMEND> [notes]` (Simulation ohne Voice).
5. `src/data/agenda.json` – committete letzte Synthese (Cache/Fallback; Format: Liste von `AgendaItem`).
6. `tests/test_core.py` – `unittest`, offline: (a) `collect_events` auf dem Repo liefert ≥ 5 Events mit gueltigen Modellen, (b) `on_decision` fuer ein irreversibles Item erzeugt `BLOCKED_ON_CHECKPOINT`, fuer ein reversibles `COMPLETED` mit ≥ 1 Artefakt, (c) `execute_action` nach `state.confirm_checkpoint` setzt `COMPLETED` (fuer `DELETE_FILES` in einem temporaeren Klon oder mit Monkeypatch des git-Aufrufs), (d) `process_post_call` ohne Schluessel liefert 3 Briefing-Zeilen. Nutze `os.environ["DAWN_STATE_PATH"]` auf eine Temp-Datei wie in `tests/test_contract.py`.

## Schritte (Reihenfolge)
1. 16:15 merge main, `python -m unittest tests.test_contract` gruen.
2. 16:20–16:45 `repo_events.py` + Seed-JSON.
3. 16:45–17:25 `gemini_client.py` + `action_engine.py` (erst Offline-Pfade, dann 1× `--seed --refresh` live am VPS mit geladenem secrets.env).
4. 17:25–17:40 `tests/test_core.py`, `--decide`-Durchlauf fuer alle 3 Items.
5. 17:40 push + Meldung @hack-chef (3 Zeilen: gebaut, Dateien, Pruefbefehl).

## Abnahmekriterium
```bash
cd /home/buzzagent/hack/wt/hack-bau1 && P=/home/buzzagent/hack/.venv/bin/python
$P -m unittest tests.test_contract tests.test_core -v                 # alles OK, ohne Netz
$P -m src.core.repo_events --out /tmp/ev.json && $P -c "import json;assert len(json.load(open('/tmp/ev.json')))>=8"
set -a; . /home/buzzagent/hack/secrets.env; set +a
$P -m src.core.action_engine --seed --refresh && $P -m src.core.state --show   # agenda=3, 1 irreversible
$P -m src.core.action_engine --decide ag-02 APPROVE "keep v3" && $P -m src.core.state --show   # blocked_on_checkpoint=1
```
Erfuellt, wenn alle Befehle ohne Fehler laufen, `src/data/overnight_events.json` und `src/data/agenda.json` committet sind, keine Schluessel im Diff (`git diff origin/main --stat` zeigt nur die 6 Dateien oben + ggf. `models.py`/`state.py`-Ergaenzungen).

## Branch-Vorgabe
Nur auf `agent/hack-bau1` arbeiten und pushen (`git push -u origin agent/hack-bau1`). Nie auf `main`. Nicht anfassen: `src/voice/*`, `src/dashboard/*`, `src/app.py`, `assets/*`, `tools/*`, `STAND.md`, `README.md`.
