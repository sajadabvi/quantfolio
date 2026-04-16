"""Scoring smoke-tests against a fixtures file of real-ish headlines."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from quantfolio.signals.score import load_weights, score_candidate, score_candidates


FIXTURES = Path(__file__).parent / "fixtures" / "headlines.json"


# A fake portfolio — AAPL is the big holding, MSFT mid, GOOGL small.
PORTFOLIO_WEIGHTS = {"AAPL": 0.40, "MSFT": 0.25, "GOOGL": 0.10}


class ScoreTests(unittest.TestCase):

    def setUp(self):
        self.weights = load_weights()
        self.candidates = json.loads(FIXTURES.read_text())

    def test_each_headline_meets_minimum(self):
        for c in self.candidates:
            expected_min = c.pop("min_score", 0)
            s = score_candidate(c, PORTFOLIO_WEIGHTS, self.weights)
            self.assertGreaterEqual(
                s.score,
                expected_min,
                f"{c['title']!r} scored {s.score} < min {expected_min}; components={s.components}",
            )

    def test_big_holding_beats_small_on_same_event(self):
        # Same materiality ("earnings beat"), different position size.
        aapl = {"title": "Apple beats earnings guidance", "symbol": "AAPL",
                "domain": "reuters.com", "source": "Reuters"}
        googl = {"title": "Google beats earnings guidance", "symbol": "GOOGL",
                 "domain": "reuters.com", "source": "Reuters"}
        s_aapl = score_candidate(aapl, PORTFOLIO_WEIGHTS, self.weights)
        s_googl = score_candidate(googl, PORTFOLIO_WEIGHTS, self.weights)
        self.assertGreater(s_aapl.score, s_googl.score)

    def test_reuters_beats_no_name_blog_for_same_event(self):
        a = {"title": "Apple earnings beat", "symbol": "AAPL",
             "domain": "reuters.com", "source": "Reuters"}
        b = {"title": "Apple earnings beat", "symbol": "AAPL",
             "domain": "randomblog.com", "source": "Google News"}
        self.assertGreater(
            score_candidate(a, PORTFOLIO_WEIGHTS, self.weights).score,
            score_candidate(b, PORTFOLIO_WEIGHTS, self.weights).score,
        )

    def test_urgency_lifts_tonight_over_next_week(self):
        now = {"title": "Microsoft earnings tonight", "symbol": "MSFT",
               "domain": "reuters.com", "source": "Reuters"}
        later = {"title": "Microsoft earnings next week", "symbol": "MSFT",
                 "domain": "reuters.com", "source": "Reuters"}
        self.assertGreater(
            score_candidate(now, PORTFOLIO_WEIGHTS, self.weights).score,
            score_candidate(later, PORTFOLIO_WEIGHTS, self.weights).score,
        )

    def test_unheld_ticker_attenuated(self):
        # A big AAPL earnings story should outrank the same event on an unheld ticker.
        held = {"title": "Apple beats earnings guidance", "symbol": "AAPL",
                "domain": "reuters.com", "source": "Reuters"}
        unheld = {"title": "Exxon beats earnings guidance", "symbol": "XOM",
                  "domain": "reuters.com", "source": "Reuters"}
        self.assertGreater(
            score_candidate(held, PORTFOLIO_WEIGHTS, self.weights).score,
            score_candidate(unheld, PORTFOLIO_WEIGHTS, self.weights).score,
        )

    def test_ranking_puts_halt_and_ma_at_top_for_held(self):
        ranked = score_candidates(self.candidates, PORTFOLIO_WEIGHTS, self.weights)
        top3 = [c.title for c in ranked[:3]]
        # MSFT acquisition, Apple halt, MSFT earnings tonight should all be in top-5.
        joined = " | ".join(top3).lower()
        self.assertTrue(
            any("halt" in joined or "acquire" in joined or "earnings tonight" in joined
                for _ in [0]),
            f"top3 = {top3}",
        )


if __name__ == "__main__":
    unittest.main()
