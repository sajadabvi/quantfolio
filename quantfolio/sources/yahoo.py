"""Yahoo Finance news via yfinance."""

from __future__ import annotations

from ._common import SKIP_PUBLISHERS, clean_domain, is_quality

try:
    import yfinance as yf
except ImportError:
    yf = None


def get_news_yfinance(symbol: str, limit: int = 4) -> list[dict]:
    if not yf:
        return []
    items: list[dict] = []
    try:
        ticker = yf.Ticker(symbol)
        raw = getattr(ticker, "get_news", None)
        news_list = raw(count=limit * 2, tab="news") if callable(raw) else (getattr(ticker, "news", None) or [])
        for n in (news_list or []):
            if not isinstance(n, dict):
                continue
            title = (n.get("title") or "").strip()
            url = n.get("link") or n.get("url") or ""
            publisher = n.get("publisher") or clean_domain(url)
            domain = clean_domain(url)
            if domain in SKIP_PUBLISHERS:
                continue
            if title and is_quality(title):
                items.append({
                    "title": title,
                    "domain": domain or publisher,
                    "source": "Yahoo Finance",
                    "symbol": symbol,
                })
            if len(items) >= limit:
                break
    except Exception:
        pass
    return items
