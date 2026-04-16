"""
Phone push via ntfy.sh (no account, no keys). Topic comes from env NTFY_TOPIC.

Safe no-op if topic is unset. Does not raise.
"""

from __future__ import annotations

import os

try:
    import requests
except ImportError:
    requests = None


NTFY_BASE = os.environ.get("NTFY_BASE", "https://ntfy.sh")


def notify_phone(title: str, message: str, priority: str = "default") -> bool:
    topic = os.environ.get("NTFY_TOPIC")
    if not topic or requests is None:
        return False
    headers = {
        "Title": title.encode("utf-8"),
        "Priority": priority,  # "min" | "low" | "default" | "high" | "urgent"
    }
    url = f"{NTFY_BASE.rstrip('/')}/{topic}"
    try:
        r = requests.post(url, data=message.encode("utf-8"), headers=headers, timeout=5)
        return r.ok
    except Exception:
        return False
