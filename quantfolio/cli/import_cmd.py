"""`quantfolio import <csv>` — load positions into the SQLite store."""

from __future__ import annotations

import csv
import os
import sys
from typing import Optional

from ..store import Position, replace_positions, session


# Brokerage column mapping (case-insensitive). Keys normalized to lowercase.
BROKER_COLUMN_MAP: dict[str, str] = {
    "ticker": "symbol",
    "symbol": "symbol",
    "quantity": "quantity",
    "shares": "quantity",
    "qty": "quantity",
    "account_id": "account_id",
    "account id": "account_id",
    "account": "account_id",
    "account_type": "account_type",
    "account type": "account_type",
}


def _get(row: dict[str, str], canonical: str) -> Optional[str]:
    low = {k.strip().lower(): k for k in row}
    for src_name, key in BROKER_COLUMN_MAP.items():
        if key == canonical and src_name in low:
            val = row.get(low[src_name])
            if val is not None and str(val).strip():
                return str(val).strip()
    return None


def load_positions_from_csv(path: str) -> list[Position]:
    positions: list[Position] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            symbol = _get(row, "symbol") or ""
            qty_str = _get(row, "quantity") or "0"
            if not symbol or not qty_str:
                continue
            try:
                qty = float(qty_str.replace(",", ""))
            except ValueError:
                continue
            if qty <= 0:
                continue
            positions.append(Position(
                symbol=symbol,
                quantity=qty,
                account_id=_get(row, "account_id"),
                account_type=_get(row, "account_type"),
            ))
    return positions


def run(csv_path: str) -> int:
    if not os.path.isfile(csv_path):
        print(f"error: file not found: {csv_path}", file=sys.stderr)
        return 2
    positions = load_positions_from_csv(csv_path)
    if not positions:
        print("error: no valid positions found in CSV.", file=sys.stderr)
        return 1
    with session() as conn:
        n = replace_positions(conn, positions)
    print(f"imported {n} position(s) from {csv_path}")
    return 0
