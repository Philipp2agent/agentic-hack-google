Modell: Fable (sonst Opus)

# Auftrag claude-05 (erweitert 17:50): Plug-and-Play fuer jedes Repo
Ziel: Jeder klont dieses Repo, traegt EIGENE Schluessel ein (Gradium, Gemini), zeigt auf SEIN Repo und bekommt in 3 Minuten seinen Anruf mit Live-Ansicht. Nichts haengt an Philipp.

## Bewiesene Basis (laeuft am VPS mit Ton auf Handy und Brille)
- dawn/main.py: gradbot simple_chat 1:1, nur die Anweisung kommt aus prompt.txt. Handler und Client NICHT veraendern.
- dawn/gen_prompt.py: Gemini 3.8 Flash verdichtet Repo-Kontext vorab zu BRIEFING, THREADS und OPENING; das Gespraech laeuft auf gemini-3.5-flash-lite (0,7 s).
- dawn/bridge.py: Live-Bruecke, Gespraechs-Log nach Gemini nach POST /api/live/event (Vertrag docs/LIVE-EVENTS.md, Live-Ansicht aus PR 4).
Diese Dateien enthalten noch feste VPS-Pfade: generalisieren.

## Lieferumfang
1. setup.sh: prueft Python 3.11+, installiert in .venv, fragt verdeckt nach GRADIUM_API_KEY und GEMINI_API_KEY, schreibt .env (nie committen), fragt nach dem Ziel-Repo (Pfad oder GitHub-URL).
2. dawn/from_repo.py: liest das Ziel-Repo (README, letzte 30 Commits, Branches, Status-Dateien wie STAND, TODO, CHANGELOG) und erzeugt mit der gen_prompt-Logik dawn/prompt.txt.
3. start.sh: startet Anruf-Server, Live-Ansicht und Bruecke; optional einen HTTPS-Tunnel (cloudflared, falls installiert); gibt Handy- und Laptop-URL aus.
4. README ganz oben: "Try it on your own repo in 3 minutes" mit genau diesen Befehlen, Voraussetzungen (eigene Keys) und einem Satz Datenschutz (Repo-Inhalt geht an Gemini).
5. Tests ohne echte API (gemockt): from_repo erzeugt eine gueltige prompt.txt; die Bruecke macht aus einer Beispiel-Logzeile Ereignisse.

## Abnahme
Pull Request; ein frischer Klon laeuft nur mit setup.sh und start.sh. Keine Schluessel im Commit.
