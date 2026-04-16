"""Google News RSS."""

from __future__ import annotations

import urllib.parse

import feedparser

from ._common import SKIP_PUBLISHERS, is_quality


def get_news_google_rss(symbol: str, limit: int = 3) -> list[dict]:
    items: list[dict] = []
    try:
        q = urllib.parse.quote_plus(f"{symbol} stock")
        url = f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"
        feed = feedparser.parse(url, request_headers={"User-Agent": "Mozilla/5.0"})
        for e in (feed.get("entries", []) or []):
            title = (e.get("title") or "").strip()
            # Google RSS title format: "Headline - Publisher"
            if " - " in title:
                headline, publisher = title.rsplit(" - ", 1)
            else:
                headline, publisher = title, "Google News"
            domain = publisher.strip()
            if domain.lower() in SKIP_PUBLISHERS:
                continue
            if headline and is_quality(headline):
                items.append({
                    "title": headline.strip(),
                    "domain": domain,
                    "source": "Google News",
                    "symbol": symbol,
                })
            if len(items) >= limit:
                break
    except Exception:
        pass
    return items
