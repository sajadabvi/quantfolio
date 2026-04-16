"""Live-price lookup via yfinance, with fallbacks."""

from __future__ import annotations

from typing import Optional

try:
    import yfinance as yf
except ImportError:
    yf = None


def fetch_prices(symbols: list[str]) -> dict[str, Optional[float]]:
    if not symbols or yf is None:
        return {s: None for s in symbols}
    out: dict[str, Optional[float]] = {}
    for sym in symbols:
        try:
            t = yf.Ticker(sym)
            info = t.info
            price = info.get("regularMarketPrice") or info.get("previousClose") or info.get("open")
            if price is not None:
                out[sym] = float(price)
            else:
                hist = t.history(period="5d")
                out[sym] = float(hist["Close"].iloc[-1]) if not hist.empty else None
        except Exception:
            out[sym] = None
    return out


def compute_portfolio_value(
    positions,
    prices: dict[str, Optional[float]],
    cash_by_account: Optional[dict[str, float]] = None,
) -> tuple[float, list[dict]]:
    cash_by_account = cash_by_account or {}
    total_cash = sum(cash_by_account.values())
    breakdown: list[dict] = []
    total_positions_value = 0.0
    for p in positions:
        price = prices.get(p.symbol)
        value = None
        if price is not None:
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
    return total_positions_value + total_cash, breakdown
