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

    def test_crazy_bull_fixture_filters_window(self):
        html_doc = (FIXTURES / "crazy_bull.html").read_text(encoding="utf-8")
        with patch("genova_outings.programme._get", return_value=html_doc):
            items = programme.crazy_bull("https://www.crazybullgenova.it/eventi", TODAY)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["titolo"], "Live Rock Night")
        self.assertIn("21:00", items[0]["quando"])
        self.assertTrue(programme.has_extractor("https://www.crazybullgenova.it/eventi"))

    def test_genova_tango_fixture_filters_window(self):
        html_doc = (FIXTURES / "genova_tango.html").read_text(encoding="utf-8")
        with patch("genova_outings.programme._get", return_value=html_doc):
            items = programme.genova_tango("https://www.genovatango.com/eventi/", TODAY)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["titolo"], "La Milonga del CBA")
        self.assertIn("21:00-01:00", items[0]["quando"])
        self.assertTrue(programme.has_extractor("https://www.genovatango.com/eventi/"))

    def test_xceed_genova_events_jsonld_and_venue_match(self):
        ld = json.dumps([
            {
                "@type": "Event",
                "name": "SATURDAY ROYALE | ESTORIL BEACH CLUB",
                "startDate": "2026-11-21T23:45:00+01:00",
                "location": {"name": "Estoril Beach Club"},
            },
            {
                "@type": "Event",
                "name": "Capodanno Lontano",
                "startDate": "2026-12-31T23:00:00+01:00",
                "location": {"name": "Estoril Beach Club"},
            },
        ])
        html_doc = f'<html><script type="application/ld+json">{ld}</script></html>'
        with patch("genova_outings.programme._get", return_value=html_doc):
            events = programme.xceed_genova_events(TODAY)
        self.assertEqual(len(events), 1)
        self.assertNotIn("|", events[0]["titolo"])
        self.assertIn("23:45", events[0]["quando"])
        matched = programme.match_venue_events("Estoril Beach Club: Discoteca sul Mare", events)
        self.assertEqual(len(matched), 1)
        self.assertIn("SATURDAY ROYALE", matched[0]["titolo"])

    def test_has_extractor_and_parse_range(self):
        self.assertTrue(programme.has_extractor("https://www.circuitocinemagenova.com/"))
        self.assertFalse(programme.has_extractor("https://example.invalid/"))
        start, end = programme.parse_range("20 novembre - 30 novembre 2026", TODAY)
        self.assertEqual(start, date(2026, 11, 20))
        self.assertEqual(end, date(2026, 11, 30))

    def test_parse_range_respects_explicit_years_and_cross_year(self):
        # Past year must not be promoted to current year
        s_past, e_past = programme.parse_range("22 novembre 2025", TODAY)
        self.assertEqual((s_past, e_past), (date(2025, 11, 22), date(2025, 11, 22)))
        self.assertFalse(programme._keep(s_past, e_past, TODAY))

        s_rng, e_rng = programme.parse_range("22-23 novembre 2025", TODAY)
        self.assertEqual((s_rng, e_rng), (date(2025, 11, 22), date(2025, 11, 23)))
        self.assertFalse(programme._keep(s_rng, e_rng, TODAY))

        # Cross-year span
        s_ny, e_ny = programme.parse_range("31 dicembre 2026 - 1 gennaio 2027", date(2026, 12, 28))
        self.assertEqual((s_ny, e_ny), (date(2026, 12, 31), date(2027, 1, 1)))
        self.assertTrue(programme._keep(s_ny, e_ny, date(2026, 12, 28)))

        # Leap day with explicit year
        s_leap, e_leap = programme.parse_range("29 febbraio 2028", date(2027, 12, 20))
        self.assertEqual((s_leap, e_leap), (date(2028, 2, 29), date(2028, 2, 29)))

    def test_venue_groups_word_boundary_no_mog_camogli_collision(self):
        camogli_ev = [{"luogo": "Camogli", "titolo": "Festa del Pesce", "quando": "sabato 21 novembre"}]
        mog_ev = [{"luogo": "MOG Mercato Orientale", "titolo": "DJ Set MOG", "quando": "sabato 21 novembre"}]
        self.assertEqual(programme.match_venue_events("MOG Mercato Orientale: Cocktail Bar", camogli_ev), [])
        self.assertEqual(programme.match_venue_events("Porticciolo di Camogli", mog_ev), [])
        self.assertEqual(len(programme.match_venue_events("MOG Mercato Orientale: Cocktail Bar", mog_ev)), 1)
        self.assertEqual(len(programme.match_venue_events("Porticciolo di Camogli", camogli_ev)), 1)

    def test_xceed_genova_events_supports_graph_and_music_event_type(self):
        ld = json.dumps({
            "@context": "https://schema.org",
            "@graph": [
                {
                    "@type": "MusicEvent",
                    "name": "TECHNO NIGHT | MENODUE",
                    "startDate": "2026-11-22T23:30:00+01:00",
                    "location": {"name": "MenoDue Club"},
                }
            ],
        })
        html_doc = f'<html><script type="application/ld+json">{ld}</script></html>'
        with patch("genova_outings.programme._get", return_value=html_doc):
            events = programme.xceed_genova_events(TODAY)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["titolo"], "TECHNO NIGHT - MENODUE")
        self.assertEqual(len(programme.match_venue_events("MenoDue Club: Elettronica", events)), 1)


if __name__ == "__main__":
    unittest.main()
