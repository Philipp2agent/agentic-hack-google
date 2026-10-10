"""Prompt interface for the 2-minute DawnDispatch video (scenes from IDEE.md section 2).

Usage:  python -m tools.video.scenes            # list scenes
        python -m tools.video.scenes 2 --extra "golden morning light"   # print the full prompt
"""
from __future__ import annotations

import argparse
import textwrap

STYLE = (
    "Cinematic, realistic, 16:9, shallow depth of field, early morning light, calm and precise. "
    "No on-screen text, no logos, no captions."
)

SCENES: dict[str, dict[str, str]] = {
    "1": {
        "title": "Walk and call (0:00-0:20)",
        "prompt": (
            "A young tech lead walks through a quiet European city street at dawn wearing smart glasses. "
            "He taps the temple of the glasses to accept a call; a phone in his hand shows a dark call screen "
            "with a single green button. He nods and keeps walking, listening."
        ),
        "audio": "Soft city ambience, footsteps, a short call chime, a calm synthetic voice saying 'Good morning. How much time do you have?'",
    },
    "2": {
        "title": "Rapid fire decisions (0:20-0:50)",
        "prompt": (
            "Close-up of the same man walking faster, answering short questions with quick 'yes' and 'no' while "
            "crossing a bridge. Subtle motion, confident, hands-free. The glasses glint in the sun."
        ),
        "audio": "Brisk voice cadence, short yes/no answers, light wind, a soft confirmation tone after each answer.",
    },
    "3": {
        "title": "Laptop reveal (0:50-1:40)",
        "prompt": (
            "He arrives at a desk, opens a laptop. On the screen a dark mission-control dashboard with a glowing "
            "knowledge graph: red and yellow nodes turn green one by one, new violet nodes grow, a large amber "
            "button pulses waiting for a click. He clicks it and leans back."
        ),
        "audio": "Keyboard tap, a satisfying click, a rising synth pad as the graph resolves.",
    },
    "4": {
        "title": "Architecture outro (1:40-2:00)",
        "prompt": (
            "Abstract animation: a voice waveform flows from smart glasses into a glowing engine that fans out "
            "into a network of agents working on code, then back into a clean dashboard. Minimal, elegant, dark."
        ),
        "audio": "Warm ambient music, no voice.",
    },
}


def build_prompt(scene: str, extra: str = "", with_audio: bool = True, style: str = STYLE) -> str:
    s = SCENES[scene]
    parts = [s["prompt"]]
    if with_audio:
        parts.append("Audio: " + s["audio"])
    if extra:
        parts.append(extra.strip())
    parts.append(style)
    return " ".join(parts)


def list_scenes() -> str:
    return "\n".join(f"{k}: {v['title']}\n   {textwrap.shorten(v['prompt'], 110)}" for k, v in SCENES.items())


def add_scene_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("prompt", nargs="?", help="free prompt; or use --scene")
    p.add_argument("--scene", choices=sorted(SCENES), help="scene number from IDEE.md video script")
    p.add_argument("--extra", default="", help="extra wording appended to the scene prompt")
    p.add_argument("--no-audio-hint", action="store_true", help="leave the audio description out of the prompt")


def resolve_prompt(a: argparse.Namespace) -> str:
    if a.scene:
        return build_prompt(a.scene, a.extra, with_audio=not a.no_audio_hint)
    if a.prompt:
        return a.prompt + (" " + a.extra if a.extra else "")
    raise SystemExit("ERROR: give a prompt or --scene N (see python -m tools.video.scenes)")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("scene", nargs="?", choices=sorted(SCENES))
    p.add_argument("--extra", default="")
    a = p.parse_args()
    print(build_prompt(a.scene, a.extra) if a.scene else list_scenes())
