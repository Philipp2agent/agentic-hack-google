#!/usr/bin/env python3
"""Video with sound from Gemini Omni (gemini-omni-1.1-flash) via google-genai generate_content.

Same pattern as tools/bild.py and tools/ton.py: ask for inline media parts and save them. Key only from
GEMINI_API_KEY (or OPENAI_COMPAT_API_KEY). Without a key or with --dry-run the request is only printed.

Usage:
  python -m tools.video.omni --scene 2 --dry-run
  python -m tools.video.omni "..." --modalities VIDEO,AUDIO --out assets/video/scene2
  python -m tools.video.omni --scene 4 --ref assets/titelbild-v3.jpg      # reference image as input part

The Omni API surface is new; if the model rejects the modalities, the error names the accepted ones -
adjust --modalities (e.g. VIDEO or AUDIO,TEXT) and rerun.
"""
from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from tools.video.scenes import add_scene_args, resolve_prompt  # noqa: E402

DEFAULT_MODEL = "gemini-omni-1.1-flash"
EXT = {"video/mp4": ".mp4", "video/webm": ".webm", "audio/wav": ".wav", "audio/mpeg": ".mp3", "audio/ogg": ".ogg",
       "image/png": ".png", "image/jpeg": ".jpg"}


def get_key() -> str | None:
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_COMPAT_API_KEY")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_scene_args(p)
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--modalities", default="VIDEO,AUDIO", help="comma list of response modalities")
    p.add_argument("--ref", action="append", default=[], help="reference image/audio file(s) as input parts")
    p.add_argument("--out", default=None, help="output base path without extension (default assets/video/omni-<timestamp>)")
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args()

    prompt = resolve_prompt(a)
    modalities = [m.strip().upper() for m in a.modalities.split(",") if m.strip()]
    base = pathlib.Path(a.out or f"assets/video/omni-{time.strftime('%Y%m%d-%H%M%S')}")
    request = {"model": a.model, "prompt": prompt, "response_modalities": modalities, "refs": a.ref, "out": str(base)}
    key = get_key()
    if a.dry_run or not key:
        why = "--dry-run" if a.dry_run else "no GEMINI_API_KEY in the environment"
        print(f"DRY-RUN ({why}); request that would be sent:")
        print(json.dumps(request, indent=2, ensure_ascii=False))
        return 0

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=key)
    parts = [types.Part.from_text(text=prompt)]
    for r in a.ref:
        mime = mimetypes.guess_type(r)[0] or "application/octet-stream"
        parts.append(types.Part.from_bytes(data=pathlib.Path(r).read_bytes(), mime_type=mime))
    print(f"OMNI: model={a.model} modalities={modalities}")
    resp = client.models.generate_content(
        model=a.model,
        contents=[types.Content(role="user", parts=parts)],
        config=types.GenerateContentConfig(response_modalities=modalities),
    )
    base.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    for cand in resp.candidates or []:
        for part in (cand.content.parts if cand.content else []) or []:
            inline = getattr(part, "inline_data", None)
            if inline and inline.data:
                mime = inline.mime_type or "application/octet-stream"
                data = inline.data if isinstance(inline.data, (bytes, bytearray)) else base64.b64decode(inline.data)
                f = base.with_name(base.name + ("" if n == 0 else f"-{n}")).with_suffix(EXT.get(mime.split(";")[0], ".bin"))
                f.write_bytes(data)
                n += 1
                print("MEDIA:", f, mime)
            elif getattr(part, "text", None):
                print("TEXT:", part.text[:300])
    if n == 0:
        print("ERROR: no media in the response", file=sys.stderr)
        return 4
    return 0


if __name__ == "__main__":
    sys.exit(main())
