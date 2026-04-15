"""
Stock portfolio value calculator.
Reads positions (CSV or manual), fetches prices via yfinance, outputs value and per-position breakdown.
Scope: stocks only (no real estate, vehicles, liabilities).
"""

import csv
import os
import sys
from dataclasses import dataclass
from typing import Optional

import yfinance as yf


@dataclass
class Position:
    symbol: str
    quantity: float
    account_id: Optional[str] = None
    account_type: Optional[str] = None

    def __post_init__(self):
        self.symbol = self.symbol.strip().upper()


# Brokerage column mapping: broker column names -> canonical keys (symbol, quantity, account_id, account_type)
# Add entries for brokers whose export columns differ from the canonical names.
BROKER_COLUMN_MAP: dict[str, str] = {
    # Symbol
    "ticker": "symbol",
    "symbol": "symbol",
    "Ticker": "symbol",
    "Symbol": "symbol",
    # Quantity
    "quantity": "quantity",
    "Quantity": "quantity",
    "shares": "quantity",
    "Shares": "quantity",
    "qty": "quantity",
    "Qty": "quantity",
    # Account
    "account_id": "account_id",
    "Account ID": "account_id",
    "account": "account_id",
    "Account": "account_id",
    "account_type": "account_type",
    "Account Type": "account_type",
}


def _get_row_value(row: dict[str, str], canonical_key: str) -> Optional[str]:
    """Resolve a canonical key to a value using BROKER_COLUMN_MAP (case-insensitive)."""
    row_lower = {k.strip().lower(): k for k in row} if row else {}
    for col_name, key in BROKER_COLUMN_MAP.items():
        if key == canonical_key and col_name.lower() in row_lower:
            actual_key = row_lower[col_name.lower()]
            val = row.get(actual_key)
            if val is not None and str(val).strip():
                return str(val).strip()
    return None


def load_positions_from_csv(path: str) -> list[Position]:
    """Load positions from a CSV. Supports flexible column names via BROKER_COLUMN_MAP."""
    positions = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            symbol = _get_row_value(row, "symbol") or row.get("symbol") or row.get("Symbol") or ""
            symbol = symbol.strip() if symbol else ""
            qty_str = (
                _get_row_value(row, "quantity")
                or row.get("quantity")
                or row.get("Quantity")
                or row.get("shares")
                or row.get("Shares")
                or row.get("Qty")
                or "0"
            )
            qty_str = qty_str.strip() if qty_str else "0"
            if not symbol or not qty_str:
                continue
            try:
                qty = float(qty_str.replace(",", ""))
            except ValueError:
                continue
            if qty <= 0:
                continue
            account_id = _get_row_value(row, "account_id") or row.get("account_id") or row.get("Account ID")
            account_type = _get_row_value(row, "account_type") or row.get("account_type") or row.get("Account Type")
            positions.append(
                Position(
                    symbol=symbol,
                    quantity=qty,
                    account_id=account_id,
                    account_type=account_type,
                )
            )
    return positions


def fetch_prices(symbols: list[str]) -> dict[str, Optional[float]]:
    """Fetch last close (or current) price for each symbol via yfinance."""
    if not symbols:
        return {}
    out = {}
    # yfinance can batch with Ticker("AAPL MSFT ...") or we loop; batching sometimes fails for mixed symbols
    for sym in symbols:
        try:
            t = yf.Ticker(sym)
            # prefer regularMarketPrice, fallback to previous close
            info = t.info
            price = info.get("regularMarketPrice") or info.get("previousClose") or info.get("open")
            if price is not None:
                out[sym] = float(price)
            else:
                hist = t.history(period="5d")
                if not hist.empty:
                    out[sym] = float(hist["Close"].iloc[-1])
                else:
                    out[sym] = None
        except Exception:
            out[sym] = None
    return out


def compute_portfolio_value(
    positions: list[Position],
    prices: dict[str, Optional[float]],
    cash_by_account: Optional[dict[str, float]] = None,
) -> tuple[float, list[dict]]:
    """Return (total_value, list of per-position breakdown dicts)."""
    cash_by_account = cash_by_account or {}
    total_cash = sum(cash_by_account.values())
    breakdown = []
    total_positions_value = 0.0
    for p in positions:
        price = prices.get(p.symbol)
        if price is None:
            value = None
        else:
            value = p.quantity * price
            total_positions_value += value
        breakdown.append({
            "symbol": p.symbol,
            "quantity": p.quantity,
            "price": price,
            "value": value,
            "account_id": p.account_id,
            "account_type": p.account_type,
        })
    total_value = total_positions_value + total_cash
    return total_value, breakdown


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Stock portfolio value (stocks only)")
    parser.add_argument(
        "csv",
        nargs="?",
        default=None,
        help="Path to positions CSV (optional; omit for cash-only mode)",
    )
    parser.add_argument("--cash", type=float, default=0, help="Total cash in brokerage (or use CSV with cash row)")
    parser.add_argument("--no-news", action="store_true", help="Skip fetching news (run news separately)")
    args = parser.parse_args()

    positions = []
    cash_total = args.cash

    if args.csv:
        if os.path.isfile(args.csv):
            positions = load_positions_from_csv(args.csv)
        else:
            # Allow numeric first arg as cash: "python portfolio.py 5000" -> cash 5000
            try:
                cash_from_arg = float(args.csv.replace(",", ""))
                if cash_from_arg > 0 and cash_total == 0:
                    cash_total = cash_from_arg
            except ValueError:
                pass
            if cash_total == args.cash and not os.path.isfile(args.csv):
                print(f"Warning: CSV not found or not a file: {args.csv}", file=sys.stderr)

    if not positions and cash_total == 0:
        print("No positions (and no cash). Provide a CSV or add positions manually.", file=sys.stderr)
        print("CSV format: symbol,quantity[,account_id,account_type]", file=sys.stderr)
        sys.exit(1)

    symbols = list({p.symbol for p in positions})
    prices = fetch_prices(symbols)
    total_value, breakdown = compute_portfolio_value(positions, prices, {"default": cash_total})

    print("Portfolio value (stocks only)\n")
    print(f"{'Symbol':<10} {'Qty':>12} {'Price':>12} {'Value':>14}")
    print("-" * 52)
    for row in breakdown:
        val_str = f"{row['value']:,.2f}" if row["value"] is not None else "N/A"
        price_str = f"{row['price']:,.2f}" if row["price"] is not None else "N/A"
        print(f"{row['symbol']:<10} {row['quantity']:>12,.2f} {price_str:>12} {val_str:>14}")
    if cash_total:
        print(f"{'CASH':<10} {'—':>12} {'—':>12} {cash_total:>14,.2f}")
    print("-" * 52)
    print(f"{'TOTAL':<10} {'':>12} {'':>12} {total_value:>14,.2f}")

    if not args.no_news:
        try:
            from news import print_news_for_positions
            print_news_for_positions(symbols)
        except ImportError:
            pass


if __name__ == "__main__":
    main()
