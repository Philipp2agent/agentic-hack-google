# Auftrag gemini-04 (P-VISUAL): Brand-Assets, Call-Avatar, Graph-Icons & Flow-Visualisierung

**Agent:** hack-visual · **Branch:** `agent/hack-visual` · **Baufenster:** bis 17:30 (Assets frueh liefern, damit bau2/bau3 sie einbauen koennen), Meldung bis 17:40, Feature-Freeze 18:00.
**Pflichtlektuere zuerst:** `IDEE.md` (Kern-Satz, Persona, Call-Screen, Graph), `docs/ARCHITEKTUR.md` Abschnitt 1 (Stationen fuer die Flow-Grafik), `tools/bild.py`.
Du arbeitest bereits an `assets/brand/`. Dieses Paket legt die endgueltigen Dateinamen fest (Vertrag mit bau2/bau3); was du schon hast, benennst du passend um.

## Ziel
Die visuelle Identitaet von DawnDispatch mit `tools/bild.py` (Nano Banana): Hero-Banner fuer das Dashboard, Avatar fuer den Incoming-Call-Screen, Icon-Set fuer die Knowledge-Graph-Knoten, App-Icon/Favicon, Architektur-Flow-Grafik fuer Pitch und Video – dokumentiert in `docs/VISUALS.md`.

## Vorgaben
- Entwuerfe mit `models/gemini-nano-banana-2.1` oder `models/gemini-3.1-flash-image` (max. 3 je Asset); Finale mit `models/gemini-3-pro-image` (max. 5 Finale insgesamt, Tageslimit 250). Schluessel nur aus der Umgebung, nie ausgeben.
- Stil-Referenz `assets/titelbild-v3.jpg` per `--ref` fuer Banner/Avatar/Flow; Farbwelt Morgendaemmerung (dunkelblau → orange/gold), klar, wenig Text. Prompts Englisch. Text im Bild nur "DawnDispatch", bei Fehlern ohne Text wiederholen.
- Seitenverhaeltnis: du darfst `tools/bild.py` um `--format` erweitern (fuegt `"imageConfig": {"aspectRatio": "16:9"}` in `generationConfig` ein; Standard unveraendert). Nur du aenderst `tools/bild.py`.
- `bild.py` waehlt die Endung nach Mime-Type. Vertragsnamen unten muessen zum Format passen: liefert die API fuer ein PNG-Ziel JPEG, nicht umbenennen, sondern erneut mit "flat icon, transparent background, PNG" prompten; bleibt es JPEG, echten Namen in VISUALS.md vermerken und @hack-bau3 informieren (das Frontend hat `onerror`-Fallbacks).

## Dateien (nur diese anlegen/aendern)
1. `assets/brand/hero_banner.jpg` – 16:9, Dashboard-Header: "Dawn over Zurich: a lone engineer walking with smart glasses at sunrise, a luminous swarm of small bee-like agents streaming from the skyline into a glowing laptop on a desk; cinematic warm dawn light, subtle UI glow, no text" (+ `--ref`). Finale pro-image.
2. `assets/brand/call_avatar.png` – 1:1, Avatar fuer "Incoming call · DawnDispatch Agent": "friendly abstract AI dispatcher avatar, glowing sunrise disc with a soft sound-wave ring, dark blue background, flat vector style, centered, no text".
3. `assets/brand/icons/agent.png`, `event.png`, `agenda.png`, `decision.png`, `action.png`, `checkpoint.png` – je 1:1, 256 px gedacht, flaches Icon-Set in einem Stil (eine Serie: "minimal flat icon, single color accent on dark circle, no text"): agent = Biene/Drohne, event = Commit-Knoten, agenda = Sprechblase mit Fragezeichen, decision = Haekchen-Siegel, action = Zahnrad/Blitz, checkpoint = Hand-Stop/Schloss. Drafts reichen (flash-image); nur einheitlich muss es sein.
4. `assets/brand/app_icon.png` – 1:1, Favicon/App-Icon: Sonne am Horizont + Schallwelle/Brillenbuegel, kraeftige Kontraste, lesbar bei 32 px, kein Text.
5. `assets/brand/system_flow.jpg` – 16:9, Pitch/Video: isometrische Flow-Grafik links→rechts mit genau diesen Stationen: "Ray-Ban glasses → phone showing an incoming call → gradbot + Gradium STT/TTS → Gemini 3.8 Flash → action engine + knowledge graph → laptop dashboard with a human checkpoint button"; Icons statt Fliesstext. Finale pro-image.
6. `docs/VISUALS.md` – Tabelle `Datei · Zweck · Modell · Prompt (Kurzform) · Entwuerfe/Finale`, Einbau-Hinweise (`/assets/brand/hero_banner.jpg` Dashboard-Header; `app_icon.png` als `<link rel="icon">`; `call_avatar.png` im Call-Screen; `icons/<kind>.png` im Graph; `system_flow.jpg` Pitch-Folie "Architecture"), Aufruf-Zaehler je Modell.
7. Optional `tools/bild.py` (`--format`). Entwuerfe nach `assets/brand/drafts/` (max. 8 Dateien) oder loeschen.

## Schritte
1. jetzt: merge main; Hero-Banner (2 Entwuerfe → 1 Finale) → **sofort pushen** und @hack-bau3 nennen (bis 16:50).
2. bis 17:05: `call_avatar.png` + `app_icon.png` → push, @hack-bau2 nennen.
3. bis 17:20: Icon-Set (6) → push, @hack-bau3 nennen.
4. bis 17:30: `system_flow.jpg`, `docs/VISUALS.md`, Drafts aufraeumen, push, Meldung @hack-chef.

## Abnahmekriterium
```bash
cd /home/buzzagent/hack/wt/hack-visual
python3 - <<'PY'
import os
need = {"assets/brand/hero_banner.jpg": b"\xff\xd8", "assets/brand/system_flow.jpg": b"\xff\xd8",
        "assets/brand/call_avatar.png": b"\x89PNG", "assets/brand/app_icon.png": b"\x89PNG"}
need.update({f"assets/brand/icons/{k}.png": b"\x89PNG" for k in ("agent","event","agenda","decision","action","checkpoint")})
for f, magic in need.items():
    b = open(f, "rb").read(8); assert b.startswith(magic), f"{f}: wrong format"; assert os.path.getsize(f) > 8_000, f"{f}: too small"
print("assets ok"); assert "hero_banner" in open("docs/VISUALS.md").read()
PY
git diff origin/main --stat
```
Erfuellt, wenn das Skript `assets ok` druckt, die Bilder zur Idee passen (Dawn, Brille, Schwarm, Call, Dashboard), `docs/VISUALS.md` vollstaendig ist und der Diff nur `assets/brand/*`, `docs/VISUALS.md` und optional `tools/bild.py` umfasst.

## Branch-Vorgabe
Nur `agent/hack-visual` (`git push -u origin agent/hack-visual`), nie `main`. Nicht anfassen: `src/*`, `tests/*`, `auftraege/*`, `STAND.md`, `README.md`.
