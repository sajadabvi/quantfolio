"""
`quantfolio watch` — the cron-driven hourly watcher.

Design: runs once, exits. A cron entry runs it every 15 minutes during
market hours. Each run:
  1. Gathers raw headlines for held tickers.
  2. Filters through novelty.
  3. Scores.
  4. Anything ≥ push_threshold (on held ticker) → push tier (rate-limited).
  5. Anything ≥ hourly_threshold → prints quiet digest to stdout.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone

from ..notify.desktop import notify_desktop
from ..notify.push import notify_phone
from ..notify.terminal import console, print_hourly_digest
from ..pricing import fetch_prices
from ..signals.pipeline import run_pipeline
from ..signals.score import load_weights
from ..store import load_positions, log_signal, portfolio_weights, pushes_today, session


def _in_market_hours(now: datetime | None = None) -> bool:
    """Cheap ET check. Assumes host is close enough to Eastern; cron handles real schedule."""
    now = now or datetime.now(timezone.utc)
    # US equities 13:30–20:00 UTC on weekdays (9:30 AM–4:00 PM ET) ignoring DST edge.
    if now.weekday() >= 5:
        return False
    hm = now.hour * 60 + now.minute
    return 13 * 60 + 30 <= hm <= 20 * 60


def run(dry_run: bool = False) -> int:
    with session() as conn:
        positions = load_positions(conn)
        if not positions:
            print("watch: no positions. Run `quantfolio import <csv>` first.", file=sys.stderr)
            return 1

        symbols = sorted({p.symbol for p in positions})
        weights = load_weights()
        push_threshold = float(weights.get("tiers", {}).get("push_threshold", 22))
        hourly_threshold = float(weights.get("tiers", {}).get("hourly_threshold", 10))
        max_pushes = int(weights.get("tiers", {}).get("max_pushes_per_day", 2))

        prices = fetch_prices(symbols)
        pw = portfolio_weights(positions, prices)
        ranked = run_pipeline(conn, positions, pw, per_symbol=4, mark_novel=not dry_run, weights=weights)

        digest = [s.as_dict() for s in ranked if s.score >= hourly_threshold]
        print_hourly_digest(digest)

        pushes_sent = pushes_today(conn) if not dry_run else 0
        for s in ranked:
            if s.score < push_threshold:
                continue
            if not s.components.get("held"):
                continue
            if pushes_sent >= max_pushes:
                console.print(f"[dim]push cap reached ({max_pushes}/day) — skipping {s.symbol}[/dim]")
                break
            title = f"Quantfolio · {s.symbol}"
            msg = f"{s.title} (score {s.score:.0f})"
            if dry_run:
                console.print(f"[yellow]would push:[/yellow] {title} — {msg}")
            else:
                notify_desktop(title, s.title, subtitle=f"score {s.score:.0f}")
                notify_phone(title, msg, priority="high")
                log_signal(conn, tier="push", symbol=s.symbol, title=s.title, score=s.score)
                pushes_sent += 1

        # Log hourly tier signals too (for journal), but only if meaningful.
        if not dry_run:
            for s in digest:
                if s["score"] < push_threshold:
                    log_signal(conn, tier="hourly", symbol=s["symbol"],
                               title=s["title"], score=s["score"])

    return 0
