# STAND agentic-hack-google

## FRAGEN AN PHILIPP
- 1. Produktname fuer Video 2 & Branding: Welcher Favorit soll es werden? (A: PromptMe | B: Dawn / DawnDispatch | C: Dispatch) -> Empfehlung: 1A (PromptMe - dreht "Human prompts Agent" genial um)
- 2. Modell-Konfiguration fuer hack-visual, hack-marketing & hack-review in Buzz (melden Provider-Fehler): (A: In Buzz Desktop Modell neu zuweisen & Neustart | B: hack-chef baut Pakete mit hack-bau1/main) -> Empfehlung: 2A

## CLAUDE-LINKS ZUM KLICKEN
- [claude-05: Plug-and-Play fuer jedes Repo (setup.sh, from_repo.py, start.sh, Deadline 18:20)](https://claude.ai/code?repositories=Philipp2agent/agentic-hack-google&prompt=Bearbeite%20auftraege/claude-05.md%20und%20liefere%20das%20Ergebnis%20als%20Branch%20mit%20Pull%20Request)
- [claude-03: Lauffaehiges MVP E2E Backend, Integration & Video-Tools (PR #3 bereit, Ton-Check)](https://claude.ai/code?repositories=Philipp2agent/agentic-hack-google&prompt=Bearbeite%20auftraege/claude-03.md%20und%20liefere%20das%20Ergebnis%20als%20Branch%20mit%20Pull%20Request)

| ID | Auftrag | Wer | Branch | Status | Naechster Schritt |
|---|---|---|---|---|---|
| Schritt-0 | Datenmodelle & docs/SCHNITTSTELLE.md | hack-chef | main | fertig, gemerged | - |
| IDEE | Schaerfung: Phone Call UI, Quick Fire, Before/After Graph | hack-chef | main | fertig, gemerged | - |
| claude-02 | docs/ARCHITEKTUR.md, state.py & Baupakete | Claude-Cloud | main | fertig, gemerged | - |
| P-CORE | src/core: Aggregator, Agenda-Synthese & Graph Engine | hack-bau1 | main | fertig, gemerged | - |
| P-VOICE-UI | Mobile Call Screen (/call) autarker Demo-Flow | hack-bau2 | main | fertig, gemerged | - |
| P-DASHBOARD-UI | Vorher-Nachher Graph (/dashboard) v1/v2 Kontrast & Checkpoint-Pulse | hack-bau3 | main | fertig, gemerged | - |
| gemini-01 | Demo-Szenario v1->v2 (85 echte Repo-Events) in src/data | hack-bau1 | main | fertig, gemerged | 85 Events & 56 Tests gruen |
| P-LIVE-SIM | Live-Demo-Events-Simulator & Vertragstests (docs/LIVE-EVENTS.md) | hack-bau2 | main | fertig, gemerged | - |
| P-DEMO-DATA | Demo-Agenda-Daten gemaess docs/LIVE-EVENTS.md | hack-bau1 | main | fertig, gemerged | - |
| P-VISUAL | Brand-Assets (Banner, Call-Avatar, Graph-Icons) | hack-bau1 | main | fertig, gemerged | assets/brand/* live |
| claude-04 | Live-Visualisierung /src/live Mission Control | Claude-Cloud | main | fertig, gemerged | PR #4 gemerged auf main |
| S-IDEEN | 15 Produktnamen (Agent promptet Menschen, merkbar) | hack-ideen | main | fertig, gemerged | docs/NAMEN.md live, Top 3 zur Wahl |
| claude-03 | Lauffaehiges MVP E2E Backend & Video-Tools | Claude-Cloud | claude/auftraege-claude-03-jh0o10 | PR #3 bereit | Merge nach Ton-Bestaetigung |
| claude-05 | Plug-and-Play fuer jedes Repo (setup.sh, start.sh) | Claude-Cloud | claude/claude-05 | vergeben | Claude-Link klicken |
| S-MKTG | Video-2-Skript (2 Min) & README-Erzaehlung "Try in 3 min" | hack-marketing | agent/hack-marketing | vergeben | docs/VIDEO_SCRIPT_V2.md |
| S-VISUAL | Neutrale Titelkarte & Abspann ("8 Gemini agents + Claude") | hack-visual | agent/hack-visual | vergeben | assets/brand/video2_* |
| S-LIVE-UI | Live-Ansicht verfeinern (Fokus zentriert, Rest gedimmt) | hack-bau2 | agent/hack-bau2 | vergeben | src/live/static/ |
| S-NACHHER | Nachher-Ansicht Live-Seite ("Das hat das Gespraech gebracht") | hack-bau3 | main | fertig, gemerged | 3 Vorher->Nachher Karten live in /live |
| S-EXAMPLE | Realistic Example Repo unter examples/ fuer Plug-and-Play | hack-bau1 | main | fertig, gemerged | PayPulse mit 30 Commits & Tests live |
| S-REVIEW | Frischer Klon E2E Test fuer claude-05 (setup.sh/start.sh) | hack-review | agent/hack-review | wartet | wartet auf claude-05 PR |

## ZEITPLAN
```mermaid
gantt
  title Hackathon-Zeitplan (Zuerich, CEST, Abgabe 19:00)
  dateFormat HH:mm
  axisFormat %H:%M
  section Phasen
  Phase 1 Rahmen & Setup         :done, p1, 14:00, 15:00
  Phase 2 Idee DawnDispatch      :done, p2, 15:00, 16:15
  Phase 3 Paralleler Bau         :done, p3, 16:15, 17:10
  Phase 4 Probelauf mit Brille   :done, p4, 17:10, 17:50
  Phase 5 Sprint 18:20 Video 2   :crit, active, p5, 17:50, 18:20
  Phase 6 Feature-Freeze & Politur :p6, 18:20, 18:45
  Phase 7 Abgabe                 :p7, 18:45, 19:00
  section Parallele Spuren Sprint 18:20
  claude-04 Live Mission Control :done, p_cl4, 17:00, 17:55
  S-IDEEN 15 Produktnamen        :done, p_ide, 17:55, 17:58
  claude-05 Plug-and-Play Repo   :crit, active, p_cl5, 17:55, 18:20
  S-MKTG Video-2-Skript & Story  :active, p_mkt, 17:55, 18:15
  S-VISUAL Titelkarte & Abspann  :active, p_vis, 17:55, 18:15
  S-LIVE-UI Brillen-Fokus Screen :active, p_b2, 17:55, 18:15
  S-NACHHER Nachher-Ansicht      :done, p_b3, 17:55, 18:03
  S-EXAMPLE Example Target Repo  :done, p_b1, 17:55, 18:00
  S-REVIEW Klon & Setup Test     :p_rev, 18:15, 18:25
```
