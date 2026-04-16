"""
Novelty / dedup layer. Uses the seen_headlines table in the SQLite store.

A candidate is considered novel if its sha256(normalize(title)|source.lower())
is not already in seen_headlines.
"""

from __future__ import annotations

from typing import Iterable

from ..store import headline_hash, is_seen, mark_seen


def filter_novel(conn, candidates: Iterable[dict], mark: bool = True) -> list[dict]:
    """Return only candidates we haven't seen before. Optionally mark them seen."""
    out: list[dict] = []
    for c in candidates:
        title = c.get("title", "")
        source = c.get("source", "") or c.get("domain", "")
        if not title:
            continue
        h = headline_hash(title, source)
        if is_seen(conn, h):
            continue
        out.append(c)
        if mark:
            mark_seen(conn, h, title, source, c.get("symbol"))
    if mark:
        conn.commit()
    return out
