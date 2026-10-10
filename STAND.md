# STAND agentic-hack-google

## FRAGEN AN PHILIPP
- Entscheidung zu Morgen-Anruf-Agent (IDEE.md): 1 (Call-Trigger: 1A Outbound vs 1B Inbound), 2 (Szenario: 2A DevOps vs 2B Ops Executive), 3 (Dashboard: 3A Action Cards vs 3B Briefing)

## CLAUDE-LINKS ZUM KLICKEN
- [claude-02: Architektur & Arbeitspakete](https://claude.ai/code?repositories=Philipp2agent/agentic-hack-google&prompt=Bearbeite%20auftraege/claude-02.md%20und%20liefere%20das%20Ergebnis%20als%20Branch%20mit%20Pull%20Request)

| ID | Auftrag | Wer | Branch | Status | Naechster Schritt |
|---|---|---|---|---|---|
| T-01 | docs/STRUKTUR.md Ordnerstruktur | hack-bau1 | agent/hack-bau1 | fertig, gemerged | - |
| T-02 | Titelbild-Entwurf assets/titelbild.jpg | hack-visual | agent/hack-visual | fertig, gemerged | - |
| T-03 | Titelbild v2 & Token-/Kostenbericht | hack-visual | agent/hack-visual | fertig, gemerged | - |
| T-04 | Titelbild v3 (Solitäre Silhouette, Bienen-Schwarm-Agents, Basstöne) | hack-visual | agent/hack-visual | fertig, gemerged | - |
| claude-01 | tools/ton.py (Gemini TTS) | Claude-Cloud | claude/... | fertig, gemerged | - |
| IDEE | IDEE.md Morgen-Anruf-Agent (DawnDispatch) | hack-chef | main | fertig, wartet auf Feedback | Philipp entscheidet (1A/1B, 2A/2B, 3A/3B) |
| claude-02 | docs/ARCHITEKTUR.md & gemini-01..03 Arbeitspakete | Claude-Cloud | claude/... | offen, wartet auf Start | Philipp startet Claude-Link |

## ZEITPLAN
```mermaid
gantt
  title Hackathon-Zeitplan (Zuerich, CEST, Abgabe 19:00)
  dateFormat HH:mm
  axisFormat %H:%M
  section Phasen
  Phase 1 Rahmen & Setup     :done, p1, 14:00, 15:00
  Phase 2 Idee & Scope       :active, p2, 15:00, 15:50
  Phase 3 Bau & Integration  :crit, p3, 15:50, 18:00
  Phase 4 Feature-Freeze & Video :p4, 18:00, 18:40
  Phase 5 Politur & Abgabe   :p5, 18:40, 19:00
  section Auftraege
  IDEE.md Konzept            :done, t_idee, 15:30, 15:40
  claude-02 Architektur      :active, t_cl2, 15:40, 16:05
  gemini-01..03 Baupakete    :t_gem, 16:05, 18:00
```
