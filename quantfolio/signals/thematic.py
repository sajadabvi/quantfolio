"""Theme graph loader + adjacency lookup. Fleshed out in step 7."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None


THEMES_PATH = Path(__file__).parent / "themes.yaml"


def load_themes(path: Path | None = None) -> dict[str, dict]:
    p = path or THEMES_PATH
    if not p.is_file() or yaml is None:
        return {}
    data = yaml.safe_load(p.read_text()) or {}
    return data.get("themes", {}) or {}


def find_adjacencies(
    themes: dict[str, dict],
    trending_symbols: Iterable[str],
    held_symbols: Iterable[str],
) -> list[dict]:
    """
    Return themes where at least one member ticker is trending but the user
    holds none of them. Output: [{theme, proxies, missing_ticker}].
    """
    held = {s.upper() for s in held_symbols}
    trending = {s.upper() for s in trending_symbols}
    out: list[dict] = []
    for name, cfg in themes.items():
        tickers = {t.upper() for t in (cfg.get("tickers") or [])}
        if not tickers or not (tickers & trending):
            continue
        if tickers & held:
            continue  # user has exposure already
        proxies = cfg.get("proxies") or []
        if not proxies:
            continue
        out.append({
            "theme": name,
            "proxies": proxies,
            "trending_ticker": sorted(tickers & trending)[0],
        })
    return out
