# Auftrag gemini-03-dashboard: Laptop Vorher-Nachher Knowledge Graph & Checkpoints

## Ziel
Entwicklung des Desktop-Web-Dashboards (`/dashboard`), das den Zustand vor und nach dem Morgenanruf als interaktiven Knowledge Graph darstellt, das Audio-Transcript anzeigt und Human-Checkpoint-Aktionskarten für irreversible Aktionen bereitstellt.

## Betroffene Dateien
- `src/dashboard/app.py`
- `src/dashboard/templates/index.html`
- `src/dashboard/static/style.css`
- `src/dashboard/static/graph.js`

## Abnahmekriterien
1. **Vorher-Nachher-Graph:** Visualisiert nebeneinander oder togglebar:
   - *Kontext Davor:* `src/data/knowledge_graph_before.json` (offene, unstrukturierte, ungelöste Knoten).
   - *Kontext Danach:* `src/data/knowledge_graph_after.json` (aufgelöste Knoten, neue Kanten, grüne Status-Badges).
2. **Call Transcript:** Zeigt das 60-Sekunden-Gespräch aus `src/data/transcript.json` übersichtlich an.
3. **Human Checkpoints:** Rendert Aktionskarten aus `src/data/actions.json` (z.B. "Deploy Staging", "Publish Hero Asset") mit Bestätigungs-Buttons, die bei Klick visuell quittieren und den Status auf `approved` setzen.
