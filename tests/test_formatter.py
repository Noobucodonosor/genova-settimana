"""Unit tests for genova_outings.formatter module.

Tests WhatsApp message formatting, informal Italian phrasing, category emojis,
tones, layouts, and automated plain-writing compliance.
"""

import unittest
from tests.conftest import assert_plain_writing
from genova_outings.models import OutingCategory, OutingOption
from genova_outings.formatter import (
    CATEGORY_EMOJIS,
    format_whatsapp_message,
)
from genova_outings.validator import validate_plain_writing


class TestFormatter(unittest.TestCase):
    """Test suite for format_whatsapp_message."""

    def setUp(self):
        self.cinema_item = OutingOption(
            id="cinema_sivori_autore",
            title="Cinema Sivori: rassegna cinema d'autore",
            category=OutingCategory.CINEMA,
            venue="Cinema Sivori",
            zone="Centro",
            address="Salita Santa Caterina 12",
            day_time="Mercoledì alle 21:15",
            verified_url="https://circuitocinemagenova.com/sivori/",
            description="Proiezione in lingua originale con sottotitoli in italiano nella storica sala.",
        )
        self.mostra_item = OutingOption(
            id="palazzo_ducale_mostra",
            title="Palazzo Ducale: mostra impressionisti",
            category=OutingCategory.MOSTRA,
            venue="Palazzo Ducale",
            zone="Centro",
            address="Piazza Matteotti 9",
            day_time="Gio-Dom 10:00-19:00",
            verified_url="https://palazzoducale.genova.it/mostre/",
            description="Opere di Renoir e Monet esposte al Sottoporticato.",
        )
        self.walk_item = OutingOption(
            id="spianata_castelletto_belvedere",
            title="Spianata Castelletto: sosta al belvedere",
            category=OutingCategory.PASSEGGIATA,
            venue="Belvedere Luigi Montaldo",
            zone="Castelletto",
            address="Spianata Castelletto",
            day_time="Tutti i giorni",
            verified_url="https://www.visitgenoa.it/it/spianata-castelletto_",
            description="Passeggiata con vista panoramica sul porto e sui tetti.",
            is_weather_dependent=True,
        )

    def test_single_item_formatting(self):
        """Single item formats with singular opener and closer."""
        msg = format_whatsapp_message([self.cinema_item])
        assert_plain_writing(self, msg)
        self.assertIn("Ho visto questa cosa a Genova", msg)
        self.assertIn("🎬 *Cinema Sivori: rassegna cinema d'autore*", msg)
        self.assertIn("Salita Santa Caterina 12", msg)
        self.assertIn("Mercoledì alle 21:15", msg)
        self.assertIn("https://circuitocinemagenova.com/sivori/", msg)
        self.assertIn("Dimmi se ti ispira!", msg)

    def test_multiple_items_formatting(self):
        """Multiple items format with plural opener, distinct emojis, and plural closer."""
        msg = format_whatsapp_message([self.cinema_item, self.mostra_item, self.walk_item])
        assert_plain_writing(self, msg)
        self.assertIn("Ti lascio un paio di idee carine", msg)
        self.assertIn("🎬", msg)
        self.assertIn("🏛️", msg)
        self.assertIn("🌿", msg)
        self.assertIn("Dimmi se ti ispira qualcosa!", msg)

    def test_empty_list_returns_friendly_notice(self):
        """Empty list returns polite empty message."""
        msg = format_whatsapp_message([])
        self.assertEqual(msg, "Nessuna attività selezionata.")

    def test_tone_variations(self):
        """Different tone choices produce valid plain-writing outputs."""
        tones = ["amichevole", "weekend", "minimal", "relaxed", "unknown_custom"]
        for tone in tones:
            msg = format_whatsapp_message([self.cinema_item], tone=tone)
            assert_plain_writing(self, msg)
            if tone == "weekend":
                self.assertIn("weekend", msg.lower())
            elif tone == "minimal":
                self.assertIn("opzioni in programma", msg.lower())

    def test_handles_dictionary_inputs(self):
        """Accepts list of dictionaries as input seamlessly."""
        opt_dict = self.cinema_item.to_dict()
        msg = format_whatsapp_message([opt_dict])
        assert_plain_writing(self, msg)
        self.assertIn("Cinema Sivori", msg)

    def test_compact_layout(self):
        """Supports compact bullet layout."""
        msg = format_whatsapp_message([self.cinema_item, self.walk_item], layout="compact")
        assert_plain_writing(self, msg)
        self.assertIn("• 🎬", msg)
        self.assertIn("• 🌿", msg)

    def test_sanitizes_dirty_fields_on_the_fly(self):
        """Input with em-dashes and buzzwords is sanitized into clean message."""
        dirty_item = OutingOption(
            id="dirty_item",
            title="Concerto Jazz — Count Basie",
            category=OutingCategory.MUSICA,
            venue="Count Basie — Club",
            zone="Centro Storico",
            day_time="Venerdì",
            verified_url="https://www.countbasie.it/.",
            description="Una serata davvero imperdibile e magica a lume di candela.",
        )
        msg = format_whatsapp_message([dirty_item])
        assert_plain_writing(self, msg)
        self.assertNotIn("—", msg)
        self.assertNotIn("imperdibile", msg.lower())
        self.assertNotIn("lume di candela", msg.lower())

    def test_category_emojis_mapping(self):
        """All OutingCategories have distinct discrete emojis."""
        for cat in OutingCategory:
            self.assertIn(cat, CATEGORY_EMOJIS)
            self.assertTrue(len(CATEGORY_EMOJIS[cat]) > 0)


if __name__ == "__main__":
    unittest.main()
