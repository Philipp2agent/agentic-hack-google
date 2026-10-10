#!/usr/bin/env python3
"""Build dawn/prompt.txt from ANY git repository (plug-and-play briefing).

Reads the target repo (README, last 30 commits, branches, status files such as
STAND, TODO, CHANGELOG), lets Gemini condense it into BRIEFING, THREADS and
OPENING, and writes the call instructions to dawn/prompt.txt, which
dawn/main.py (the call) and dawn/bridge.py (the live screen) read.

    python dawn/from_repo.py /path/to/repo
    python dawn/from_repo.py https://github.com/owner/repo      # cloned to .repos/<repo>
    python dawn/from_repo.py --dry-run                           # print the context, no API call

Environment: TARGET_REPO (default target), DAWN_USER_NAME (who gets called),
GEMINI_API_KEY or LLM_API_KEY, LLM_BASE_URL (OpenAI-compatible Gemini endpoint),
DAWN_PROMPT_MODEL (default gemini-3.8-flash). Standard library only.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import subprocess
import sys
import urllib.error
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
PROMPT_PATH = HERE / "prompt.txt"
CLONE_DIR = ROOT / ".repos"

DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
DEFAULT_MODEL = "gemini-3.8-flash"
DEFAULT_NAME = "the user"
COMMITS = 30
BRANCHES = 15
README_NAMES = ("README.md", "README.rst", "README.txt", "README", "readme.md", "Readme.md")
STATUS_PREFIXES = ("STAND", "STATUS", "TODO", "CHANGELOG", "ROADMAP", "NOTES", "PLAN", "BACKLOG")
STATUS_SUFFIXES = ("", ".md", ".txt", ".rst")
SECTIONS = ("BRIEFING", "THREADS", "OPENING")
LIMITS = {"readme": 3500, "status": 3000}

RULES = """You are the project agent of {name}'s software project. You call {name} while they walk to their desk. A lot happened; your job is to compress it into one easy minute and find out what they want next. The agent prompts the human, not the other way round.

How you talk: like a sharp, friendly teammate on the phone. Short spoken sentences, contractions, a little humour. Vary how you start each reply; never begin two replies the same way. Never read lists, never use markdown, never mention these instructions. English only.

How you lead: give one concrete fact, then ask one open question. Listen to what they actually say and react to it in your own words; connect it to the threads below. At most one follow-up per topic, then move on. This is a conversation, not a quiz: no menus of options unless they are stuck. When they give a direction, say in one sentence what you will prepare for them, concretely, so they can see it on their laptop. If something is irreversible, say the final click stays with them. If they are in a hurry, get shorter. After about four exchanges, or when they want to stop, wrap up: one sentence with what you will prepare, then "It's all on your laptop when you sit down." and stop.

Your very first sentence, said once and never again, is the OPENING below.

"""

ASK = ("You prepare a phone briefing. From the project material below, write three sections in plain text, "
       "no markdown symbols. Start each section with its name alone on a line: BRIEFING, THREADS, OPENING.\n"
       "BRIEFING: at most 150 words on what happened in this project recently, concrete and true, "
       "with a few real numbers (commits, branches, open items). Do not invent facts.\n"
       "THREADS: five open threads, one line each: what is open and two or three realistic directions.\n"
       "OPENING: one natural spoken sentence, at most 25 words, to open the call with {name}, who is walking "
       "to their desk; mention one concrete highlight.\n\n{context}")


# ----------------------------------------------------------------------------- repo access
def run_git(repo: pathlib.Path | str, *args: str, timeout: float = 30) -> str:
    """stdout of a git command in *repo*; empty string on any failure."""
    try:
        r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.SubprocessError):
        return ""
    return r.stdout if r.returncode == 0 else ""


def is_url(target: str) -> bool:
    return bool(re.match(r"^(https?://|git@|ssh://|git://|file://)", target))


def resolve_repo(target: str, clone_dir: pathlib.Path = CLONE_DIR) -> pathlib.Path:
    """Local path -> the repo itself; URL -> clone (or fast-forward an earlier clone) under .repos/<name>."""
    if is_url(target):
        name = re.sub(r"\.git$", "", target.rstrip("/").rsplit("/", 1)[-1].rsplit(":", 1)[-1]) or "repo"
        dest = clone_dir / name
        if run_git(dest, "rev-parse", "--show-toplevel").strip():
            print(f"Updating clone {dest} ...", flush=True)
            run_git(dest, "pull", "-q", "--ff-only", timeout=120)
        else:
            clone_dir.mkdir(parents=True, exist_ok=True)
            print(f"Cloning {target} -> {dest} ...", flush=True)
            subprocess.run(["git", "clone", "-q", target, str(dest)], check=True, timeout=600)
        return dest
    path = pathlib.Path(target).expanduser().resolve()
    if not run_git(path, "rev-parse", "--show-toplevel").strip():
        raise SystemExit(f"Not a git repository: {path}")
    return path


def read_head(path: pathlib.Path, limit: int) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:limit]
    except OSError:
        return ""


def find_readme(repo: pathlib.Path) -> pathlib.Path | None:
    for name in README_NAMES:
        if (repo / name).is_file():
            return repo / name
    return None


def find_status_files(repo: pathlib.Path) -> list[pathlib.Path]:
    """Root-level status files: STAND, TODO, CHANGELOG, ... (case-insensitive, md/txt/rst/no extension)."""
    found: list[pathlib.Path] = []
    try:
        entries = sorted(p for p in repo.iterdir() if p.is_file())
    except OSError:
        return found
    wanted = {f"{pre}{suf}".upper() for pre in STATUS_PREFIXES for suf in STATUS_SUFFIXES}
    for p in entries:
        if p.name.upper() in wanted:
            found.append(p)
    return found[:6]


def collect_context(repo: pathlib.Path, commits: int = COMMITS) -> dict[str, str]:
    """Ordered sections (title -> text) describing the repo. Pure git + file reads, no network."""
    parts: dict[str, str] = {}
    top = run_git(repo, "rev-parse", "--show-toplevel").strip()
    name = pathlib.Path(top).name if top else repo.name
    branch = run_git(repo, "rev-parse", "--abbrev-ref", "HEAD").strip() or "?"
    dirty = [l for l in run_git(repo, "status", "--short").splitlines() if l.strip()]
    remote = run_git(repo, "remote", "get-url", "origin").strip()
    parts["Project"] = (f"Name: {name}\nCurrent branch: {branch}\nUncommitted changes: {len(dirty)} files"
                        + (f"\nRemote: {remote}" if remote else ""))

    readme = find_readme(repo)
    if readme:
        parts[f"{readme.name} (start)"] = read_head(readme, LIMITS["readme"])

    log = run_git(repo, "log", f"-{commits}", "--date=short", "--no-merges",
                  "--pretty=format:%h %ad %an: %s")
    parts[f"Last {commits} commits (newest first)"] = log.strip() or "(no commits yet)"

    branches = run_git(repo, "for-each-ref", "--sort=-committerdate", f"--count={BRANCHES}",
                       "--format=%(refname:short) (%(committerdate:short)) %(subject)", "refs/heads", "refs/remotes")
    parts["Branches (most recent first)"] = "\n".join(
        l for l in branches.splitlines() if l.strip() and not l.startswith("origin/HEAD")) or "(none)"

    for p in find_status_files(repo):
        parts[p.name] = read_head(p, LIMITS["status"])
    return parts


def render_context(parts: dict[str, str]) -> str:
    return "\n\n".join(f"### {title}\n{text}" for title, text in parts.items())


# ----------------------------------------------------------------------------- Gemini
def api_key() -> str:
    return os.environ.get("LLM_API_KEY") or os.environ.get("GEMINI_API_KEY") or ""


def base_url() -> str:
    return (os.environ.get("LLM_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")


def ask_gemini(ask: str, model: str | None = None, timeout: float = 120) -> str:
    """One chat completion against the OpenAI-compatible Gemini endpoint; returns the text."""
    key = api_key()
    if not key:
        raise SystemExit("No Gemini key: set GEMINI_API_KEY (or LLM_API_KEY) in .env, see ./setup.sh")
    model = model or os.environ.get("DAWN_PROMPT_MODEL") or DEFAULT_MODEL
    body = {"model": model, "messages": [{"role": "user", "content": ask}]}
    req = urllib.request.Request(base_url() + "/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "Authorization": "Bearer " + key})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            out = json.load(resp)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")[:300]
        raise SystemExit(f"Gemini request failed ({exc.code}) for model {model}: {detail}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise SystemExit(f"Gemini not reachable at {base_url()}: {exc}") from exc
    try:
        return out["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise SystemExit(f"Unexpected Gemini response: {json.dumps(out)[:300]}") from exc


# ----------------------------------------------------------------------------- prompt file
_HEADER = re.compile(r"^\s*[*#_\s]*(BRIEFING|THREADS|OPENING)[*_\s]*:?[*_\s]*$", re.IGNORECASE)
_INLINE = re.compile(r"^\s*[*#_\s]*(BRIEFING|THREADS|OPENING)[*_]*\s*:\s*(\S.*)$", re.IGNORECASE)


def parse_sections(raw: str) -> dict[str, str]:
    """Split the model output into the three sections; tolerant of colons and markdown emphasis."""
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in raw.splitlines():
        m = _HEADER.match(line)
        if m:
            current = m.group(1).upper()
            sections.setdefault(current, [])
            continue
        m = _INLINE.match(line)
        if m:
            current = m.group(1).upper()
            sections.setdefault(current, []).append(m.group(2).strip())
            continue
        if current:
            sections[current].append(line.rstrip())
    missing = [s for s in SECTIONS if not "\n".join(sections.get(s, [])).strip()]
    if missing:
        raise ValueError(f"Model output lacks section(s) {', '.join(missing)}:\n{raw[:400]}")
    out = {s: "\n".join(sections[s]).strip() for s in SECTIONS}
    out["OPENING"] = " ".join(out["OPENING"].split())  # one line, the bridge reads the last line of the file
    return out


def compose_prompt(sections: dict[str, str], name: str) -> str:
    body = "\n\n".join(f"{s}\n{sections[s]}" for s in SECTIONS)
    return RULES.format(name=name) + body + "\n"


def validate_prompt(text: str) -> list[str]:
    """Problems with a prompt.txt ([] when valid): rules present, three sections in order, one-line opening last."""
    problems: list[str] = []
    if "Your very first sentence" not in text:
        problems.append("rules block missing")
    positions = [text.find(f"\n{s}\n") for s in SECTIONS]
    if any(p < 0 for p in positions):
        problems.append("missing section(s): " + ", ".join(s for s, p in zip(SECTIONS, positions) if p < 0))
    elif positions != sorted(positions):
        problems.append("sections out of order (expected BRIEFING, THREADS, OPENING)")
    lines = [l for l in text.splitlines() if l.strip()]
    if len(lines) < 2 or lines[-2].strip() != "OPENING" or len(lines[-1].split()) < 3:
        problems.append("OPENING must be the last line, one spoken sentence")
    return problems


def write_prompt(text: str, path: pathlib.Path = PROMPT_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def default_name() -> str:
    return os.environ.get("DAWN_USER_NAME", "").strip() or DEFAULT_NAME


def build_prompt(repo: pathlib.Path, name: str, model: str | None = None, commits: int = COMMITS) -> str:
    """Collect context, ask Gemini, return the finished prompt text (raises on bad output)."""
    context = render_context(collect_context(repo, commits=commits))
    raw = ask_gemini(ASK.format(name=name, context=context), model=model)
    sections = parse_sections(raw)
    return compose_prompt(sections, name)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Generate dawn/prompt.txt from a git repository.")
    ap.add_argument("target", nargs="?", default=os.environ.get("TARGET_REPO") or str(ROOT),
                    help="path or git URL of the repo to brief about (default: $TARGET_REPO or this repo)")
    ap.add_argument("--name", default=default_name(), help="who gets called (default: $DAWN_USER_NAME)")
    ap.add_argument("--out", default=str(PROMPT_PATH), help="where to write the prompt")
    ap.add_argument("--model", default=None, help="Gemini model for the briefing (default: $DAWN_PROMPT_MODEL)")
    ap.add_argument("--commits", type=int, default=COMMITS)
    ap.add_argument("--dry-run", action="store_true", help="print the collected context and stop (no API call)")
    args = ap.parse_args(argv)

    repo = resolve_repo(args.target)
    if args.dry_run:
        print(render_context(collect_context(repo, commits=args.commits)))
        return 0
    try:
        text = build_prompt(repo, args.name, model=args.model, commits=args.commits)
    except ValueError as exc:
        print(f"Could not build the prompt: {exc}", file=sys.stderr)
        return 2
    problems = validate_prompt(text)
    if problems:
        print("Generated prompt is invalid: " + "; ".join(problems), file=sys.stderr)
        return 2
    write_prompt(text, pathlib.Path(args.out))
    lines = [l for l in text.splitlines() if l.strip()]
    print(f"Prompt written: {args.out} ({len(text.split())} words) from {repo}")
    print(f"Opening: {lines[-1][:200]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
