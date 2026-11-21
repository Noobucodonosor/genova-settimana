"""Unit tests for genova_outings/models.py."""

import unittest
from genova_outings.models import OutingCategory, OutingOption, WeeklyCatalog


class TestOutingCategory(unittest.TestCase):
    """Test OutingCategory enum and synonym resolution."""

    def test_enum_members_exist(self):
        expected = {
            "cinema", "mostra", "passeggiata", "biblioteca",
            "laboratorio", "musica", "ritrovo", "altro"
        }
        actual = {m.value for m in OutingCategory}
        self.assertEqual(expected, actual)

    def test_enum_string_comparison(self):
        self.assertEqual(OutingCategory.CINEMA, "cinema")
        self.assertEqual(OutingCategory.MOSTRA.value, "mostra")
        self.assertEqual(str(OutingCategory.PASSEGGIATA), "passeggiata")

    def test_from_str_standard(self):
        self.assertEqual(OutingCategory.from_str("cinema"), OutingCategory.CINEMA)
        self.assertEqual(OutingCategory.from_str("MOSTRA"), OutingCategory.MOSTRA)
        self.assertEqual(OutingCategory.from_str("passeggiata"), OutingCategory.PASSEGGIATA)

    def test_from_str_synonyms(self):
        self.assertEqual(OutingCategory.from_str("film"), OutingCategory.CINEMA)
        self.assertEqual(OutingCategory.from_str("cineclub"), OutingCategory.CINEMA)
        self.assertEqual(OutingCategory.from_str("museo"), OutingCategory.MOSTRA)
        self.assertEqual(OutingCategory.from_str("parco"), OutingCategory.PASSEGGIATA)
        self.assertEqual(OutingCategory.from_str("studio"), OutingCategory.BIBLIOTECA)
        self.assertEqual(OutingCategory.from_str("bottega"), OutingCategory.LABORATORIO)
        self.assertEqual(OutingCategory.from_str("live"), OutingCategory.MUSICA)
        self.assertEqual(OutingCategory.from_str("caffe"), OutingCategory.RITROVO)

    def test_from_str_fallback_altro(self):
        self.assertEqual(OutingCategory.from_str("unknown_xyz"), OutingCategory.ALTRO)
        self.assertEqual(OutingCategory.from_str(""), OutingCategory.ALTRO)


class TestOutingOption(unittest.TestCase):
    """Test OutingOption data model attributes and behaviors."""

    def setUp(self):
        self.sample = OutingOption(
            id="sivori_film",
            title="Cinema Sivori: Rassegna d'Essai",
            category=OutingCategory.CINEMA,
            venue="Cinema Sivori",
            zone="Centro",
            day_time="Mercoledì ore 21:15",
            verified_url="https://circuitocinemagenova.com/sivori/",
            description="Proiezione d'autore in lingua originale.",
            source_type="live_web",
            is_weather_dependent=False,
        )

    def test_basic_fields(self):
        self.assertEqual(self.sample.id, "sivori_film")
        self.assertEqual(self.sample.title, "Cinema Sivori: Rassegna d'Essai")
        self.assertEqual(self.sample.category, OutingCategory.CINEMA)
        self.assertEqual(self.sample.venue, "Cinema Sivori")
        self.assertEqual(self.sample.zone, "Centro")
        self.assertEqual(self.sample.day_time, "Mercoledì ore 21:15")
        self.assertEqual(self.sample.verified_url, "https://circuitocinemagenova.com/sivori/")
        self.assertEqual(self.sample.description, "Proiezione d'autore in lingua originale.")
        self.assertEqual(self.sample.source_type, "live_web")
        self.assertFalse(self.sample.is_weather_dependent)

    def test_compatibility_properties(self):
        # source_url alias
        self.assertEqual(self.sample.source_url, self.sample.verified_url)
        self.sample.source_url = "https://example.com/new"
        self.assertEqual(self.sample.verified_url, "https://example.com/new")

        # days_display alias
        self.assertEqual(self.sample.days_display, self.sample.day_time)
        self.sample.days_display = "Giovedì ore 18:00"
        self.assertEqual(self.sample.day_time, "Giovedì ore 18:00")

        # verified property
        self.assertTrue(self.sample.verified)

    def test_serialization_roundtrip(self):
        d = self.sample.to_dict()
        self.assertEqual(d["id"], "sivori_film")
        self.assertEqual(d["category"], "cinema")
        self.assertIn("verified_url", d)

        rebuilt = OutingOption.from_dict(d)
        self.assertEqual(rebuilt.id, self.sample.id)
        self.assertEqual(rebuilt.category, self.sample.category)
        self.assertEqual(rebuilt.venue, self.sample.venue)
        self.assertEqual(rebuilt.verified_url, self.sample.verified_url)

    def test_defaults_and_extended_fields(self):
        minimal = OutingOption(
            id="spianata",
            title="Spianata Castelletto",
            category=OutingCategory.PASSEGGIATA,
            venue="Spianata",
            zone="Castelletto",
            day_time="h24",
            verified_url="https://visitgenoa.it",
            description="Vista panoramica.",
        )
        self.assertEqual(minimal.source_type, "verified_local")
        self.assertFalse(minimal.is_weather_dependent)
        self.assertEqual(minimal.address, "")
        self.assertEqual(minimal.time_slot, "flessibile")
        self.assertIsNone(minimal.cost_info)
        self.assertFalse(minimal.is_free)
        self.assertEqual(minimal.tags, [])
        self.assertEqual(minimal.raw_metadata, {})


class TestWeeklyCatalog(unittest.TestCase):
    """Test WeeklyCatalog collection and filtering."""

    def test_filter_by_category(self):
        act1 = OutingOption(
            id="1", title="Film", category=OutingCategory.CINEMA, venue="Sivori",
            zone="Centro", day_time="h21", verified_url="https://sivori.it", description="Film"
        )
        act2 = OutingOption(
            id="2", title="Mostra", category=OutingCategory.MOSTRA, venue="Ducale",
            zone="Centro", day_time="h10", verified_url="https://ducale.it", description="Arte"
        )
        catalog = WeeklyCatalog(
            week_label="Settimana 4-10 Novembre 2026",
            generated_at="2026-11-04T10:00:00Z",
            activities=[act1, act2],
        )

        cinemas = catalog.filter_by_category(OutingCategory.CINEMA)
        self.assertEqual(len(cinemas), 1)
        self.assertEqual(cinemas[0].id, "1")

        mostre = catalog.filter_by_category("mostra")
        self.assertEqual(len(mostre), 1)
        self.assertEqual(mostre[0].id, "2")

        empty = catalog.filter_by_category("musica")
        self.assertEqual(len(empty), 0)

    def test_serialization(self):
        catalog = WeeklyCatalog(
            week_label="Settimana 4-10 Novembre 2026",
            generated_at="2026-11-04T10:00:00Z",
            activities=[],
        )
        d = catalog.to_dict()
        self.assertEqual(d["week_label"], "Settimana 4-10 Novembre 2026")
        rebuilt = WeeklyCatalog.from_dict(d)
        self.assertEqual(rebuilt.week_label, catalog.week_label)


if __name__ == "__main__":
    unittest.main()
