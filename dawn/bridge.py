"""Bridge: call log -> Gemini -> decision board state (+ Nano Banana images)."""
import base64, json, os, re, threading, time, urllib.request, pathlib

HERE = pathlib.Path(__file__).parent
LOG = os.environ.get("DAWN_LOG", "dawn.log")
STATE = HERE / "board_state.json"
APPROVALS = HERE / "approvals.json"
IMG = HERE / "board_img"
IMG.mkdir(exist_ok=True)
CFG = json.loads((HERE / "board_config.json").read_text())
LLM = os.environ["LLM_BASE_URL"].rstrip("/") + "/chat/completions"
KEY = os.environ["LLM_API_KEY"]
GKEY = os.environ.get("GEMINI_API_KEY") or KEY
STYLE = "Clean minimal editorial illustration, dark navy background, one teal accent colour, soft light, no text, no letters, wide 16:9. Subject: "
LOCK = threading.Lock()
S = {}


def save():
    S["v"] = S.get("v", 0) + 1
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(S))
    tmp.replace(STATE)


def reset(status="waiting"):
    S.clear()
    S.update({"status": status, "started": None, "ended": None, "transcript": [], "decisions": {}, "hangup_at": None, "config": CFG})
    try:
        APPROVALS.unlink()
    except FileNotFoundError:
        pass
    save()


def gen_image(subject, name):
    for m in ["gemini-3.1-flash-image", "gemini-nano-banana-2.1"]:
        try:
            url = "https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent" % m
            body = {"contents": [{"parts": [{"text": STYLE + subject}]}], "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]}}
            req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "x-goog-api-key": GKEY})
            r = json.load(urllib.request.urlopen(req, timeout=120))
            for p in r["candidates"][0]["content"]["parts"]:
                if "inlineData" in p:
                    (IMG / name).write_bytes(base64.b64decode(p["inlineData"]["data"]))
                    print("Bild", name, "mit", m, flush=True)
                    with LOCK:
                        save()
                    return
        except Exception as e:
            print("Bild-Fehler", name, m, str(e)[:120], flush=True)


def pregen():
    for c in CFG.values():
        for o in c["options"]:
            if not (IMG / o["img"]).exists():
                gen_image(o["subject"], o["img"])


def classify(text):
    menu = {k: {"question": c["question"], "options": [o["title"] for o in c["options"]]} for k, c in CFG.items()}
    ask = ("A phone call between Philipp and his project agent. The agent asks three decisions, usually in the order A, B, C:\n"
           + json.dumps(menu) + "\nAlready decided: " + ",".join(S["decisions"].keys())
           + "\nRecent things Philipp said: " + " | ".join(S["transcript"][-4:])
           + "\nPhilipp just said: \"" + text + "\"\n\n"
           "Return only JSON: {\"key\": \"A\", \"B\", \"C\" or null, \"said\": \"his words, max 14 words\", "
           "\"understood\": \"what he wants, max 10 words\", \"option\": index of the matching option or -1 if it is something new, "
           "\"new_title\": \"max 5 words, only if option is -1\", \"task\": \"concrete next task for his agents, max 10 words\", "
           "\"wants_to_end\": true or false}. key is null if he did not answer a decision (small talk or a question).")
    body = {"model": "gemini-3.5-flash-lite", "messages": [{"role": "user", "content": ask}]}
    req = urllib.request.Request(LLM, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "Authorization": "Bearer " + KEY})
    raw = json.load(urllib.request.urlopen(req, timeout=20))["choices"][0]["message"]["content"]
    return json.loads(raw[raw.find("{"): raw.rfind("}") + 1])


def handle(text):
    with LOCK:
        S["transcript"].append(text)
        save()
    try:
        r = classify(text)
    except Exception as e:
        print("Klassifikation fehlgeschlagen:", e, flush=True)
        r = {}
    k = r.get("key")
    with LOCK:
        if k in CFG and k not in S["decisions"]:
            opt = r.get("option", -1)
            if not isinstance(opt, int) or opt >= len(CFG[k]["options"]):
                opt = -1
            d = {"said": r.get("said") or text[:90], "understood": r.get("understood", ""), "option": opt,
                 "task": r.get("task") or (CFG[k]["options"][opt]["task"] if opt >= 0 else ""), "new_title": r.get("new_title", "")}
            d["img"] = "%s-live-%d.png" % (k, int(time.time()))
            threading.Thread(target=gen_image, args=((d["understood"] or d["new_title"] or text) + ". Topic: " + CFG[k]["question"], d["img"]), daemon=True).start()
            S["decisions"][k] = d
            print("Entscheidung", k, json.dumps(d)[:150], flush=True)
        if len(S["decisions"]) >= len(CFG) and not S.get("hangup_at") and time.time() - (S.get("started") or 0) > 45:
            S["hangup_at"] = time.time() + 20
            S["status"] = "wrapping"
        save()


def main():
    reset()
    pending, last_t = None, 0.0
    try:
        pos = os.path.getsize(LOG)
    except OSError:
        pos = 0
    print("Board-Bruecke laeuft", flush=True)
    while True:
        try:
            size = os.path.getsize(LOG)
        except OSError:
            time.sleep(0.5)
            continue
        if size < pos:
            pos = 0
        with open(LOG, errors="replace") as f:
            f.seek(pos)
            chunk = f.read()
            pos = f.tell()
        for line in chunk.splitlines():
            if '"WebSocket /ws/chat" [accepted]' in line:
                with LOCK:
                    reset("live")
                    S["started"] = time.time()
                    save()
            m = re.search(r'user_text: "([^"]*)', line)
            if m and m.group(1).strip():
                pending, last_t = m.group(1).strip(), time.time()
            if "connection closed" in line and S.get("status") in ("live", "wrapping"):
                with LOCK:
                    S["status"], S["ended"], S["hangup_at"] = "done", time.time(), None
                    save()
        if pending and time.time() - last_t > 1.0:
            text, pending = pending, None
            threading.Thread(target=handle, args=(text,), daemon=True).start()
        time.sleep(0.3)


if __name__ == "__main__":
    main()
