"""Novelty / dedup unit tests."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from quantfolio.signals.novelty import filter_novel
from quantfolio.store import connect, headline_hash


class NoveltyTests(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.conn = connect(self.tmp.name)

    def tearDown(self):
        self.conn.close()
        Path(self.tmp.name).unlink(missing_ok=True)

    def test_first_run_marks_all_novel(self):
        items = [
            {"title": "Apple beats earnings", "source": "Reuters", "symbol": "AAPL"},
            {"title": "MSFT to acquire Activision", "source": "Bloomberg", "symbol": "MSFT"},
        ]
        out = filter_novel(self.conn, items)
        self.assertEqual(len(out), 2)

    def test_duplicate_removed_on_second_pass(self):
        items = [{"title": "Apple beats earnings", "source": "Reuters", "symbol": "AAPL"}]
        self.assertEqual(len(filter_novel(self.conn, items)), 1)
        self.assertEqual(len(filter_novel(self.conn, items)), 0)

    def test_normalization_matches_trivial_edits(self):
        a = {"title": "Apple beats earnings!!", "source": "Reuters", "symbol": "AAPL"}
        b = {"title": "apple BEATS earnings", "source": "Reuters", "symbol": "AAPL"}
        self.assertEqual(
            headline_hash(a["title"], a["source"]),
            headline_hash(b["title"], b["source"]),
        )
        filter_novel(self.conn, [a])
        self.assertEqual(len(filter_novel(self.conn, [b])), 0)

    def test_different_source_is_separate(self):
        a = {"title": "Apple beats earnings", "source": "Reuters", "symbol": "AAPL"}
        b = {"title": "Apple beats earnings", "source": "Bloomberg", "symbol": "AAPL"}
        filter_novel(self.conn, [a])
        self.assertEqual(len(filter_novel(self.conn, [b])), 1)

    def test_mark_false_does_not_persist(self):
        items = [{"title": "Apple beats earnings", "source": "Reuters", "symbol": "AAPL"}]
        filter_novel(self.conn, items, mark=False)
        self.assertEqual(len(filter_novel(self.conn, items)), 1)  # still novel


if __name__ == "__main__":
    unittest.main()
