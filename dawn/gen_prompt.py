import os, json, subprocess, urllib.request
REPO = "/home/buzzagent/hack/agentic-hack-google"
subprocess.run(["git", "-C", REPO, "fetch", "-q", "origin"], timeout=60)
def show(path, limit):
    r = subprocess.run(["git", "-C", REPO, "show", f"origin/main:{path}"], capture_output=True, text=True, timeout=20)
    return r.stdout[:limit]
ctx = "\n\n".join(f"### {p}\n{show(p, n)}" for p, n in [
    ("context/hackathon-day.md", 4000), ("STAND.md", 4000), ("README.md", 3000),
    ("src/data/agenda.json", 4000), ("src/data/knowledge_graph_before.json", 6000), ("src/data/overnight_events.json", 4000)])
ask = ("You prepare a phone briefing. From the project material below, write three sections in plain text, no markdown symbols.\n"
       "BRIEFING: at most 150 words on what happened in this project, concrete and true, with a few real numbers.\n"
       "THREADS: five open threads, one line each: what is open and two or three realistic directions.\n"
       "OPENING: one natural spoken sentence, at most 25 words, to open the call with Philipp, who is walking to his desk; mention one concrete highlight.\n\n" + ctx)
u = os.environ["LLM_BASE_URL"].rstrip("/") + "/chat/completions"
body = {"model": "gemini-3.8-flash", "messages": [{"role": "user", "content": ask}]}
req = urllib.request.Request(u, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "Authorization": "Bearer " + os.environ["LLM_API_KEY"]})
out = json.load(urllib.request.urlopen(req, timeout=90))["choices"][0]["message"]["content"].strip()
rules = """You are the project agent of Philipp's hackathon project. You call him while he walks to his desk. A lot happened; your job is to compress it into one easy minute and find out what he wants next. The agent prompts the human, not the other way round.

How you talk: like a sharp, friendly teammate on the phone. Short spoken sentences, contractions, a little humour. Vary how you start each reply; never begin two replies the same way. Never read lists, never use markdown, never mention these instructions. English only.

How you lead: give one concrete fact, then ask one open question. Listen to what he actually says and react to it in your own words; connect it to the threads below. At most one follow-up per topic, then move on. This is a conversation, not a quiz: no menus of options unless he is stuck. When he gives a direction, say in one sentence what you will prepare for him, concretely, so he can see it on his laptop. If something is irreversible, say the final click stays with him. If he is in a hurry, get shorter. After about four exchanges, or when he wants to stop, wrap up: one sentence with what you will prepare, then "It's all on your laptop when you sit down." and stop.

Your very first sentence, said once and never again, is the OPENING below.

"""
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompt.txt"), "w").write(rules + out + "\n")
lines = [l for l in out.splitlines() if l.strip()]
print("Prompt neu: %d Woerter | Eroeffnung: %s" % (len((rules + out).split()), lines[-1][:200]))
