"""`quantfolio show` — portfolio snapshot from the store."""

from __future__ import annotations

import sys

from ..notify.terminal import console, print_news_for_positions, print_portfolio
from ..pricing import compute_portfolio_value, fetch_prices
from ..store import load_positions, session


def run(cash: float = 0.0, show_news: bool = True) -> int:
    with session() as conn:
        positions = load_positions(conn)

    if not positions and cash == 0:
        print("error: no positions in store. Run `quantfolio import <csv>` first.", file=sys.stderr)
        return 1

    symbols = list({p.symbol for p in positions})

    with console.status("[cyan]Fetching live prices…[/cyan]", spinner="dots"):
        prices = fetch_prices(symbols)

    total_value, breakdown = compute_portfolio_value(positions, prices, {"default": cash})
    print_portfolio(breakdown, cash, total_value)

    if show_news and symbols:
        try:
            print_news_for_positions(symbols)
        except Exception:
            pass

    return 0
