"""Check GitHub for the latest release and cache the result."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from pathlib import Path

from .version import API_LATEST_URL, RELEASE_URL, VERSION

CACHE_TTL = 24 * 3600  # 24h


class UpdateInfo:
    def __init__(self, latest: str, current: str, has_update: bool, url: str = RELEASE_URL, checked_at: float = 0.0):
        self.latest = latest
        self.current = current
        self.has_update = has_update
        self.url = url
        self.checked_at = checked_at

    def to_dict(self) -> dict:
        return {
            "current": self.current,
            "latest": self.latest,
            "has_update": self.has_update,
            "url": self.url,
            "checked_at": self.checked_at,
        }


def _cache_path(data_dir: str | Path) -> Path:
    return Path(data_dir) / "update_cache.json"


def _load_cache(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("latest") and time.time() - data.get("checked_at", 0) < CACHE_TTL:
            return data
    except (OSError, json.JSONDecodeError):
        pass
    return None


def _save_cache(path: Path, data: dict) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass


def check_for_update(data_dir: str | Path = "", force: bool = False) -> UpdateInfo:
    """Query GitHub latest release; returns cached result if fresh (or on network failure)."""
    cache = _cache_path(data_dir) if data_dir else None
    if cache and not force:
        cached = _load_cache(cache)
        if cached:
            return UpdateInfo(
                latest=cached.get("latest", VERSION),
                current=VERSION,
                has_update=cached.get("has_update", False),
                url=cached.get("url", RELEASE_URL),
                checked_at=cached.get("checked_at", 0.0),
            )
    # 网络查询（静默失败 → 返回无更新，不打断主流程）
    latest = VERSION
    has_update = False
    url = RELEASE_URL
    try:
        req = urllib.request.Request(API_LATEST_URL, headers={"User-Agent": "StoreMonitorAgent/update-check", "Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8", "replace"))
        latest = str(data.get("tag_name") or VERSION).lstrip("v")
        url = data.get("html_url") or RELEASE_URL
        has_update = _version_gt(latest, VERSION)
    except (urllib.error.URLError, json.JSONDecodeError, OSError):
        pass
    info = UpdateInfo(latest=latest, current=VERSION, has_update=has_update, url=url, checked_at=time.time())
    if cache:
        _save_cache(cache, info.to_dict())
    return info


def _version_gt(a: str, b: str) -> bool:
    """Semver-ish compare. '0.6.4' > '0.6.4-rc1' > '0.6.3'. Returns True if a > b."""
    def parse(v: str):
        base, *pre = v.split("-", 1)
        parts = [int(c) for c in base.split(".") if c.isdigit()] or [0]
        # 补足 3 段
        while len(parts) < 3:
            parts.append(0)
        # 后缀：无后缀=正式版(最新)；rc/beta/alpha 依次更旧
        # 用第 4 位值区分：正式版=99，rc=1，beta=2，alpha=3（值越小越旧）
        if pre:
            tag = pre[0].lower()
            if tag.startswith("rc"):
                parts.append(1)
            elif tag.startswith("beta"):
                parts.append(2)
            elif tag.startswith("alpha"):
                parts.append(3)
            else:
                parts.append(1)
        else:
            parts.append(99)  # 正式版
        return parts

    return parse(a) > parse(b)