"""DingTalk custom-robot webhook notifier.

Docs: https://open.dingtalk.com/document/orgapp/custom-robots-send-group-messages

Key differences vs Feishu:
- Signing:  timestamp + "\\n" + secret -> HMAC-SHA256 -> base64 -> URL-encoded
             appended to the request URL as &timestamp=..&sign=..
- Markdown supports remote image URLs natively (msgtype=markdown).
- Rate limit: 20 messages/min per robot.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request


class NotifyError(RuntimeError):
    pass


class DingTalkWebhookNotifier:
    def __init__(self, webhook_url: str, secret: str = "", timeout: int = 15, verify_ssl: bool = True):
        self.webhook_url = webhook_url
        self.secret = secret
        self.timeout = timeout
        self.verify_ssl = verify_ssl

    def enabled(self) -> bool:
        return bool(self.webhook_url)

    def send_text(self, text: str) -> None:
        self._send({"msgtype": "text", "text": {"content": text}})

    def send_markdown(self, title: str, markdown: str) -> None:
        """Send a markdown message (renders remote images via ![url])."""
        if not self.webhook_url:
            return
        self._send({"msgtype": "markdown", "markdown": {"title": title[:100], "text": markdown}})

    def send_action_card(self, title: str, markdown: str, url: str, url_text: str = "查看商品") -> None:
        """Send an actionCard with a single jump button."""
        if not self.webhook_url:
            return
        self._send(
            {
                "msgtype": "actionCard",
                "actionCard": {
                    "title": title[:100],
                    "text": markdown,
                    "singleURL": url,
                    "singleTitle": url_text,
                    "btnOrientation": "1",
                },
            }
        )

    def _send(self, payload: dict) -> None:
        if not self.webhook_url:
            return
        target_url = self.webhook_url
        if self.secret:
            timestamp = str(round(time.time() * 1000))
            target_url += f"&timestamp={timestamp}&sign={self._sign(timestamp)}"
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            target_url,
            data=data,
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )
        try:
            self._post(req, verify=self.verify_ssl)
        except urllib.error.URLError as exc:
            # SSL cert verify failure (常见于本机代理 MITM 自签名证书) -> retry without verify
            if isinstance(exc.reason, ssl.SSLError) and "CERTIFICATE_VERIFY_FAILED" in str(exc.reason):
                try:
                    self._post(req, verify=False)
                    return
                except urllib.error.URLError as exc2:
                    raise NotifyError(f"DingTalk request failed: {exc2}") from exc2
            raise NotifyError(f"DingTalk request failed: {exc}") from exc

    def _post(self, req, verify: bool = True) -> None:
        if verify:
            response = urllib.request.urlopen(req, timeout=self.timeout)
        else:
            context = ssl._create_unverified_context()
            response = urllib.request.urlopen(req, timeout=self.timeout, context=context)
        body = response.read().decode("utf-8", errors="replace")
        status = getattr(response, "status", 200)
        if status >= 300:
            raise NotifyError(f"DingTalk HTTP {status}: {body[:300]}")
        try:
            parsed = json.loads(body)
            code = parsed.get("errcode", 0)
            if code != 0:
                raise NotifyError(f"DingTalk API error: {body[:300]}")
        except json.JSONDecodeError:
            pass

    def _sign(self, timestamp: str) -> str:
        # DingTalk: hmac(secret, timestamp\nsecret)
        secret_enc = self.secret.encode("utf-8")
        string_to_sign = f"{timestamp}\n{self.secret}".encode("utf-8")
        digest = hmac.new(secret_enc, string_to_sign, digestmod=hashlib.sha256).digest()
        return urllib.parse.quote_plus(base64.b64encode(digest))