"""
Quantfolio entry point (backward-compatible wrapper).

Legacy usage still works:
    python portfolio.py positions_sample.csv [--cash N] [--no-news]

Internally delegates to the quantfolio package.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Optional


# Re-export legacy symbols so external callers that do
#   from portfolio import load_positions_from_csv, fetch_prices, compute_portfolio_value
# keep working.
from quantfolio.cli.import_cmd import (
    BROKER_COLUMN_MAP,  # noqa: F401  (re-exported)
    load_positions_from_csv,
)
from quantfolio.notify.terminal import console, print_portfolio
from quantfolio.pricing import compute_portfolio_value, fetch_prices
from quantfolio.store import Position  # noqa: F401  (re-exported)


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Stock portfolio value (stocks only)")
    parser.add_argument("csv", nargs="?", default=None)
    parser.add_argument("--cash", type=float, default=0)
    parser.add_argument("--no-news", action="store_true")
    args = parser.parse_args()

    positions = []
    cash_total = args.cash

    if args.csv:
        if os.path.isfile(args.csv):
            positions = load_positions_from_csv(args.csv)
        else:
            try:
                cash_from_arg = float(args.csv.replace(",", ""))
                if cash_from_arg > 0 and cash_total == 0:
                    cash_total = cash_from_arg
            except ValueError:
                pass
            if not os.path.isfile(args.csv):
                console.print(f"[yellow]Warning:[/yellow] CSV not found: {args.csv}", file=sys.stderr)

    if not positions and cash_total == 0:
        console.print("[red]No positions and no cash.[/red] Provide a CSV or --cash amount.", file=sys.stderr)
        sys.exit(1)

    symbols = list({p.symbol for p in positions})

    with console.status("[cyan]Fetching live prices…[/cyan]", spinner="dots"):
        prices = fetch_prices(symbols)

    total_value, breakdown = compute_portfolio_value(positions, prices, {"default": cash_total})
    print_portfolio(breakdown, cash_total, total_value)

    if not args.no_news:
        try:
            from quantfolio.notify.terminal import print_news_for_positions
            print_news_for_positions(symbols)
        except ImportError:
            pass


if __name__ == "__main__":
    main()
