"""CLI dispatcher for `quantfolio` command."""

from __future__ import annotations

import argparse
import sys


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="quantfolio", description="Portfolio-aware signal engine.")
    sub = p.add_subparsers(dest="cmd", required=False)

    p_import = sub.add_parser("import", help="Import positions from a CSV into the store.")
    p_import.add_argument("csv", help="Path to positions CSV.")

    p_show = sub.add_parser("show", help="Show the current portfolio snapshot.")
    p_show.add_argument("--cash", type=float, default=0.0)
    p_show.add_argument("--no-news", action="store_true")

    p_brief = sub.add_parser("brief", help="Morning 3-signal brief.")
    p_brief.add_argument("--no-llm", action="store_true", help="Force rule-based synthesis.")
    p_brief.add_argument("--limit", type=int, default=3, help="Number of signals (default 3).")

    p_watch = sub.add_parser("watch", help="Cron-driven watcher: hourly digest + push tier.")
    p_watch.add_argument("--dry-run", action="store_true", help="Do not write/push; just print.")

    p_journal = sub.add_parser("journal", help="Rate recent signals as useful/noise.")
    p_journal.add_argument("--days", type=int, default=7)

    sub.add_parser("themes", help="List theme graph.")

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.cmd:
        parser.print_help()
        return 0

    if args.cmd == "import":
        from .import_cmd import run as run_import
        return run_import(args.csv)
    if args.cmd == "show":
        from .show import run as run_show
        return run_show(cash=args.cash, show_news=not args.no_news)
    if args.cmd == "brief":
        from .brief import run as run_brief
        return run_brief(use_llm=not args.no_llm, limit=args.limit)
    if args.cmd == "watch":
        from .watch import run as run_watch
        return run_watch(dry_run=args.dry_run)
    if args.cmd == "journal":
        from .journal import run as run_journal
        return run_journal(days=args.days)
    if args.cmd == "themes":
        from .themes_cmd import run as run_themes
        return run_themes()

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
