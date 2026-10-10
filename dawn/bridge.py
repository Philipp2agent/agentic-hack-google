"""Live bridge: gradbot log of the call -> Gemini -> live events on the laptop screen."""
import json, os, re, time, urllib.request, pathlib

LOG = "/home/buzzagent/hack/run/demo.log"
LIVE = os.environ.get("LIVE_URL", "http://127.0.0.1:8098")
PROMPT = (pathlib.Path(__file__).parent / "prompt.txt").read_text()
OPENING = [l for l in PROMPT.splitlines() if l.strip()][-1]
try:
    AGENDA = json.loads(pathlib.Path("/home/buzzagent/hack/demo-c4/src/data/agenda.json").read_text())
except Exception:
    AGENDA = []
LLM = os.environ["LLM_BASE_URL"].rstrip("/") + "/chat/completions"
KEY = os.environ["LLM_API_KEY"]

def post(path, payload=None):
    req = urllib.request.Request(LIVE + path, data=json.dumps(payload or {}).encode(), method="POST", headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=5).read()
    except Exception as e:
        print("POST fehlgeschlagen", path, e, flush=True)

def event(etype, data):
    post("/api/live/event", {"type": etype, "data": data})
    print("event", etype, json.dumps(data)[:120], flush=True)

def classify(text, history):
    ask = ("You turn what a user says on a phone call into events for a live dashboard.\n"
           "Project briefing and open threads:\n" + PROMPT[-3000:] + "\n\n"
           "Agenda items (use these item_id values when the user decides on one):\n" + json.dumps(AGENDA)[:2500] + "\n\n"
           "Earlier user turns: " + " | ".join(history[-4:]) + "\n"
           "The user just said: \"" + text + "\"\n\n"
           "Return only JSON {\"events\": [...]} with zero to two events, each {\"type\": ..., \"data\": {...}}. Allowed:\n"
           "decision {item_id, decision (APPROVE, REJECT, HOLD or AMEND), summary (max 8 words)};\n"
           "v2_idea {id, title (max 6 words), linked_to: [item_id]};\n"
           "checkpoint {item_id, action (max 6 words), reason} only for irreversible things like publishing or submitting;\n"
           "participants_scaled {count: 42, label} only if he agrees to offer this to the other teams;\n"
           "speed_changed {speed: 1.3, reason} only if he signals hurry.\n"
           "If he decided nothing, return {\"events\": []}.")
    body = {"model": "gemini-3.5-flash-lite", "messages": [{"role": "user", "content": ask}]}
    req = urllib.request.Request(LLM, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "Authorization": "Bearer " + KEY})
    raw = json.load(urllib.request.urlopen(req, timeout=20))["choices"][0]["message"]["content"]
    return json.loads(raw[raw.find("{"): raw.rfind("}") + 1]).get("events", [])

def main():
    pos, pending, last_t, history, started = 0, None, 0.0, [], None
    print("Bruecke laeuft:", LOG, "->", LIVE, flush=True)
    while True:
        try:
            size = os.path.getsize(LOG)
        except OSError:
            time.sleep(0.5); continue
        if size < pos:
            pos = 0
        with open(LOG, errors="replace") as f:
            f.seek(pos); chunk = f.read(); pos = f.tell()
        for line in chunk.splitlines():
            if '"WebSocket /ws/chat" [accepted]' in line:
                post("/api/live/reset"); started = time.time(); history = []
                event("call_started", {"opening": OPENING})
            m = re.search(r'user_text: "([^"]*)', line)
            if m and m.group(1).strip():
                pending, last_t = m.group(1).strip(), time.time()
            if "connection closed" in line and started:
                event("call_ended", {"duration_s": int(time.time() - started)}); event("brief_ready", {}); started = None
        if pending and time.time() - last_t > 1.2:
            text, pending = pending, None
            event("user_said", {"text": text[:140]}); history.append(text)
            try:
                for ev in classify(text, history)[:2]:
                    if isinstance(ev, dict) and ev.get("type"):
                        event(ev["type"], ev.get("data", {}))
            except Exception as e:
                print("Klassifikation fehlgeschlagen:", e, flush=True)
        time.sleep(0.3)

if __name__ == "__main__":
    main()
