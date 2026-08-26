#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
mkdir -p logs

if [ -f monitor.pid ] && kill -0 "$(cat monitor.pid)" 2>/dev/null; then
  echo "monitor daemon already running: $(cat monitor.pid)"
  exit 0
fi

nohup python3 -m monitor run >> logs/monitor.log 2>&1 &
echo $! > monitor.pid
echo "monitor daemon started: $(cat monitor.pid)"
