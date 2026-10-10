# Video 2 Visual Assets (S-VISUAL)

Dieses Dokument spezifiziert die visuellen Grafiken für **Video 2** ("Hands-Free Repo Triage", 120 Sekunden Sprint bis 18:20) gemäß Auftrag `S-VISUAL`. Alle Assets liegen versioniert unter `assets/brand/` bereit.

---

## 1. Übersicht der Video-2 Assets

| Datei | Zweck & Szene | Format | Modell / Tool | Kern-Inhalt |
|---|---|---|---|---|
| `assets/brand/video2_title.jpg` | **Titelkarte (Intro/Start)**<br>Optional bei 0:00 oder Titel-Overlay | 16:9 (1376×768)<br>JPEG (>600 KB) | `models/gemini-3.1-flash-image`<br>via `tools/bild.py` | Minimalistisches Dark-Theme (#05070c / Deep Navy), leuchtender Horizont, Smart-Glasses-Kontur, vorbereitet für endgültigen Produktnamen / Logo |
| `assets/brand/video2_outro.jpg` | **Abspann (Outro)**<br>Phase 4 (1:52 – 2:00) | 16:9 (1376×768)<br>JPEG (>600 KB) | `models/gemini-3.1-flash-image`<br>via `tools/bild.py` | **URL:** `https://github.com/Philipp2agent/agentic-hack-google`<br>**Credits:** *"Built in one afternoon by 8 Gemini agents + Claude"*<br>**Call-to-Action:** *"Try it on your own repo in 3 minutes"* |

---

## 2. Einbindung im Video-2 Schnitt (`docs/VIDEO_SCRIPT_V2.md`)

1. **Titelkarte (`video2_title.jpg`):**
   - Einsatz am Anfang des Videos oder als Titel-Thumbnail für YouTube / Devpost.
   - Neutral gehalten, damit Philipps finaler Produktname (PromptMe / DawnDispatch / Dispatch) als Text-Layer oder Logo nahtlos überlagert werden kann.

2. **Abspannkarte (`video2_outro.jpg`):**
   - Einsatz in **Phase 4** (Timecode 1:52 bis 2:00) nach dem Terminal-Screencast (`./setup.sh` -> `./start.sh`).
   - Gestochen scharfer visueller Abschluss vor dem Fade-to-Black mit dem GitHub-Repository-Link und dem Hackathon-Team-Statement:
     > *"Built in one afternoon by 8 Gemini agents + Claude"*
     > *"Try it on your own repo in 3 minutes."*

---

## 3. Technische Validierung

Die Assets erfüllen alle Magic-Byte- und Größenkriterien:

```python
import os
files = ["assets/brand/video2_title.jpg", "assets/brand/video2_outro.jpg"]
for f in files:
    data = open(f, "rb").read(8)
    assert data.startswith(b"\xff\xd8"), f"{f}: ungültige JPEG Magic Bytes"
    assert os.path.getsize(f) > 50_000, f"{f}: Datei zu klein (<50 KB)"
print("Video-2 Visuals OK")
```
