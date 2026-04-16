"""`quantfolio themes` — list the theme graph."""

from __future__ import annotations

from ..notify.terminal import console
from ..signals.thematic import load_themes


def run() -> int:
    themes = load_themes()
    if not themes:
        console.print("[dim]No themes defined.[/dim]")
        return 0
    for name, cfg in themes.items():
        tickers = ", ".join(cfg.get("tickers", []) or []) or "—"
        proxies = ", ".join(cfg.get("proxies", []) or []) or "—"
        private = ", ".join(cfg.get("private", []) or []) or "—"
        console.print(f"[bold magenta]{name}[/bold magenta]")
        console.print(f"  tickers: {tickers}")
        console.print(f"  proxies: [yellow]{proxies}[/yellow]")
        console.print(f"  private: [dim]{private}[/dim]")
        console.print()
    return 0
