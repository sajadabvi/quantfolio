"""Shared helpers for source fetchers."""

from __future__ import annotations

import re
from urllib.parse import urlparse


# Publishers to skip (paywalls / low signal)
SKIP_PUBLISHERS: set[str] = {"seekingalpha.com", "fool.com"}


def clean_domain(url: str) -> str:
    """Return just the domain for display, stripping long redirect URLs."""
    if not url:
        return ""
    try:
        host = urlparse(url).netloc.lower().replace("www.", "")
        return host
    except Exception:
        return url[:60]


_NOISE_PATTERNS = [
    re.compile(r"^\$[A-Z]+"),
    re.compile(r"\bsqueeze\b", re.IGNORECASE),
    re.compile(r"\bpump\b", re.IGNORECASE),
    re.compile(r"\bmooon\b", re.IGNORECASE),
    re.compile(r"\byolo\b", re.IGNORECASE),
    re.compile(r"!{3,}"),
]


def is_quality(title: str) -> bool:
    """Skip titles that look like social noise."""
    return not any(p.search(title) for p in _NOISE_PATTERNS)
