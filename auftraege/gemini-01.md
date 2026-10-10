# Auftrag gemini-01 (P-CORE): Repo Event Aggregator, Agenda & Knowledge Graph, Action Engine

**Agent:** hack-bau1 · **Branch:** `agent/hack-bau1` · **Baufenster:** bis 17:45, Meldung bis 17:50, Feature-Freeze 18:00.
**Pflichtlektuere zuerst:** `docs/ARCHITEKTUR.md` (Abschnitte 2, 3 Interactions-API, 4, 6), `docs/SCHNITTSTELLE.md`, `IDEE.md`.
Du arbeitest bereits an P-CORE. Dieses Paket praezisiert Dateinamen, Funktionssignaturen und Abnahme; was du schon hast, behaelst du und gleichst nur die Namen an.

## Ziel
Der Kern von DawnDispatch: echte Repo-Ereignisse aus `Philipp2agent/agentic-hack-google` sammeln, daraus mit Gemini 3.8 Flash (Interactions API) eine 3-Punkte-Agenda und den Knowledge Graph "before" bauen, Entscheidungen in Aktionen umsetzen (Reversibles sofort, Unumkehrbares als Checkpoint) und nach dem Anruf Beschluesse, Graph "after" und ein 3-Zeilen-Briefing erzeugen.

## Vorgaben
- `src/core/models.py` und `src/core/state.py` liegen auf `main` (claude-02, formalisieren SCHNITTSTELLE.md; die Seeds validieren unveraendert). Du darfst **ergaenzen**, nie umbenennen/entfernen. Schreibzugriffe nur ueber `src.core.state` (`set_inputs`, `add_decision`, `add_action`, `set_action_status`, `set_meta`, `end_call`).
- Voraussetzung: `git fetch origin && git merge origin/main`; `test -f src/core/state.py` muss wahr sein (sonst @hack-chef).
- Schluessel nur aus der Umgebung (`GEMINI_API_KEY`); nie ausgeben. Tests laufen **ohne** Netz/Schluessel und mit `DAWN_DATA_DIR` auf Temp (Muster `tests/test_contract.py`). Live-Aufrufe nur hinter `--refresh`/`--live`; Gemini sparsam (Agenda 1 Aufruf, Graph-Labels 0–1, Post-Call 1).
- Sprache: Code, Prompts, Strings Englisch. Nur `google-genai`, `pydantic`, Standardbibliothek.

## Dateien (nur diese anlegen/aendern)
1. `src/core/repo_events.py` – `collect_events(repo_root: Path, since_hours: int = 24) -> list[OvernightEvent]`: Quellen `git log --since` (Agent aus Commit-Praefix/Branch: `merge: ... von agent/<name>`, `feat(assets)` → hack-visual, `claude` → claude-cloud), `git branch -r` (offene `agent/*`-Branches mit Commits vor `main` → WARNING + `proposed_action` "merge?"), `STAND.md`-Tabelle (Status ≠ fertig → `source="STAND.md"`), `assets/**` (Bilder), optional GitHub PRs via `https://api.github.com/repos/Philipp2agent/agentic-hack-google/pulls?state=all` (urllib, Timeout 5 s, Fehler ignorieren). `severity` INFO/WARNING/ERROR, `ref` maschinenlesbar. CLI `python -m src.core.repo_events --out src/data/overnight_events.json`.
2. `src/data/overnight_events.json` – echter Seed (≥ 8 Events), ersetzt hack-chefs Platzhalter.
3. `src/core/gemini_client.py` – `gemini_json(system, user, schema, previous_interaction_id=None) -> tuple[dict, str | None]`: primaer `client.interactions.create(... response_format={"type":"text","mime_type":"application/json","schema":...}, response_mime_type="application/json")`, bei Fehler Fallback `client.models.generate_content(..., config={"response_mime_type":"application/json","response_schema":schema})`. Ohne `GEMINI_API_KEY` → `RuntimeError`.
4. `src/core/action_engine.py` – **exakt diese Signaturen** (Naehte fuer bau2/bau3):
   - `synthesize_agenda(events, refresh=False) -> list[AgendaItem]`: ohne `refresh` Cache `src/data/agenda.json`; sonst Gemini; max. 3 Items, genau 1 `is_irreversible` wenn ein Kandidat existiert; `item_id` = `agenda-01..03`, `priority` 1..3, `event_ids` gesetzt; `state.set_inputs(agenda=...)`, `meta["agenda_interaction_id"]`.
   - `on_decision(record) -> list[ActionExecution]`: APPROVE/AMEND → Action (`action_type` aus Item); Item reversibel → sofort `execute_action`; Item `is_irreversible` → `BLOCKED_ON_CHECKPOINT` mit `checkpoint_reason` und `artifacts["pending_url"]="/dashboard#<action_id>"`. REJECT/HOLD → `NOTE`-Action `COMPLETED` mit `artifacts["note"]`. Idempotent je `decision_id` (zweiter Aufruf erzeugt nichts).
   - `execute_action(action_id) -> ActionExecution`: `EXECUTING` → `COMPLETED|FAILED`, echte Artefakte: `MERGE_BRANCH` → `artifacts["diff"] = git diff --stat main...origin/<branch>`, `["log"] = git log --oneline -5` (Vorschau, **kein** Merge); `DISPATCH_AGENT` → `src/data/dispatch/<agent>.md` (`["file"]`); `RUN_TESTS` → Ausgabe von `python -m unittest tests.test_contract` (`["log"]`); `UPDATE_BUDGET` → `meta["budget:<key>"]` (`["note"]`); `DELETE_FILES` (nur nach Checkpoint) → `git rm` + Commit auf neuem Branch `dawn/exec-<action_id>` (`["commit"]`, nie main); `DEPLOY`/`TAG_RELEASE`/`PUBLISH_ASSET` → simuliert, `["log"]="would run: ..."`; unbekannter Typ → `COMPLETED` mit `["note"]`. Unterprozesse Timeout 20 s, Fehler → `FAILED` + `["reason"]`.
   - `process_post_call() -> CallRecord`: Items ohne `voice_tool`-Decision aus `call.transcript` extrahieren (Gemini, `source="post_call"`, dann `on_decision`), Briefing 3 Bullets Englisch → `state.end_call(briefing=...)`; ohne Transkript/Schluessel deterministisch aus den Decisions (kein Fehler). Danach `graph.build_graph(state,"after")` nach `src/data/knowledge_graph_after.json`.
   - CLI: `python -m src.core.action_engine --seed [--refresh]` (collect → synthesize → `state.reset()` → `knowledge_graph_before.json`), `--decide <item_id> <APPROVE|REJECT|HOLD|AMEND> [notes]`, `--execute <action_id>`, `--process-call`.
5. `src/core/graph.py` – `build_graph(state, phase) -> KnowledgeGraph` deterministisch nach ARCHITEKTUR 2 (Knoten agent/event/agenda/decision/action/checkpoint, Status open/blocked/resolved/info); CLI `python -m src.core.graph --phase before|after --out src/data/knowledge_graph_<phase>.json`. Optional: Gemini-Kantenlabels (max. 1 Aufruf, hinter `--refresh`).
6. `src/data/agenda.json`, `src/data/knowledge_graph_before.json`, `src/data/knowledge_graph_after.json` – committete Ergebnisse (Cache/Fallback fuer Dashboard-Dev).
7. `tests/test_core.py` – `unittest`, offline, Temp-`DAWN_DATA_DIR`: (a) `collect_events` liefert ≥ 5 gueltige Events; (b) `on_decision` fuer ein irreversibles Item → `BLOCKED_ON_CHECKPOINT`, fuer ein reversibles → `COMPLETED` mit ≥ 1 Artefakt-Schluessel; (c) nach `state.confirm_checkpoint` setzt `execute_action` `COMPLETED` (git-Aufruf gemockt oder Temp-Klon); (d) `process_post_call` ohne Schluessel → 3 Briefing-Zeilen; (e) `build_graph(...,"after")` hat fuer jede Decision einen Knoten und `agenda→decision`-Kante.

## Schritte
1. jetzt: merge main, `python -m unittest tests.test_contract` gruen, Namen angleichen.
2. bis 16:55: `repo_events.py` + echter Seed.
3. bis 17:25: `gemini_client.py`, `action_engine.py`, `graph.py`; einmal `--seed --refresh` live am VPS.
4. bis 17:40: `tests/test_core.py`, `--decide`-Durchlauf fuer alle 3 Items, push, Meldung @hack-chef.

## Abnahmekriterium
```bash
cd /home/buzzagent/hack/wt/hack-bau1 && P=/home/buzzagent/hack/.venv/bin/python
$P -m unittest tests.test_contract tests.test_core -v                              # OK, ohne Netz
set -a; . /home/buzzagent/hack/secrets.env; set +a
$P -m src.core.action_engine --seed --refresh && $P -m src.core.state --show       # agenda=3 decisions=0
$P -m src.core.action_engine --decide agenda-02 APPROVE "yes" && $P -m src.core.state --show   # blocked_on_checkpoint=1
$P -m src.core.graph --phase after --out /tmp/g.json && $P -c "import json;g=json.load(open('/tmp/g.json'));assert g['nodes'] and g['edges'];print('graph ok')"
git status --short src/data/   # nur beabsichtigte Seeds geaendert
```
Erfuellt, wenn alles ohne Fehler laeuft, die Seeds echte Repo-Daten enthalten, keine Schluessel im Diff und `git diff origin/main --stat` nur die Dateien oben (+ ggf. `models.py`/`state.py`-Ergaenzungen) zeigt.

## Branch-Vorgabe
Nur `agent/hack-bau1` (`git push -u origin agent/hack-bau1`), nie `main`. Nicht anfassen: `src/voice/*`, `src/dashboard/*`, `src/app.py`, `assets/*`, `tools/*`, `STAND.md`, `README.md`.
