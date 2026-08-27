from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Missing dependency: PyYAML. Run: pip install -r requirements.txt") from exc


DEFAULT_CONFIG_PATH = Path("config.yaml")

try:
    # MONITOR_AGENT_DIR 环境变量可覆盖固定数据目录（打包版优先使用）
    _data_dir = Path(os.environ.get("MONITOR_AGENT_DIR", "")).expanduser() if os.environ.get("MONITOR_AGENT_DIR") else None
except NameError:
    _data_dir = None


def data_dir() -> Path:
    """Resolve where config/data live.

    Priority:
      1. $MONITOR_AGENT_DIR
      2. PyInstaller packaged binary -> $HOME/monitor-agent   (fixed, ignores cwd)
      3. source/dev run with existing ./config.yaml -> cwd      (compat)
      4. otherwise -> $HOME/monitor-agent

    Packaged binaries ALWAYS use the fixed location so users see the same
    sites/webhooks no matter where they run the binary from (fixes the
    'config in Downloads vs elsewhere' confusion).
    """
    import os as _os
    import sys as _sys

    env = _os.environ.get("MONITOR_AGENT_DIR", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    packaged = getattr(_sys, "frozen", False)
    if packaged:
        # Windows 直接读用户目录(USERPROFILE)，macOS/Linux 用 HOME
        home = Path(_os.environ.get("USERPROFILE") or _os.path.expanduser("~"))
        return (home / "monitor-agent").resolve()
    old = Path("config.yaml")
    if old.exists():
        # 开发/迁移场景：工作目录已有 config 就继续用它
        return Path.cwd().resolve()
    return (Path.home() / "monitor-agent").resolve()


def config_path() -> Path:
    return data_dir() / "config.yaml"


def storage_path() -> Path:
    return data_dir() / "data" / "monitor.db"


def export_path() -> Path:
    return data_dir() / "exports"

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


def init_config(path: Path | None = None) -> Path:
    """Create/merge config at the resolved path (default: fixed data dir).

    - If config doesn't exist: write the full preset template (31 sites + empty webhooks).
    - If config exists: merge the preset sites by id — any preset site the user
      doesn't already have gets appended; user's own sites/webhooks are untouched.
    """
    if path is None:
        path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(DEFAULT_CONFIG_YAML, encoding="utf-8")
        return path
    # Merge: load existing, add preset sites that are missing
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        existing_ids = {str(s.get("id")) for s in raw.get("sites") or []}
        template = yaml.safe_load(DEFAULT_CONFIG_YAML) or {}
        added = []
        for site in template.get("sites") or []:
            if str(site.get("id")) not in existing_ids:
                raw.setdefault("sites", []).append(site)
                existing_ids.add(str(site.get("id")))
                added.append(site.get("id"))
        if added:
            path.write_text(yaml.safe_dump(raw, allow_unicode=True, sort_keys=False), encoding="utf-8")
            print(f"[init_config] 已合并预设站点: {', '.join(added)}")
        else:
            print("[init_config] 站点已是最新，无需合并")
    except yaml.YAMLError:
        # 旧配置损坏，备份后重建
        backup = path.with_suffix(path.suffix + ".bad")
        path.rename(backup)
        path.write_text(DEFAULT_CONFIG_YAML, encoding="utf-8")
        print(f"[init_config] 配置损坏，备份为 {backup.name} 并重建")
    return path


def load_config(path: Path | None = None) -> AppConfig:
    if path is None:
        path = config_path()
    if not path.exists():
        raise SystemExit(f"Config not found: {path}. Run: python -m monitor.cli init")
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return parse_config(raw)


def save_config(config: AppConfig, path: Path | None = None) -> None:
    if path is None:
        path = config_path()
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
    base = data_dir()
    storage_raw = dict(raw.get("storage") or {})
    export_raw = dict(raw.get("export") or {})
    if not (storage_raw.get("path") or "").startswith(("/", "~", "$")):
        storage_raw["path"] = str(base / (storage_raw.get("path") or "data/monitor.db"))
    if not (export_raw.get("dir") or "").startswith(("/", "~", "$")):
        export_raw["dir"] = str(base / (export_raw.get("dir") or "exports"))
    return AppConfig(
        sites=sites,
        feishu=FeishuConfig(**(raw.get("feishu") or {})),
        dingtalk=DingTalkConfig(**(raw.get("dingtalk") or {})),
        storage=StorageConfig(**storage_raw),
        export=ExportConfig(**export_raw),
    )


def get_site(config: AppConfig, site_id: str) -> SiteConfig:
    for site in config.sites:
        if site.id == site_id:
            return site
    raise SystemExit(f"Unknown site: {site_id}")
