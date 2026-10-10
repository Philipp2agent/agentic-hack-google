# STAND agentic-hack-google

## FRAGEN AN PHILIPP
- Entscheidung zu IDEE.md: 1 (Szenario: 1A FieldOps vs 1B CareOps), 2 (Interface: 2A Web-Dashboard vs 2B Twilio), 3 (Visuals: 3A Nano Banana vs 3B Tabelle)

## CLAUDE-LINKS ZUM KLICKEN
- keine

| ID | Auftrag | Wer | Branch | Status | Naechster Schritt |
|---|---|---|---|---|---|
| T-01 | docs/STRUKTUR.md Ordnerstruktur | hack-bau1 | agent/hack-bau1 | fertig, gemerged | - |
| T-02 | Titelbild-Entwurf assets/titelbild.jpg | hack-visual | agent/hack-visual | fertig, gemerged | - |
| T-03 | Titelbild v2 & Token-/Kostenbericht | hack-visual | agent/hack-visual | fertig, gemerged | - |
| claude-01 | tools/ton.py (Gemini TTS) | Claude-Cloud | claude/... | fertig, gemerged | - |
| IDEE | IDEE.md Produktkonzept VoxField Copilot | hack-chef | main | fertig, wartet auf Feedback | Philipp entscheidet (1A/1B, 2A/2B, 3A/3B) |

## ZEITPLAN
```mermaid
gantt
  title Hackathon-Zeitplan (Zuerich, CEST, Abgabe 19:00)
  dateFormat HH:mm
  axisFormat %H:%M
  section Phasen
  Idee & Scope (bis 15:30)  :done, p1, 15:00, 15:30
  Bau & Integration         :active, p2, 15:30, 18:00
  Feature-Freeze & Video    :p3, 18:00, 18:40
  Politur & Abgabe (19:00)  :p4, 18:40, 19:00
```
