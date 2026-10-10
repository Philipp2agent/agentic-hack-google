#!/usr/bin/env bash
# DawnDispatch setup: Python 3.12+ venv, YOUR keys (Gradium, Gemini) in .env, your target repo, first briefing.
#
#   ./setup.sh                                  interactive (keys are typed hidden)
#   ./setup.sh --repo /path/or/https://github.com/you/repo --name Alex
#   GRADIUM_API_KEY=... GEMINI_API_KEY=... TARGET_REPO=... ./setup.sh --yes      non-interactive
#
# Writes .env (git-ignored, mode 600). Never prints or commits keys.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

REPO_ARG="${TARGET_REPO:-}"
NAME_ARG="${DAWN_USER_NAME:-}"
YES=0
SKIP_PROMPT=0
while [ $# -gt 0 ]; do
  case "$1" in
    --repo) REPO_ARG="$2"; shift 2 ;;
    --name) NAME_ARG="$2"; shift 2 ;;
    --yes|-y) YES=1; shift ;;
    --skip-prompt) SKIP_PROMPT=1; shift ;;
    -h|--help) sed -n '2,8p' "$0"; exit 0 ;;
    *) echo "unknown option: $1"; exit 1 ;;
  esac
done

say() { printf '\n== %s\n' "$*"; }
die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
env_value() { grep -E "^$1=" .env 2>/dev/null | head -1 | cut -d= -f2- || true; }
interactive() { [ "$YES" -eq 0 ] && [ -t 0 ]; }

# --- 1. prerequisites -------------------------------------------------------------------
say "Checking prerequisites"
command -v git >/dev/null 2>&1 || die "git is required"
PY=""
for c in python3.13 python3.12 python3 python; do
  command -v "$c" >/dev/null 2>&1 || continue
  if "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)' 2>/dev/null; then PY="$c"; break; fi
done
[ -n "$PY" ] || die "Python 3.12 or newer is required (the gradbot voice library ships wheels for 3.12 and 3.13 only). Found: $(python3 --version 2>&1 || echo none)"
echo "Python: $("$PY" --version) ($(command -v "$PY"))"
command -v cloudflared >/dev/null 2>&1 && echo "cloudflared: found (HTTPS tunnel for the phone will be started by ./start.sh)" \
  || echo "cloudflared: not found (optional; mobile browsers allow the microphone only over HTTPS - see README)"

# --- 2. virtualenv + dependencies -------------------------------------------------------
say "Installing into .venv"
[ -x .venv/bin/python ] || "$PY" -m venv .venv
.venv/bin/python -m pip install -q --upgrade pip
.venv/bin/python -m pip install -q -r requirements.txt
.venv/bin/python -c 'import gradbot, fastapi, uvicorn' || die "installation incomplete (see pip output above)"
echo "ok: $(.venv/bin/python -c 'import gradbot, importlib.metadata as m; print("gradbot", m.version("gradbot"))')"

# --- 3. keys (typed hidden; existing .env values or exported variables are kept) -------
say "API keys (input is hidden; stored only in .env)"
ask_secret() {  # ask_secret VAR "label" "where to get it"
  local var="$1" label="$2" hint="$3" current="" input=""
  current="${!var:-}"
  [ -n "$current" ] || current="$(env_value "$var")"
  if [ -n "$current" ]; then
    if interactive; then
      read -rs -p "$label [Enter keeps the saved one]: " input; echo
      [ -n "$input" ] && current="$input"
    fi
  else
    interactive || die "$var is not set (export it or run interactively). Get one: $hint"
    while [ -z "$current" ]; do read -rs -p "$label ($hint): " current; echo; done
  fi
  printf -v "$var" '%s' "$current"
}
ask_secret GRADIUM_API_KEY "Gradium API key" "https://gradium.ai"
ask_secret GEMINI_API_KEY "Gemini API key" "https://aistudio.google.com/apikey"

# --- 4. target repo and who gets called ------------------------------------------------
say "Target repository"
[ -n "$REPO_ARG" ] || REPO_ARG="$(env_value TARGET_REPO)"
if interactive; then
  read -r -p "Repo to brief about - local path or GitHub URL [${REPO_ARG:-this repo}]: " input
  [ -n "$input" ] && REPO_ARG="$input"
fi
[ -n "$REPO_ARG" ] || REPO_ARG="$(pwd)"
case "$REPO_ARG" in
  http://*|https://*|git@*|ssh://*|git://*) echo "will clone $REPO_ARG into .repos/ on first use" ;;
  *) REPO_ARG="$(cd "${REPO_ARG/#\~/$HOME}" 2>/dev/null && pwd)" || die "not a directory: $REPO_ARG"
     git -C "$REPO_ARG" rev-parse --show-toplevel >/dev/null 2>&1 || die "not a git repository: $REPO_ARG" ;;
esac
[ -n "$NAME_ARG" ] || NAME_ARG="$(env_value DAWN_USER_NAME)"
[ -n "$NAME_ARG" ] || NAME_ARG="$(git config user.name 2>/dev/null | awk '{print $1}')"
if interactive; then
  read -r -p "Your first name, as the agent should address you [${NAME_ARG:-the user}]: " input
  [ -n "$input" ] && NAME_ARG="$input"
fi
[ -n "$NAME_ARG" ] || NAME_ARG="the user"

# --- 5. write .env --------------------------------------------------------------------
say "Writing .env"
LLM_BASE_URL_VALUE="${LLM_BASE_URL:-$(env_value LLM_BASE_URL)}"
LLM_MODEL_VALUE="${LLM_MODEL:-$(env_value LLM_MODEL)}"
PROMPT_MODEL_VALUE="${DAWN_PROMPT_MODEL:-$(env_value DAWN_PROMPT_MODEL)}"
BRIDGE_MODEL_VALUE="${DAWN_BRIDGE_MODEL:-$(env_value DAWN_BRIDGE_MODEL)}"
umask 077
cat > .env <<EOF
# DawnDispatch - written by setup.sh on $(date -u +%Y-%m-%dT%H:%MZ). Git-ignored. NEVER commit.
GRADIUM_API_KEY=$GRADIUM_API_KEY
GEMINI_API_KEY=$GEMINI_API_KEY
# gradbot (the voice loop) reads the Gemini key through its OpenAI-compatible endpoint:
LLM_API_KEY=$GEMINI_API_KEY
LLM_BASE_URL=${LLM_BASE_URL_VALUE:-https://generativelanguage.googleapis.com/v1beta/openai/}
LLM_MODEL=${LLM_MODEL_VALUE:-gemini-3.5-flash-lite}
# briefing (dawn/from_repo.py) and live bridge (dawn/bridge.py)
DAWN_PROMPT_MODEL=${PROMPT_MODEL_VALUE:-gemini-3.8-flash}
DAWN_BRIDGE_MODEL=${BRIDGE_MODEL_VALUE:-gemini-3.5-flash-lite}
# your repo and your name
TARGET_REPO=$REPO_ARG
DAWN_USER_NAME=$NAME_ARG
# ports used by ./start.sh
CALL_PORT=${CALL_PORT:-8090}
LIVE_PORT=${LIVE_PORT:-8098}
EOF
chmod 600 .env
echo ".env written (keys hidden). Repo: $REPO_ARG  Name: $NAME_ARG"

# --- 6. first briefing ----------------------------------------------------------------
if [ "$SKIP_PROMPT" -eq 0 ]; then
  say "Generating the first briefing from your repo (Gemini; README, commits, branches, status files are sent)"
  set -a; . ./.env; set +a
  .venv/bin/python dawn/from_repo.py || die "briefing failed - fix the key or repo above and run: ./setup.sh"
fi

say "Done. Next: ./start.sh"
