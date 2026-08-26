from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Missing dependency: PyYAML. Run: pip install -r requirements.txt") from exc


DEFAULT_CONFIG_PATH = Path("config.yaml")


@dataclass
class SiteConfig:
    id: str
    name: str
    base_url: str
    adapter: str = "shopify_products_json"
    interval_minutes: int = 15
    enabled: bool = True
    full_scan_pages: int = 40
    incremental_pages: int = 1
    notify: dict[str, bool] = field(default_factory=dict)


@dataclass
class FeishuConfig:
    webhook_url: str = ""
    secret: str = ""


@dataclass
class StorageConfig:
    path: str = "./data/monitor.db"


@dataclass
class ExportConfig:
    dir: str = "./exports"


@dataclass
class AppConfig:
    sites: list[SiteConfig]
    feishu: FeishuConfig = field(default_factory=FeishuConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    export: ExportConfig = field(default_factory=ExportConfig)


def init_config(path: Path = DEFAULT_CONFIG_PATH) -> Path:
    if path.exists():
        return path
    template = Path(__file__).resolve().parents[1] / "config.example.yaml"
    shutil.copyfile(template, path)
    return path


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> AppConfig:
    if not path.exists():
        raise SystemExit(f"Config not found: {path}. Run: python -m monitor.cli init")
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return parse_config(raw)


def save_config(config: AppConfig, path: Path = DEFAULT_CONFIG_PATH) -> None:
    raw = {
        "sites": [site.__dict__ for site in config.sites],
        "feishu": config.feishu.__dict__,
        "storage": config.storage.__dict__,
        "export": config.export.__dict__,
    }
    path.write_text(yaml.safe_dump(raw, allow_unicode=True, sort_keys=False), encoding="utf-8")


def parse_config(raw: dict[str, Any]) -> AppConfig:
    sites = [SiteConfig(**site) for site in raw.get("sites", [])]
    return AppConfig(
        sites=sites,
        feishu=FeishuConfig(**(raw.get("feishu") or {})),
        storage=StorageConfig(**(raw.get("storage") or {})),
        export=ExportConfig(**(raw.get("export") or {})),
    )


def get_site(config: AppConfig, site_id: str) -> SiteConfig:
    for site in config.sites:
        if site.id == site_id:
            return site
    raise SystemExit(f"Unknown site: {site_id}")
