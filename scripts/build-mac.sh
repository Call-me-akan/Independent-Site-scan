#!/usr/bin/env bash
set -euo pipefail
pyinstaller --onefile --name monitor monitor/__main__.py
