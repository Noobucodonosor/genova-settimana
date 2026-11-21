"""Offline unit tests for export_static.py (TASK-QA-01)."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from genova_outings import export_static
from genova_outings.models import OutingCategory, OutingOption


class TestExportStaticOffline(unittest.TestCase):
    def test_dedupe_prefers_richer_programme_entry(self):
        a = OutingOption(
            id="a1",
            title="Cinema Sivori",
            category=OutingCategory.CINEMA,
            venue="Cinema Sivori",
            zone="centro",
            day_time="Ogni sera",
            description="Breve",
            verified_url="https://www.circuitocinemagenova.com/sale/sivori/",
            raw_metadata={},
        )
        b = OutingOption(
            id="a2",
            title="Cinema Sivori (programma)",
            category=OutingCategory.CINEMA,
            venue="Cinema Sivori",
            zone="centro",
            day_time="Ogni sera",
            description="Breve",
            verified_url="https://www.circuitocinemagenova.com/sale/sivori",
            raw_metadata={"programma": [{"titolo": "Film", "quando": "21:00"}]},
        )
        res = export_static._dedupe([a, b])
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].id, "a2")

    def test_build_writes_clean_index_html(self):
        opt = OutingOption(
            id="c1",
            title="Cinema Sivori",
            category=OutingCategory.CINEMA,
            venue="Cinema Sivori",
            zone="centro",
            day_time="Sabato 21:00",
            description="Proiezione serale.",
            verified_url="https://www.circuitocinemagenova.com/",
            raw_metadata={"programma": [{"titolo": "La Chimera", "quando": "Sab 21:00"}]},
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            with patch("genova_outings.export_static.get_weekly_catalog", return_value=[opt]), \
                 patch("genova_outings.export_static.attach_programmes", return_value=1):
                target = export_static.build(out_dir)
            self.assertTrue(target.exists())
            content = target.read_text(encoding="utf-8")
            self.assertIn("Cinema Sivori", content)
            self.assertIn("La Chimera", content)
            for placeholder in ("__DATA__", "__LABELS__", "__RANGE__", "__UPDATED__"):
                self.assertNotIn(placeholder, content)


if __name__ == "__main__":
    unittest.main()
