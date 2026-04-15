# Stock Portfolio Estimator

Estimates your **stock portfolio value** and shows **real-time news** (and tweet-like feeds) that can significantly affect your positions. Scope is **stocks only**—no real estate, vehicles, or liabilities.

## Features

- **Portfolio value**: Load positions from CSV (or add cash via CLI), fetch current/last prices via Yahoo Finance, output total value and per-position breakdown.
- **Real-time news**:
  - **News articles**: Yahoo Finance and Google News RSS per ticker (no API keys).
  - **Tweet-like feed**: StockTwits stream per symbol (no API key; public endpoint).

## Setup

```bash
cd portfolio-estimator
pip install -r requirements.txt
```

## Usage

### 1. Portfolio value only

```bash
# From a CSV of positions
python portfolio.py positions_sample.csv

# Cash-only (no positions CSV)
python portfolio.py --cash 5000

# With extra cash in brokerage
python portfolio.py positions_sample.csv --cash 5000

# Skip news (faster)
python portfolio.py positions_sample.csv --no-news
```

### 2. News (and StockTwits) for your tickers

```bash
# After running portfolio, news runs automatically. Or run alone:
python news.py AAPL MSFT GOOGL
```

### CSV format

Your positions CSV should have at least:

| Column       | Required | Description                    |
|-------------|----------|--------------------------------|
| `symbol`    | Yes      | Ticker (e.g. AAPL, MSFT)      |
| `quantity`  | Yes      | Number of shares              |
| `account_id`| No       | Account label                 |
| `account_type` | No    | e.g. taxable, IRA             |

Headers are case-flexible (`Symbol`/`Quantity`/`Shares` also work). Example:

```csv
symbol,quantity,account_id,account_type
AAPL,10,brokerage_1,taxable
MSFT,5,,taxable
```

### Brokerage CSV import

Most brokers let you export “Positions” or “Holdings” as CSV. If column names differ, either rename columns to `symbol` and `quantity` or edit `BROKER_COLUMN_MAP` in `portfolio.py`. Common names (`Ticker`, `Symbol`, `Shares`, `Quantity`, `Qty`, `Account`, `Account ID`, `Account Type`) are supported automatically, case-insensitive. To add more mappings, edit `BROKER_COLUMN_MAP` in `portfolio.py`.

## Data sources

- **Prices**: Yahoo Finance (yfinance).
- **News**: Yahoo Finance + Google News RSS (no keys).
- **Tweets / social**: StockTwits public API (no key). For actual Twitter/X, the API is paid; this uses StockTwits as a free alternative for short, position-relevant messages.

## Scope

This tool focuses only on **stocks** (and ETFs if you add them as symbols). It does not track real estate, vehicles, bank balances, or liabilities.
