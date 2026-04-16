"""
Backward-compatible wrapper. Raw sources live in quantfolio/sources/, terminal
rendering in quantfolio/notify/terminal.py.
"""

from __future__ import annotations

from quantfolio.notify.terminal import print_news_for_positions
from quantfolio.sources import get_news_google_rss, get_news_yfinance  # noqa: F401


def main():
    import sys
    symbols = [s.strip().upper() for s in sys.argv[1:]] if len(sys.argv) > 1 else ["AAPL", "MSFT"]
    print_news_for_positions(symbols)


if __name__ == "__main__":
    main()
