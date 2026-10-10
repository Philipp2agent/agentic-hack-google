# Parallelstart (Philipp, 16:05) - sofort umsetzen; den Plan aus claude-02 (Fable) einarbeiten, sobald sein Branch da ist

## Struktur (verbindlich, wie in claude-02)
src/voice, src/core, src/dashboard, src/data

## Schritt 0 - hack-chef, zuerst, hoechstens 10 Minuten
Datenmodelle aus claude-02 (OvernightEvent, AgendaItem, DecisionRecord, ActionExecution) als JSON-Beispiele nach src/data/ und als Beschreibung nach docs/SCHNITTSTELLE.md. Committen, pushen.

## Dann parallel per @-Erwaehnung
- hack-bau3 -> src/voice/: Basis gradbot demos/simple_chat (Vorlage am VPS: /home/buzzagent/hack/vendor/gradbot/demos/simple_chat; Python: /home/buzzagent/hack/.venv/bin/python; Schluessel laden: set -a; . /home/buzzagent/hack/secrets.env; set +a). Der Agent spricht zuerst; Agenda aus src/data/agenda.json in die Anweisungen; Werkzeug log_decision schreibt src/data/decisions.json; Werkzeug mark_irreversible_checkpoint; lokal Port 8090; Englisch.
- hack-bau2 -> src/dashboard/: Dashboard "Show me, dont tell me" (Action Cards, Status, Freigabe-Knopf fuer unumkehrbare Punkte), liest src/data/*.json; dazu eine Handy-Startseite fuer den Anruf mit grossem Start-Knopf.
- hack-bau1 -> src/core/: Aggregator der Repo-Ereignisse (git log, STAND.md, Branches) nach src/data/overnight_events.json; Agenda-Synthese mit gemini-3.8-flash nach src/data/agenda.json; Nachbereitung der Entscheidungen nach src/data/actions.json.
- hack-visual -> assets/brand/: Logo und Kopfbild fuer DawnDispatch (Morgenspaziergang mit Smart-Glasses), mit Nano Banana 2.1.
Antwortet hack-bau2 oder hack-bau3 nicht (noch nicht angelegt): Paket an hack-bau1 geben oder selbst uebernehmen und in STAND.md vermerken.

## Regeln
- Jeder Bauer arbeitet auf seinem Branch agent/<name>; hack-chef merged nach Abnahme nach main.
- Status jedes Pakets steht in STAND.md. Feature-Freeze 18:00.
- In Buzz-Nachrichten keine Dateiendungen wie md oder py ausschreiben (die App bricht beim Link-Vorschau-Versuch ab): Dateinamen ohne Endung oder in Backticks nennen.
