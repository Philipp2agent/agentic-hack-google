"""Live bridge: gradbot log of the call -> Gemini -> live events on the laptop screen.

Tails the call server's log (uvicorn + gradbot, see start.sh) and turns it into events
for the live screen (contract: docs/LIVE-EVENTS.md), posted to POST /api/live/event:

  "WebSocket /ws/chat" [accepted]   -> POST /api/live/reset, then call_started {opening}
  user_text: "..."                  -> user_said {text}; then up to two classified events
                                       (decision, v2_idea, checkpoint, participants_scaled, speed_changed)
  connection closed                 -> call_ended {duration_s}, brief_ready {}

    python dawn/bridge.py [LOGFILE]

Environment: DAWN_CALL_LOG (default run/call.log), LIVE_URL (default http://127.0.0.1:8098),
DAWN_AGENDA (agenda JSON for item ids; default src/data/agenda.json when present),
DAWN_BRIDGE_MODEL (default gemini-3.5-flash-lite), GEMINI_API_KEY or LLM_API_KEY, LLM_BASE_URL.
The parsing lives in the Bridge class and runs without network or keys (see tests/test_bridge.py).
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import sys
import time
import urllib.request
from typing import Callable

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
PROMPT_PATH = HERE / "prompt.txt"
DEFAULT_LOG = ROOT / "run" / "call.log"
DEFAULT_LIVE = "http://127.0.0.1:8098"
DEFAULT_MODEL = "gemini-3.5-flash-lite"
DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
DEFAULT_AGENDA = ROOT / "src" / "data" / "agenda.json"
SETTLE_S = 1.2  # a user turn counts as final when no newer user_text arrived for this long

ACCEPTED = '"WebSocket /ws/chat" [accepted]'
CLOSED = "connection closed"
USER_TEXT = re.compile(r'user_text: "([^"]*)')
MAX_EVENTS_PER_TURN = 2

Classifier = Callable[[str, list[str]], list[dict]]


# ----------------------------------------------------------------------------- inputs
def load_opening(path: pathlib.Path = PROMPT_PATH) -> str:
    """The OPENING sentence is the last non-empty line of prompt.txt (see dawn/from_repo.py)."""
    try:
        lines = [l for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    except OSError:
        return ""
    return lines[-1].strip() if lines else ""


def load_prompt(path: pathlib.Path = PROMPT_PATH) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def load_agenda(path: str | pathlib.Path | None = None) -> list:
    p = pathlib.Path(path or os.environ.get("DAWN_AGENDA") or DEFAULT_AGENDA)
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return data if isinstance(data, list) else data.get("items", []) if isinstance(data, dict) else []


# ----------------------------------------------------------------------------- outputs
def post(live: str, path: str, payload: dict | None = None) -> bool:
    req = urllib.request.Request(live.rstrip("/") + path, data=json.dumps(payload or {}).encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=5).read()
        return True
    except Exception as exc:  # the live screen may not be running; the call must not depend on it
        print("POST failed", path, exc, flush=True)
        return False


def emit(live: str, ev: dict) -> None:
    if ev.get("type") == "reset":
        post(live, "/api/live/reset")
    else:
        post(live, "/api/live/event", ev)
    print("event", ev.get("type"), json.dumps(ev.get("data", {}))[:120], flush=True)


# ----------------------------------------------------------------------------- classification (Gemini)
def extract_json(raw: str) -> dict:
    """The first {...} object in a model reply (models like to wrap JSON in prose or fences)."""
    start, end = raw.find("{"), raw.rfind("}")
    if start < 0 or end <= start:
        return {}
    try:
        data = json.loads(raw[start:end + 1])
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def classify_ask(prompt: str, agenda: list, text: str, history: list[str]) -> str:
    return ("You turn what a user says on a phone call into events for a live dashboard.\n"
            "Project briefing and open threads:\n" + prompt[-3000:] + "\n\n"
            "Agenda items (use these item_id values when the user decides on one):\n" + json.dumps(agenda)[:2500] + "\n\n"
            "Earlier user turns: " + " | ".join(history[-4:]) + "\n"
            "The user just said: \"" + text + "\"\n\n"
            "Return only JSON {\"events\": [...]} with zero to two events, each {\"type\": ..., \"data\": {...}}. Allowed:\n"
            "decision {item_id, decision (APPROVE, REJECT, HOLD or AMEND), summary (max 8 words)};\n"
            "v2_idea {id, title (max 6 words), linked_to: [item_id]};\n"
            "checkpoint {item_id, action (max 6 words), reason} only for irreversible things like publishing or submitting;\n"
            "participants_scaled {count, label} only if they agree to offer this to other people or teams;\n"
            "speed_changed {speed: 1.3, reason} only if they signal hurry.\n"
            "If they decided nothing, return {\"events\": []}.")


def make_classifier(prompt: str | None = None, agenda: list | None = None, model: str | None = None) -> Classifier:
    """Gemini-backed classifier; reads keys lazily so importing this module needs no environment."""
    prompt = load_prompt() if prompt is None else prompt
    agenda = load_agenda() if agenda is None else agenda
    model = model or os.environ.get("DAWN_BRIDGE_MODEL") or DEFAULT_MODEL
    key = os.environ.get("LLM_API_KEY") or os.environ.get("GEMINI_API_KEY") or ""
    url = (os.environ.get("LLM_BASE_URL") or DEFAULT_BASE_URL).rstrip("/") + "/chat/completions"
    if not key:
        raise SystemExit("No Gemini key: set GEMINI_API_KEY (or LLM_API_KEY) in .env, see ./setup.sh")

    def classify(text: str, history: list[str]) -> list[dict]:
        body = {"model": model, "messages": [{"role": "user", "content": classify_ask(prompt, agenda, text, history)}]}
        req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json", "Authorization": "Bearer " + key})
        raw = json.load(urllib.request.urlopen(req, timeout=20))["choices"][0]["message"]["content"]
        events = extract_json(raw).get("events", [])
        return events if isinstance(events, list) else []

    return classify


# ----------------------------------------------------------------------------- the bridge itself
class Bridge:
    """Turns log lines into live events. No I/O: feed() lines, tick() the clock, send what comes back."""

    def __init__(self, opening: str, classify: Classifier | None = None,
                 clock: Callable[[], float] = time.time, settle_s: float = SETTLE_S):
        self.opening, self.classify, self.clock, self.settle_s = opening, classify, clock, settle_s
        self.pending: str | None = None
        self.last_t = 0.0
        self.history: list[str] = []
        self.started: float | None = None

    @staticmethod
    def _ev(etype: str, data: dict | None = None) -> dict:
        return {"type": etype, "data": data or {}}

    def feed(self, line: str) -> list[dict]:
        """Events for one log line (a reset pseudo-event means POST /api/live/reset)."""
        out: list[dict] = []
        if ACCEPTED in line:
            self.started, self.history = self.clock(), []
            out += [self._ev("reset"), self._ev("call_started", {"opening": self.opening})]
        m = USER_TEXT.search(line)
        if m and m.group(1).strip():
            self.pending, self.last_t = m.group(1).strip(), self.clock()
        if CLOSED in line and self.started is not None:
            out += [self._ev("call_ended", {"duration_s": int(self.clock() - self.started)}), self._ev("brief_ready")]
            self.started = None
        return out

    def tick(self) -> list[dict]:
        """Flush a settled user turn: user_said plus up to two classified events."""
        if not self.pending or self.clock() - self.last_t <= self.settle_s:
            return []
        text, self.pending = self.pending, None
        out = [self._ev("user_said", {"text": text[:140]})]
        self.history.append(text)
        if self.classify is None:
            return out
        try:
            events = self.classify(text, self.history)
        except Exception as exc:  # classification is best effort; the transcript line is already out
            print("classification failed:", exc, flush=True)
            return out
        for ev in events[:MAX_EVENTS_PER_TURN]:
            if isinstance(ev, dict) and isinstance(ev.get("type"), str) and ev["type"]:
                data = ev.get("data", {})
                out.append(self._ev(ev["type"], data if isinstance(data, dict) else {}))
        return out


def run(log: pathlib.Path, live: str, bridge: Bridge, poll_s: float = 0.3) -> None:
    pos = 0
    print("bridge running:", log, "->", live, flush=True)
    while True:
        try:
            size = os.path.getsize(log)
        except OSError:
            time.sleep(0.5)
            continue
        if size < pos:  # log truncated or rotated
            pos = 0
        with open(log, errors="replace") as f:
            f.seek(pos)
            chunk = f.read()
            pos = f.tell()
        for line in chunk.splitlines():
            for ev in bridge.feed(line):
                emit(live, ev)
        for ev in bridge.tick():
            emit(live, ev)
        time.sleep(poll_s)


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    log = pathlib.Path(argv[0] if argv else os.environ.get("DAWN_CALL_LOG") or DEFAULT_LOG)
    live = os.environ.get("LIVE_URL", DEFAULT_LIVE)
    opening = load_opening()
    if not opening:
        print(f"warning: no opening found in {PROMPT_PATH} (run dawn/from_repo.py)", flush=True)
    run(log, live, Bridge(opening, classify=make_classifier()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
