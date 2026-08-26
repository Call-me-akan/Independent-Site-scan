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