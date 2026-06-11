#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/xuelong/projects/Tools/QuarkTransfer"
URL="http://127.0.0.1:8765"
LOG_FILE="$ROOT/config/tracker.log"

cd "$ROOT"
mkdir -p config

current_config="$(curl --silent --fail "$URL/api/config" 2>/dev/null || true)"
if [[ -n "$current_config" ]]; then
  if [[ "$current_config" == *'"feishu_enabled": true'* ]]; then
    exit 0
  fi
  echo "Port 8765 is occupied by an older QuarkTransfer instance. Stop it before starting the WSL Home version." >&2
  exit 2
fi

nohup python3 server.py --host 127.0.0.1 --port 8765 >>"$LOG_FILE" 2>&1 </dev/null &

for _ in $(seq 1 30); do
  current_config="$(curl --silent --fail "$URL/api/config" 2>/dev/null || true)"
  if [[ "$current_config" == *'"feishu_enabled": true'* ]]; then
    exit 0
  fi
  sleep 0.3
done

echo "QuarkTransfer did not start. Check $LOG_FILE" >&2
exit 1
