"""Rich-rendered terminal output. Hosts the visual hook."""

from __future__ import annotations

from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text
from rich import box

console = Console()


def print_portfolio(breakdown: list[dict], cash_total: float, total_value: float) -> None:
    table = Table(
        box=box.SIMPLE_HEAVY,
        show_footer=True,
        header_style="bold cyan",
        footer_style="bold white",
        border_style="dim",
        pad_edge=True,
        padding=(0, 1),
    )
    table.add_column("Symbol",  style="bold white", footer="TOTAL", min_width=8)
    table.add_column("Qty",     style="white",      footer="", justify="right", min_width=10)
    table.add_column("Price",   style="yellow",     footer="", justify="right", min_width=12)
    table.add_column("Value",   style="bold green", footer=f"${total_value:>12,.2f}", justify="right", min_width=14)
    table.add_column("Account", style="dim white",  footer="", min_width=10)

    for row in breakdown:
        price_str = f"${row['price']:,.2f}" if row["price"] is not None else "[dim]N/A[/dim]"
        value_str = f"${row['value']:,.2f}" if row["value"] is not None else "[dim]N/A[/dim]"
        acct = row.get("account_type") or row.get("account_id") or "—"
        table.add_row(
            row["symbol"],
            f"{row['quantity']:,.2f}",
            price_str,
            value_str,
            acct,
        )

    if cash_total:
        table.add_row("CASH", "—", "—", f"[cyan]${cash_total:,.2f}[/cyan]", "—")

    console.print()
    console.print(Panel(table, title="[bold cyan]Quantfolio[/bold cyan]  ·  Portfolio Snapshot",
                        border_style="cyan", padding=(0, 1)))
    console.print()


def print_news_for_positions(symbols: list[str], news_per_symbol: int = 4) -> None:
    """Legacy per-ticker news panel, kept for `portfolio.py` backward compat."""
    from ..sources import get_news_google_rss, get_news_yfinance

    console.print(Rule("[bold cyan]Market Headlines[/bold cyan]  ·  relevant to your positions", style="cyan"))
    console.print()

    for symbol in symbols:
        seen: set[str] = set()
        headlines: list[dict] = []

        for item in get_news_yfinance(symbol, limit=news_per_symbol):
            if item["title"] not in seen:
                seen.add(item["title"])
                headlines.append(item)

        for item in get_news_google_rss(symbol, limit=3):
            if item["title"] not in seen and len(headlines) < news_per_symbol + 2:
                seen.add(item["title"])
                headlines.append(item)

        lines = Text()
        if headlines:
            for i, h in enumerate(headlines[:news_per_symbol]):
                lines.append(f"  {h['title']}\n", style="white")
                lines.append(f"  {h['domain']}\n", style="dim cyan")
                if i < len(headlines) - 1:
                    lines.append("\n")
        else:
            lines.append("  No recent headlines found.", style="dim")

        console.print(Panel(
            lines,
            title=f"[bold yellow]{symbol}[/bold yellow]",
            border_style="dim yellow",
            padding=(0, 1),
        ))
        console.print()


def print_brief(signals: list[dict], synthesis: str, adjacencies: Optional[list[dict]] = None) -> None:
    """Morning brief: top-3 ranked signals + synthesis + optional adjacencies."""
    console.print()
    console.print(Panel(
        Text(synthesis, style="white"),
        title="[bold cyan]Morning Brief[/bold cyan]",
        border_style="cyan",
        padding=(1, 2),
    ))
    console.print()

    table = Table(box=box.SIMPLE_HEAVY, header_style="bold cyan", border_style="dim", padding=(0, 1))
    table.add_column("#", style="dim", min_width=2, justify="right")
    table.add_column("Ticker", style="bold yellow", min_width=6)
    table.add_column("Weight", style="magenta", justify="right", min_width=7)
    table.add_column("Score", style="green", justify="right", min_width=6)
    table.add_column("Headline", style="white", overflow="fold")
    table.add_column("Source", style="dim cyan", min_width=10)

    for i, s in enumerate(signals, 1):
        w = s.get("portfolio_weight")
        weight_str = f"{w*100:.1f}%" if isinstance(w, (int, float)) else "—"
        table.add_row(
            str(i),
            s.get("symbol") or "—",
            weight_str,
            f"{s.get('score', 0):.1f}",
            s.get("title", ""),
            s.get("domain", ""),
        )

    console.print(Panel(table, title="[bold cyan]Top Signals[/bold cyan]", border_style="cyan", padding=(0, 1)))
    console.print()

    if adjacencies:
        adj_text = Text()
        for a in adjacencies:
            adj_text.append(f"• {a['theme']}", style="bold magenta")
            adj_text.append(f" — trending but no direct exposure. Proxies: ", style="white")
            adj_text.append(", ".join(a["proxies"]), style="yellow")
            adj_text.append("\n")
        console.print(Panel(adj_text, title="[bold magenta]Adjacent Opportunities[/bold magenta]",
                            border_style="magenta", padding=(0, 1)))
        console.print()


def print_hourly_digest(deltas: list[dict]) -> None:
    """Quiet terminal output of deltas since last hour."""
    if not deltas:
        console.print("[dim]No new signals this hour.[/dim]")
        return
    console.print(Rule("[cyan]Hourly Digest[/cyan]", style="dim cyan"))
    for d in deltas:
        console.print(
            f"  [yellow]{d.get('symbol','—'):<6}[/yellow] "
            f"[green]{d.get('score', 0):5.1f}[/green]  "
            f"[white]{d.get('title','')}[/white]  "
            f"[dim]{d.get('domain','')}[/dim]"
        )
    console.print()
