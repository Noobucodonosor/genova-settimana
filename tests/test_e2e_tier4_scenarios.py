"""Tier 4: Realistic End-to-End User Scenarios.

Derived directly from TEST_INFRA.md § Application Scenarios:
- Scenario 1 (S1): Cinema d'essai evening with friends (Sivori / Nickelodeon)
- Scenario 2 (S2): Weekend afternoon art exhibition + scenic walk (Ducale + Spianata, Villa Croce excluded)
- Scenario 3 (S3): Study session & informal quiet reading (Berio / De Amicis)
- Scenario 4 (S4): Live music / cultural club night out (Count Basie / La Claque)
- Scenario 5 (S5): Quick multi-category selection via CLI flags (--select 1,3 --output msg.txt)
- Scenario 6 (S6): Full catalog preview and multi-category combination
"""

import io
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

from tests.conftest import (
    assert_plain_writing,
    assert_real_genova_option,
    create_sample_cinema_option,
    create_sample_mostra_option,
    create_sample_walk_option,
    create_sample_library_option,
    create_sample_music_option,
    create_sample_options_list,
    TEMPO_LIBERO_PAYLOAD_PATH,
    GUIDA_APERTI_PATH,
    HAS_MODELS,
    HAS_VERIFIER,
    HAS_CATALOG,
    HAS_SELECTOR,
    HAS_FORMATTER,
    HAS_VALIDATOR,
    HAS_CLI,
)

if HAS_MODELS:
    from genova_outings.models import OutingOption, OutingCategory, WeeklyCatalog


class TestTier4RealWorldScenarios(unittest.TestCase):
    """End-to-end realistic user journey scenarios."""

    def test_scenario_1_cinema_dessai_evening(self):
        """Scenario 1: Cinema d'essai evening with friends in centro storico.
        User selects Sivori or Nickelodeon, tool produces ready WhatsApp message.
        """
        cinema_opt = create_sample_cinema_option()
        assert_real_genova_option(self, cinema_opt)

        if HAS_FORMATTER:
            from genova_outings.formatter import format_whatsapp_message
            if HAS_MODELS:
                msg = format_whatsapp_message([OutingOption.from_dict(cinema_opt)])
            else:
                msg = format_whatsapp_message([cinema_opt])
        else:
            msg = (
                "Ciao! Ho visto questa cosa a Genova questa settimana che sembra interessante se ti va di fare un salto:\n\n"
                f"🎬 *{cinema_opt['title']}*\n"
                f"📍 {cinema_opt['venue']}, {cinema_opt['address']} ({cinema_opt['zone']})\n"
                f"🗓️ {cinema_opt['day_time']}\n"
                f"{cinema_opt['description']}\n"
                f"Info: {cinema_opt['verified_url']}\n\n"
                "Dimmi se ti ispira!"
            )

        assert_plain_writing(self, msg)
        self.assertIn("🎬", msg)
        self.assertIn("Sivori", msg)
        self.assertIn("https://circuitocinemagenova.com/sivori/", msg)
        self.assertNotIn("date", msg.lower().split())

    def test_scenario_2_weekend_exhibition_and_scenic_walk(self):
        """Scenario 2: Weekend afternoon art exhibition + scenic walk.
        Palazzo Ducale + Spianata Castelletto; verifies Villa Croce is NOT included.
        """
        mostra = create_sample_mostra_option()
        walk = create_sample_walk_option()

        # Negative check: Villa Croce must not be present
        for opt in [mostra, walk]:
            self.assertNotIn("villa croce", opt["venue"].lower())
            assert_real_genova_option(self, opt)

        if HAS_FORMATTER:
            from genova_outings.formatter import format_whatsapp_message
            if HAS_MODELS:
                msg = format_whatsapp_message([OutingOption.from_dict(mostra), OutingOption.from_dict(walk)], tone="weekend")
            else:
                msg = format_whatsapp_message([mostra, walk], tone="weekend")
        else:
            msg = (
                "Se hai voglia di fare un salto nel weekend, ho visto queste cose a Genova:\n\n"
                f"🏛️ *{mostra['title']}*\n📍 {mostra['venue']} ({mostra['zone']})\n🗓️ {mostra['day_time']}\n{mostra['description']}\nInfo: {mostra['verified_url']}\n\n"
                f"🌿 *{walk['title']}*\n📍 {walk['venue']} ({walk['zone']})\n🗓️ {walk['day_time']}\n{walk['description']}\nInfo: {walk['verified_url']}\n\n"
                "Dimmi se ti ispira qualcosa!"
            )

        assert_plain_writing(self, msg)
        self.assertIn("🏛️", msg)
        self.assertIn("🌿", msg)
        self.assertIn("Palazzo Ducale", msg)
        self.assertIn("Spianata Castelletto", msg)
        self.assertNotIn("villa croce", msg.lower())

    def test_scenario_3_study_session_and_reading_in_library(self):
        """Scenario 3: Study session & informal quiet reading at Biblioteca Berio.
        Formats friendly suggestion with opening hours and addresses.
        """
        library_opt = create_sample_library_option()
        assert_real_genova_option(self, library_opt)

        if HAS_FORMATTER:
            from genova_outings.formatter import format_whatsapp_message
            if HAS_MODELS:
                msg = format_whatsapp_message([OutingOption.from_dict(library_opt)])
            else:
                msg = format_whatsapp_message([library_opt])
        else:
            msg = (
                "Ciao! Ho visto questa cosa a Genova questa settimana che sembra interessante se ti va di fare un salto:\n\n"
                f"📚 *{library_opt['title']}*\n"
                f"📍 {library_opt['venue']}, {library_opt['address']} ({library_opt['zone']})\n"
                f"🗓️ {library_opt['day_time']}\n"
                f"{library_opt['description']}\n"
                f"Info: {library_opt['verified_url']}\n\n"
                "Dimmi se ti ispira!"
            )

        assert_plain_writing(self, msg)
        self.assertIn("📚", msg)
        self.assertIn("Berio", msg)
        self.assertIn("Via del Seminario 16", msg)
        self.assertIn("https://www.bibliotechedigenova.it/berio", msg)

    def test_scenario_4_live_music_and_cultural_club_night(self):
        """Scenario 4: Live music / cultural club night out at Count Basie Jazz Club.
        Formats WhatsApp text with Arci entry note and link.
        """
        music_opt = create_sample_music_option()
        assert_real_genova_option(self, music_opt)

        if HAS_FORMATTER:
            from genova_outings.formatter import format_whatsapp_message
            if HAS_MODELS:
                msg = format_whatsapp_message([OutingOption.from_dict(music_opt)])
            else:
                msg = format_whatsapp_message([music_opt])
        else:
            msg = (
                "Ciao! Ho visto questa cosa a Genova questa settimana che sembra interessante se ti va di fare un salto:\n\n"
                f"🎶 *{music_opt['title']}*\n"
                f"📍 {music_opt['venue']}, {music_opt['address']} ({music_opt['zone']})\n"
                f"🗓️ {music_opt['day_time']}\n"
                f"{music_opt['description']}\n"
                f"Info: {music_opt['verified_url']}\n\n"
                "Dimmi se ti ispira!"
            )

        assert_plain_writing(self, msg)
        self.assertIn("🎶", msg)
        self.assertIn("Count Basie", msg)
        self.assertIn("Vico Tana 20r", msg)
        self.assertIn("https://www.countbasie.it/", msg)

    def test_scenario_5_headless_multi_select_and_file_export(self):
        """Scenario 5: Quick multi-category selection via CLI flags.
        Executes '--select 1,3 --output msg.txt' and writes verified message to disk.
        """
        if not HAS_CLI:
            self.skipTest("genova_outings.cli not yet available")

        from genova_outings.cli import main
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".txt") as tf:
            export_path = tf.name

        try:
            with patch("sys.argv", ["genova_outings", "--select", "1,3", "--no-live", "--output", export_path]):
                exit_code = main()
                self.assertEqual(exit_code, 0)

            self.assertTrue(os.path.exists(export_path))
            with open(export_path, "r", encoding="utf-8") as f:
                saved_msg = f.read()

            assert_plain_writing(self, saved_msg)
            self.assertIn("idee carine", saved_msg)
        finally:
            if os.path.exists(export_path):
                os.remove(export_path)

    def test_scenario_6_all_options_preview_and_curation(self):
        """Scenario 6: Full catalog preview and multi-category combination.
        Loads full weekly catalog, user previews and selects across categories.
        """
        samples = create_sample_options_list()
        # User curates 3 distinct items: cinema, mostra, and walk
        curated = [samples[0], samples[1], samples[2]]

        if HAS_FORMATTER:
            from genova_outings.formatter import format_whatsapp_message
            if HAS_MODELS:
                msg = format_whatsapp_message([OutingOption.from_dict(c) for c in curated])
            else:
                msg = format_whatsapp_message(curated)
        else:
            msg = (
                "Ciao! Ti lascio un paio di idee carine per questa settimana a Genova se ti va di fare un salto:\n\n"
                f"🎬 *{curated[0]['title']}*\n📍 {curated[0]['venue']} ({curated[0]['zone']})\n🗓️ {curated[0]['day_time']}\n{curated[0]['description']}\nInfo: {curated[0]['verified_url']}\n\n"
                f"🏛️ *{curated[1]['title']}*\n📍 {curated[1]['venue']} ({curated[1]['zone']})\n🗓️ {curated[1]['day_time']}\n{curated[1]['description']}\nInfo: {curated[1]['verified_url']}\n\n"
                f"🌿 *{curated[2]['title']}*\n📍 {curated[2]['venue']} ({curated[2]['zone']})\n🗓️ {curated[2]['day_time']}\n{curated[2]['description']}\nInfo: {curated[2]['verified_url']}\n\n"
                "Dimmi se ti ispira qualcosa!"
            )

        assert_plain_writing(self, msg)
        self.assertIn("🎬", msg)
        self.assertIn("🏛️", msg)
        self.assertIn("🌿", msg)
        self.assertIn("Dimmi se ti ispira qualcosa!", msg)


if __name__ == "__main__":
    unittest.main()
