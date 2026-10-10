#!/usr/bin/env bash
# Starts everything for one call: call server (phone), live screen (laptop), bridge between them,
# plus an HTTPS tunnel for the phone when cloudflared is installed. Ctrl-C stops all of it.
#
#   ./start.sh                re-uses dawn/prompt.txt from ./setup.sh
#   ./start.sh --fresh        re-reads your repo first (new commits -> new briefing)
#   ./start.sh --no-tunnel    LAN only (http://<laptop-ip>:8090; the mic then works only on localhost/HTTPS)
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

FRESH=0; TUNNEL=1
while [ $# -gt 0 ]; do
  case "$1" in
    --fresh) FRESH=1; shift ;;
    --no-tunnel) TUNNEL=0; shift ;;
    -h|--help) sed -n '2,7p' "$0"; exit 0 ;;
    *) echo "unknown option: $1"; exit 1 ;;
  esac
done

die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
[ -f .env ] || die "no .env yet - run ./setup.sh first"
[ -x .venv/bin/python ] || die "no .venv yet - run ./setup.sh first"
set -a; . ./.env; set +a
[ -n "${GRADIUM_API_KEY:-}" ] && [ -n "${GEMINI_API_KEY:-${LLM_API_KEY:-}}" ] || die "keys missing in .env - run ./setup.sh"
PY=.venv/bin/python
CALL_PORT="${CALL_PORT:-8090}"
LIVE_PORT="${LIVE_PORT:-8098}"
export LIVE_URL="${LIVE_URL:-http://127.0.0.1:$LIVE_PORT}"
export DAWN_CALL_LOG="$PWD/run/call.log"
mkdir -p run
: > run/call.log

port_free() { "$PY" - "$1" <<'EOF'
import socket, sys
s = socket.socket(); s.settimeout(0.3)
sys.exit(1 if s.connect_ex(("127.0.0.1", int(sys.argv[1]))) == 0 else 0)
EOF
}
wait_http() {  # wait_http URL SECONDS
  "$PY" - "$1" "$2" <<'EOF'
import sys, time, urllib.request
url, deadline = sys.argv[1], time.time() + float(sys.argv[2])
while time.time() < deadline:
    try:
        urllib.request.urlopen(url, timeout=1).read(); sys.exit(0)
    except Exception:
        time.sleep(0.5)
sys.exit(1)
EOF
}
lan_ip() { "$PY" - <<'EOF'
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
try:
    s.connect(("8.8.8.8", 80)); print(s.getsockname()[0])
except Exception:
    print("127.0.0.1")
EOF
}

port_free "$CALL_PORT" || die "port $CALL_PORT is busy (old call server still running? CALL_PORT=... ./start.sh)"
port_free "$LIVE_PORT" || die "port $LIVE_PORT is busy (LIVE_PORT=... ./start.sh)"

# --- briefing -------------------------------------------------------------------------
if [ "$FRESH" -eq 1 ] || [ ! -s dawn/prompt.txt ]; then
  echo "== Briefing from ${TARGET_REPO:-this repo} (Gemini)"
  "$PY" dawn/from_repo.py || die "briefing failed"
fi

# --- processes ------------------------------------------------------------------------
PIDS=""
cleanup() {
  trap - INT TERM EXIT
  echo; echo "== Stopping"
  for p in $PIDS; do kill "$p" 2>/dev/null || true; done
  sleep 1
  for p in $PIDS; do kill -9 "$p" 2>/dev/null || true; done
  exit 0
}
trap cleanup INT TERM EXIT

echo "== Call server     :$CALL_PORT  (log: run/call.log)"
"$PY" -m uvicorn dawn.main:app --host 0.0.0.0 --port "$CALL_PORT" >>run/call.log 2>&1 &
PIDS="$PIDS $!"

LIVE_OK=0
if [ -f src/live/app.py ]; then
  echo "== Live screen     :$LIVE_PORT  (log: run/live.log)"
  "$PY" -m uvicorn src.live.app:app --host 0.0.0.0 --port "$LIVE_PORT" >run/live.log 2>&1 &
  PIDS="$PIDS $!"; LIVE_OK=1
else
  echo "== Live screen: src/live not in this checkout (merge the live-view branch); the call works without it"
fi

echo "== Bridge          call log -> Gemini -> live screen  (log: run/bridge.log)"
"$PY" dawn/bridge.py >run/bridge.log 2>&1 &
PIDS="$PIDS $!"

PHONE_URL="http://$(lan_ip):$CALL_PORT"
HTTPS_NOTE="no HTTPS tunnel: phones allow the microphone only over HTTPS (install cloudflared, or test on this laptop at http://localhost:$CALL_PORT)"
if [ "$TUNNEL" -eq 1 ] && command -v cloudflared >/dev/null 2>&1; then
  echo "== HTTPS tunnel    cloudflared (log: run/tunnel.log)"
  cloudflared tunnel --url "http://127.0.0.1:$CALL_PORT" --no-autoupdate >run/tunnel.log 2>&1 &
  PIDS="$PIDS $!"
  for _ in $(seq 1 40); do
    u="$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' run/tunnel.log 2>/dev/null | head -1 || true)"
    [ -n "$u" ] && { PHONE_URL="$u"; HTTPS_NOTE=""; break; }
    sleep 1
  done
  [ -n "$HTTPS_NOTE" ] && HTTPS_NOTE="tunnel did not come up within 40 s (see run/tunnel.log); using the LAN URL"
fi

wait_http "http://127.0.0.1:$CALL_PORT/" 40 || { tail -20 run/call.log; die "call server did not start (see run/call.log)"; }
[ "$LIVE_OK" -eq 1 ] && { wait_http "http://127.0.0.1:$LIVE_PORT/api/health" 20 || echo "warning: live screen not answering (see run/live.log)"; }

echo
echo "=================================================================="
echo "  PHONE  (tap the screen, glasses or headset via Bluetooth):"
echo "      $PHONE_URL"
[ "$LIVE_OK" -eq 1 ] && echo "  LAPTOP (live screen):" && echo "      http://localhost:$LIVE_PORT/live"
echo "  Opening line: $(tail -1 dawn/prompt.txt)"
[ -n "$HTTPS_NOTE" ] && echo "  Note: $HTTPS_NOTE"
echo "  Ctrl-C stops everything. Logs in run/."
echo "=================================================================="

# keep running until a service dies or Ctrl-C
while :; do
  for p in $PIDS; do
    kill -0 "$p" 2>/dev/null || { echo "a service stopped (pid $p) - check run/*.log"; exit 1; }
  done
  sleep 2
done
