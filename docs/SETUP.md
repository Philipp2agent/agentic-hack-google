# SETUP agentic-hack-google (Stand 10.10.2026, ohne Geheimnisse)

## Architektur
- Buzz-Relay (buzz-next) am VPS; Agenten laufen als Linux-User buzzagent, Harness buzz-agent, Provider openai-compat gegen die Google-Gemini-API (Workshop-Key, Tier 1).
- Channel agentic-hack-google; Sitzungsmodus thread: jeder Thread ist eine eigene Sitzung ohne Gedaechtnis anderer Threads. Gemeinsamer Zustand nur im Repo: STAND.md (Lagebrett), AGENTEN.md (Team), HACKATHON.md (Rahmen), IDEE.md.
- hack-chef steuert (Hauptsteuerung), arbeitet auf main, merged. Bauer arbeiten je in eigenem Git-Worktree auf Branch agent/<name>. Agenten reagieren nur auf @-Erwaehnung.
- Claude-Cloud (Claude Code Cloud-Sessions, bezahlt aus einem 250-Dollar-Guthaben): Auftraege als auftraege/claude-NN.md, gestartet per Link durch Philipp (ein Klick). Claude hat KEINEN Google-Key; Tests mit Google laufen am VPS durch Buzz-Agenten.
- Werkzeuge im Repo: tools/bild.py (Nano Banana, Bild aus Text, Key nur aus der Umgebung).

## Neue Agenten
- Philipp legt in der Buzz-App an (Run on: vps, Each thread, Name) und nimmt in den Channel auf; danach eine Zeile: agent-einrichten.sh <hack-name> <models/...> "<Schwerpunkt>" (Rolle, Worktree, Modell, Neustart, AGENTEN.md).
- Namensregel: hack-<rolle>; nie auf -cos oder -lead enden, nie t<Zahl>-... (sonst ueberschreibt ein Profil Modell und Key).

## Grenzen
- VPS: 2 vCPU, 7,8 GB RAM (davon ca. 4 GB frei); Agenten selbst ca. 15 MB, Last entsteht durch Builds/Tests.
- Relay drosselt viele Agenten pro Channel: 4-6 pro Channel, darueber zweiter Channel.
- Gemini 3.x ueber openai-compat: gelegentlich HTTP 400 "missing thought_signature" bei mehrstufiger Werkzeugarbeit (beobachtet bei gemini-3.5-flash); gemini-2.5-* ist tolerant.
- Kein Node/npm fuer buzzagent installiert (Python 3 vorhanden).
- Schluessel: Commit-Sperre (pre-commit Hook) im Klon; nie Schluessel ausgeben oder committen.
- Gemessen: aktiver Agent bis ca. 14 Aufrufe/min, 8k-60k Eingabe-Tokens je Aufruf (grossteils Cache).

## Google-Kontingente (Tier 1, je Modell eigenes Kontingent: RPM / TPM / RPD)
| Modell | RPM | TPM | RPD |
|---|---|---|---|
| gemini-3.8-flash, 3.7-flash, 3.6-flash, 3.5-flash, 3-flash-preview | 1K | 2M | 10K |
| gemini-3.5-flash-lite, 3.1-flash-lite | 4K | 4M | 150K |
| gemini-2.5-flash | 1K | 1M | 10K |
| gemini-2.5-flash-lite | 4K | 4M | unbegrenzt |
| gemini-2.5-pro | 150 | 2M | 1K |
| gemini-3.1-pro-preview | 25 | 2M | 250 |
| Nano Banana 2 (gemini-3.1-flash-image), Nano Banana 2.1 | 100 | 200K | 1K |
| Nano Banana Pro (gemini-3-pro-image) | 20 | 100K | 250 |
| Nano Banana (gemini-2.5-flash-image) | 500 | 500K | 2K |
| gemini-3.8-flash-tts (Sprache) | 10 | 10K | 100 |
| Veo 3 Fast (Video) | 2 | - | 10 |
| Deep Research Pro Preview | 1 | 500K | 1.44K |
| gemini-3.8-live (Echtzeit) | unbegrenzt | 150K | unbegrenzt |
| gemini-embedding-2 | 3K | 1M | unbegrenzt |
