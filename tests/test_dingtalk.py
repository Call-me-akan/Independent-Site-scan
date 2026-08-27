import urllib.parse

from monitor.notifiers.dingtalk import DingTalkWebhookNotifier
from monitor.scanner import format_new_products_dingtalk
from monitor.config import SiteConfig


def test_dingtalk_sign():
    """DingTalk sign = quote_plus(base64(hmac_sha256(secret, timestamp\\nsecret)))."""
    notifier = DingTalkWebhookNotifier("https://oapi.dingtalk.com/robot/send?access_token=x", secret="SECtest")
    sign = notifier._sign("1735000000000")
    import base64
    import hashlib
    import hmac as hmac_mod

    string_to_sign = "1735000000000\nSECtest".encode("utf-8")
    digest = hmac_mod.new(b"SECtest", string_to_sign, digestmod=hashlib.sha256).digest()
    expected = urllib.parse.quote_plus(base64.b64encode(digest).decode("utf-8"))
    assert sign == expected


def test_send_markdown_payload(tmp_path):
    notifier = DingTalkWebhookNotifier.__new__(DingTalkWebhookNotifier)
    notifier.webhook_url = "https://oapi.dingtalk.com/robot/send?access_token=x"
    notifier.secret = "SECtest"
    notifier.timeout = 1
    notifier.verify_ssl = True
    payload = {}
    notifier._send = lambda p: payload.update(p)
    notifier.send_markdown("标题", "**商品**  \n![图](https://img.com/a.png)")
    assert payload["msgtype"] == "markdown"
    assert payload["markdown"]["title"] == "标题"
    assert "![图](https://img.com/a.png)" in payload["markdown"]["text"]


def test_send_action_card_payload():
    notifier = DingTalkWebhookNotifier.__new__(DingTalkWebhookNotifier)
    notifier.webhook_url = "https://oapi.dingtalk.com/robot/send?access_token=x"
    notifier.secret = ""
    notifier.timeout = 1
    notifier.verify_ssl = True
    payload = {}
    notifier._send = lambda p: payload.update(p)
    notifier.send_action_card("标题", "正文", "https://t.com/p/1", "查看商品")
    assert payload["msgtype"] == "actionCard"
    assert payload["actionCard"]["singleURL"] == "https://t.com/p/1"


def test_format_dingtalk_markdown_includes_image():
    site = SiteConfig(id="t", name="Test", base_url="https://t.com")
    product = {
        "title": "Nice Item",
        "price_min": 5.5,
        "price_max": 5.5,
        "published_at": "2026-08-27T00:00:00Z",
        "url": "https://t.com/products/nice",
        "image": "https://img.com/a.png",
    }
    title, markdown, url = format_new_products_dingtalk(site, [product])
    assert "1 个新品" in title
    assert "Nice Item" in markdown
    assert "![图片]" in markdown or "![](" in markdown
    assert "https://img.com/a.png" in markdown
    assert url == "https://t.com/products/nice"