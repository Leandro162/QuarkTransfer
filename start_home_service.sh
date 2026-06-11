#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/xuelong/projects/Tools/QuarkTransfer"
URL="http://127.0.0.1:8765"
LOG_FILE="$ROOT/config/tracker.log"

cd "$ROOT"
mkdir -p config

if curl --silent --fail "$URL/api/config" >/dev/null 2>&1; then
  exit 0
fi

nohup python3 server.py --host 127.0.0.1 --port 8765 >>"$LOG_FILE" 2>&1 </dev/null &

for _ in $(seq 1 30); do
  if curl --silent --fail "$URL/api/config" >/dev/null 2>&1; then
    exit 0
  fi
  sleep 0.3
done

echo "QuarkTransfer did not start. Check $LOG_FILE" >&2
exit 1
