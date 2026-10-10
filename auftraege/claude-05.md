Modell: Fable (sonst Opus)

# Auftrag claude-05: Bring your own repo - jedes Team kann Dawn an sein GitHub-Repo haengen

## Basis (bewiesen lauffaehig, mit Ton auf Handy und Brille)
dawn/main.py (gradbot simple_chat 1:1, nur Anweisung ausgetauscht) und dawn/prompt.txt. Audio-Weg, Handler und Client NICHT veraendern.

## Ziel
1. Werkzeug dawn/from_repo.py: nimmt einen lokalen Pfad oder eine GitHub-URL (oeffentlich), liest README, die letzten 30 Commits, Branches und vorhandene Status-Dateien (z. B. STAND, TODO, CHANGELOG) und erzeugt mit Gemini (Variablen LLM_API_KEY, LLM_BASE_URL ohne Schraegstrich am Ende, LLM_MODEL) eine neue dawn/prompt.txt im selben Stil: echter Projektkontext in 3 Saetzen, Eroeffnung einmalig, genau drei einfache, konkrete Entscheidungen mit je zwei Optionen, Abschluss.
2. README-Abschnitt "Point Dawn at your repo": drei Befehle (installieren, from_repo, starten) plus Hinweis auf GRADIUM_API_KEY und Gemini-Key.
3. Test ohne echte API: from_repo mit einem kleinen Fake-Repo und gemocktem LLM erzeugt eine gueltige prompt.txt.

## Abnahme
Branch mit Pull Request; dawn/main.py unveraendert lauffaehig; keine Schluessel im Commit.
