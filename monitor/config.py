from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Missing dependency: PyYAML. Run: pip install -r requirements.txt") from exc


DEFAULT_CONFIG_PATH = Path("config.yaml")

DEFAULT_CONFIG_YAML = """sites:
  - id: example
    name: example
    base_url: https://example.com
    source_url: ""
    adapter: shopify_products_json
    interval_minutes: 15
    enabled: true
    full_scan_pages: 40
    incremental_pages: 1
    notify:
      new_product: true
      price_change: false
      update: false
      error: true

feishu:
  webhook_url: ""
  secret: ""
  verify_ssl: true

dingtalk:
  webhook_url: ""
  secret: ""
  verify_ssl: true

storage:
  path: ./data/monitor.db

export:
  dir: ./exports
"""


@dataclass
class SiteConfig:
    id: str
    name: str
    base_url: str
    source_url: str = ""
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
    verify_ssl: bool = True


@dataclass
class DingTalkConfig:
    webhook_url: str = ""
    secret: str = ""
    verify_ssl: bool = True


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
    dingtalk: DingTalkConfig = field(default_factory=DingTalkConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    export: ExportConfig = field(default_factory=ExportConfig)


def init_config(path: Path = DEFAULT_CONFIG_PATH) -> Path:
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(DEFAULT_CONFIG_YAML, encoding="utf-8")
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
        "dingtalk": config.dingtalk.__dict__,
        "storage": config.storage.__dict__,
        "export": config.export.__dict__,
    }
    path.write_text(yaml.safe_dump(raw, allow_unicode=True, sort_keys=False), encoding="utf-8")


def parse_config(raw: dict[str, Any]) -> AppConfig:
    sites = [SiteConfig(**site) for site in raw.get("sites", [])]
    return AppConfig(
        sites=sites,
        feishu=FeishuConfig(**(raw.get("feishu") or {})),
        dingtalk=DingTalkConfig(**(raw.get("dingtalk") or {})),
        storage=StorageConfig(**(raw.get("storage") or {})),
        export=ExportConfig(**(raw.get("export") or {})),
    )


def get_site(config: AppConfig, site_id: str) -> SiteConfig:
    for site in config.sites:
        if site.id == site_id:
            return site
    raise SystemExit(f"Unknown site: {site_id}")
