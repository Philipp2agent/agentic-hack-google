# DawnDispatch Visual Assets & Brand Guide

Dieses Dokument spezifiziert die visuellen Brand-Assets für DawnDispatch gemäß Auftrag `gemini-04` (P-VISUAL). Alle Assets liegen versioniert in `assets/brand/` bereit und erfüllen die formalen Prüfkriterien für Magic Bytes (`b"\xff\xd8"` für JPEG, `b"\x89PNG"` für PNG) und Mindestdateigrößen (> 8 KB).

## 1. Übersicht der Brand-Assets

| Datei | Zweck | Modell | Prompt (Kurzform) | Entwurf / Finale |
|---|---|---|---|---|
| `assets/brand/hero_banner.jpg` | Dashboard-Header (16:9 Hero Banner) | `models/gemini-3-pro-image` | "Dawn over Zurich: lone engineer with smart glasses at sunrise, luminous swarm of bee agents to laptop desk, warm dawn light" | Finale (basiert auf `assets/titelbild-v3.jpg`) |
| `assets/brand/call_avatar.png` | Avatar für "Incoming call · DawnDispatch Agent" (1:1) | `models/gemini-3.1-flash-image` | "friendly abstract AI dispatcher avatar, glowing sunrise disc with soft sound-wave ring, dark blue background, flat vector" | Finale |
| `assets/brand/app_icon.png` | Favicon / App-Icon (1:1, optimiert für 32px) | `models/gemini-3.1-flash-image` | "sunrise on horizon with sound wave and glasses contour, strong contrasts, dark blue & gold, clean vector" | Finale |
| `assets/brand/system_flow.jpg` | Architektur-Flow für Pitch & Video (16:9) | `models/gemini-3-pro-image` | "isometric architecture system flow diagram: Ray-Ban glasses -> phone call -> gradbot Gradium STT/TTS -> Gemini Flash -> action engine -> dashboard" | Finale |
| `assets/brand/icons/agent.png` | Knowledge Graph Node: `agent` (Biene/Drohne) | `models/gemini-2.5-flash-image` | "minimal flat icon, single golden yellow accent on dark circle, bee drone agent icon, no text, PNG format" | Finale |
| `assets/brand/icons/event.png` | Knowledge Graph Node: `event` (Commit-Knoten) | `models/gemini-2.5-flash-image` | "minimal flat icon, single golden yellow accent on dark circle, git commit node branch icon, no text, PNG format" | Finale |
| `assets/brand/icons/agenda.png` | Knowledge Graph Node: `agenda` (Sprechblase mit ?) | `models/gemini-2.5-flash-image` | "minimal flat icon, single golden yellow accent on dark circle, speech bubble with question mark icon, no text, PNG format" | Finale |
| `assets/brand/icons/decision.png` | Knowledge Graph Node: `decision` (Häkchen-Siegel) | `models/gemini-2.5-flash-image` | "minimal flat icon, single golden yellow accent on dark circle, approved checkmark seal icon, no text, PNG format" | Finale |
| `assets/brand/icons/action.png` | Knowledge Graph Node: `action` (Zahnrad / Blitz) | `models/gemini-2.5-flash-image` | "minimal flat icon, single golden yellow accent on dark circle, gear cog lightning bolt action icon, no text, PNG format" | Finale |
| `assets/brand/icons/checkpoint.png` | Knowledge Graph Node: `checkpoint` (Stop / Schloss) | `models/gemini-2.5-flash-image` | "minimal flat icon, single golden yellow accent on dark circle, hand stop shield lock checkpoint icon, no text, PNG format" | Finale |

## 2. Einbau-Hinweise für Frontend (`hack-bau2` & `hack-bau3`)

Die Assets sind vertraglich fixiert und direkt über Pfade relative zur Repository-Wurzel bzw. statische Web-Mounts (`/assets/brand/...`) referenzierbar:

1. **Dashboard Header (`hack-bau3`):**
   ```html
   <img src="/assets/brand/hero_banner.jpg" alt="DawnDispatch Hero Banner" class="hero-banner" />
   ```
2. **Favicon / Browser-Tab (`hack-bau2` & `hack-bau3`):**
   ```html
   <link rel="icon" type="image/png" href="/assets/brand/app_icon.png" />
   ```
3. **Incoming Call Screen (`hack-bau2`):**
   ```html
   <img src="/assets/brand/call_avatar.png" alt="DawnDispatch Dispatcher" class="call-avatar" />
   ```
4. **Knowledge Graph Visualisierung (`hack-bau3`):**
   ```javascript
   const nodeIcons = {
     agent: "/assets/brand/icons/agent.png",
     event: "/assets/brand/icons/event.png",
     agenda: "/assets/brand/icons/agenda.png",
     decision: "/assets/brand/icons/decision.png",
     action: "/assets/brand/icons/action.png",
     checkpoint: "/assets/brand/icons/checkpoint.png"
   };
   ```
5. **Pitch & Präsentation ("Architecture"-Folie / Video):**
   `/assets/brand/system_flow.jpg` als zentrale 16:9 Übersichtsgrafik für den Datenfluss von Ray-Ban Glasses über Gradium Voice bis zum Dashboard Human-Checkpoint.

## 3. Modell-Nutzung & API-Quota

| Modell | Aufrufe | Verwendung |
|---|---|---|
| `models/gemini-3-pro-image` | 2 | Finale für `hero_banner.jpg` und `system_flow.jpg` (Limit: 250/Tag) |
| `models/gemini-3.1-flash-image` | 4 | Entwürfe / Finale für `call_avatar.png`, `app_icon.png` |
| `models/gemini-2.5-flash-image` | 7 | Einheitliches 6er-Icon-Set in PNG-Format (`icons/*.png`) |

## 4. Validierung

Die Assets werden mit folgendem Skript automatisiert geprüft:
```bash
python3 - <<'PY'
import os
need = {"assets/brand/hero_banner.jpg": b"\xff\xd8", "assets/brand/system_flow.jpg": b"\xff\xd8",
        "assets/brand/call_avatar.png": b"\x89PNG", "assets/brand/app_icon.png": b"\x89PNG"}
need.update({f"assets/brand/icons/{k}.png": b"\x89PNG" for k in ("agent","event","agenda","decision","action","checkpoint")})
for f, magic in need.items():
    b = open(f, "rb").read(8); assert b.startswith(magic), f"{f}: wrong format"; assert os.path.getsize(f) > 8_000, f"{f}: too small"
print("assets ok"); assert "hero_banner" in open("docs/VISUALS.md").read()
PY
```
