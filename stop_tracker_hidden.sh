#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
python3 tracker_launcher.py stop --port 8765
