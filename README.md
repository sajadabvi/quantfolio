# Quantfolio

**A portfolio-aware signal engine for the terminal.** Quantfolio watches your
holdings and surfaces only what changes your decisions — ranked, filtered to
your positions, quiet unless something actually matters.

Not another dashboard. Not a news feed. A deliberately small tool that answers
one question: *given what I own, what changed today that I need to know?*

## Three tiers, attention-matched

1. **Morning brief** — exactly 3 ranked signals with a 1–2 sentence synthesis:
   "this changes your thesis on X because Y." Never "buy" or "sell."
2. **Hourly digest** — quiet terminal output of deltas since last hour. No push.
3. **Push-now** — rare. Only for earnings miss while held, trading halt, M&A,
   FDA action, SEC filing, analyst revision beyond threshold. Hard cap:
   2 pushes/day default, tunable.

## How it scores

Every candidate headline is scored along four axes:

| Axis             | What it measures                                                      |
|------------------|-----------------------------------------------------------------------|
| **Materiality** | Keyword rubric (earnings, guidance, FDA, halt, …) + source tier      |
| **Portfolio impact** | Scaled by your position weight — a 40% holding dominates a 2%   |
| **Novelty**      | SHA-256 of normalized title+source. Yesterday's story doesn't re-surface |
| **Urgency**      | Time-to-action (tonight > next week)                                  |

Weights live in [`quantfolio/signals/weights.yaml`](quantfolio/signals/weights.yaml).
Edit the YAML — no code changes.

## Theme graph

When a theme is trending in the news but you hold none of its members,
Quantfolio surfaces an adjacent public proxy (e.g. no space stocks → ARKX/UFO).
Seed list of ~20 themes in
[`quantfolio/signals/themes.yaml`](quantfolio/signals/themes.yaml).

## LLM-as-analyst (narrow use)

News discovery stays rule-based (fast, cheap). The Claude API is used for
*one* step: take the top scored headlines + your portfolio, produce a
3-bullet brief. Set `ANTHROPIC_API_KEY` to opt in. Without it, a rule-based
template produces the same structure.

Default model: `claude-sonnet-4-6`.

## Install

```bash
git clone https://github.com/sajadabvi/quantfolio.git
cd quantfolio
pip install -r requirements.txt
```

Requires Python 3.10+.

## CLI

```bash
quantfolio import <csv>      # one-time, persists positions
quantfolio show              # existing portfolio snapshot (legacy UI)
quantfolio brief             # morning 3-signal brief
quantfolio watch             # hourly-digest + push-tier (cron this)
quantfolio journal           # review past signals, mark useful/noise
quantfolio themes            # list the theme graph
```

`python portfolio.py <csv>` still works for backward compatibility.

### Typical flow

```bash
# One time
python -m quantfolio import positions_sample.csv

# Every morning
python -m quantfolio brief

# Every 15 min during market hours (via cron or launchd)
python -m quantfolio watch

# Whenever you want to review what you've seen
python -m quantfolio journal
```

## Persistence

SQLite at `~/.quantfolio/quantfolio.db`:

| Table             | Purpose                                                     |
|-------------------|-------------------------------------------------------------|
| `positions`       | symbol, quantity, account_id, account_type, updated_at      |
| `seen_headlines`  | hash, title, source, symbol, first_seen_at (dedup)          |
| `signal_log`      | tier, symbol, title, score, pushed_at, user_rating (journal)|

## Notifications

- **Terminal** — rich-rendered panels (the visual hook).
- **Desktop push (macOS)** — `osascript` display notification.
- **Phone push** — [ntfy.sh](https://ntfy.sh) (free, no account). Set `NTFY_TOPIC`.

## Position CSV format

Auto-maps broker exports (Fidelity, E*TRADE, Schwab, IBKR). Recognized columns:

| Column                                   | Required | Notes               |
|------------------------------------------|----------|---------------------|
| `Ticker` / `Symbol` / `symbol`           | ✓        | Case-insensitive    |
| `Shares` / `Quantity` / `Qty`            | ✓        | Supports fractional |
| `Account` / `Account ID` / `account_id`  |          | Multi-account OK    |
| `Account Type` / `account_type`          |          | e.g. taxable / IRA  |

Example:

```csv
symbol,quantity,account_id,account_type
AAPL,100.5,brokerage_1,taxable
SPY,50,retirement_1,IRA
MSFT,25.25,brokerage_1,taxable
```

## Cron / launchd

`deploy/crontab.example` and `deploy/com.quantfolio.watch.plist` are templates
for running `watch` every 15 min during market hours. Edit the repo path, then:

```bash
# cron
crontab deploy/crontab.example

# or launchd
cp deploy/com.quantfolio.watch.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.quantfolio.watch.plist
```

## Layout

```
portfolio.py                 # thin wrapper, delegates to quantfolio package
news.py                      # thin wrapper, delegates to quantfolio.sources
quantfolio/
  store.py                   # sqlite access
  pricing.py                 # yfinance
  sources/{yahoo,google_rss}.py
  signals/
    score.py                 # scoring pipeline
    novelty.py               # dedup
    thematic.py              # theme graph lookup
    synthesize.py            # Claude API call
    pipeline.py              # glue
    weights.yaml
    themes.yaml
  notify/{terminal,desktop,push}.py
  cli/                       # argparse dispatcher + per-command files
deploy/                      # cron + launchd templates
tests/                       # unit tests (scoring, novelty)
```

## Scope

**In scope:** equity positions (stocks, ETFs), news-driven signals, CLI +
terminal + desktop + phone push.

**Out of scope:** derivatives, crypto, fixed income, web UI. By design.

## License

MIT.
