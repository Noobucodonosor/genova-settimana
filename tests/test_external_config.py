"""Tests for externalized editorial config and validity dates (TASK-DATA-01)."""

import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from genova_outings import catalog, verifier


class TestExternalizedConfig(unittest.TestCase):
    def test_authoritative_outings_loaded_from_json(self):
        self.assertGreaterEqual(len(catalog.AUTHORITATIVE_LIVE_OUTINGS), 20)
        self.assertGreaterEqual(len(verifier.BLACKLISTED_SUBSTRINGS), 30)
        self.assertIn("villa croce", verifier.BLACKLISTED_SUBSTRINGS)
        self.assertIn("palazzo rosso", verifier.MONDAY_CLOSED_MUSEUMS)

    def test_valid_from_and_valid_to_filtering(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg_dir = Path(tmpdir) / "data" / "config"
            cfg_dir.mkdir(parents=True)
            entries = [
                {
                    "id": "active",
                    "title": "Mostra Attiva",
                    "category": "mostra",
                    "venue": "Palazzo Ducale",
                    "zone": "centro",
                    "day_time": "Ogni giorno",
                    "verified_url": "https://palazzoducale.genova.it/",
                    "description": "Attiva ora.",
                    "valid_from": "2026-11-01",
                    "valid_to": "2026-12-31",
                },
                {
                    "id": "expired",
                    "title": "Mostra Scaduta",
                    "category": "mostra",
                    "venue": "Palazzo Ducale",
                    "zone": "centro",
                    "day_time": "Ogni giorno",
                    "verified_url": "https://palazzoducale.genova.it/",
                    "description": "Scaduta.",
                    "valid_to": "2026-11-10",
                },
                {
                    "id": "future",
                    "title": "Mostra Futura",
                    "category": "mostra",
                    "venue": "Palazzo Ducale",
                    "zone": "centro",
                    "day_time": "Ogni giorno",
                    "verified_url": "https://palazzoducale.genova.it/",
                    "description": "Futura.",
                    "valid_from": "2026-12-01",
                },
            ]
            (cfg_dir / "authoritative_outings.json").write_text(json.dumps(entries), encoding="utf-8")
            opts = catalog.load_authoritative_live_options(today=date(2026, 11, 21), data_dir=Path(tmpdir))
            self.assertEqual([o.id for o in opts], ["active"])


if __name__ == "__main__":
    unittest.main()
