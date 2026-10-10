# Auftrag gemini-04: Visual Identity, Hero Banners & Dashboard Assets

**Agent:** hack-visual · **Branch:** `agent/hack-visual` · **Baufenster:** 16:15–17:30 (Assets frueh liefern, damit hack-bau3 sie einbauen kann), Meldung bis 17:40, Feature-Freeze 18:00.
**Pflichtlektuere zuerst:** `IDEE.md` (Kern-Satz, Persona), `docs/ARCHITEKTUR.md` Abschnitt 1 (Komponenten fuer die Flow-Grafik), `tools/bild.py`.

## Ziel
Erzeuge mit `tools/bild.py` (Nano Banana) die drei visuellen Assets von DawnDispatch – Hero-Banner fuer das Dashboard, Architektur-/Flow-Visualisierung fuer Pitch und Video, App-Icon/Favicon – und dokumentiere sie in `docs/VISUALS.md`.

## Vorgaben
- Entwuerfe mit `models/gemini-3.1-flash-image` (max. 3 pro Asset), Finale mit `models/gemini-3-pro-image` (max. 3 Finale insgesamt, Tageslimit 250). Schluessel nur aus der Umgebung, nie ausgeben.
- Stil-Referenz: `assets/titelbild-v3.jpg` (Kommandeur + Bienen-Schwarm-Agenten, Basstoene) per `--ref assets/titelbild-v3.jpg` mitgeben, damit die Marke konsistent bleibt. Farbwelt: Morgendaemmerung (dunkelblau → orange/gold), klar, modern, wenig Text.
- Prompts Englisch. Text im Bild nur, wenn kurz und noetig ("DawnDispatch"); Modelle schreiben Text unzuverlaessig – bei Fehlern Prompt ohne Text wiederholen.
- Seitenverhaeltnis: `bild.py` setzt keins. Du darfst `tools/bild.py` um ein Argument `--format` erweitern (fuegt `"imageConfig": {"aspectRatio": "16:9"}` in `generationConfig` ein; Standard unveraendert). Nur du aenderst `tools/bild.py`.
- Dateinamen sind Vertrag mit hack-bau3: `assets/hero_banner.jpg`, `assets/system_flow.jpg`, `assets/app_icon.png`. `bild.py` waehlt die Endung nach Mime-Type; liefert die API PNG statt JPG, Datei entsprechend umbenennen ist **nicht** erlaubt (kaputte Datei) → stattdessen die gelieferte Datei behalten **und** zusaetzlich eine Kopie unter dem Vertragsnamen nur dann anlegen, wenn das Format passt; sonst in VISUALS.md den echten Dateinamen vermerken und @hack-bau3 im Thread informieren.

## Dateien (nur diese anlegen/aendern)
1. `assets/hero_banner.jpg` – 16:9, Dashboard-Header: "Dawn over Zurich: a lone engineer walking with smart glasses at sunrise, a luminous swarm of small bee-like agents streaming from the city skyline into a glowing laptop on a desk; cinematic, warm dawn light, subtle UI glow, no text" (+ `--ref`). Finale mit pro-image.
2. `assets/system_flow.jpg` – 16:9, Pitch/Video: schematische Flow-Grafik mit genau diesen Stationen von links nach rechts: "Ray-Ban glasses → phone (web audio) → gradbot + Gradium STT/TTS → Gemini 3.8 Flash → action engine → laptop dashboard with a human checkpoint button"; isometrisch, klare Pfeile, Icons statt Fliesstext, dieselbe Farbwelt.
3. `assets/app_icon.png` – 1:1 quadratisch, flaches Icon: stilisierte Sonne am Horizont + Schallwelle/Brillenbuegel, kraeftige Kontraste, funktioniert bei 32 px; kein Text. Muss PNG sein (Favicon).
4. `docs/VISUALS.md` – Tabelle `Datei · Zweck · Modell · Prompt (Kurzform) · Entwuerfe/Finale`, Einbau-Hinweise (`/assets/hero_banner.jpg` im Dashboard-Header, `app_icon.png` als `<link rel="icon">`, `system_flow.jpg` fuer Pitch-Folie 4 "Architecture"), Token-/Kostenhinweis (Anzahl Aufrufe je Modell).
5. Optional `tools/bild.py` (`--format`).
Entwuerfe nach `assets/drafts/` (committen erlaubt, hoechstens 6 Dateien) oder nach der Auswahl loeschen.

## Schritte (Reihenfolge)
1. 16:15 merge main. Hero-Banner: 2 Entwuerfe flash-image → beste Variante 1× pro-image → `assets/hero_banner.jpg`. **Sofort pushen und @hack-bau3 im Thread nennen** (16:45).
2. 16:45 App-Icon (flash-image reicht, falls sauber; sonst 1× pro-image) → push.
3. 17:00 System-Flow (2 Entwuerfe, 1 Finale) → push.
4. 17:20 `docs/VISUALS.md`, Entwuerfe aufraeumen, push + Meldung @hack-chef.

## Abnahmekriterium
```bash
cd /home/buzzagent/hack/wt/hack-visual
ls -la assets/hero_banner.jpg assets/system_flow.jpg assets/app_icon.png docs/VISUALS.md
python3 - <<'PY'
import os
for f, magic in [("assets/hero_banner.jpg", b"\xff\xd8"), ("assets/system_flow.jpg", b"\xff\xd8"), ("assets/app_icon.png", b"\x89PNG")]:
    b = open(f, "rb").read(8); assert b.startswith(magic), f"{f}: wrong format"; assert os.path.getsize(f) > 20_000, f"{f}: too small"
print("assets ok")
PY
git log --oneline origin/main..HEAD | head && git diff origin/main --stat
```
Erfuellt, wenn das Skript `assets ok` druckt, alle drei Bilder zur Idee passen (Dawn, Brille, Schwarm, Dashboard), `docs/VISUALS.md` die Tabelle enthaelt und der Diff nur `assets/*`, `docs/VISUALS.md` und optional `tools/bild.py` umfasst.

## Branch-Vorgabe
Nur auf `agent/hack-visual` arbeiten und pushen (`git push -u origin agent/hack-visual`). Nie auf `main`. Nicht anfassen: `src/*`, `tests/*`, `auftraege/*`, `STAND.md`, `README.md`.
