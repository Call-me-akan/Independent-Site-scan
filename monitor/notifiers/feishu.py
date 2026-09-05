from __future__ import annotations

import base64
import hashlib
import hmac
import json
import ssl
import time
import urllib.error
import urllib.request

from .base import NotifyError


class FeishuWebhookNotifier:
    def __init__(self, webhook_url: str, secret: str = "", timeout: int = 15, verify_ssl: bool = True):
        self.webhook_url = webhook_url
        self.secret = secret
        self.timeout = timeout
        self.verify_ssl = verify_ssl

    def enabled(self) -> bool:
        return bool(self.webhook_url)

    def send_text(self, text: str) -> None:
        self._send({"msg_type": "text", "content": {"text": text}})

    def send_card(self, title: str, markdown: str, url: str = "", url_text: str = "查看商品") -> None:
        """Send a Feishu interactive card message.

        Note: Feishu custom-bot webhook cards cannot embed remote images
        (requires image_key from an upload API), so product image URLs are
        shown in the markdown body as small text.
        """
        if not self.webhook_url:
            return
        elements = []
        if markdown:
            elements.append({"tag": "markdown", "content": markdown})
        if url:
            elements.append(
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {"tag": "plain_text", "content": url_text},
                            "type": "primary",
                            "url": url,
                        }
                    ],
                }
            )
        card = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {"tag": "plain_text", "content": title},
                    "template": "blue",
                },
                "elements": elements,
            },
        }
        self._send(card)

    def _send(self, payload: dict) -> None:
        if not self.webhook_url:
            return
        if self.secret:
            timestamp = str(int(time.time()))
            payload["timestamp"] = timestamp
            payload["sign"] = self._sign(timestamp)
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            self.webhook_url,
            data=data,
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )
        try:
            self._post(req, verify=self.verify_ssl)
        except urllib.error.URLError as exc:
            # SSL 证书校验失败（常见于本机代理 MITM 自签名证书）→ 自动降级为不校验重试一次
            if isinstance(exc.reason, ssl.SSLError) and "CERTIFICATE_VERIFY_FAILED" in str(exc.reason):
                try:
                    self._post(req, verify=False)
                    return
                except urllib.error.URLError as exc2:
                    raise NotifyError(f"Feishu request failed: {exc2}") from exc2
            raise NotifyError(f"Feishu request failed: {exc}") from exc

    def _post(self, req, verify: bool = True) -> None:
        response = self._urlopen(req, verify=verify)
        body = response.read().decode("utf-8", errors="replace")
        status = getattr(response, "status", 200)
        if status >= 300:
            raise NotifyError(f"Feishu HTTP {status}: {body[:300]}")
        try:
            parsed = json.loads(body)
            code = parsed.get("code")
            if code not in (None, 0):
                raise NotifyError(f"Feishu API error: {body[:300]}")
        except json.JSONDecodeError:
            pass

    def _urlopen(self, req, verify: bool = True):
        if verify:
            return urllib.request.urlopen(req, timeout=self.timeout)
        context = ssl._create_unverified_context()
        return urllib.request.urlopen(req, timeout=self.timeout, context=context)

    def _sign(self, timestamp: str) -> str:
        string_to_sign = f"{timestamp}\n{self.secret}".encode("utf-8")
        digest = hmac.new(string_to_sign, digestmod=hashlib.sha256).digest()
        return base64.b64encode(digest).decode("utf-8")
