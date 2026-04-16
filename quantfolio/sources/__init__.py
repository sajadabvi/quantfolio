"""Raw news fetchers. Each source returns a list of {title, domain, source} dicts."""

from .yahoo import get_news_yfinance
from .google_rss import get_news_google_rss

__all__ = ["get_news_yfinance", "get_news_google_rss"]
