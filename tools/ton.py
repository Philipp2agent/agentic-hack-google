#!/usr/bin/env python3
"""Sprache aus Text per Gemini TTS. Schluessel nur aus OPENAI_COMPAT_API_KEY, wird nie ausgegeben.
Aufruf: python3 tools/ton.py "Text" [--stimme Puck] [--modell models/gemini-3.8-flash-tts] [--aus assets/name.wav]
Stimmen z. B.: Puck (Standard), Aoede, Kore, Charon, Fenrir"""
import argparse, base64, json, os, re, sys, time, urllib.error, urllib.request, wave
p = argparse.ArgumentParser(); p.add_argument("text")
p.add_argument("--stimme", default="Puck"); p.add_argument("--modell", default="models/gemini-3.8-flash-tts")
p.add_argument("--aus", default=None); a = p.parse_args()
key = os.environ.get("OPENAI_COMPAT_API_KEY")
if not key: sys.exit("FEHLER: kein Schluessel in OPENAI_COMPAT_API_KEY")
m = a.modell if a.modell.startswith("models/") else "models/" + a.modell
body = {"contents": [{"parts": [{"text": a.text}]}], "generationConfig": {"responseModalities": ["AUDIO"],
        "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": a.stimme}}}}}
req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/{m}:generateContent", data=json.dumps(body).encode(),
                             headers={"Content-Type": "application/json", "x-goog-api-key": key})
try: d = json.load(urllib.request.urlopen(req, timeout=180))
except urllib.error.HTTPError as e: sys.exit(f"FEHLER HTTP {e.code}: {e.read().decode()[:400]}")
pcm, mime = b"", ""
for c in d.get("candidates", []):
    for pt in c.get("content", {}).get("parts", []):
        inl = pt.get("inlineData") or pt.get("inline_data")
        if inl: pcm += base64.b64decode(inl["data"]); mime = mime or inl.get("mimeType") or inl.get("mime_type") or ""
        elif pt.get("text"): print("TEXT:", pt["text"][:300])
if not pcm: sys.exit("FEHLER: keine Audiodaten: " + json.dumps(d)[:400])
f = os.path.splitext(a.aus or f"assets/ton-{time.strftime('%Y%m%d-%H%M%S')}")[0] + ".wav"
os.makedirs(os.path.dirname(f) or ".", exist_ok=True)
if pcm[:4] == b"RIFF": open(f, "wb").write(pcm)  # bereits WAV
else:  # Gemini liefert rohes PCM (audio/L16;rate=24000), 16 Bit mono -> WAV-Kopf ergaenzen
    rate = int((re.search(r"rate=(\d+)", mime) or [0, 24000])[1])
    with wave.open(f, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate); w.writeframes(pcm)
print("TON:", f)
