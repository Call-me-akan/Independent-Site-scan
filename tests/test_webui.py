from __future__ import annotations

import json

import pytest

from monitor.config import DEFAULT_CONFIG_YAML, load_config, save_config
from monitor.webui import create_app

from monitor.config import SiteConfig, FeishuConfig, StorageConfig, ExportConfig, AppConfig


def make_config(tmp_path):
    cfg = AppConfig(
        sites=[
            SiteConfig(
                id="test-site",
                name="Test Site",
                base_url="https://test.example.com",
                source_url="https://test.example.com/collections/all",
                adapter="shopify_products_json",
                interval_minutes=1,
                enabled=True,
                full_scan_pages=1,
                incremental_pages=1,
                notify={"new_product": True, "price_change": False, "update": False, "error": True},
            )
        ],
        feishu=FeishuConfig(),
        storage=StorageConfig(path=str(tmp_path / "data" / "monitor.db")),
        export=ExportConfig(dir=str(tmp_path / "exports")),
    )
    cfg_path = tmp_path / "config.yaml"
    save_config(cfg, cfg_path)
    return cfg_path


@pytest.fixture()
def app(tmp_path):
    cfg_path = make_config(tmp_path)
    app = create_app(str(cfg_path))
    app.config["TESTING"] = True
    return app


@pytest.fixture()
def client(app):
    return app.test_client()


def test_index_page(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "独立站商品监控" in resp.get_data(as_text=True)


def test_api_status(client):
    resp = client.get("/api/status")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["feishu_configured"] is False
    assert len(data["sites"]) == 1
    assert data["sites"][0]["id"] == "test-site"
    assert data["sites"][0]["products"] == 0


def test_api_add_site(client, tmp_path):
    resp = client.post(
        "/api/sites",
        json={
            "id": "new-site",
            "name": "New Site",
            "url": "https://newsite.com",
            "adapter": "embedded_page_products",
            "source_url": "https://newsite.com/search?q=",
            "interval": 30,
        },
    )
    assert resp.status_code == 200
    assert resp.get_json()["ok"] is True

    # verify persisted
    cfg = load_config(tmp_path / "config.yaml")
    assert any(s.id == "new-site" for s in cfg.sites)


def test_api_add_site_requires_url(client):
    resp = client.post("/api/sites", json={"id": "x"})
    assert resp.status_code == 400


def test_api_delete_site(client, tmp_path):
    resp = client.delete("/api/sites/test-site")
    assert resp.status_code == 200
    cfg = load_config(tmp_path / "config.yaml")
    assert all(s.id != "test-site" for s in cfg.sites)


def test_api_toggle_site(client, tmp_path):
    resp = client.post("/api/sites/test-site/toggle")
    assert resp.status_code == 200
    assert resp.get_json()["enabled"] is False
    cfg = load_config(tmp_path / "config.yaml")
    assert cfg.sites[0].enabled is False


def test_api_feishu_roundtrip(client, tmp_path):
    resp = client.get("/api/feishu")
    assert resp.get_json()["configured"] is False

    resp = client.post("/api/feishu", json={"webhook_url": "https://open.feishu.cn/open-apis/bot/v2/hook/abc", "secret": ""})
    assert resp.get_json()["ok"] is True

    cfg = load_config(tmp_path / "config.yaml")
    assert cfg.feishu.webhook_url == "https://open.feishu.cn/open-apis/bot/v2/hook/abc"

    resp = client.get("/api/feishu")
    assert resp.get_json()["configured"] is True


def test_api_feishu_test_empty(client):
    resp = client.post("/api/feishu/test")
    assert resp.status_code == 400


def test_api_products_empty(client):
    resp = client.get("/api/products?site=test-site")
    assert resp.status_code == 200
    assert resp.get_json()["products"] == []


def test_api_export_requires_site(client):
    resp = client.get("/api/export")
    assert resp.status_code == 400


def test_config_template_has_sites(tmp_path):
    from monitor.config import DEFAULT_CONFIG_PATH, init_config

    p = tmp_path / "config.yaml"
    init_config(p)
    text = p.read_text(encoding="utf-8")
    assert "sites:" in text
    assert "feishu:" in text

def test_send_pending_drains_full_backlog(client, tmp_path, monkeypatch):
    """250 条积压事件一次「发送待发事件」应全部处理完，不再卡在 100 条上限。"""
    from monitor import db as dbmod
    from monitor.config import load_config, save_config
    from monitor.notifiers.feishu import FeishuWebhookNotifier
    from monitor.notifiers.dingtalk import DingTalkWebhookNotifier

    cfg = load_config(tmp_path / "config.yaml")
    cfg.feishu.webhook_url = "https://open.feishu.cn/open-apis/bot/v2/hook/dummy"
    cfg.dingtalk.webhook_url = "https://oapi.dingtalk.com/robot/send?access_token=dummy"
    save_config(cfg, tmp_path / "config.yaml")

    # 造 250 条未通知的新品事件
    dbmod.init_db(cfg.storage.path)
    with dbmod.db(cfg.storage.path) as conn:
        for i in range(250):
            dbmod.insert_event(
                conn,
                "test-site",
                "new_product",
                str(i),
                f"Product {i}",
                {"product": {"id": str(i), "title": f"Product {i}", "url": f"https://test.example.com/products/p{i}"}},
                notified=False,
            )
        assert len(dbmod.pending_notify_events(conn)) == 250

    # 屏蔽真实网络发送
    sent = []
    monkeypatch.setattr(FeishuWebhookNotifier, "send_card", lambda self, *a, **k: sent.append(a))
    monkeypatch.setattr(DingTalkWebhookNotifier, "send_markdown", lambda self, *a, **k: sent.append(a))

    resp = client.post("/api/send-pending", json={})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["events"] == 250
    assert data["notified_events"] == 250
    assert data["remaining"] == 0
    # 每个 notifier 各发一条聚合消息（按站点聚合）
    assert len(sent) == 2

    with dbmod.db(cfg.storage.path) as conn:
        assert len(dbmod.pending_notify_events(conn)) == 0


def test_send_pending_all_failed_keeps_events(client, tmp_path, monkeypatch):
    """所有通道都发送失败时，事件不能被标记为已通知（否则积压被吞掉）。"""
    from monitor import db as dbmod
    from monitor.config import load_config, save_config
    from monitor.notifiers.base import NotifyError
    from monitor.notifiers.feishu import FeishuWebhookNotifier
    from monitor.notifiers.dingtalk import DingTalkWebhookNotifier

    cfg = load_config(tmp_path / "config.yaml")
    cfg.feishu.webhook_url = "https://open.feishu.cn/open-apis/bot/v2/hook/dummy"
    cfg.dingtalk.webhook_url = "https://oapi.dingtalk.com/robot/send?access_token=dummy"
    save_config(cfg, tmp_path / "config.yaml")

    dbmod.init_db(cfg.storage.path)
    with dbmod.db(cfg.storage.path) as conn:
        dbmod.insert_event(conn, "test-site", "new_product", "1", "P1", {"product": {"id": "1", "title": "P1"}}, notified=False)
        dbmod.insert_event(conn, "test-site", "new_product", "2", "P2", {"product": {"id": "2", "title": "P2"}}, notified=False)

    def fail_feishu(self, *a, **k):
        raise NotifyError("feishu down")

    def fail_dingtalk(self, *a, **k):
        raise NotifyError("dingtalk down")

    monkeypatch.setattr(FeishuWebhookNotifier, "send_card", fail_feishu)
    monkeypatch.setattr(DingTalkWebhookNotifier, "send_markdown", fail_dingtalk)

    resp = client.post("/api/send-pending", json={})
    assert resp.status_code == 500

    with dbmod.db(cfg.storage.path) as conn:
        assert len(dbmod.pending_notify_events(conn)) == 2  # 仍待发
