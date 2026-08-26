#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [ ! -f monitor.pid ]; then
  echo "monitor daemon is not running: monitor.pid not found"
  exit 0
fi

PID="$(cat monitor.pid)"
if kill -0 "$PID" 2>/dev/null; then
  kill "$PID"
  echo "monitor daemon stopped: $PID"
else
  echo "monitor daemon process not found: $PID"
fi
rm -f monitor.pid
