"""
End-to-end signal pipeline:
    fetch raw news → dedup via novelty → score → rank.

Kept thin on purpose; each step is testable in isolation.
"""

from __future__ import annotations

from typing import Optional

from ..sources import get_news_google_rss, get_news_yfinance
from ..store import Position
from .novelty import filter_novel
from .score import load_weights, score_candidates


def gather_raw_candidates(symbols: list[str], per_symbol: int = 4) -> list[dict]:
    """Pull headlines from all sources for the given symbols. Dedups titles."""
    seen_titles: set[str] = set()
    items: list[dict] = []
    for sym in symbols:
        for item in get_news_yfinance(sym, limit=per_symbol):
            if item["title"] in seen_titles:
                continue
            seen_titles.add(item["title"])
            items.append(item)
        for item in get_news_google_rss(sym, limit=per_symbol):
            if item["title"] in seen_titles:
                continue
            seen_titles.add(item["title"])
            items.append(item)
    return items


def run_pipeline(
    conn,
    positions: list[Position],
    portfolio_weights: dict[str, float],
    per_symbol: int = 4,
    mark_novel: bool = True,
    weights: Optional[dict] = None,
) -> list:
    """Return ranked ScoredCandidate list."""
    symbols = sorted({p.symbol for p in positions})
    raw = gather_raw_candidates(symbols, per_symbol=per_symbol)
    novel = filter_novel(conn, raw, mark=mark_novel)
    w = weights or load_weights()
    return score_candidates(novel, portfolio_weights, w)
