from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
import urllib.error
import urllib.request


class NotifyError(RuntimeError):
    pass


class FeishuWebhookNotifier:
    def __init__(self, webhook_url: str, secret: str = "", timeout: int = 15):
        self.webhook_url = webhook_url
        self.secret = secret
        self.timeout = timeout

    def enabled(self) -> bool:
        return bool(self.webhook_url)

    def send_text(self, text: str) -> None:
        if not self.webhook_url:
            return
        payload = {
            "msg_type": "text",
            "content": {"text": text},
        }
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
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = resp.read().decode("utf-8", errors="replace")
                if getattr(resp, "status", 200) >= 300:
                    raise NotifyError(f"Feishu HTTP {resp.status}: {body[:300]}")
                try:
                    parsed = json.loads(body)
                    code = parsed.get("code")
                    if code not in (None, 0):
                        raise NotifyError(f"Feishu API error: {body[:300]}")
                except json.JSONDecodeError:
                    pass
        except urllib.error.URLError as exc:
            raise NotifyError(f"Feishu request failed: {exc}") from exc

    def _sign(self, timestamp: str) -> str:
        string_to_sign = f"{timestamp}\n{self.secret}".encode("utf-8")
        digest = hmac.new(string_to_sign, digestmod=hashlib.sha256).digest()
        return base64.b64encode(digest).decode("utf-8")
