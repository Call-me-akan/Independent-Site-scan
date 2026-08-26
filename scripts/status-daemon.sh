#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [ -f monitor.pid ] && kill -0 "$(cat monitor.pid)" 2>/dev/null; then
  echo "monitor daemon running: $(cat monitor.pid)"
else
  echo "monitor daemon not running"
fi
python3 -m monitor status
