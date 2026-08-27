"""Persistent daemon control state shared between WebUI and daemon."""

from __future__ import annotations

import json
from pathlib import Path


class ControlState:
    """A tiny JSON state file to toggle the daemon from the WebUI."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def load(self) -> dict:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}

    def save(self, data: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    def read(self, key: str, default=None):
        return self.load().get(key, default)

    def write(self, key: str, value) -> None:
        data = self.load()
        data[key] = value
        self.save(data)