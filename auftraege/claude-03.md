Modell: Fable (sonst Opus)

# Auftrag claude-03: Integration und Voice - ein lauffaehiges MVP bis 17:15

## Kontext lesen
HACKATHON.md, IDEE.md, docs/SCHNITTSTELLE.md, context/hackathon-day.md, auftraege/claude-02.md, auftraege/gemini-02-voice.md, auftraege/gemini-03-dashboard.md.

## Ausgangslage
main enthaelt bereits src/core (Aggregator, Agenda, Graph, Aktionen), src/dashboard (FastAPI, Vorher-Nachher-Graph, Freigaben), src/data (Seeds) und tests. Dein Plan-Branch claude/auftraege-claude-02-q690zb (Vertrag, state, app, requirements) ist NICHT gemerged. src/voice fehlt.

## Ziel: EIN Startbefehl, der alles serviert
1. Fuehre deinen claude-02-Branch in diese Arbeit ein; bei Konflikten gilt der auf main gebaute, funktionierende Stand.
2. src/voice: mobile Seite /call (simulierter eingehender Anruf mit Annehmen-Knopf) und WebSocket /ws/chat auf Basis des pip-Pakets gradbot (Vorlage: github.com/gradium-ai/gradbot, demos/simple_chat). Der Agent spricht zuerst. Ablauf: "How much time do you have?", dann Schnellfeuer-Fragen aus src/data/agenda.json. Werkzeuge log_decision, mark_irreversible_checkpoint und set_time_budget schreiben ueber src/core nach src/data. Am Ende process_post_call: knowledge_graph_after.json und actions.json.
3. Inhalt fuer die Demo: Version 1 (heute gebaut, aus context/hackathon-day und dem Repo), dann fragt der Agent Philipp, was Version 2 werden soll, und haelt seine Entscheidungen fest. Leitsatz: The agent owns the code and the human.
4. Einstieg src/app.py: mountet /call, /ws/chat und /dashboard. Start mit uvicorn auf 127.0.0.1:8090. Schluessel nur aus der Umgebung: GRADIUM_API_KEY, LLM_API_KEY, LLM_BASE_URL (ohne Schraegstrich am Ende, sonst 404), LLM_MODEL; optional DAWN_VOICE_ID.
5. requirements.txt vollstaendig; README-Abschnitt Run locally mit genau den Startbefehlen.
6. pytest gruen, dazu ein Smoke-Test: App importierbar, /dashboard und /call antworten mit 200 (ohne echte API-Aufrufe).

## Laufzeit am VPS (dort wird es gestartet)
Python 3.12, gradbot (aktuell aus PyPI), google-genai 2.29, fastapi 0.143, uvicorn 0.54.

## Abnahme
Branch mit Pull Request; im PR-Text die exakten Startbefehle. Keine Schluessel, keine .env im Commit.
