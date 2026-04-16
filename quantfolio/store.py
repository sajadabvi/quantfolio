"""
SQLite persistence for Quantfolio.

Tables:
  positions       — symbol, quantity, account_id, account_type, updated_at
  seen_headlines  — hash, title, source, symbol, first_seen_at
  signal_log      — id, tier, symbol, title, score, pushed_at, user_rating
"""

from __future__ import annotations

import hashlib
import os
import re
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator, Optional


DEFAULT_DB_PATH = Path.home() / ".quantfolio" / "quantfolio.db"


@dataclass
class Position:
    symbol: str
    quantity: float
    account_id: Optional[str] = None
    account_type: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class SignalRecord:
    id: Optional[int]
    tier: str          # "brief", "hourly", "push"
    symbol: str
    title: str
    score: float
    pushed_at: str
    user_rating: Optional[str] = None  # "useful" | "noise" | None


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def normalize_title(title: str) -> str:
    """Lowercase + collapse whitespace + strip punctuation for dedup."""
    t = title.lower()
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def headline_hash(title: str, source: str) -> str:
    key = f"{normalize_title(title)}|{(source or '').lower().strip()}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def connect(db_path: Optional[os.PathLike | str] = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else DEFAULT_DB_PATH
    _ensure_parent(path)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    _init_schema(conn)
    return conn


def _init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS positions (
            symbol        TEXT NOT NULL,
            quantity      REAL NOT NULL,
            account_id    TEXT NOT NULL DEFAULT '',
            account_type  TEXT,
            updated_at    TEXT NOT NULL,
            PRIMARY KEY (symbol, account_id)
        );

        CREATE TABLE IF NOT EXISTS seen_headlines (
            hash           TEXT PRIMARY KEY,
            title          TEXT NOT NULL,
            source         TEXT,
            symbol         TEXT,
            first_seen_at  TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS signal_log (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            tier         TEXT NOT NULL,
            symbol       TEXT,
            title        TEXT NOT NULL,
            score        REAL NOT NULL,
            pushed_at    TEXT NOT NULL,
            user_rating  TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_seen_symbol ON seen_headlines(symbol);
        CREATE INDEX IF NOT EXISTS idx_signal_pushed_at ON signal_log(pushed_at);
        """
    )
    conn.commit()


@contextmanager
def session(db_path: Optional[os.PathLike | str] = None) -> Iterator[sqlite3.Connection]:
    conn = connect(db_path)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


# -------- positions --------

def replace_positions(conn: sqlite3.Connection, positions: Iterable[Position]) -> int:
    """Replace the entire positions table with the given set. Returns count."""
    now = _utc_now()
    rows = [
        (p.symbol.upper(), float(p.quantity), p.account_id or "", p.account_type, now)
        for p in positions
        if p.symbol and p.quantity > 0
    ]
    conn.execute("DELETE FROM positions")
    conn.executemany(
        "INSERT INTO positions (symbol, quantity, account_id, account_type, updated_at) "
        "VALUES (?, ?, ?, ?, ?)",
        rows,
    )
    conn.commit()
    return len(rows)


def load_positions(conn: sqlite3.Connection) -> list[Position]:
    cur = conn.execute(
        "SELECT symbol, quantity, account_id, account_type, updated_at FROM positions"
    )
    out = []
    for r in cur.fetchall():
        d = dict(r)
        if d.get("account_id") == "":
            d["account_id"] = None
        out.append(Position(**d))
    return out


def portfolio_weights(positions: list[Position], prices: dict[str, Optional[float]]) -> dict[str, float]:
    """Return fraction of portfolio by symbol (by market value). Unknown prices skipped."""
    values: dict[str, float] = {}
    for p in positions:
        price = prices.get(p.symbol)
        if price is None:
            continue
        values[p.symbol] = values.get(p.symbol, 0.0) + p.quantity * price
    total = sum(values.values())
    if total <= 0:
        return {s: 0.0 for s in values}
    return {s: v / total for s, v in values.items()}


# -------- seen headlines --------

def is_seen(conn: sqlite3.Connection, h: str) -> bool:
    row = conn.execute("SELECT 1 FROM seen_headlines WHERE hash = ?", (h,)).fetchone()
    return row is not None


def mark_seen(conn: sqlite3.Connection, h: str, title: str, source: str, symbol: Optional[str]) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO seen_headlines (hash, title, source, symbol, first_seen_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (h, title, source, symbol, _utc_now()),
    )


# -------- signal log --------

def log_signal(
    conn: sqlite3.Connection,
    tier: str,
    symbol: Optional[str],
    title: str,
    score: float,
) -> int:
    cur = conn.execute(
        "INSERT INTO signal_log (tier, symbol, title, score, pushed_at) VALUES (?, ?, ?, ?, ?)",
        (tier, symbol, title, float(score), _utc_now()),
    )
    conn.commit()
    return int(cur.lastrowid)


def recent_signals(conn: sqlite3.Connection, days: int = 7) -> list[sqlite3.Row]:
    cur = conn.execute(
        "SELECT id, tier, symbol, title, score, pushed_at, user_rating "
        "FROM signal_log "
        "WHERE pushed_at >= datetime('now', ?) "
        "ORDER BY pushed_at DESC",
        (f"-{int(days)} days",),
    )
    return cur.fetchall()


def rate_signal(conn: sqlite3.Connection, signal_id: int, rating: str) -> None:
    if rating not in {"useful", "noise", "skip"}:
        raise ValueError(f"unknown rating: {rating}")
    conn.execute(
        "UPDATE signal_log SET user_rating = ? WHERE id = ?",
        (rating, int(signal_id)),
    )
    conn.commit()


def pushes_today(conn: sqlite3.Connection) -> int:
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM signal_log "
        "WHERE tier = 'push' AND pushed_at >= datetime('now', 'start of day')"
    ).fetchone()
    return int(row["n"] if row else 0)
