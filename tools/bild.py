#!/usr/bin/env python3
"""Bild aus Text per Gemini (Nano Banana). Schluessel nur aus der Umgebung, wird nie ausgegeben.
Aufruf: python3 tools/bild.py "Prompt" [--modell models/gemini-3.1-flash-image] [--aus assets/name] [--ref eingabe.png ...]
Modelle: models/gemini-3.1-flash-image (Entwurf), models/gemini-nano-banana-2.1, models/gemini-3-pro-image (Finale, max 250/Tag)"""
import argparse, base64, json, mimetypes, os, sys, time, urllib.error, urllib.request
p = argparse.ArgumentParser(); p.add_argument("prompt")
p.add_argument("--modell", default="models/gemini-3.1-flash-image"); p.add_argument("--aus", default=None)
p.add_argument("--ref", action="append", default=[]); p.add_argument("--format", default=None); a = p.parse_args()
key = os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_COMPAT_API_KEY")
if not key: sys.exit("FEHLER: kein Schluessel in GEMINI_API_KEY oder OPENAI_COMPAT_API_KEY")
m = a.modell if a.modell.startswith("models/") else "models/" + a.modell
parts = [{"text": a.prompt}]
for r in a.ref:
    parts.append({"inline_data": {"mime_type": mimetypes.guess_type(r)[0] or "image/png", "data": base64.b64encode(open(r, "rb").read()).decode()}})
body = {"contents": [{"parts": parts}], "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]}}
if a.format: body["generationConfig"]["imageConfig"] = {"aspectRatio": a.format}
req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/{m}:generateContent", data=json.dumps(body).encode(),
                             headers={"Content-Type": "application/json", "x-goog-api-key": key})
try: d = json.load(urllib.request.urlopen(req, timeout=180))
except urllib.error.HTTPError as e: sys.exit(f"FEHLER HTTP {e.code}: {e.read().decode()[:400]}")
base = os.path.splitext(a.aus or f"assets/bild-{time.strftime('%Y%m%d-%H%M%S')}")[0]
os.makedirs(os.path.dirname(base) or ".", exist_ok=True); n = 0
for c in d.get("candidates", []):
    for pt in c.get("content", {}).get("parts", []):
        inl = pt.get("inlineData") or pt.get("inline_data")
        if inl:
            ext = ".jpg" if "jpeg" in (inl.get("mimeType") or inl.get("mime_type") or "") else ".png"
            f = base + ("" if n == 0 else f"-{n}") + ext; open(f, "wb").write(base64.b64decode(inl["data"])); n += 1; print("BILD:", f)
        elif pt.get("text"): print("TEXT:", pt["text"][:300])
if n == 0: sys.exit("FEHLER: keine Bilddaten: " + json.dumps(d)[:400])
