"""`quantfolio brief` — top-N ranked signals with synthesis."""

from __future__ import annotations

import sys

from ..notify.terminal import console, print_brief
from ..pricing import fetch_prices
from ..signals.pipeline import run_pipeline
from ..signals.synthesize import brief_text
from ..signals.thematic import find_adjacencies, load_themes
from ..store import load_positions, log_signal, portfolio_weights, session


def run(use_llm: bool = True, limit: int = 3) -> int:
    with session() as conn:
        positions = load_positions(conn)
        if not positions:
            print("error: no positions. Run `quantfolio import <csv>` first.", file=sys.stderr)
            return 1

        symbols = sorted({p.symbol for p in positions})
        with console.status("[cyan]Fetching prices and headlines…[/cyan]", spinner="dots"):
            prices = fetch_prices(symbols)
            weights_map = portfolio_weights(positions, prices)
            ranked = run_pipeline(conn, positions, weights_map, per_symbol=4, mark_novel=True)

        top = ranked[:limit]
        signals_dicts = [s.as_dict() for s in top]

        themes = load_themes()
        trending = [s.symbol for s in ranked[: max(10, limit)] if s.symbol]
        adjacencies = find_adjacencies(themes, trending, held_symbols=symbols) if themes else []

        text, backend = brief_text(top, weights_map, limit=limit, use_llm=use_llm)

        print_brief(signals_dicts, text, adjacencies=adjacencies)
        console.print(f"[dim]synthesis: {backend}[/dim]")

        for s in top:
            log_signal(conn, tier="brief", symbol=s.symbol, title=s.title, score=s.score)

    return 0
