#!/usr/bin/env bash
set -uo pipefail

ROOT="/home/xuelong/projects/Tools/QuarkTransfer"
URL="http://127.0.0.1:8765/api/config"
LOG_FILE="$ROOT/config/tracker.log"
MAX_LOG_BYTES=$((5 * 1024 * 1024))

cd "$ROOT" || exit 1
mkdir -p config

rotate_log() {
  if [[ -f "$LOG_FILE" ]] && (( $(stat -c %s "$LOG_FILE" 2>/dev/null || echo 0) > MAX_LOG_BYTES )); then
    mv -f "$LOG_FILE" "$LOG_FILE.1"
  fi
}

while true; do
  while curl --silent --fail --max-time 2 "$URL" >/dev/null 2>&1; do
    sleep 5
  done

  rotate_log
  printf '%s Starting QuarkTransfer on 127.0.0.1:8765\n' "$(date --iso-8601=seconds)" >>"$LOG_FILE"
  python3 server.py --host 127.0.0.1 --port 8765 >>"$LOG_FILE" 2>&1
  exit_code=$?
  printf '%s QuarkTransfer exited with code %s; restarting in 3 seconds\n' \
    "$(date --iso-8601=seconds)" "$exit_code" >>"$LOG_FILE"
  sleep 3
done
