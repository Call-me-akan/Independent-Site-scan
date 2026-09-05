import json

from monitor.notifiers.feishu import FeishuWebhookNotifier
from monitor.notifiers.dingtalk import DingTalkWebhookNotifier
from monitor.scanner import format_new_products_card
from monitor.config import SiteConfig


def test_notify_error_is_shared_class():
    """feishu/dingtalk 必须抛同一个 NotifyError，scanner 才能统一捕获。"""
    from monitor.notifiers.feishu import NotifyError as FeishuNotifyError
    from monitor.notifiers.dingtalk import NotifyError as DingTalkNotifyError
    from monitor.notifiers.base import NotifyError as BaseNotifyError

    assert FeishuNotifyError is BaseNotifyError
    assert DingTalkNotifyError is BaseNotifyError
    assert FeishuNotifyError is DingTalkNotifyError


def test_send_card_payload_is_interactive():
    """Verify card payload structure without hitting network."""
    notifier = FeishuWebhookNotifier.__new__(FeishuWebhookNotifier)
    notifier.webhook_url = "https://open.feishu.cn/open-apis/bot/v2/hook/test"
    notifier.secret = ""
    notifier.timeout = 1
    payload = {}
    # monkeypatch _send to capture payload
    notifier._send = lambda p: payload.update(p)
    notifier.send_card("测试标题", "**商品**  \n价格信息", url="https://example.com/p/1")
    assert payload["msg_type"] == "interactive"
    assert payload["card"]["header"]["title"]["content"] == "测试标题"
    assert payload["card"]["elements"][0]["tag"] == "markdown"
    assert payload["card"]["elements"][1]["tag"] == "action"
    assert payload["card"]["elements"][1]["actions"][0]["url"] == "https://example.com/p/1"


def test_format_card_produces_title_markdown_url():
    site = SiteConfig(id="t", name="Test", base_url="https://t.com")
    product = {
        "title": "Nice Product",
        "price_min": 9.99,
        "price_max": 9.99,
        "published_at": "2026-08-27T00:00:00Z",
        "url": "https://t.com/products/nice",
        "image": "https://img.com/a.png",
    }
    title, markdown, url = format_new_products_card(site, [product])
    assert "Test" in title
    assert "1 个新品" in title
    assert "Nice Product" in markdown
    assert "💰 9.99" in markdown
    assert "https://img.com/a.png" in markdown
    assert url == "https://t.com/products/nice"