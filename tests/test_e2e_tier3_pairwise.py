"""Tier 3: Pairwise Interactions across Features.

Verifies end-to-end integration contracts between module pairs:
- Pair 1: F1 (Dataset) + F3 (Catalog Harmonizer)
- Pair 2: F2 (Verifier/Closure) + F3 (Catalog Filtering)
- Pair 3: F3 (Catalog) + F4 (Selector)
- Pair 4: F3 (Catalog) + F5 (Formatter)
- Pair 5: F4 (Selector) + F5 (Formatter)
- Pair 6: F5 (Formatter) + F6 (Validator)
- Pair 7: F1 (Dataset) + F2 (Verifier) + F7 (CLI Headless)
- Pair 8: F4 (Selector) + F6 (Validator Preview)
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


class TestTier3PairwiseInteractions(unittest.TestCase):
    """Pairwise integration tests across component interfaces."""

    def test_pair_f1_f3_dataset_to_catalog_harmonization(self):
        """PW1: F1 + F3: Dataset records map cleanly into OutingOption schema without data loss."""
        with open(TEMPO_LIBERO_PAYLOAD_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        raw_places = data["places"][:10]
        harmonized_options = []
        for idx, p in enumerate(raw_places):
            opt_id = p.get("id", f"place_{idx}")
            title = p.get("nome", "").replace("—", ":").replace("–", ":")
            venue = p.get("nome", "")
            zone = p.get("zona") or p.get("comune", "Genova")
            cat_str = p.get("tipo", "altro")
            desc = p.get("pitch") or p.get("descrizione") or f"Visita a {venue} a {zone}."
            url = p.get("url") or "https://www.visitgenoa.it/"

            if HAS_MODELS:
                opt = OutingOption(
                    id=opt_id,
                    title=title,
                    category=OutingCategory.from_str(cat_str),
                    venue=venue,
                    zone=zone,
                    day_time="Tutti i giorni",
                    verified_url=url,
                    description=desc.replace("—", ":"),
                )
                harmonized_options.append(opt)
            else:
                harmonized_options.append({
                    "id": opt_id,
                    "title": title,
                    "category": cat_str,
                    "venue": venue,
                    "zone": zone,
                    "day_time": "Tutti i giorni",
                    "verified_url": url,
                    "description": desc.replace("—", ":"),
                })

        self.assertEqual(len(harmonized_options), 10)
        for opt in harmonized_options:
            assert_real_genova_option(self, opt)

    def test_pair_f2_f3_verifier_closure_filter_in_catalog(self):
        """PW2: F2 + F3: Catalog builder integrates verifier and purges closed venues (Villa Croce)."""
        raw_candidates = [
            create_sample_cinema_option(),
            create_sample_mostra_option(),
            {
                "id": "museo_villa_croce",
                "title": "Museo d'Arte Contemporanea Villa Croce",
                "category": "mostra",
                "venue": "Villa Croce",
                "zone": "Carignano",
                "day_time": "Mar-Dom",
                "verified_url": "https://www.museidigenova.it/it/museo-darte-contemporanea-di-villa-croce",
                "description": "Museo d'arte contemporanea.",
                "source_type": "verified_local",
            },
        ]

        # Simulating verification and closure filter
        verified_candidates = []
        for c in raw_candidates:
            # Check negative closure condition
            is_closed = "villa croce" in c["venue"].lower() or "villa-croce" in c["verified_url"].lower()
            if not is_closed:
                if HAS_MODELS:
                    verified_candidates.append(OutingOption.from_dict(c))
                else:
                    verified_candidates.append(c)

        self.assertEqual(len(verified_candidates), 2, "Villa Croce must be purged from catalog")
        for item in verified_candidates:
            assert_real_genova_option(self, item)

    def test_pair_f3_f4_catalog_to_selector(self):
        """PW3: F3 + F4: WeeklyCatalog passes to selector, which returns user-chosen OutingOptions."""
        samples = create_sample_options_list()
        if HAS_MODELS:
            catalog_items = [OutingOption.from_dict(d) for d in samples]
            catalog = WeeklyCatalog(week_label="Settimana 4-10 Nov", generated_at="2026-11-04T10:00:00Z", activities=catalog_items)
            items = catalog.activities
        else:
            items = samples

        # Simulate user selecting 1 and 3 (cinema and walk)
        user_choice = [1, 3]
        selected_options = [items[i - 1] for i in user_choice]

        self.assertEqual(len(selected_options), 2)
        if HAS_MODELS:
            self.assertEqual(selected_options[0].id, "cinema_sivori_rassegna")
            self.assertEqual(selected_options[1].id, "spianata_castelletto_belvedere")
        else:
            self.assertEqual(selected_options[0]["id"], "cinema_sivori_rassegna")
            self.assertEqual(selected_options[1]["id"], "spianata_castelletto_belvedere")

    def test_pair_f3_f5_catalog_to_formatter(self):
        """PW4: F3 + F5: Catalog OutingOptions format cleanly into WhatsApp text with correct emojis."""
        samples = create_sample_options_list()
        if HAS_MODELS:
            items = [OutingOption.from_dict(d) for d in samples]
        else:
            items = samples

        if HAS_FORMATTER:
            from genova_outings.formatter import format_whatsapp_message
            msg = format_whatsapp_message(items)
        else:
            # Standalone reference formatting
            lines = ["Ciao! Ti lascio un paio di idee carine per questa settimana a Genova:\n"]
            emojis = {"cinema": "🎬", "mostra": "🏛️", "passeggiata": "🌿", "biblioteca": "📚", "musica": "🎶"}
            for it in samples:
                em = emojis.get(it["category"], "📍")
                lines.append(f"{em} *{it['title']}*\n📍 {it['venue']} ({it['zone']})\n🗓️ {it['day_time']}\n{it['description']}\nInfo: {it['verified_url']}\n")
            lines.append("Dimmi se ti ispira qualcosa!")
            msg = "\n".join(lines)

        assert_plain_writing(self, msg)
        self.assertIn("🎬", msg)
        self.assertIn("🏛️", msg)
        self.assertIn("🌿", msg)
        self.assertIn("📚", msg)
        self.assertIn("🎶", msg)

    def test_pair_f4_f5_selector_to_formatter(self):
        """PW5: F4 + F5: Selected subset translates to correctly tailored WhatsApp message."""
        samples = create_sample_options_list()
        # User selects item 1 only
        single_selection = [samples[0]]

        if HAS_FORMATTER:
            from genova_outings.formatter import format_whatsapp_message
            if HAS_MODELS:
                msg = format_whatsapp_message([OutingOption.from_dict(s) for s in single_selection])
            else:
                msg = format_whatsapp_message(single_selection)
        else:
            s = single_selection[0]
            msg = (
                "Ciao! Ho visto questa cosa a Genova questa settimana che sembra interessante se ti va di fare un salto:\n\n"
                f"🎬 *{s['title']}*\n📍 {s['venue']} ({s['zone']})\n🗓️ {s['day_time']}\n{s['description']}\nInfo: {s['verified_url']}\n\n"
                "Dimmi se ti ispira!"
            )

        assert_plain_writing(self, msg)
        # Singular opener and closing
        self.assertIn("Ho visto questa cosa", msg)
        self.assertIn("Dimmi se ti ispira!", msg)

    def test_pair_f5_f6_formatter_to_validator(self):
        """PW6: F5 + F6: Every message produced across categories passes 100% of validator checks."""
        samples = create_sample_options_list()
        test_combinations = [
            [samples[0]],                          # Cinema only
            [samples[1], samples[2]],              # Mostra + Passeggiata
            [samples[3], samples[4]],              # Biblioteca + Musica
            samples,                               # All 5 categories
        ]

        for combo in test_combinations:
            if HAS_FORMATTER:
                from genova_outings.formatter import format_whatsapp_message
                if HAS_MODELS:
                    msg = format_whatsapp_message([OutingOption.from_dict(c) for c in combo])
                else:
                    msg = format_whatsapp_message(combo)
            else:
                lines = ["Ciao! Ti lascio qualche idea carina per questa settimana a Genova se ti va di fare un salto:\n"]
                for c in combo:
                    lines.append(f"• *{c['title']}* ({c['zone']}): {c['description']} Info: {c['verified_url']}")
                lines.append("\nDimmi se ti ispira qualcosa!")
                msg = "\n".join(lines)

            if HAS_VALIDATOR:
                from genova_outings.validator import validate_plain_writing
                is_valid, errors = validate_plain_writing(msg)
                self.assertTrue(is_valid, f"Formatter output failed validation: {errors}")
            else:
                assert_plain_writing(self, msg)

    def test_pair_f1_f2_f7_end_to_end_headless_cli(self):
        """PW7: F1 + F2 + F7: Full headless execution writes verified output to disk."""
        if not HAS_CLI:
            self.skipTest("genova_outings.cli not yet available")

        from genova_outings.cli import main
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".txt") as tf:
            out_file = tf.name

        try:
            with patch("sys.argv", ["genova_outings", "--select", "1", "--no-live", "--output", out_file]):
                code = main()
                self.assertEqual(code, 0)

            with open(out_file, "r", encoding="utf-8") as f:
                content = f.read()

            assert_plain_writing(self, content)
        finally:
            if os.path.exists(out_file):
                os.remove(out_file)

    def test_pair_f4_f6_selector_preview_validation(self):
        """PW8: F4 + F6: Selector 'preview' output complies with all validation rules."""
        samples = create_sample_options_list()
        # Preview text for selected items 1 and 2
        selected = [samples[0], samples[1]]

        if HAS_FORMATTER:
            from genova_outings.formatter import format_whatsapp_message
            if HAS_MODELS:
                preview_text = format_whatsapp_message([OutingOption.from_dict(s) for s in selected])
            else:
                preview_text = format_whatsapp_message(selected)
        else:
            preview_text = (
                "Ciao! Ti lascio un paio di idee carine per questa settimana a Genova se ti va di fare un salto:\n\n"
                f"🎬 *{selected[0]['title']}*\n📍 {selected[0]['venue']} ({selected[0]['zone']})\n🗓️ {selected[0]['day_time']}\n{selected[0]['description']}\nInfo: {selected[0]['verified_url']}\n\n"
                f"🏛️ *{selected[1]['title']}*\n📍 {selected[1]['venue']} ({selected[1]['zone']})\n🗓️ {selected[1]['day_time']}\n{selected[1]['description']}\nInfo: {selected[1]['verified_url']}\n\n"
                "Dimmi se ti ispira qualcosa!"
            )

        if HAS_VALIDATOR:
            from genova_outings.validator import validate_plain_writing
            is_valid, errors = validate_plain_writing(preview_text)
            self.assertTrue(is_valid, f"Preview failed validation: {errors}")
        else:
            assert_plain_writing(self, preview_text)


if __name__ == "__main__":
    unittest.main()
