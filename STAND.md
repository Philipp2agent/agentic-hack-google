# STAND agentic-hack-google

## FRAGEN AN PHILIPP
- Keine offenen Fragen. Bau laeuft voll parallel auf 4 Spuren.

## CLAUDE-LINKS ZUM KLICKEN
- [claude-02: Architektur & Bau-Pakete](https://claude.ai/code?repositories=Philipp2agent/agentic-hack-google&prompt=Bearbeite%20auftraege/claude-02.md%20und%20liefere%20das%20Ergebnis%20als%20Branch%20mit%20Pull%20Request)

| ID | Auftrag | Wer | Branch | Status | Naechster Schritt |
|---|---|---|---|---|---|
| Schritt-0 | Datenmodelle & docs/SCHNITTSTELLE.md | hack-chef | main | fertig, gemerged | - |
| IDEE | DawnDispatch Schaerfung (Call UI, Quick Fire, Graph) | hack-chef | main | fertig, gemerged | - |
| P-CORE | src/core: Knowledge Graph Engine & Agenda-Inferenz | hack-bau1 | agent/hack-bau1 | vergeben, laeuft | Bau & PR |
| P-VOICE | src/voice: Mobile Call Screen (/call) & Gradium Audio | hack-bau2 | agent/hack-bau2 | vergeben, laeuft | Bau & PR |
| P-DASHBOARD | src/dashboard: Vorher-Nachher Graph UI & Checkpoints | hack-bau3 | agent/hack-bau3 | vergeben, laeuft | Bau & PR |
| P-VISUAL | assets/brand: Graph-Icons, Call-Avatar, Banner | hack-visual | agent/hack-visual | vergeben, laeuft | Bildgenerierung |
| claude-02 | docs/ARCHITEKTUR.md & gemini-Pakete | Claude-Cloud | claude/... | laeuft in Cloud | Merge nach PR |

## ZEITPLAN
```mermaid
gantt
  title Hackathon-Zeitplan (Zuerich, CEST, Abgabe 19:00)
  dateFormat HH:mm
  axisFormat %H:%M
  section Phasen
  Phase 1 Rahmen & Setup         :done, p1, 14:00, 15:00
  Phase 2 Idee DawnDispatch      :done, p2, 15:00, 16:15
  Phase 3 Paralleler Bau         :crit, active, p3, 16:15, 18:00
  Phase 4 Feature-Freeze & Video :p4, 18:00, 18:40
  Phase 5 Politur & Abgabe       :p5, 18:40, 19:00
  section Parallele Spuren
  P-CORE Knowledge Graph Engine   :crit, active, p_core, 16:15, 17:45
  P-VOICE Mobile Call & Gradium   :crit, active, p_voi, 16:20, 17:45
  P-DASHBOARD Vorher-Nachher UI   :crit, active, p_dash, 16:20, 17:45
  P-VISUAL Graph Icons & Banner   :active, p_vis, 16:15, 17:15
```
