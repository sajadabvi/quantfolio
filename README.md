# Quantfolio: Quantitative Portfolio Intelligence Platform

A lightweight, **API-key-free** quantitative portfolio analytics engine that combines real-time equity pricing with multi-source market intelligence. Built for quant researchers, prop traders, and portfolio analysts who need fast, reliable position tracking and event-driven sentiment signals.

**Zero external dependencies** (except yfinance, requests, feedparser). No authentication overhead. Deploy locally or in your trading infrastructure.

## Features

### Core Analytics
- **Real-time portfolio valuation**: Ingest positions from CSV or CLI, fetch live/historical prices via Yahoo Finance API, compute position-level P&L and portfolio Greeks-ready data structures
- **Flexible position import**: Auto-map brokerage CSV formats (E*TRADE, Fidelity, Interactive Brokers, etc.) with zero configuration
- **Per-position breakdown**: Account type awareness (taxable/IRA), quantity tracking, price history for backtesting prep

### Market Intelligence
- **Multi-source news aggregation**: 
  - **RSS feeds**: Yahoo Finance + Google News (no API keys required)
  - **Sentiment proxy**: StockTwits public API for retail positioning signals
  - **Real-time filtering**: Surface news/sentiment relevant to your positions
- **Event-driven alerts**: Flag significant news that could impact position value

## Installation

```bash
git clone https://github.com/sajadabvi/quantfolio.git
cd quantfolio
pip install -r requirements.txt
```

**Requirements:** Python 3.9+, ~15MB disk footprint

## Quick Start

### Portfolio Valuation (Single Command)

```bash
# Load positions and compute portfolio value with sentiment
python portfolio.py positions_sample.csv

# Cash-only strategy (useful for simulations)
python portfolio.py --cash 100000

# Combined positions + cash (typical use)
python portfolio.py positions_sample.csv --cash 50000

# Performance mode (skip news fetch)
python portfolio.py positions_sample.csv --no-news
```

**Output:** ASCII table with symbol, qty, price, position value + cash + total portfolio value

### Real-Time Sentiment & News

```bash
# Auto-runs with portfolio.py; or invoke separately:
python news.py AAPL MSFT GOOGL TLT

# Output: Yahoo Finance + Google News RSS + StockTwits sentiment per ticker
```

### Position CSV Format

Positions file should include at minimum:

| Column       | Required | Type  | Notes                    |
|-------------|----------|-------|--------------------------|
| `symbol`    | ✓ Yes    | str   | Ticker symbol (e.g. AAPL, SPY) |
| `quantity`  | ✓ Yes    | float | Number of shares (supports decimals for fractional shares) |
| `account_id`| No       | str   | Account identifier for reporting |
| `account_type` | No    | str   | e.g. `taxable`, `IRA`, `401k` (useful for tax-aware analytics) |

**Example:**
```csv
symbol,quantity,account_id,account_type
AAPL,100.5,brokerage_1,taxable
SPY,50,retirement_1,IRA
MSFT,25.25,brokerage_1,taxable
```

### Broker Integration (Zero Configuration)

Export your broker's positions as CSV (Fidelity, E*TRADE, Interactive Brokers, etc.). Column names are automatically mapped—no manual editing required. Supported variants:
- `Ticker` / `Symbol` / `symbol`
- `Shares` / `Quantity` / `Qty` / `quantity`
- `Account` / `Account ID` / `account_id`
- `Account Type` / `account_type`

To add additional broker column mappings, edit `BROKER_COLUMN_MAP` in `portfolio.py` (~50 lines).

## Data Sources & APIs

| Source        | Endpoint      | Data Provided | Rate Limit | Auth |
|---------------|---------------|---------------|-----------|------|
| **yfinance**  | Yahoo Finance | Live/historical OHLCV, fundamentals | ~2000 calls/hour | None |
| **Google News RSS** | News feeds | Curated news per ticker | Standard RSS | None |
| **Yahoo Finance RSS** | News feeds | Market news + earnings | Standard RSS | None |
| **StockTwits**| Public API | Retail sentiment, discussion volume | ~1000 calls/day | None |

**No API keys required.** Production-grade for backtesting and analysis. Not suitable for microsecond-latency strategies.

## Architecture & Design

- **Modular design**: Portfolio valuation (`portfolio.py`) and news aggregation (`news.py`) are independent modules
- **Efficient pricing**: Batch yfinance calls with fallback to historical OHLC
- **Flexible I/O**: CSV in, human-readable ASCII table + structured data dicts out
- **Extensibility**: Easy to add new data sources, account types, or analytics

## Use Cases

- **Portfolio monitoring**: Track multi-account positions and performance in real-time
- **Quantitative backtesting**: Feed position data + pricing into your factor models
- **Event-driven research**: Correlate portfolio movements with news/sentiment signals
- **Risk management**: Rapid P&L snapshots across accounts and position types
- **Prop trading desk**: Lightweight, zero-latency position tracking for multiple traders

## Scope & Limitations

**In scope:** Equity positions (stocks, ETFs) with flexible account structures  
**Out of scope:** Fixed income, derivatives, real estate, crypto, cash balances, liabilities (planned for v2.0)

**Performance:** Processes typical retail portfolios (100–1000 positions) in <5 seconds with news; <1 second without.

## Examples

### Load a Fidelity Export + Check Market Sentiment

```bash
# Export from Fidelity (Accounts > Positions > Download)
python portfolio.py ~/Downloads/Fidelity_Positions.csv --cash 10000

# Output:
# Symbol     Qty           Price         Value
# AAPL       100.00      182.52      18,252.00
# MSFT        50.00      380.25      19,012.50
# ...
# TOTAL                                 50,000.00
#
# [Automatically fetches news for AAPL, MSFT, ... ]
```

### Backtest Integration

```python
from portfolio import load_positions_from_csv, fetch_prices, compute_portfolio_value

positions = load_positions_from_csv("my_positions.csv")
prices = fetch_prices(["AAPL", "SPY", "TSLA"])
total_value, breakdown = compute_portfolio_value(positions, prices)

for row in breakdown:
    print(f"{row['symbol']}: ${row['value']:,.2f}")
```

## Contributing

Contributions welcome! Areas of interest:
- Additional data sources (Polygon.io, IEX Cloud, etc.)
- Derivatives support (options P&L)
- Tax-aware reporting (wash sale, cost basis)
- Real-time websocket updates
- Web dashboard frontend

## License

MIT License - see LICENSE file for details
