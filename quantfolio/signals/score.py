"""
Scoring pipeline. Inputs: list of raw headline dicts + portfolio weights.
Output: scored candidates with explanation.

A candidate dict:
    {"title": str, "domain": str, "source": str, "symbol": str}

Score components:
    materiality_keywords + source_weight + urgency  (base)
    × portfolio_impact_multiplier                    (scales to holding size)
    − novelty_penalty (if duplicate)                 (post-hoc)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None


WEIGHTS_PATH = Path(__file__).parent / "weights.yaml"


def load_weights(path: Path | None = None) -> dict:
    p = path or WEIGHTS_PATH
    if yaml is None:
        raise RuntimeError("PyYAML is required. Install with: pip install pyyaml")
    if not p.is_file():
        raise FileNotFoundError(f"weights file not found: {p}")
    return yaml.safe_load(p.read_text()) or {}


@dataclass
class ScoredCandidate:
    title: str
    symbol: Optional[str]
    domain: str
    source: str
    score: float
    portfolio_weight: Optional[float]
    components: dict  # materiality, source, urgency, impact_mult, held

    def as_dict(self) -> dict:
        return {
            "title": self.title,
            "symbol": self.symbol,
            "domain": self.domain,
            "source": self.source,
            "score": self.score,
            "portfolio_weight": self.portfolio_weight,
            "components": self.components,
        }


def _keyword_score(title: str, keyword_map: dict) -> tuple[float, list[str]]:
    t = title.lower()
    total = 0.0
    hits: list[str] = []
    for kw, pts in keyword_map.items():
        if kw.lower() in t:
            total += float(pts)
            hits.append(kw)
    return total, hits


def _source_score(domain: str, source: str, weights: dict) -> float:
    src_map = weights.get("materiality", {}).get("source_weight", {}) or {}
    default = float(weights.get("materiality", {}).get("default_source_weight", 0) or 0)
    for key in (domain, source):
        if key and key in src_map:
            return float(src_map[key])
    # Try lowercase domain match too.
    if domain:
        for k, v in src_map.items():
            if k.lower() == domain.lower():
                return float(v)
    return default


def score_candidate(
    candidate: dict,
    portfolio_weights: dict[str, float],
    weights: dict,
) -> ScoredCandidate:
    title = candidate.get("title", "") or ""
    symbol = (candidate.get("symbol") or "").upper() or None
    domain = candidate.get("domain", "") or ""
    source = candidate.get("source", "") or ""

    mat_map = weights.get("materiality", {}).get("keywords", {}) or {}
    urg_map = weights.get("urgency_keywords", {}) or {}

    mat_score, mat_hits = _keyword_score(title, mat_map)
    urg_score, urg_hits = _keyword_score(title, urg_map)
    src_score = _source_score(domain, source, weights)

    base = mat_score + src_score + urg_score

    pw = portfolio_weights.get(symbol) if symbol else None
    held = pw is not None and pw > 0
    scale = float(weights.get("portfolio_weight_scale", 3.0))
    unheld_mult = float(weights.get("unheld_multiplier", 0.4))

    if held:
        impact = 1.0 + (pw or 0.0) * scale
    else:
        impact = unheld_mult

    final = base * impact

    return ScoredCandidate(
        title=title,
        symbol=symbol,
        domain=domain,
        source=source,
        score=round(final, 2),
        portfolio_weight=pw,
        components={
            "materiality": round(mat_score, 2),
            "materiality_hits": mat_hits,
            "source": round(src_score, 2),
            "urgency": round(urg_score, 2),
            "urgency_hits": urg_hits,
            "impact_multiplier": round(impact, 3),
            "held": held,
        },
    )


def score_candidates(
    candidates: Iterable[dict],
    portfolio_weights: dict[str, float],
    weights: dict | None = None,
) -> list[ScoredCandidate]:
    w = weights or load_weights()
    scored = [score_candidate(c, portfolio_weights, w) for c in candidates]
    scored.sort(key=lambda s: s.score, reverse=True)
    return scored
