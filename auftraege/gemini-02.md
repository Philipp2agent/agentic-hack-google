# Auftrag gemini-02: Voice Dialog Pipeline & Web-Audio Backend

**Agent:** hack-bau2 · **Branch:** `agent/hack-bau2` · **Baufenster:** 16:15–17:45, Meldung bis 17:50, Feature-Freeze 18:00.
**Pflichtlektuere zuerst:** `docs/ARCHITEKTUR.md` (Abschnitte 0, 3, 5, 7), `IDEE.md` Demo-Skript; Referenzcode `/home/buzzagent/hack/vendor/gradbot/demos/simple_chat/main.py`, `.../demos/hotel/main.py` (Tool-Calling-Muster), `.../demos/npc_3d_game/main.py` (One-Shot-TTS), `.../demos/voice_design/voice_generator.py` (Voice Design REST).

## Ziel
Baue den Web-Voice-Call von DawnDispatch: ein FastAPI-Router mit `/ws/chat` auf Basis von `gradbot.websocket.handle_session`, der die Agenda aus dem State spricht (Gradium TTS, Custom Voice), Philipps Antworten per Gradium STT versteht und ueber Gemini-Tool-Calls (`log_decision`, `mark_irreversible_checkpoint`) Beschluesse in Echtzeit in den State schreibt. Kein Twilio, kein WhatsApp: Audio kommt aus dem Handy-Browser (Ray-Ban per Bluetooth).

## Vorgaben
- Voraussetzung: `git fetch origin && git merge origin/main`; `src/core/models.py`, `src/core/state.py`, `src/data/state.example.json` muessen vorhanden sein (sonst @hack-chef).
- Zustand nur ueber `src.core.state` (`load`, `add_decision`, `start_call`, `append_turn`, `end_call`, `update`). `src/core/action_engine` ist **optional** importieren (`try/except ImportError`), Naht-Funktionen `on_decision(record)` und `process_post_call()` in `asyncio.to_thread` aufrufen, wenn vorhanden.
- gradbot-Konfiguration ueber `gradbot.config.from_env()` (liest `LLM_MODEL`, `LLM_BASE_URL`, `LLM_API_KEY`, `GRADIUM_API_KEY`). Keine Schluessel in Dateien, nie loggen.
- Gemini 3.x ueber OpenAI-compat: genau **ein** Tool-Call pro Turn, kurze Tool-Ergebnisse (ARCHITEKTUR 7). Tritt HTTP 400 `thought_signature` auf: `llm_extra_config=json.dumps({"reasoning_effort":"low"})` versuchen, sonst `LLM_MODEL=gemini-2.5-flash` dokumentieren.
- Sprache: Code/Prompts Englisch. Call-Sprache `en` (Default) oder `de` ueber `start.language` bzw. `DAWN_LANGUAGE`; Prompt bleibt Englisch mit "Speak {language_name}".
- Die Audio-JS-Bundles liegen unter `/static/js/` (mountet `src/app.py`); in deiner Standalone-App mountest du sie selbst ueber `gradbot.routes.setup(app, config=cfg, static_dir=..., with_voices=True)`.

## Dateien (nur diese anlegen/aendern)
1. `src/voice/prompt.py` – `build_instructions(agenda: list[AgendaItem], lead: str = "Philipp", language: str = "en") -> str` exakt nach ARCHITEKTUR 3 (Begruessung, ein Item pro Turn, max. 2 Saetze, Tool-Regeln, Irreversibel-Satz, Schlusssatz, < 90 s); `TOOLS: list[gradbot.ToolDef]` (`log_decision`, `mark_irreversible_checkpoint`), `LANGUAGE_NAMES = {"en":"English","de":"German"}`.
2. `src/voice/server.py`
   - `router = fastapi.APIRouter()` mit `@router.websocket("/ws/chat")`, `@router.websocket("/ws/tts")` (One-Shot wie `npc_3d_game`: `{"type":"speak","text":...}` → `clients = await gradbot.create_clients(**cfg.client_kwargs)` einmal cachen → `await clients.tts_synthesize(text, voice_id=..., rewrite_rules=gradbot.Lang.En.rewrite_rules)` → Audio-Bytes je Chunk + `{"type":"done"}`), `@router.get("/api/voices")`, `@router.get("/api/audio-config")`.
   - `on_start(msg)`: `lang = msg.get("language") or os.environ.get("DAWN_LANGUAGE","en")`, `voice_id = msg.get("voice_id") or os.environ.get("DAWN_VOICE_ID") or DEFAULT_VOICE_ID`, Agenda = `state.load().agenda` (sortiert nach `priority`), `state.start_call(lang, voice_id)`, Client-Event `{"type":"agenda","items":[...]}` senden, `SessionConfig(..., assistant_speaks_first=True, silence_timeout_s=6.0, tools=TOOLS, **cfg.session_kwargs)`.
   - `on_tool_call(handle, input_handle, websocket)`: Verhalten je Tool exakt nach ARCHITEKTUR 3 (Validierung `item_id`, `DecisionRecord(source="voice_tool")`, `state.add_decision`, Naht `on_decision`, `handle.send_json({...,"next_item_id":...})`, Client-Events `decision_logged` / `checkpoint_marked`). Unbekanntes Tool → `handle.send_error`.
   - Transkript-Persistenz ueber `TranscriptTap`-Proxy um das WebSocket (`__getattr__` delegiert; `send_json` faengt `user_text`/`agent_text` ab → `state.append_turn(TranscriptTurn(...))`).
   - Nach `handle_session`: `state.end_call()`, Client-Event `call_ended` (best effort), Naht `process_post_call` in `asyncio.to_thread`.
   - Standalone-Dev-App am Dateiende: `app = fastapi.FastAPI(); app.include_router(router); gradbot.routes.setup(app, config=cfg, static_dir=Path(__file__).parent/"static", with_voices=True)`.
3. `src/voice/static/index.html` – Kopie von `simple_chat/static/index.html`, minimal angepasst: Start-Nachricht `{"type":"start","language":"en","lead":"Philipp"}`, Agenda-/Decision-Events in einer Liste anzeigen. Nur Dev-Testseite; die Demo-Seite `/call` baut hack-bau3.
4. `src/voice/voice_design.py` – CLI `python -m src.voice.voice_design "warm, calm, energetic morning dispatcher, mid-30s, clear diction" --name Dawn --language en`: `POST {GRADIUM_BASE_URL}/voice-generator/generate` (`prompt`, `language`, `n_samples=1`, `json_config={"cfg_scale":...}`) → `embedding_id` → bereit pollen → `POST /voices/from-embedding` (`voxium_embedding_id`, `name`, `description`) → druckt `DAWN_VOICE_ID=<uid>` (Muster: `voice_generator.py` im vendor-Ordner; Header `x-api-key`). Ohne Schluessel → klare Fehlermeldung. Fallback im Server: Katalogstimme (`DEFAULT_VOICE_ID = "cLONiZ4hQ8VpQ4Sz"` Skyler oder eine englische Stimme aus `/api/voices`).
5. `src/voice/simulate_call.py` – `python -m src.voice.simulate_call` (offline): `state.reset()`, dann die Tool-Logik mit einem `FakeHandle` (sammelt `send_json`/`send_error`) und einem `FakeWebSocket` ueber ein Skript treiben: `log_decision(ag-01, APPROVE)`, `log_decision(ag-02, APPROVE, "keep v3")`, `mark_irreversible_checkpoint(ag-02, ...)`, `log_decision(ag-03, AMEND, "30 instead of 40")`; anschliessend `end_call` und Zusammenfassung drucken (`python -m src.core.state --show` → decisions=3). `--live`: oeffnet `ws://localhost:8000/ws/chat`, sendet `start`, wartet max. 20 s auf das erste `agent_text`, druckt es, sendet `stop` (Smoke-Test der Gradium/Gemini-Strecke ohne Mikro; braucht laufenden Server + secrets.env).
6. `tests/test_voice.py` – `unittest`, offline: (a) `build_instructions` enthaelt alle 3 `item_id`s, den Begruessungssatz und den Schlusssatz; (b) `TOOLS` haben die Namen `log_decision`, `mark_irreversible_checkpoint` und gueltiges JSON-Schema; (c) Simulation (Punkt 5, offline) ergibt 3 Decisions, `ag-02` mit Checkpoint-Reason in `meta`; (d) `TranscriptTap` schreibt `user_text`/`agent_text` ins Transkript und reicht andere Nachrichten durch. Temp-State via `DAWN_STATE_PATH` wie in `tests/test_contract.py`. `gradbot`-Import im Test absichern (`unittest.skipUnless`), damit der Test auch ohne gradbot laeuft.

## Schritte (Reihenfolge)
1. 16:15 merge main, `simple_chat` lesen, Standalone-App `uvicorn src.voice.server:app --port 8002` starten (mit secrets.env) und die Dev-Seite im Laptop-Browser sprechen hoeren (Katalogstimme).
2. 16:40 `prompt.py` + Tools, erster Tool-Call aus echtem Dialog → `python -m src.core.state --show` zeigt `decisions=1`.
3. 17:05 `TranscriptTap`, `end_call`, `/ws/tts`, Events an den Client.
4. 17:20 `voice_design.py` einmal ausfuehren, `DAWN_VOICE_ID` in den Thread an @Philipp2agent melden (keine Secrets), Server mit Custom Voice testen.
5. 17:35 `simulate_call.py`, `tests/test_voice.py`, push, Meldung @hack-chef.

## Abnahmekriterium
```bash
cd /home/buzzagent/hack/wt/hack-bau2 && P=/home/buzzagent/hack/.venv/bin/python
$P -m unittest tests.test_contract tests.test_voice -v                          # OK, ohne Netz
$P -m src.voice.simulate_call && $P -m src.core.state --show                     # decisions=3 call=ended
set -a; . /home/buzzagent/hack/secrets.env; set +a
($P -m uvicorn src.voice.server:app --port 8002 &) && sleep 3 && $P -m src.voice.simulate_call --live   # druckt erste Agent-Zeile mit "Good morning"
```
Erfuellt, wenn alle Befehle laufen, ein echter Browser-Dialog ueber `/ws/chat` mindestens eine `log_decision` im State hinterlaesst (Screenshot/Transkript im Thread) und `git diff origin/main --stat` nur die 6 Dateien oben zeigt.

## Branch-Vorgabe
Nur auf `agent/hack-bau2` arbeiten und pushen (`git push -u origin agent/hack-bau2`). Nie auf `main`. Nicht anfassen: `src/core/*`, `src/dashboard/*`, `src/app.py`, `src/data/*.json`, `assets/*`, `tools/*`, `STAND.md`.
