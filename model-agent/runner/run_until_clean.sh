#!/usr/bin/env bash
# Poll retries in background; one submit-next-retry at a time (upload is heavy).
set -uo pipefail
cd "$(dirname "$0")"
LOG=~/claude/vibe-agent/install_marathon_v3_console.log
HB_LOG=~/claude/vibe-agent/install_marathon_heartbeat.log
STATE=~/claude/vibe-agent/install_marathon_v2_state.json
SRC_ARGS=(
  --source-repo amralieg/lakehouse-industry-data-models-fix
  --source-ref fix/metric-view-column-names
)

score() {
  python3 -c "
import json
from pathlib import Path
s=json.loads(Path('$STATE').read_text())
items=s.get('waves',{}).get('pool',{}).get('items',{})
c={'clean':0,'warning':0,'failed':0}
for v in items.values():
    b=v.get('bucket')
    if b in c: c[b]+=1
print(c['clean'], c['warning'], c['failed'])
"
}

inflight() {
  python3 -c "
import json, time
from datetime import datetime
from pathlib import Path
s=json.loads(Path('$STATE').read_text())
ret=s.get('retries',{})
now=time.time()
def active(v):
    if v.get('final_bucket'):
        return False
    if v.get('run_id'):
        return True
    claimed=v.get('submitting_at')
    if not claimed:
        return False
    try:
        age=now-datetime.fromisoformat(claimed.replace('Z','+00:00')).timestamp()
        return age < 900
    except Exception:
        return False
print(sum(1 for v in ret.values() if active(v)))
"
}

cleanup() {
  kill "$POLL_PID" 2>/dev/null || true
  kill "$HB_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

if ! pgrep -f 'marathon_heartbeat.py' >/dev/null 2>&1; then
  python3 marathon_heartbeat.py >>"$HB_LOG" 2>&1 &
  HB_PID=$!
fi

if ! pgrep -f 'poll-retries-only' >/dev/null 2>&1; then
  python3 install_marathon.py --poll-retries-only --resume --poll 60 --max-parallel 40 \
    "${SRC_ARGS[@]}" >>"$LOG" 2>&1 &
  POLL_PID=$!
  echo "[supervisor] poll-only pid=$POLL_PID"
fi

while true; do
  read -r CLEAN WARN FAIL <<<"$(score)"
  if [[ "$CLEAN" == "80" && "$WARN" == "0" && "$FAIL" == "0" ]]; then
    echo "[supervisor] $(date -u +%Y-%m-%dT%H:%M:%SZ) DONE 80/80 clean"
    exit 0
  fi
  RUNNING=$(inflight)
  if [[ "$RUNNING" -lt 1 ]]; then
    python3 install_marathon.py --submit-next-retry --resume --max-parallel 40 \
      "${SRC_ARGS[@]}" >>"$LOG" 2>&1
  fi
  echo "[supervisor] $(date -u +%Y-%m-%dT%H:%M:%SZ) clean=$CLEAN warn=$WARN fail=$FAIL inflight=$RUNNING"
  sleep 45
done
