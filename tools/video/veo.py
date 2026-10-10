#!/usr/bin/env python3
"""Text-to-video with Veo via google-genai. Key only from GEMINI_API_KEY (or OPENAI_COMPAT_API_KEY), never printed.

Usage:
  python -m tools.video.veo --scene 1 --dry-run
  python -m tools.video.veo "A tech lead walks at dawn..." --duration 8 --out assets/video/scene1.mp4
  python -m tools.video.veo --scene 3 --image assets/titelbild-v3.jpg      # image-to-video from a still

Dry-run is automatic when no key is set. Quota (docs/SETUP.md): Veo 3 Fast 2 RPM / 10 RPD - use sparingly.
Model ids change often; override with --model if the default is rejected (the error names the valid ones).
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from tools.video.scenes import add_scene_args, resolve_prompt  # noqa: E402

DEFAULT_MODEL = "veo-3.1-fast-generate-preview"


def get_key() -> str | None:
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_COMPAT_API_KEY")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_scene_args(p)
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--duration", type=int, default=8, help="seconds (Veo: 4-8)")
    p.add_argument("--aspect", default="16:9", choices=["16:9", "9:16"])
    p.add_argument("--resolution", default="720p", choices=["720p", "1080p"])
    p.add_argument("--image", help="optional still image to animate (image-to-video)")
    p.add_argument("--negative", default="text, captions, logos, watermark, blurry")
    p.add_argument("--no-audio", action="store_true", help="generate without audio")
    p.add_argument("--out", default=None, help="output .mp4 (default assets/video/veo-<timestamp>.mp4)")
    p.add_argument("--dry-run", action="store_true", help="print the request, do not call the API")
    p.add_argument("--poll", type=int, default=10, help="seconds between operation polls")
    p.add_argument("--timeout", type=int, default=600, help="max seconds to wait")
    a = p.parse_args()

    prompt = resolve_prompt(a)
    out = pathlib.Path(a.out or f"assets/video/veo-{time.strftime('%Y%m%d-%H%M%S')}.mp4")
    request = {
        "model": a.model,
        "prompt": prompt,
        "image": a.image,
        "config": {
            "duration_seconds": a.duration,
            "aspect_ratio": a.aspect,
            "resolution": a.resolution,
            "negative_prompt": a.negative,
            "generate_audio": not a.no_audio,
            "number_of_videos": 1,
        },
        "out": str(out),
    }
    key = get_key()
    if a.dry_run or not key:
        why = "--dry-run" if a.dry_run else "no GEMINI_API_KEY in the environment"
        print(f"DRY-RUN ({why}); request that would be sent:")
        print(json.dumps(request, indent=2, ensure_ascii=False))
        return 0

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=key)
    kwargs: dict = {}
    if a.image:
        kwargs["image"] = types.Image.from_file(location=a.image)
    print(f"VEO: model={a.model} duration={a.duration}s aspect={a.aspect}")
    op = client.models.generate_videos(
        model=a.model,
        prompt=prompt,
        config=types.GenerateVideosConfig(**request["config"]),
        **kwargs,
    )
    t0 = time.time()
    while not op.done:
        if time.time() - t0 > a.timeout:
            print("ERROR: timeout waiting for the video operation", file=sys.stderr)
            return 2
        time.sleep(a.poll)
        op = client.operations.get(op)
        print(f"  ... waiting ({int(time.time() - t0)}s)")
    if getattr(op, "error", None):
        print(f"ERROR: {op.error}", file=sys.stderr)
        return 3
    videos = (op.response.generated_videos if op.response else None) or []
    if not videos:
        print("ERROR: no video in the response", file=sys.stderr)
        return 4
    out.parent.mkdir(parents=True, exist_ok=True)
    video = videos[0].video
    client.files.download(file=video)
    video.save(str(out))
    print("VIDEO:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
