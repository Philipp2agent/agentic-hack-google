# Auftrag gemini-02 (P-VOICE): Incoming-Call-Screen, Rapid-Fire Voice Dialog & Web-Audio Backend

**Agent:** hack-bau2 · **Branch:** `agent/hack-bau2` · **Baufenster:** bis 17:45, Meldung bis 17:50, Feature-Freeze 18:00.
**Pflichtlektuere zuerst:** `docs/ARCHITEKTUR.md` (Abschnitte 0, 3, 5, 7), `IDEE.md` Skript 0:00–0:50; Referenzcode `/home/buzzagent/hack/vendor/gradbot/demos/simple_chat/` (main.py + static/index.html), `.../demos/hotel/main.py` (Tool-Calling, Sprechtempo), `.../demos/npc_3d_game/main.py` (One-Shot-TTS `/ws/tts`), `.../demos/voice_design/voice_generator.py` (Voice Design REST).
Antwortet hack-bau2 nicht (noch nicht angelegt), uebernimmt hack-chef oder hack-bau1 dieses Paket unveraendert.

## Ziel
Der Web-Voice-Call von DawnDispatch: mobile Seite `/call` als simulierter eingehender Anruf (Klingelton, Accept, Timer), dahinter `/ws/chat` auf Basis von `gradbot.websocket.handle_session`. Der Agent fragt "How much time do you have?", stellt dann im Rapid-Fire Ja/Nein-Fragen zur Agenda (Gradium TTS, Custom Voice, schnelle Kadenz) und schreibt Beschluesse per Gemini-Tool-Calls (`set_time_budget`, `log_decision`, `mark_irreversible_checkpoint`) in Echtzeit in den State. Kein Twilio, kein WhatsApp.

## Vorgaben
- Voraussetzung: `git fetch origin && git merge origin/main`; `src/core/state.py` und `src/data/agenda.json` vorhanden (sonst @hack-chef).
- Zustand nur ueber `src.core.state` (`load`, `start_call`, `set_time_budget`, `add_decision`, `set_meta`, `append_turn`, `end_call`). `src.core.action_engine` **optional** (`try/except ImportError`), Naehte `on_decision(record)` / `process_post_call()` in `asyncio.to_thread`.
- gradbot-Konfiguration ueber `gradbot.config.from_env()`. Keine Schluessel in Dateien/Logs. Ein Tool-Call pro Turn (ARCHITEKTUR 7); bei HTTP 400 `thought_signature`: `llm_extra_config=json.dumps({"reasoning_effort":"low"})`, sonst `LLM_MODEL=gemini-2.5-flash` dokumentieren.
- Sprache: Code/Prompts Englisch; Call-Sprache `en` (Default) oder `de` via `start.language`/`DAWN_LANGUAGE`.
- Dev-Port 8090 (Vorgabe hack-chef). Audio-JS liegt unter `/static/js/` (mountet `src/app.py`; standalone via `gradbot.routes.setup`).

## Dateien (nur diese anlegen/aendern)
1. `src/voice/prompt.py` – `build_instructions(agenda, lead="Philipp", language="en", time_budget_s=None) -> str` exakt nach ARCHITEKTUR 3 (Eroeffnungssatz, Zeitfrage, "Rapid fire.", ein Item je Turn, Wort→Decision-Mapping, Irreversibel-Satz, Schlusssatz); `TOOLS` (3 ToolDefs); `LANGUAGE_NAMES`; `items_for_budget(agenda, seconds) -> list[AgendaItem]` (< 45 s nur `priority == 1`).
2. `src/voice/server.py`
   - `router = fastapi.APIRouter()`: `GET /call` → `FileResponse(static/call.html)`; `@router.websocket("/ws/chat")`; `@router.websocket("/ws/tts")` (One-Shot wie `npc_3d_game`: `clients = await gradbot.create_clients(**cfg.client_kwargs)` einmal cachen, `await clients.tts_synthesize(text, voice_id=..., rewrite_rules=gradbot.Lang.En.rewrite_rules)` → Bytes je Chunk + `{"type":"done"}`); `GET /api/voices`; `GET /api/audio-config`.
   - `on_start(msg)`: Sprache/Voice wie oben (`DAWN_VOICE_ID` → sonst `DEFAULT_VOICE_ID = "cLONiZ4hQ8VpQ4Sz"` Skyler), Agenda aus `state.load().agenda` (nach `priority`), `state.start_call(lang, voice_id)`, Client-Event `agenda`, `SessionConfig(..., assistant_speaks_first=True, silence_timeout_s=6.0, padding_bonus=-1.5, tools=TOOLS, **cfg.session_kwargs)`.
   - `on_tool_call(handle, input_handle, websocket)`: exakt ARCHITEKTUR 3 (set_time_budget → `state.set_time_budget` + Event `time_budget`; log_decision → Validierung, `DecisionRecord(source="voice_tool")`, `state.add_decision`, Naht `on_decision`, `handle.send_json` mit `next_item_id`, Event `decision_logged`; mark_irreversible_checkpoint → `state.set_meta`, ggf. `set_action_status(checkpoint_reason=...)`, Event `checkpoint_marked`). Unbekannt → `handle.send_error`.
   - `TranscriptTap`-Proxy um das WebSocket (`send_json` faengt `user_text`/`agent_text` → `state.append_turn`).
   - Nach `handle_session`: `state.end_call()`, Event `call_ended` (best effort), Naht `process_post_call` in `asyncio.to_thread`.
   - Standalone-App: `app = fastapi.FastAPI(); app.include_router(router); gradbot.routes.setup(app, config=cfg, static_dir=Path(__file__).parent/"static", with_voices=True)` → `uvicorn src.voice.server:app --port 8090`.
3. `src/voice/static/call.html` + `src/voice/static/call.js` – Incoming-Call-Screen (mobile-first, 390 px): Vollbild "Incoming call · DawnDispatch Agent" mit Avatar (`/assets/brand/call_avatar.png`, `onerror` → Initialen), Klingelton als WebAudio-Chime (Oszillator, 2 Toene, Loop; kein Asset noetig), Buttons **Accept** (gruen) / Decline; nach Accept: Call-Timer (mm:ss), Status, Agenda-Karten (Event `agenda`), Decision-Chips (`decision_logged` gruen/rot/amber), Badge "Waits for your laptop click" (`checkpoint_marked`), Live-Transkript, Hang-up-Button → `stop` + Auflege-Ton + "Open your laptop dashboard". Audio-JS wie `simple_chat` (`/static/js/opus-encoder.js`, `audio-processor.js`, `synced-audio-player.js`; `SyncedAudioPlayer({basePath:'/static/js', ...})`, `AudioContext` im Tap). `?lang=en|de`. Wake Lock best effort. **Fallback `?demo=1`** (Stretch, nur wenn Zeit): spielt `/data/audio/line_NN.ogg` mit Skript-Transkript ab und postet dieselben Decisions ueber `POST /api/demo/decide` (Endpunkt in deinem Router).
4. `src/voice/voice_design.py` – CLI `python -m src.voice.voice_design "warm, calm, energetic morning dispatcher, mid-30s, crisp diction, fast" --name Dawn --language en`: `POST {GRADIUM_BASE_URL}/voice-generator/generate` (`prompt`, `language`, `n_samples=1`, `json_config`), bereit pollen, `POST /voices/from-embedding` (`voxium_embedding_id`, `name`, `description`) → druckt `DAWN_VOICE_ID=<uid>` (Header `x-api-key`; Muster `voice_generator.py`). Ohne Schluessel → klare Fehlermeldung.
5. `src/voice/simulate_call.py` – offline: `state.reset()`, Tool-Logik mit `FakeHandle`/`FakeWebSocket` durch das Skript treiben (`set_time_budget 60`, `log_decision agenda-01 APPROVE`, `log_decision agenda-02 APPROVE "yes"`, `mark_irreversible_checkpoint agenda-02 ...`, `log_decision agenda-03 AMEND "30 instead of 50"`), `end_call`, Zusammenfassung drucken. `--live`: WS zu `ws://localhost:8090/ws/chat`, `start` senden, max. 20 s auf erstes `agent_text` warten, drucken, `stop`.
6. `tests/test_voice.py` – `unittest`, offline, Temp-`DAWN_DATA_DIR`: (a) `build_instructions` enthaelt alle `item_id`s, Eroeffnungs- und Schlusssatz, bei `time_budget_s=30` nur Priority-1-Items; (b) `TOOLS` = 3 Namen mit gueltigem JSON-Schema; (c) Offline-Simulation → 3 Decisions, `time_budget_s == 60`, `meta["checkpoint_reason:agenda-02"]` gesetzt; (d) `TranscriptTap` persistiert `user_text`/`agent_text`, reicht Rest durch. `gradbot`-abhaengige Tests mit `unittest.skipUnless`.

## Schritte
1. jetzt: merge main; `simple_chat` als Standalone unter 8090 zum Sprechen bringen (secrets.env geladen).
2. bis 16:55: `prompt.py` + Tools; erster echter Tool-Call → `python -m src.core.state --show` zeigt `decisions=1`.
3. bis 17:20: `call.html/js` (Incoming-Call, Accept, Timer, Events), `TranscriptTap`, `/ws/tts`.
4. bis 17:30: `voice_design.py` einmal ausfuehren, `DAWN_VOICE_ID` im Thread an @Philipp2agent (kein Secret) fuer `secrets.env`.
5. bis 17:40: `simulate_call.py`, `tests/test_voice.py`, push, Meldung @hack-chef (+ Screenshot `/call` vom Handy).

## Abnahmekriterium
```bash
cd /home/buzzagent/hack/wt/hack-bau2 && P=/home/buzzagent/hack/.venv/bin/python
$P -m unittest tests.test_contract tests.test_voice -v                              # OK, ohne Netz
DAWN_DATA_DIR=/tmp/dawn $P -m src.voice.simulate_call && DAWN_DATA_DIR=/tmp/dawn $P -m src.core.state --show   # decisions=3 call=ended
set -a; . /home/buzzagent/hack/secrets.env; set +a
($P -m uvicorn src.voice.server:app --port 8090 &) && sleep 3 && curl -s localhost:8090/call | grep -c "Incoming" \
  && $P -m src.voice.simulate_call --live                                            # erste Agent-Zeile enthaelt "How much time"
```
Erfuellt, wenn alles laeuft, ein echter Handy-Dialog ueber `/call` ≥ 1 `log_decision` im State hinterlaesst (Transkript im Thread) und `git diff origin/main --stat` nur die Dateien oben zeigt.

## Branch-Vorgabe
Nur `agent/hack-bau2` (`git push -u origin agent/hack-bau2`), nie `main`. Nicht anfassen: `src/core/*`, `src/dashboard/*`, `src/app.py`, `src/data/*.json`, `assets/*`, `tools/*`, `STAND.md`.
