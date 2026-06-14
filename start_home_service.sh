#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/xuelong/projects/Tools/QuarkTransfer"

cd "$ROOT"
exec bash "$ROOT/run_home_service_forever.sh"
