Modell: Fable (sonst Opus)

# Auftrag claude-04: Live Mission Control - die Visualisierung, die aus dem Anruf live entsteht (bis 17:30)

Lies HACKATHON.md, IDEE.md, docs/LIVE-EVENTS.md (verbindlicher Vertrag), context/hackathon-day.md, src/data/*.json.

## Ziel
Ein Laptop-Bildschirm /live, auf dem sich waehrend des Anrufs alles sichtbar aufbaut. Wird im Video durch die Kamera einer Smart-Glasses-Brille gefilmt: dunkles Design, sehr grosse Schrift, hoher Kontrast, 16:9, wenig Text, Animationen von 0,5 bis 1,5 s. Peak UI, wie ein Mission-Control-Screen.

## Bausteine (vorgefertigt, je Ereignistyp eine Animation, kein LLM im Darstellungspfad)
- Wissensgraph aus src/data/knowledge_graph_before.json; Knoten wechseln animiert von rot/gelb auf gruen (decision), Checkpoint-Knoten pulsieren und haben einen grossen Freigabe-Knopf (checkpoint, POST loest checkpoint_resolved aus).
- Seitenleiste: Agenda-Fortschritt (agenda_item), Zeit-Budget und Sprechtempo als Anzeige (time_budget, speed_changed), letzte Saetze des Nutzers (user_said, kurz).
- v2_idea: neue violette Knoten wachsen aus den verknuepften Knoten.
- participants_scaled: ein Netz von Teilnehmer-Knoten breitet sich vom Projekt aus (Wow-Moment).
- call_ended und brief_ready: Uebergang zur Nachher-Ansicht v1 zu v2 mit drei Kernaussagen.

## Technik
- Nur src/live/ (router.py mit FastAPI APIRouter namens router, bus.py, static/). src/voice und src/app.py gehoeren claude-03; dort wird dein Router per try-import gemountet.
- bus.py nach Vertrag; jedes Ereignis wird je Sitzung mitgeschrieben (src/data/live_session.jsonl), damit /api/live/replay es erneut abspielen kann; /api/live/reset leert den Zustand fuer den naechsten Dreh.
- Bibliotheken per CDN erlaubt (z. B. d3 oder cytoscape, GSAP); alles in einer Seite lauffaehig.
- Test: ein Skript tools/live_demo_events sendet die Demo-Agenda als Ereignisfolge, damit man /live ohne Anruf vorfuehren kann.

## Abnahme
Branch mit Pull Request. /live laeuft mit dem Testskript sichtbar durch alle Ereignistypen; im PR-Text die genauen Befehle.
