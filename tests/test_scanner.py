from __future__ import annotations

from monitor import db as dbmod
from monitor.config import AppConfig, SiteConfig, FeishuConfig, StorageConfig, ExportConfig
from monitor.notifiers.base import NotifyError
from monitor.notifiers.feishu import FeishuWebhookNotifier
from monitor.scanner import scan_site


class FakeAdapter:
    """迭代 1 页、返回 3 个商品的假适配器。"""

    def __init__(self, products):
        self._products = products

    def iter_product_pages(self, max_pages=1, start_page=1):
        yield start_page, self._products


def _make_config(tmp_path, feishu_url: str = "https://open.feishu.cn/open-apis/bot/v2/hook/dummy-test"):
    site = SiteConfig(
        id="test-site",
        name="Test Site",
        base_url="https://test.example.com",
        source_url="https://test.example.com/collections/all",
        adapter="shopify_products_json",
        interval_minutes=15,
        enabled=True,
        full_scan_pages=40,
        incremental_pages=1,
        notify={"new_product": True, "price_change": False, "update": False, "error": True},
    )
    cfg = AppConfig(
        sites=[site],
        feishu=FeishuConfig(webhook_url=feishu_url),
        storage=StorageConfig(path=str(tmp_path / "monitor.db")),
        export=ExportConfig(dir=str(tmp_path / "exports")),
    )
    return cfg


def _products():
    return [
        {
            "id": f"p{i}",
            "title": f"Product {i}",
            "handle": f"product-{i}",
            "url": f"https://test.example.com/products/product-{i}",
            "price_min": 9.9,
            "price_max": 9.9,
            "image": f"https://img.example.com/{i}.png",
            "created_at": "2026-09-01T00:00:00Z",
            "published_at": "2026-09-01T00:00:00Z",
            "updated_at": "2026-09-01T00:00:00Z",
            "vendor": "",
            "product_type": "",
            "tags": [],
            "body_html": "",
            "variants": [],
            "images": [],
            "raw": {},
        }
        for i in range(3)
    ]


def _seed_baseline(tmp_path):
    """建一个 baseline 已完成的站点（这样扫描是 incremental 且会触发通知）。"""
    cfg = _make_config(tmp_path)
    dbmod.init_db(cfg.storage.path)
    with dbmod.db(cfg.storage.path) as conn:
        dbmod.upsert_site(conn, cfg.sites[0])
        dbmod.set_baseline_complete(conn, cfg.sites[0].id, True)
    return cfg


def test_notify_failure_does_not_fail_scan(tmp_path, monkeypatch):
    """推送失败（NotifyError）不应让扫描报错：扫描成功、事件留待补发。"""
    cfg = _seed_baseline(tmp_path)

    def boom(self, *args, **kwargs):
        raise NotifyError("DingTalk API error: 系统繁忙")

    monkeypatch.setattr(FeishuWebhookNotifier, "send_card", boom)
    monkeypatch.setattr("monitor.scanner.get_adapter", lambda *a, **k: FakeAdapter(_products()))

    result = scan_site(cfg, cfg.sites[0], notify=True)

    assert result.scan_type == "incremental"
    assert result.product_count == 3
    assert result.new_count == 3
    assert result.notified is False  # 推送失败但扫描成功

    with dbmod.db(cfg.storage.path) as conn:
        run = conn.execute("SELECT status FROM scan_runs ORDER BY id DESC LIMIT 1").fetchone()
        assert run["status"] == "success"  # 不再卡在 running
        events = conn.execute("SELECT event_type, notified FROM events").fetchall()
        types = {(e["event_type"], e["notified"]) for e in events}
        assert ("new_product", 0) in types  # 新品事件保留待发
        assert ("notify_error", 0) in types  # 失败原因已记录
        assert dbmod.pending_notify_events(conn).__len__() == 3  # 3 个新品待补发


def test_notify_success_marks_events_notified(tmp_path, monkeypatch):
    cfg = _seed_baseline(tmp_path)
    monkeypatch.setattr(FeishuWebhookNotifier, "send_card", lambda self, *a, **k: None)
    monkeypatch.setattr("monitor.scanner.get_adapter", lambda *a, **k: FakeAdapter(_products()))

    result = scan_site(cfg, cfg.sites[0], notify=True)

    assert result.notified is True
    with dbmod.db(cfg.storage.path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM events WHERE notified = 1").fetchone()[0] == 3


def test_adapter_error_leaves_failed_record(tmp_path, monkeypatch):
    """适配器失败（404/HTML 挑战页）时必须落库一条 failed 记录，不能再被回滚吞掉。"""
    cfg = _seed_baseline(tmp_path)
    from monitor.adapters.base import AdapterError

    def boom(*a, **k):
        raise AdapterError("HTTP 404: .../products.json")

    monkeypatch.setattr("monitor.scanner.get_adapter", boom)

    try:
        scan_site(cfg, cfg.sites[0], notify=True)
        assert False, "应抛出 AdapterError"
    except AdapterError:
        pass

    with dbmod.db(cfg.storage.path) as conn:
        run = conn.execute("SELECT status, error_message FROM scan_runs ORDER BY id DESC LIMIT 1").fetchone()
        assert run["status"] == "failed"
        assert "HTTP 404" in run["error_message"]
        assert conn.execute("SELECT COUNT(*) FROM events WHERE event_type = 'scan_error'").fetchone()[0] == 1
