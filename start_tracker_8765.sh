#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
echo "Quark tracker is starting..."
echo
echo "Tracker page:"
echo "http://127.0.0.1:8765/tracker"
echo
echo "Press Ctrl+C to stop the service."
python3 server.py --port 8765
