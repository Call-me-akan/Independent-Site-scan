"""Shared notifier exceptions.

IMPORTANT: all notifier implementations MUST raise this same NotifyError class,
so callers (scanner, webui) can catch it regardless of which notifier is used.

Historical bug: feishu.py and dingtalk.py each defined their own
``class NotifyError(RuntimeError)``, so ``except NotifyError`` in scanner.py
(imported from feishu) silently missed DingTalk failures — a DingTalk
"系统繁忙"/rate-limit error escaped and aborted the whole scan, leaving the
scan_run stuck in "running" and new-product events stuck pending.
"""


class NotifyError(RuntimeError):
    """Raised when a webhook notification fails (network/API/rate-limit)."""
