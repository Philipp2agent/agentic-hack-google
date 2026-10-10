import os, json, subprocess, urllib.request, pathlib
HERE = pathlib.Path(__file__).parent
REPO = os.environ.get("DAWN_REPO", "..")
subprocess.run(["git", "-C", REPO, "fetch", "-q", "origin"], timeout=60)
def show(path, limit):
    r = subprocess.run(["git", "-C", REPO, "show", f"origin/main:{path}"], capture_output=True, text=True, timeout=20)
    return r.stdout[:limit]
ctx = "\n\n".join(f"### {p}\n{show(p, n)}" for p, n in [
    ("context/hackathon-day.md", 4000), ("STAND.md", 4000), ("README.md", 3000),
    ("src/data/agenda.json", 3000), ("src/data/knowledge_graph_before.json", 5000), ("src/data/overnight_events.json", 3000)])
ask = ("From the project material below, write two sections in plain text, no markdown symbols.\n"
       "BRIEFING: at most 120 words on what was built and how, concrete and true, so you can answer follow-up questions on a call.\n"
       "THREADS: five open threads, one line each.\n\n" + ctx)
u = os.environ["LLM_BASE_URL"].rstrip("/") + "/chat/completions"
body = {"model": "gemini-3.8-flash", "messages": [{"role": "user", "content": ask}]}
req = urllib.request.Request(u, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "Authorization": "Bearer " + os.environ["LLM_API_KEY"]})
out = json.load(urllib.request.urlopen(req, timeout=90))["choices"][0]["message"]["content"].strip()
opening = (HERE / "opening.txt").read_text().strip()
prompt = ((HERE / "rules.txt").read_text() + "\nOPENING (say it once, word for word, as your very first sentence; never greet again): " + opening
          + "\n\nPROJECT CONTEXT (for answering questions, do not recite):\n" + out + "\n")
(HERE / "prompt.txt").write_text(prompt)
print("Prompt v3: %d Woerter" % len(prompt.split()))
