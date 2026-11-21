"""Verification tests for Genova Civica 2.0 upgrades."""

import io
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

from genova_outings import export_static, html_utils, programme


class TestGenovaCivica2(unittest.TestCase):
    def test_shared_nav_includes_storie_and_pwa_assets_exist(self):
        nav = html_utils.render_shared_nav("storie")
        self.assertIn("storie.html", nav)
        self.assertIn("Storie dalle Strade", nav)
        root = Path(__file__).resolve().parent.parent
        self.assertTrue((root / "site" / "manifest.webmanifest").exists())
        self.assertTrue((root / "site" / "sw.js").exists())

    def test_async_html_pages_stay_lightweight(self):
        root = Path(__file__).resolve().parent.parent
        for name in ("esercenti.html", "dashboard.html", "storie.html"):
            target = root / "site" / name
            self.assertTrue(target.exists(), name)
            self.assertLess(target.stat().st_size, 64 * 1024, f"{name} exceeded 64 KB")

    def test_export_static_has_weather_sel_ics_and_persistence(self):
        for marker in (
            "api.open-meteo.com",
            "genova_civica_sel_v1",
            "downloadIcs",
            "genova-programma.ics",
            'p.set("sel"',
            "toneSel",
        ):
            self.assertIn(marker, export_static.PAGE)

    def test_programme_get_retries_once_on_transient_timeout(self):
        class DummyResp:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def read(self):
                return b"<html>ok</html>"

        with patch("urllib.request.urlopen", side_effect=[TimeoutError("slow"), DummyResp()]) as m, \
             patch("time.sleep"):
            out = programme._get("https://example.org/", timeout=1.0)
        self.assertEqual(out, "<html>ok</html>")
        self.assertEqual(m.call_count, 2)


if __name__ == "__main__":
    unittest.main()
