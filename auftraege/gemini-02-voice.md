# Auftrag gemini-02-voice: Mobile Call Screen & Gradium Voice Pipeline

## Ziel
Entwicklung der mobilen Web-Ansicht (`/call`) zur realistischen Simulation eines eingehenden Anrufs von "DawnDispatch" (für Meta Ray-Ban Bluetooth-Audio) und Anbindung der Gradium Voice STT/TTS-Pipeline für schnelles Yes/No-Fragetempo.

## Betroffene Dateien
- `src/voice/app.py`
- `src/voice/gradium_client.py`
- `src/voice/static/call.html`
- `src/voice/static/call.js`
- `src/voice/static/call.css`

## Abnahmekriterien
1. **Call UI:** `/call` liefert auf Mobilgeräten einen realistischen Anruf-Screen ("Incoming Call: DawnDispatch", Profil-Avatar, Grüner Abheben-Button).
2. **Ray-Ban Audio:** Bei Annahme wird Web-Audio aktiviert (Mikrofon-Aufnahme & Lautsprecher-Wiedergabe).
3. **Dialog-Flow:**
   - Eröffnung: "Good morning Philipp. How much time do you have?"
   - Bei Input schaltet der Agent auf Rapid Quick Fire (schnelle Audioausgabe, Yes/No-Fragen aus `src/data/agenda.json`).
4. **Export:** Nach Anruf-Ende wird das Gespräch als `src/data/transcript.json` abgelegt und ein Event für das Dashboard ausgelöst.
