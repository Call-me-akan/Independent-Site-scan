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
  - id: viqzes
    name: viqzes
    base_url: https://viqzes.com
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
  - id: giftfors-com
    name: giftfors
    base_url: https://giftfors.com
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
  - id: umlovegift-com
    name: umlovegift
    base_url: https://umlovegift.com
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
  - id: flairgifts-com
    name: flairgifts
    base_url: https://flairgifts.com
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
  - id: artveragifts-com
    name: artveragifts
    base_url: https://artveragifts.com
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
  - id: presentgivers-com
    name: presentgivers
    base_url: https://presentgivers.com
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
  - id: citybuyiyds-com
    name: citybuyiyds
    base_url: https://www.citybuyiyds.com
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
  - id: algal-bloom-com
    name: algal-bloom
    base_url: https://algal-bloom.com
    source_url: "https://algal-bloom.com/search?page=1&sort=created-descending"
    adapter: embedded_page_products
    interval_minutes: 15
    enabled: true
    full_scan_pages: 40
    incremental_pages: 1
    notify:
      new_product: true
      price_change: false
      update: false
      error: true
  - id: breliance-com
    name: breliance
    base_url: https://www.breliance.com
    source_url: "https://www.breliance.com/collections/all?&type=collections&page_size=48&sort=created-descending&slug=all"
    adapter: embedded_page_products
    interval_minutes: 15
    enabled: true
    full_scan_pages: 40
    incremental_pages: 1
    notify:
      new_product: true
      price_change: false
      update: false
      error: true
  - id: wilddrootss-com
    name: wilddrootss
    base_url: https://www.wilddrootss.com
    source_url: "https://www.wilddrootss.com/search?page=1&sort=created-descending"
    adapter: embedded_page_products
    interval_minutes: 15
    enabled: true
    full_scan_pages: 40
    incremental_pages: 1
    notify:
      new_product: true
      price_change: false
      update: false
      error: true
  - id: beast-fox-com
    name: beast-fox
    base_url: https://www.beast-fox.com
    source_url: "https://www.beast-fox.com/search?type=search&page_size=12&price_4=0%3A1000&page=1&sort=created-descending"
    adapter: embedded_page_products
    interval_minutes: 15
    enabled: true
    full_scan_pages: 40
    incremental_pages: 1
    notify:
      new_product: true
      price_change: false
      update: false
      error: true
  - id: dreamofup-com
    name: dreamofup
    base_url: https://www.dreamofup.com
    source_url: "https://www.dreamofup.com/search?q=&page=1"
    adapter: embedded_page_products
    interval_minutes: 15
    enabled: true
    full_scan_pages: 40
    incremental_pages: 1
    notify:
      new_product: true
      price_change: false
      update: false
      error: true
  - id: tidepick-com
    name: tidepick
    base_url: https://www.tidepick.com
    source_url: "https://www.tidepick.com/search?q="
    adapter: embedded_page_products
    interval_minutes: 15
    enabled: true
    full_scan_pages: 40
    incremental_pages: 1
    notify:
      new_product: true
      price_change: false
      update: false
      error: true
  - id: milorza-com
    name: milorza
    base_url: https://www.milorza.com
    source_url: "https://www.milorza.com/collections/all"
    adapter: embedded_page_products
    interval_minutes: 15
    enabled: true
    full_scan_pages: 40
    incremental_pages: 1
    notify:
      new_product: true
      price_change: false
      update: false
      error: true
  - id: practiqustin-com
    name: practiqustin
    base_url: https://www.practiqustin.com
    source_url: "https://www.practiqustin.com/collections/all?&type=collections&page_size=48&sort=published-descending&slug=all"
    adapter: embedded_page_products
    interval_minutes: 15
    enabled: true
    full_scan_pages: 40
    incremental_pages: 1
    notify:
      new_product: true
      price_change: false
      update: false
      error: true
  - id: forecastg-com
    name: forecastg
    base_url: https://www.forecastg.com
    source_url: "https://www.forecastg.com/collections/all"
    adapter: embedded_page_products
    interval_minutes: 15
    enabled: true
    full_scan_pages: 40
    incremental_pages: 1
    notify:
      new_product: true
      price_change: false
      update: false
      error: true
  - id: asementribut-com
    name: asementribut
    base_url: https://www.asementribut.com
    source_url: "https://www.asementribut.com/collections/all"
    adapter: embedded_page_products
    interval_minutes: 15
    enabled: true
    full_scan_pages: 40
    incremental_pages: 1
    notify:
      new_product: true
      price_change: false
      update: false
      error: true
  - id: gardenerk-com
    name: gardenerk
    base_url: https://gardenerk.com
    source_url: "https://gardenerk.com/collections/all"
    adapter: embedded_page_products
    interval_minutes: 15
    enabled: true
    full_scan_pages: 40
    incremental_pages: 1
    notify:
      new_product: true
      price_change: false
      update: false
      error: true
  - id: allfucore-com
    name: allfucore
    base_url: https://allfucore.com
    source_url: "https://allfucore.com/search?q="
    adapter: embedded_page_products
    interval_minutes: 15
    enabled: true
    full_scan_pages: 40
    incremental_pages: 1
    notify:
      new_product: true
      price_change: false
      update: false
      error: true
  - id: nzeindustrio-com
    name: nzeindustrio
    base_url: https://www.nzeindustrio.com
    source_url: "https://www.nzeindustrio.com/collections/all-product?&type=collections&page_size=48&price_2=0%3A998&page=1&slug=all-product&sort=created-descending"
    adapter: embedded_page_products
    interval_minutes: 15
    enabled: true
    full_scan_pages: 40
    incremental_pages: 1
    notify:
      new_product: true
      price_change: false
      update: false
      error: true
  - id: endeavoir-com
    name: endeavoir
    base_url: https://www.endeavoir.com
    source_url: "https://www.endeavoir.com/search?sort=published-descending&page=1"
    adapter: embedded_page_products
    interval_minutes: 15
    enabled: true
    full_scan_pages: 40
    incremental_pages: 1
    notify:
      new_product: true
      price_change: false
      update: false
      error: true
  - id: speedvel-com
    name: speedvel
    base_url: https://www.speedvel.com
    source_url: "https://www.speedvel.com/search?q=&page=1"
    adapter: embedded_page_products
    interval_minutes: 15
    enabled: true
    full_scan_pages: 40
    incremental_pages: 1
    notify:
      new_product: true
      price_change: false
      update: false
      error: true
  - id: donna-spring-com
    name: donna-spring
    base_url: https://www.donna-spring.com
    source_url: "https://www.donna-spring.com/collections/all?&type=collections&page_size=32&sort=created-descending&slug=all"
    adapter: embedded_page_products
    interval_minutes: 15
    enabled: true
    full_scan_pages: 40
    incremental_pages: 1
    notify:
      new_product: true
      price_change: false
      update: false
      error: true
  - id: cocopopcornshop-com
    name: cocopopcornshop
    base_url: https://cocopopcornshop.com
    source_url: "https://cocopopcornshop.com/collections/all?&type=collections&page_size=48&sort=created-descending&slug=all"
    adapter: embedded_page_products
    interval_minutes: 15
    enabled: true
    full_scan_pages: 40
    incremental_pages: 1
    notify:
      new_product: true
      price_change: false
      update: false
      error: true
  - id: leaderiship-com
    name: leaderiship
    base_url: https://www.leaderiship.com
    source_url: "https://www.leaderiship.com/collections/all"
    adapter: embedded_page_products
    interval_minutes: 15
    enabled: true
    full_scan_pages: 40
    incremental_pages: 1
    notify:
      new_product: true
      price_change: false
      update: false
      error: true
  - id: geelolo-com
    name: geelolo
    base_url: https://www.geelolo.com
    source_url: "https://www.geelolo.com/search"
    adapter: embedded_page_products
    interval_minutes: 15
    enabled: true
    full_scan_pages: 40
    incremental_pages: 1
    notify:
      new_product: true
      price_change: false
      update: false
      error: true
  - id: coloureshop-com
    name: coloureshop
    base_url: https://coloureshop.com
    source_url: "https://coloureshop.com/search?sort=created-descending"
    adapter: embedded_page_products
    interval_minutes: 15
    enabled: true
    full_scan_pages: 40
    incremental_pages: 1
    notify:
      new_product: true
      price_change: false
      update: false
      error: true
  - id: progressty-com
    name: progressty
    base_url: https://www.progressty.com
    source_url: "https://www.progressty.com/search?type=search&page_size=12&q=&price_4=0.00:999.31&page=1"
    adapter: embedded_page_products
    interval_minutes: 15
    enabled: true
    full_scan_pages: 40
    incremental_pages: 1
    notify:
      new_product: true
      price_change: false
      update: false
      error: true
  - id: dehorss-com
    name: dehorss
    base_url: https://dehorss.com
    source_url: "https://dehorss.com/collections/all?&type=collections&page_size=60&sort=published-descending&slug=all"
    adapter: embedded_page_products
    interval_minutes: 15
    enabled: true
    full_scan_pages: 40
    incremental_pages: 1
    notify:
      new_product: true
      price_change: false
      update: false
      error: true
  - id: speculatek-com
    name: speculatek
    base_url: https://www.speculatek.com
    source_url: "https://www.speculatek.com/collections/all?&type=collections&page_size=48&sort=published-descending&slug=all"
    adapter: embedded_page_products
    interval_minutes: 15
    enabled: true
    full_scan_pages: 40
    incremental_pages: 1
    notify:
      new_product: true
      price_change: false
      update: false
      error: true
  - id: kivoret-com
    name: kivoret
    base_url: https://www.kivoret.com
    source_url: "https://www.kivoret.com/collections/all?&type=collections&page_size=48&sort=published-descending&slug=all"
    adapter: embedded_page_products
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
