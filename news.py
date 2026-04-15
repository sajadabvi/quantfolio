"""
Real-time news (and social/tweets) relevant to your positions.
Uses yfinance news, optional Google News RSS; tweets via StockTwits if available.
Focus: news that can significantly affect your stock positions.
"""

import feedparser
import requests
import urllib.parse
from typing import Optional

try:
    import yfinance as yf
except ImportError:
    yf = None


def get_news_yfinance(symbol: str, limit: int = 8) -> list[dict]:
    """Fetch recent news for a ticker from Yahoo Finance (no API key)."""
    if not yf:
        return []
    items = []
    try:
        ticker = yf.Ticker(symbol)
        # Prefer get_news for consistency; fallback to .news
        raw = getattr(ticker, "get_news", None)
        if callable(raw):
            news_list = raw(count=limit, tab="news")
        else:
            news_list = getattr(ticker, "news", None) or []
        for n in (news_list or [])[:limit]:
            if isinstance(n, dict):
                items.append({
                    "title": n.get("title", ""),
                    "url": n.get("link") or n.get("url", ""),
                    "publisher": n.get("publisher", ""),
                    "published": n.get("providerPublishTime") or n.get("published", ""),
                    "source": "Yahoo Finance",
                })
            else:
                items.append({"title": str(n), "url": "", "source": "Yahoo Finance"})
    except Exception:
        pass
    return items


def get_news_google_rss(symbol: str, limit: int = 5) -> list[dict]:
    """Fetch news for a ticker from Google News RSS (no API key)."""
    items = []
    try:
        q = urllib.parse.quote_plus(symbol)
        url = f"https://news.google.com/rss/search?q={q}+stock&hl=en-US&gl=US&ceid=US:en"
        feed = feedparser.parse(url, request_headers={"User-Agent": "Mozilla/5.0"})
        for e in feed.get("entries", [])[:limit]:
            items.append({
                "title": e.get("title", ""),
                "url": e.get("link", ""),
                "published": e.get("published", ""),
                "source": "Google News",
            })
    except Exception:
        pass
    return items


def get_stocktwits_messages(symbol: str, limit: int = 15) -> list[dict]:
    """Fetch recent messages (tweet-like) for a ticker from StockTwits public API (no key required)."""
    items = []
    try:
        url = f"https://api.stocktwits.com/api/2/streams/symbol/{symbol.upper()}.json"
        r = requests.get(url, timeout=10, headers={"User-Agent": "PortfolioNews/1.0"})
        if r.status_code != 200:
            return items
        data = r.json()
        for m in data.get("messages", [])[:limit]:
            body = m.get("body", "")
            user = (m.get("user") or {}).get("username", "")
            created = m.get("created_at", "")
            items.append({
                "title": body[:200] + ("..." if len(body) > 200 else ""),
                "url": f"https://stocktwits.com/symbol/{symbol}",
                "published": created,
                "source": "StockTwits",
                "user": user,
            })
    except Exception:
        pass
    return items


def print_news_for_positions(
    symbols: list[str],
    news_per_symbol: int = 6,
    include_tweets: bool = True,
    include_google_rss: bool = True,
):
    """Print real-time news (and tweet-like StockTwits) for each position."""
    print("\n--- Real-time news (may significantly affect your positions) ---\n")
    for symbol in symbols:
        print(f"  [{symbol}]")
        seen_titles = set()
        # 1) Yahoo Finance news
        for item in get_news_yfinance(symbol, limit=news_per_symbol):
            title = (item.get("title") or "").strip()
            if title and title not in seen_titles:
                seen_titles.add(title)
                url = item.get("url", "")
                src = item.get("source", "News")
                print(f"    • {title}")
                if url:
                    print(f"      {url}")
                print(f"      ({src})")
        # 2) Google News RSS
        if include_google_rss:
            for item in get_news_google_rss(symbol, limit=3):
                title = (item.get("title") or "").strip()
                if title and title not in seen_titles:
                    seen_titles.add(title)
                    url = item.get("url", "")
                    print(f"    • {title}")
                    if url:
                        print(f"      {url}")
                    print(f"      (Google News)")
        # 3) StockTwits (tweet-like)
        if include_tweets:
            for item in get_stocktwits_messages(symbol, limit=5):
                title = (item.get("title") or "").strip()
                if title and title not in seen_titles:
                    seen_titles.add(title)
                    user = item.get("user", "")
                    print(f"    • [{user}] {title}")
                    print(f"      (StockTwits)")
        if not seen_titles:
            print("    (No recent headlines found)")
        print()


def main():
    import sys
    symbols = [s.strip().upper() for s in sys.argv[1:]] if len(sys.argv) > 1 else ["AAPL", "MSFT"]
    print_news_for_positions(symbols)


if __name__ == "__main__":
    main()
