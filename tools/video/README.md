# tools/video - Veo und Omni fuer das Pitch-/Demo-Video

Schluessel nur aus der Umgebung (`GEMINI_API_KEY`, ersatzweise `OPENAI_COMPAT_API_KEY`); ohne Schluessel laufen beide
Skripte automatisch als Dry-Run und drucken nur die Anfrage. Nichts wird je ausgegeben oder committet.

```bash
python -m tools.video.scenes                       # Szenen 1-4 aus IDEE.md (Video-Skript) auflisten
python -m tools.video.scenes 2 --extra "rain"      # fertigen Prompt fuer Szene 2 ansehen
python -m tools.video.veo  --scene 1 --dry-run     # Veo-Anfrage pruefen
python -m tools.video.veo  --scene 1 --out assets/video/scene1.mp4          # echter Lauf (2 RPM / 10 RPD!)
python -m tools.video.veo  --scene 3 --image assets/titelbild-v3.jpg        # Bild-zu-Video
python -m tools.video.omni --scene 2 --dry-run     # Omni (Video mit Ton) pruefen
python -m tools.video.omni --scene 4 --modalities VIDEO,AUDIO --out assets/video/scene4
```

- `scenes.py`: Prompt-Interface (Szene + Stil + Audio-Hinweis), auch fuer eigene Prompts (`"..." --extra`).
- `veo.py`: `client.models.generate_videos` + Polling der Operation, speichert MP4. Modell-ID per `--model` anpassbar.
- `omni.py`: `generate_content` mit `response_modalities`; speichert alle Inline-Medien. Modalitaeten per `--modalities`.
- Ausgaben landen unter `assets/video/` (nicht committen, bis sie final sind; Repo wird oeffentlich).
