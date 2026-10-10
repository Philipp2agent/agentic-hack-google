# Auftrag claude-01: Werkzeug tools/ton.py

## Ziel
Erstelle das CLI-Werkzeug `tools/ton.py`, das per Gemini-API (Modell `gemini-3.8-flash-tts`) Text in Sprache umwandelt und als WAV-Datei nach `assets/` speichert.
Der Aufbau und Code-Stil soll exakt `tools/bild.py` entsprechen (kompakt, nur Python-Standardbibliothek: argparse, base64, json, os, sys, time, urllib).

## Vorgaben & Details
- **Aufruf:** `python3 tools/ton.py "Text" [--stimme STIMME] [--modell gemini-3.8-flash-tts] [--aus assets/name.wav]`
- **API-Schlüssel:** Ausschließlich aus der Umgebungsvariable `OPENAI_COMPAT_API_KEY` einlesen (kein Fallback auf andere Variablen). Wenn nicht gesetzt, mit Fehler abbrechen. Schlüssel niemals ausgeben.
- **Modell:** Standard `models/gemini-3.8-flash-tts` (wenn ohne `models/` übergeben, Präfix ergänzen analog zu `bild.py`).
- **Stimme:** Über Argument `--stimme` wählbar (z. B. Standardstimme `Puck` oder `Aoede` über `speechConfig`).
- **Gemini REST API Call:**
  - Endpoint: `https://generativelanguage.googleapis.com/v1beta/{modell}:generateContent`
  - Header: `Content-Type: application/json`, `x-goog-api-key: {OPENAI_COMPAT_API_KEY}`
  - Modalities: `AUDIO`
- **Ausgabe:**
  - Audio-Daten aus `candidates[].content.parts[].inlineData.data` dekodieren und als WAV-Datei speichern.
  - Standardpfad: `assets/ton-%Y%m%d-%H%M%S.wav` (Verzeichnis bei Bedarf erstellen).
  - Konsolenausgabe: `TON: <Dateipfad>`.

## Dateien
- `tools/ton.py` (neu anlegen, ausführbar machen)

## Abnahmekriterien
1. `tools/ton.py` existiert, ist ausführbar und benötigt keine Drittpakete (nur Python 3 Standardbibliothek).
2. Liest den Schlüssel strikt und nur aus `OPENAI_COMPAT_API_KEY`.
3. Akzeptiert Eingabetext sowie optionale Parameter `--stimme`, `--modell`, `--aus`.
4. Speichert Audio zuverlässig als WAV unter `assets/` und gibt `TON: <Pfad>` aus.
5. Fehlerbehandlung analog zu `tools/bild.py` (fehlender Key, HTTP-Fehler, keine Audiodaten).
