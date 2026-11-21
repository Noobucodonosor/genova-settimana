"""Offline unit tests for programme.py extractors using HTML/JSON fixtures (TASK-QA-01)."""

import json
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from genova_outings import programme

FIXTURES = Path(__file__).resolve().parent / "fixtures"
TODAY = date(2026, 11, 21)


class TestProgrammeExtractorsOffline(unittest.TestCase):
    def test_circuito_cinema_fixture(self):
        html_doc = (FIXTURES / "circuito_cinema.html").read_text(encoding="utf-8")
        with patch("genova_outings.programme._get", return_value=html_doc):
            items = programme.circuito_cinema("https://www.circuitocinemagenova.com/sale/sivori/", TODAY)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["titolo"], "La Chimera")
        self.assertIn("Sab 21 Nov 18:30 21:00", items[0]["quando"])

    def test_nickelodeon_fixture(self):
        html_doc = (FIXTURES / "nickelodeon.html").read_text(encoding="utf-8")
        with patch("genova_outings.programme._get", return_value=html_doc):
            items = programme.nickelodeon("https://www.cineclubnickelodeon.it/", TODAY)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["titolo"], "Il Tempo Che Ci Vuole")
        self.assertIn("19:00 / 21:15", items[0]["quando"])
        self.assertIn("17:30", items[0]["quando"])

    def test_teatro_nazionale_fixture_filters_window(self):
        html_doc = (FIXTURES / "teatro_nazionale.html").read_text(encoding="utf-8")
        with patch("genova_outings.programme._get", return_value=html_doc):
            items = programme.teatro_nazionale("https://www.teatronazionalegenova.it/spettacolo_sala/ivo-chiesa/", TODAY)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["titolo"], "La Coscienza di Zeno")

    def test_tribe_events_json_fixture(self):
        payload = json.dumps({
            "events": [
                {"title": "Concerto d&#8217;Autunno", "start_date": "2026-11-22 20:30:00"},
                {"title": "Evento Lontano", "start_date": "2026-12-28 20:30:00"},
            ]
        })
        with patch("genova_outings.programme._get", return_value=payload):
            items = programme.tribe_events("https://www.teatrosocialecamogli.it/", TODAY)
        self.assertEqual(len(items), 1)
        self.assertIn("20:30", items[0]["quando"])

    def test_carlo_felice_fixture(self):
        html_doc = (
            '<div class="elementor-slide-heading">La_Traviata</div>'
            '<div class="elementor-slide-description">Dal 20 al 26 Novembre 2026</div>'
        )
        with patch("genova_outings.programme._get", return_value=html_doc):
            items = programme.carlo_felice("https://carlofelice.it/", TODAY)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["titolo"], "La Traviata")

    def test_has_extractor_and_parse_range(self):
        self.assertTrue(programme.has_extractor("https://www.circuitocinemagenova.com/"))
        self.assertFalse(programme.has_extractor("https://example.invalid/"))
        start, end = programme.parse_range("20 novembre - 30 novembre 2026", TODAY)
        self.assertEqual(start, date(2026, 11, 20))
        self.assertEqual(end, date(2026, 11, 30))


if __name__ == "__main__":
    unittest.main()
