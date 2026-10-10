# STAND agentic-hack-google

## ENTSCHEIDUNGEN AUS LIVE-CALL (18:20 CEST)
- **Call-Entscheidung A:** Echte WhatsApp Calls gewuenscht -> Task `NACHT-A` an hack-bau2 vergeben.
- **Call-Entscheidung B:** Repo vorerst privat halten bis Abschluss -> Task `NACHT-B` bestaetigt, Checkpoint schuetzt vor unzeitiger Veroeffentlichung.

## FRAGEN AN PHILIPP
- 1. Produktname fuer Video 2 & Branding: Welcher Favorit soll es werden? (A: PromptMe | B: Dawn / DawnDispatch | C: Dispatch) -> Empfehlung: 1A (PromptMe - dreht "Human prompts Agent" genial um)

## CLAUDE-LINKS ZUM KLICKEN
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
| claude-05 | Plug-and-Play fuer jedes Repo (setup.sh, start.sh) | Claude-Cloud | main | fertig, gemerged | setup.sh, start.sh, dawn/from_repo.py & 84 Tests gruen |
| S-MKTG | Video-2-Skript (2 Min) & README-Erzaehlung "Try in 3 min" | hack-bau1 | main | fertig, gemerged | docs/VIDEO_SCRIPT_V2.md & README live |
| S-VISUAL | Neutrale Titelkarte & Abspann ("8 Gemini agents + Claude") | hack-bau3 | main | fertig, gemerged | assets/brand/video2_* & docs/VISUALS_V2.md live |
| S-LIVE-UI | Live-Ansicht verfeinern (Fokus zentriert, Rest gedimmt) | hack-bau2 | main | fertig, gemerged | HUD-Fokus & Dimmung fuer Brillenkamera live |
| S-NACHHER | Nachher-Ansicht Live-Seite ("Das hat das Gespraech gebracht") | hack-bau3 | main | fertig, gemerged | 3 Vorher->Nachher Karten live in /live |
| S-EXAMPLE | Realistic Example Repo unter examples/ fuer Plug-and-Play | hack-bau1 | main | fertig, gemerged | PayPulse mit 30 Commits & Tests live |
| S-REVIEW | Frischer Klon E2E Test fuer claude-05 (setup.sh/start.sh) | hack-bau3 | main | fertig, gemerged | E2E-Validierung erfolgreich, docs/REVIEW_CLAUDE_05.md live, 84/84 Tests gruen |
| NACHT-A | Nachtschicht: Echte WhatsApp Calls konfigurieren | hack-bau2 | main | fertig, gemerged | WhatsApp Media Stream Adapter, docs/WHATSAPP.md, 90/90 Tests gruen |
| NACHT-B | Nachtschicht: Repo privat halten bis Abgabe-Checkpoint | hack-chef | main | fertig | Checkpoint aktiv, Veroeffentlichung erst bei Abgabe |

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
  Phase 5 Sprint 18:20 Video 2   :done, p5, 17:50, 18:20
  Phase 6 Feature-Freeze & Politur :crit, active, p6, 18:20, 18:45
  Phase 7 Abgabe                 :p7, 18:45, 19:00
  section Parallele Spuren Feature-Freeze
  S-REVIEW Klon & Setup Test     :done, p_rev, 18:20, 18:28
  NACHT-A WhatsApp Call Config   :done, p_na, 18:20, 18:30
  NACHT-B Privacy Checkpoint     :done, p_nb, 18:20, 18:25
```
