# HACKATHON: {Tech: Europe} Agentic AI Hack Zuerich, 10.10.2026 (Open Innovation)

## Termine (Zeitzone Zuerich/Wien, CEST)
- ABGABE: 19:00. Finalisten praesentieren live ab 20:00 (5 Minuten, Live-Demo mit echten Eingaben).
- Feature-Freeze: 18:00 (gilt statt der 90-Minuten-Regel). Danach nur Fehlerbehebung, README, Doku, Video.
- Video aufnehmen: 18:15-18:40. Abgabe spaetestens 18:50.

## Was abgegeben wird
- 2-Minuten-Video (Loom o. ae.): Erklaerung der Loesung und Live-Walkthrough der Kernfunktionen.
- OEFFENTLICHES GitHub-Repo: vollstaendiger Code, README mit Setup und Installation, Doku aller APIs, Frameworks und Tools, genug technische Doku fuer die Jury.

## Regeln
- Team hoechstens 5 Personen. Projekt neu am Hackathon (Boilerplates erlaubt).
- Mindestens 2 Partner-Technologien: Google DeepMind (Gemini) und Gradium (Voice). Entire ist optionaler Bonus.

## Bewertung
- Stufe 1: technische Komplexitaet, Kreativitaet, loest ein echtes Problem; Bonus fuer Partner-Technologie. 5 Finalisten.
- Stufe 2: 5 Minuten live vor Jury und Publikum; Jury waehlt die Top 3.
- DeepMind-Kriterien: (1) handelt: plant, nutzt Werkzeuge, erledigt Aufgaben; (2) hilft einer echten, benennbaren Person bei einem Problem; (3) Mensch behaelt Kontrolle: fragt vor allem Unumkehrbaren; (4) laeuft live mit echten Eingaben.

## Technik
- Google: Interactions API (google-genai >= 2.3.0) fuer Modelle und Managed Agents, serverseitiger Zustand, Hintergrund-Tasks.
- Modelle: gemini-3.8-flash (Planen, Code), antigravity-preview-09-2026 (Managed Agent mit Sandbox), deep-research-preview-04-2026, gemini-3.8-live, gemini-nano-banana-2.1 (Bilder), gemini-omni-1.1-flash (Video mit Ton), lyria-3.5 (Musik), gemma-4-31b-it.
- Gemini-API-Skills fuer Coding-Agenten: npx skills add google-gemini/gemini-skills --skill gemini-api-dev
- Muster: Orchestrator und Worker; Voice Front Door; Human Checkpoint; Private by default.
- Gradium: STT und TTS (REST und WebSocket, Header x-api-key, Deutsch und Englisch), semantische Sprechpausen-Erkennung, Voice Cloning. Basis-Framework gradbot (github.com/gradium-ai/gradbot): STT-LLM-TTS-Schleife, jede OpenAI-kompatible LLM (auch Gemini), Werkzeuge, MCP, Twilio-Telefonie.

## Konto-Regeln (temporaeres Google-Konto)
- KEIN MISSBRAUCH: Nutzung, die nicht nach normalem Hackathon aussieht (z. B. tausende Anfragen), fuehrt zur Disqualifikation. Agenten-Schleifen sparsam, keine Massentests.
- KEINE SCHLUESSEL im Repo, auch nicht in der Git-Historie: das Repo wird oeffentlich, ein Leak schliesst das Konto. Schluessel nur aus Umgebungsvariablen; .env.example ohne Werte.
- Das Konto wird morgen geloescht: Code und Assets bis Abgabe exportieren.
