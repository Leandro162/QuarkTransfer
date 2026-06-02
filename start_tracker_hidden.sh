#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
python3 tracker_launcher.py start --port 8765
echo "Tracker started: http://127.0.0.1:8765/tracker"
