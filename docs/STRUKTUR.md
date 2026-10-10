# Projektstruktur: agentic-hack-google

Vorgeschlagene Ordnerstruktur für das Hackathon-Projekt und Aufgabenbereiche der Agenten.

## Übersicht

```
agentic-hack-google/
├── .gitignore               # Ignorierte Dateien und temporäre Artefakte
├── README.md                # Projektübersicht und Schnellstart
├── AGENTEN.md               # Übersicht der Agenten, Modelle und Rollen
├── auftraege/               # Spezifische Arbeitsaufträge und Prompts für Agenten
│   └── claude-*.md          # Aufgabenbeschreibungen
├── docs/                    # Projektdokumentation und Spezifikationen
│   ├── STRUKTUR.md          # Diese Strukturübersicht
│   ├── IDEE.md              # Projektidee und Vision
│   └── HACKATHON.md         # Rahmenbedingungen, Zeitplan und Ziele
├── tools/                   # CLI-Werkzeuge und Hilfsskripte (Python-Standardbibliothek)
│   ├── bild.py              # Bildgenerierung via Gemini (Nano Banana)
│   └── ton.py               # Audio-/TTS-Synthese via Gemini
├── assets/                  # Mediendateien, generierte Artefakte und Testdaten
│   ├── bilder/              # Generierte oder bereitgestellte Bilddaten
│   └── audio/               # Generierte Sprach- und Tondateien
├── src/                     # Hauptquellcode / Kernlogik des Projekts
│   ├── api/                 # Schnittstellen und API-Clients
│   ├── core/                # Anwendungslogik und Agenten-Pipeline
│   └── ui/                  # Benutzeroberfläche (CLI, Web oder Streamlit)
└── tests/                   # Automatisierte Tests und Integrationsprüfungen
```

## Verzeichnisse und Zweck

### 1. `auftraege/`
- **Zweck:** Definierte Arbeitsaufträge für autonome Agenten (z. B. hack-bau1, hack-visual, externe LLMs).
- **Inhalt:** Markdown-Dateien mit Zielen, Vorgaben, Modellen und Akzeptanzkriterien.

### 2. `docs/`
- **Zweck:** Zentrale Dokumentation für Mensch und Agenten.
- **Inhalt:** Architekturpläne, Konzeptdokumente (`IDEE.md`), Hackathon-Vorgaben (`HACKATHON.md`) und Konventionen.

### 3. `tools/`
- **Zweck:** Schlanke, eigenständige CLI-Skripte zur Interaktion mit APIs (z. B. Gemini-REST-Endpoints).
- **Konvention:** Nur Python-Standardbibliothek (keine externen Pakete wie `requests`), API-Keys strikt aus Umgebungsvariablen (`GEMINI_API_KEY` / `OPENAI_COMPAT_API_KEY`), Schlüssel niemals ausgeben.

### 4. `assets/`
- **Zweck:** Ablage für Eingabe- und Ausgabemedien.
- **Inhalt:** Logos, Referenzbilder, generierte Bilder (`assets/*.png`, `assets/*.jpg`) und Sprachdateien (`assets/*.wav`).

### 5. `src/` (Vorbereitung)
- **Zweck:** Modulare Kernanwendung, falls das Projekt über eigenständige Werkzeuge hinauswächst.
- **Konvention:** Saubere Trennung von Schnittstellen, Agenten-Orchestrierung und Ausgabe.

### 6. `tests/` (Vorbereitung)
- **Zweck:** Unit- und Integrationstests zur Validierung von Werkzeugen und Workflows.
