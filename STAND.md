# STAND agentic-hack-google

## FRAGEN AN PHILIPP
- 1. Modell-Konfiguration fuer hack-visual, hack-marketing & hack-review in Buzz: Alle 3 Agenten melden 'the configured model wasn't found at the provider's endpoint'. Bitte in Buzz Desktop unter Agent-Settings fuer diese 3 Agenten ein aktives Modell waehlen und neu starten. -> Empfehlung: 1A

## CLAUDE-LINKS ZUM KLICKEN
- [claude-03: Lauffaehiges MVP E2E Backend, Integration & Video-Tools (Deadline 17:10)](https://claude.ai/code?repositories=Philipp2agent/agentic-hack-google&prompt=Bearbeite%20auftraege/claude-03.md%20und%20liefere%20das%20Ergebnis%20als%20Branch%20mit%20Pull%20Request)

| ID | Auftrag | Wer | Branch | Status | Naechster Schritt |
|---|---|---|---|---|---|
| Schritt-0 | Datenmodelle & docs/SCHNITTSTELLE.md | hack-chef | main | fertig, gemerged | - |
| IDEE | Schaerfung: Phone Call UI, Quick Fire, Before/After Graph | hack-chef | main | fertig, gemerged | - |
| claude-02 | docs/ARCHITEKTUR.md, state.py & Baupakete | Claude-Cloud | main | fertig, gemerged | - |
| P-CORE | src/core: Aggregator, Agenda-Synthese & Graph Engine | hack-bau1 | main | fertig, gemerged | - |
| P-VOICE-UI | Mobile Call Screen (/call) statische UI | hack-bau2 | main | fertig, gemerged | E2E Integration in claude-03 |
| P-DASHBOARD-UI | Vorher-Nachher Graph (/dashboard) statische UI | hack-bau3 | main | fertig, gemerged | E2E Integration in claude-03 |
| gemini-01 | Demo-Szenario v1->v2 (context/hackathon-day.md) in src/data | hack-bau1 | agent/hack-bau1 | vergeben, laeuft | auf v1->v2 schaerfen |
| claude-03 | Lauffaehiges MVP E2E Backend & Video-Tools (Deadline 17:10) | Claude-Cloud | claude/... | vergeben | Klick durch Philipp, PR bis 17:10 |
| P-VISUAL | assets/brand: Graph Icons, Call Avatar, Banner (Nano Banana) | hack-visual | agent/hack-visual | blockiert (Modellfehler in Buzz) | Modell in Agent-Settings anpassen |
| P-MARKETING | 2-Minuten-Video-Skript & README-Erzaehlung | hack-marketing | agent/hack-marketing | blockiert (Modellfehler in Buzz) | Modell in Agent-Settings anpassen |
| P-REVIEW | Testplan & Vorbereitung fuer E2E-Test 17:10 | hack-review | agent/hack-review | blockiert (Modellfehler in Buzz) | Modell in Agent-Settings anpassen |

## ZEITPLAN
```mermaid
gantt
  title Hackathon-Zeitplan (Zuerich, CEST, Abgabe 19:00)
  dateFormat HH:mm
  axisFormat %H:%M
  section Phasen
  Phase 1 Rahmen & Setup         :done, p1, 14:00, 15:00
  Phase 2 Idee DawnDispatch      :done, p2, 15:00, 16:15
  Phase 3 Paralleler Bau         :crit, active, p3, 16:15, 17:10
  Phase 4 Probelauf mit Brille   :crit, p4, 17:10, 17:30
  Phase 5 Feature-Freeze & Video :p5, 18:00, 18:40
  Phase 6 Politur & Abgabe       :p6, 18:40, 19:00
  section Parallele Spuren
  P-CORE Knowledge Graph Inferenz   :done, p_core, 16:15, 16:20
  P-VOICE-UI Mobile Call Screen     :done, p_vui, 16:35, 16:45
  P-DASHBOARD-UI Graph Split-View   :done, p_dui, 16:35, 16:43
  gemini-01 Szenario v1->v2         :crit, active, p_gem1, 16:35, 17:05
  claude-03 E2E MVP & Video-Tools   :crit, active, p_cl3, 16:40, 17:10
  Probelauf Ray-Ban Brille          :crit, p_probe, 17:10, 17:30
```
