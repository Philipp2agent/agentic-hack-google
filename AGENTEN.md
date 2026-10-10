| Agent | Modell | Aufgabe | Branch |
|---|---|---|---|
| hack-chef | models/gemini-3.8-flash | Steuerung, Abnahme, Merge | main |
| hack-bau1 | models/gemini-3.7-flash | Core Data Models, Repo Swarm Aggregator, Action Engine | agent/hack-bau1 |
| hack-bau2 | models/gemini-3.7-flash | Voice Pipeline, gradbot Web Audio, Gradium STT/TTS | agent/hack-bau2 |
| hack-bau3 | models/gemini-3.7-flash | Web Dashboard ("Show me, don't tell me"), Checkpoint UI | agent/hack-bau3 |
| hack-visual | models/gemini-3.5-flash | Visuals mit Nano Banana ueber tools/bild.py: Entwuerfe mit models/gemini-3.1-flash-image, Finale mit models/gemini-3-pro-image (hoechstens 250 pro Tag); Bilder nach assets/ im eigenen Worktree | agent/hack-visual |
| hack-ideen | models/gemini-3.8-flash | Exploration: Ideen, Wow-Features, Alternativen und Wettbewerb; baut zu jeder offenen Entscheidung von hack-chef die Optionen als kurze Entwuerfe auf Branches opt/nr-A und opt/nr-B vor | agent/hack-ideen |
