"""`quantfolio journal` — rate recent signals as useful/noise/skip."""

from __future__ import annotations

import sys

from ..notify.terminal import console
from ..store import rate_signal, recent_signals, session


def run(days: int = 7) -> int:
    with session() as conn:
        rows = recent_signals(conn, days=days)
        if not rows:
            console.print(f"[dim]No signals logged in the last {days} days.[/dim]")
            return 0

        console.print(f"[bold cyan]Journal[/bold cyan] · rating last {days} days of signals. "
                      f"[dim]y = useful, n = noise, s = skip, q = quit[/dim]")
        console.print()

        for r in rows:
            if r["user_rating"] is not None:
                continue
            sym = r["symbol"] or "—"
            ts = (r["pushed_at"] or "")[:16]
            console.print(
                f"[dim]{ts}[/dim]  [bold yellow]{sym:<6}[/bold yellow] "
                f"[green]{r['score']:5.1f}[/green]  "
                f"[white]{r['title']}[/white] [dim]({r['tier']})[/dim]"
            )
            try:
                choice = input("  → useful / noise / skip (y/n/s, q=quit): ").strip().lower()
            except EOFError:
                break
            if choice in {"q", "quit"}:
                break
            rating = {"y": "useful", "useful": "useful",
                      "n": "noise", "noise": "noise",
                      "s": "skip", "": "skip"}.get(choice, "skip")
            rate_signal(conn, r["id"], rating)
            console.print(f"  [dim]→ {rating}[/dim]\n")

    return 0
