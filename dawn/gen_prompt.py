#!/usr/bin/env python3
"""DawnDispatch's own briefing: condense THIS repo's hackathon material into dawn/prompt.txt.

Reads context/hackathon-day.md, STAND.md, README.md and the src/data seeds from a git ref
(origin/main when the remote exists, else HEAD) and uses the shared Gemini + prompt logic
from dawn/from_repo.py. For any other repository use dawn/from_repo.py directly.

    python dawn/gen_prompt.py [--repo PATH] [--ref origin/main] [--name NAME]

Environment: GEMINI_API_KEY or LLM_API_KEY, LLM_BASE_URL, DAWN_PROMPT_MODEL, DAWN_USER_NAME.
"""
from __future__ import annotations

import argparse
import os
import pathlib
import subprocess
import sys

import from_repo  # run as a script from dawn/ (python dawn/gen_prompt.py)

FILES = [
    ("context/hackathon-day.md", 4000), ("STAND.md", 4000), ("README.md", 3000),
    ("src/data/agenda.json", 4000), ("src/data/knowledge_graph_before.json", 6000), ("src/data/overnight_events.json", 4000),
]


def pick_ref(repo: pathlib.Path, ref: str | None) -> str:
    if ref:
        return ref
    if from_repo.run_git(repo, "remote", "get-url", "origin").strip():
        subprocess.run(["git", "-C", str(repo), "fetch", "-q", "origin"], timeout=60, check=False)
        if from_repo.run_git(repo, "rev-parse", "--verify", "-q", "origin/main").strip():
            return "origin/main"
    return "HEAD"


def collect(repo: pathlib.Path, ref: str) -> str:
    return "\n\n".join(f"### {path}\n{from_repo.run_git(repo, 'show', f'{ref}:{path}', timeout=20)[:limit]}"
                       for path, limit in FILES)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Generate dawn/prompt.txt for the DawnDispatch repo itself.")
    ap.add_argument("--repo", default=os.environ.get("DAWN_REPO") or str(from_repo.ROOT))
    ap.add_argument("--ref", default=None, help="git ref to read from (default: origin/main if present, else HEAD)")
    ap.add_argument("--name", default=os.environ.get("DAWN_USER_NAME", "").strip() or "Philipp")
    ap.add_argument("--out", default=str(from_repo.PROMPT_PATH))
    args = ap.parse_args(argv)

    repo = from_repo.resolve_repo(args.repo)
    ref = pick_ref(repo, args.ref)
    raw = from_repo.ask_gemini(from_repo.ASK.format(name=args.name, context=collect(repo, ref)))
    try:
        text = from_repo.compose_prompt(from_repo.parse_sections(raw), args.name)
    except ValueError as exc:
        print(f"Could not build the prompt: {exc}", file=sys.stderr)
        return 2
    from_repo.write_prompt(text, pathlib.Path(args.out))
    lines = [l for l in text.splitlines() if l.strip()]
    print(f"Prompt neu: {len(text.split())} Woerter ({ref}) | Eroeffnung: {lines[-1][:200]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
