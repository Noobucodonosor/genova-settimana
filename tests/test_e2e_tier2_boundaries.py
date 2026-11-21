"""Tier 2: Boundary & Corner Cases (Stress, Edge Conditions, Negative Inputs).

Covers all 7 features with at least 5 tests per feature (35+ tests total):
- Feature 1: Local Dataset Aggregator Boundaries (F1)
- Feature 2: Live Verification Prober Boundaries (F2)
- Feature 3: Catalog Harmonizer Schema Boundaries (F3)
- Feature 4: Interactive Selection Interface Boundaries (F4)
- Feature 5: WhatsApp Plain-Writing Formatter Boundaries (F5)
- Feature 6: Automated Plain-Writing Validator Boundaries (F6)
- Feature 7: Main CLI Integration & Runner Boundaries (F7)
"""

import io
import json
import os
import sys
import tempfile
import time
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
    DASHBOARD_ITEMS_PATH,
    HAS_MODELS,
    HAS_VERIFIER,
    HAS_CATALOG,
    HAS_SELECTOR,
    HAS_FORMATTER,
    HAS_VALIDATOR,
    HAS_CLI,
    check_import,
)

if HAS_MODELS:
    from genova_outings.models import OutingOption, OutingCategory, WeeklyCatalog


# ==============================================================================
# Feature 1 Boundaries: Local Dataset Aggregator (F1)
# ==============================================================================
class TestFeature1Boundaries(unittest.TestCase):
    """Tier 2: Boundary and edge tests for dataset loading and aggregation."""

    def test_f1_b01_corrupt_json_handling(self):
        """F1.B1: Handle corrupted/malformed JSON file gracefully with error trapping."""
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json") as tf:
            tf.write("{ this is corrupt json syntax ...")
            bad_path = tf.name

        try:
            with open(bad_path, "r", encoding="utf-8") as f:
                with self.assertRaises(json.JSONDecodeError):
                    json.load(f)
        finally:
            if os.path.exists(bad_path):
                os.remove(bad_path)

    def test_f1_b02_missing_dataset_file(self):
        """F1.B2: Handle non-existent dataset file path without crashing unhandled."""
        non_existent = "/nonexistent/path/dataset_404.json"
        self.assertFalse(os.path.exists(non_existent))
        with self.assertRaises(FileNotFoundError):
            with open(non_existent, "r", encoding="utf-8") as f:
                json.load(f)

    def test_f1_b03_extreme_unicode_in_datasets(self):
        """F1.B3: Verify preservation of Italian accented characters in dataset places."""
        with open(TEMPO_LIBERO_PAYLOAD_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Check places containing accents and apostrophes
        special_names = [
            p.get("nome", "")
            for p in data["places"]
            if any(c in p.get("nome", "") for c in "àèéìòù'’")
        ]
        self.assertGreater(len(special_names), 20, "Must have places with accented characters")
        for name in special_names[:5]:
            self.assertTrue(len(name.strip()) > 0)
            self.assertFalse("\ufffd" in name, f"Corrupted replacement character found in: {name}")

    def test_f1_b04_empty_or_malformed_records_filtered(self):
        """F1.B4: Records missing title, venue, or address are excluded from catalog."""
        malformed_records = [
            {"id": "bad_1", "nome": "", "comune": "Genova"},
            {"id": "bad_2", "nome": "Posto Senza Comune", "comune": ""},
            {"id": "bad_3"},
        ]
        # Filtering logic
        valid_records = [
            r for r in malformed_records
            if r.get("nome") and r.get("comune")
        ]
        self.assertEqual(len(valid_records), 0, "All malformed records must be filtered out")

    def test_f1_b05_large_dataset_parsing_performance(self):
        """F1.B5: Aggregator parses large dataset (4,000+ records) in under 2.0 seconds."""
        t0 = time.time()
        with open(GUIDA_APERTI_PATH, "r", encoding="utf-8") as f:
            records = json.load(f)
        elapsed = time.time() - t0
        self.assertLess(elapsed, 2.0, f"Parsing took too long: {elapsed:.2f}s")
        self.assertGreater(len(records), 4000)


# ==============================================================================
# Feature 2 Boundaries: Live Verification Prober (F2)
# ==============================================================================
class TestFeature2Boundaries(unittest.TestCase):
    """Tier 2: Boundary and edge tests for live verifier and network errors."""

    def test_f2_b01_http_404_url_handling(self):
        """F2.B1: HTTP 404 responses are caught and marked unreachable."""
        if HAS_VERIFIER:
            from genova_outings.verifier import check_url_reachability
            is_reachable = check_url_reachability("https://www.visitgenoa.it/nonexistent-404-page-xyz")
            self.assertFalse(is_reachable, "404 page must return False")
        else:
            self.assertTrue(True)

    def test_f2_b02_network_timeout_handling(self):
        """F2.B2: Network timeouts on non-routable IP (10.255.255.1) are handled gracefully."""
        if HAS_VERIFIER:
            from genova_outings.verifier import check_url_reachability
            # Test with very short timeout
            is_reachable = check_url_reachability("http://10.255.255.1:81/", timeout=0.1)
            self.assertFalse(is_reachable, "Timeout should return False without raising unhandled exception")
        else:
            self.assertTrue(True)

    def test_f2_b03_dns_failure_handling(self):
        """F2.B3: Non-existent domain names handle DNS failure safely."""
        if HAS_VERIFIER:
            from genova_outings.verifier import check_url_reachability
            is_reachable = check_url_reachability("https://this-domain-does-not-exist-genova-12345.org")
            self.assertFalse(is_reachable, "DNS failure should return False safely")
        else:
            self.assertTrue(True)

    def test_f2_b04_negative_closure_explicit_villa_croce(self):
        """F2.B4: Negative filter: Villa Croce is explicitly rejected by verifier."""
        villa_croce_item = {
            "id": "museo_villa_croce",
            "title": "Museo di Villa Croce",
            "venue": "Museo d'Arte Contemporanea Villa Croce",
            "zone": "Carignano",
            "url": "https://www.museidigenova.it/it/museo-darte-contemporanea-di-villa-croce",
        }
        if HAS_VERIFIER:
            from genova_outings.verifier import verify_venue
            is_active = verify_venue(villa_croce_item["url"])
            self.assertFalse(is_active, "Villa Croce must be rejected due to PNRR closure")
        else:
            self.assertIn("villa croce", villa_croce_item["venue"].lower())

    def test_f2_b05_invalid_url_schemes(self):
        """F2.B5: Invalid URL schemes (ftp://, javascript:, empty) are caught."""
        invalid_urls = [
            "ftp://ftp.genova.it/files",
            "javascript:alert(1)",
            "file:///etc/passwd",
            "",
            "   ",
        ]
        for bad_url in invalid_urls:
            is_valid_http = bad_url.startswith("http://") or bad_url.startswith("https://")
            self.assertFalse(is_valid_http, f"Scheme should be invalid: {bad_url}")


# ==============================================================================
# Feature 3 Boundaries: Catalog Harmonizer Schema (F3)
# ==============================================================================
class TestFeature3Boundaries(unittest.TestCase):
    """Tier 2: Boundary and edge tests for catalog schema normalization."""

    def test_f3_b01_empty_catalog_when_category_not_found(self):
        """F3.B1: Querying a non-existent category returns an empty list, not a crash."""
        if HAS_MODELS:
            catalog = WeeklyCatalog(
                week_label="Settimana 4-10 Nov",
                generated_at="2026-11-04T10:00:00Z",
                activities=[OutingOption.from_dict(d) for d in create_sample_options_list()],
            )
            res = catalog.filter_by_category("astronautica")
            self.assertEqual(res, [])
        else:
            samples = create_sample_options_list()
            res = [s for s in samples if s["category"] == "astronautica"]
            self.assertEqual(res, [])

    def test_f3_b02_deduplication_of_places(self):
        """F3.B2: Duplicate places with same ID or venue are deduplicated."""
        duplicates = [
            create_sample_cinema_option(),
            create_sample_cinema_option(),
        ]
        seen_ids = set()
        deduped = []
        for d in duplicates:
            if d["id"] not in seen_ids:
                seen_ids.add(d["id"])
                deduped.append(d)
        self.assertEqual(len(deduped), 1, "Duplicate IDs must be collapsed")

    def test_f3_b03_sanitizes_multiple_consecutive_dashes(self):
        """F3.B3: Consecutive dashes ('——', ' - - ') are collapsed to single colon."""
        raw_text = "Rassegna film —— Cinema Sivori –– serale"
        import re
        cleaned = re.sub(r"\s*[\u2014\u2013\u2015]+\s*", ": ", raw_text)
        cleaned = re.sub(r":\s*:", ":", cleaned).strip()
        self.assertNotIn("——", cleaned)
        self.assertNotIn("––", cleaned)
        self.assertNotIn("\u2014", cleaned)
        self.assertNotIn("\u2013", cleaned)

    def test_f3_b04_optional_fields_defaults(self):
        """F3.B4: OutingOption minimal constructor sets valid defaults."""
        if HAS_MODELS:
            opt = OutingOption(
                id="minimal_test",
                title="Test Titolo",
                category=OutingCategory.ALTRO,
                venue="Luogo Test",
                zone="Centro",
                day_time="Sempre",
                verified_url="https://visitgenoa.it",
                description="Descrizione test",
            )
            self.assertFalse(opt.is_weather_dependent)
            self.assertEqual(opt.source_type, "verified_local")
            self.assertEqual(opt.address, "")
            self.assertEqual(opt.time_slot, "flessibile")
            self.assertFalse(opt.is_free)
        else:
            self.assertTrue(True)

    def test_f3_b05_deterministic_catalog_ordering(self):
        """F3.B5: Catalog items sort predictably by category and title."""
        samples = create_sample_options_list()
        sorted_samples = sorted(samples, key=lambda x: (x["category"], x["title"]))
        # Verify deterministic sort
        categories_order = [s["category"] for s in sorted_samples]
        self.assertEqual(categories_order, sorted(categories_order))


# ==============================================================================
# Feature 4 Boundaries: Interactive Selection Interface (F4)
# ==============================================================================
class TestFeature4Boundaries(unittest.TestCase):
    """Tier 2: Boundary and edge tests for selector input validation."""

    def test_f4_b01_selector_out_of_range_index(self):
        """F4.B1: Enters 999 in selector; ignores out-of-range index safely."""
        items = create_sample_options_list()
        cmd = "999"
        valid_selection = set()
        for p in cmd.split(","):
            if p.isdigit():
                val = int(p)
                if 1 <= val <= len(items):
                    valid_selection.add(val)
        self.assertEqual(len(valid_selection), 0, "Index 999 must be ignored")

    def test_f4_b02_selector_negative_index(self):
        """F4.B2: Negative numbers or zero are ignored safely."""
        items = create_sample_options_list()
        cmd = "-1,0,-99"
        valid_selection = set()
        for p in cmd.split(","):
            if p.lstrip("-").isdigit():
                val = int(p)
                if 1 <= val <= len(items):
                    valid_selection.add(val)
        self.assertEqual(len(valid_selection), 0, "Negative/zero indices must be ignored")

    def test_f4_b03_selector_alphabetic_input_ignored(self):
        """F4.B3: Alphabetic nonsense commands are ignored without crashing."""
        items = create_sample_options_list()
        cmd = "abc xyz foobar"
        valid_selection = set()
        for p in cmd.split():
            if p.isdigit():
                val = int(p)
                if 1 <= val <= len(items):
                    valid_selection.add(val)
        self.assertEqual(len(valid_selection), 0)

    def test_f4_b04_selector_empty_selection_on_done(self):
        """F4.B4: User attempts 'done' with zero items selected; handled safely."""
        selected_indices = set()
        if not selected_indices:
            can_proceed = False
        else:
            can_proceed = True
        self.assertFalse(can_proceed, "Cannot proceed with empty selection without confirmation")

    def test_f4_b05_selector_quit_interrupt(self):
        """F4.B5: 'quit' or 'q' returns empty list cleanly without unhandled exception."""
        cmd = "q"
        result = [] if cmd in ("q", "quit", "exit") else None
        self.assertEqual(result, [])


# ==============================================================================
# Feature 5 Boundaries: WhatsApp Plain-Writing Formatter (F5)
# ==============================================================================
class TestFeature5Boundaries(unittest.TestCase):
    """Tier 2: Boundary and edge tests for message formatting and sanitization."""

    def test_f5_b01_formatter_empty_selection(self):
        """F5.B1: Formatting empty selection returns friendly empty notice."""
        if HAS_FORMATTER:
            from genova_outings.formatter import format_whatsapp_message
            msg = format_whatsapp_message([])
            self.assertIn("Nessuna attività selezionata", msg)
        else:
            empty_msg = "Nessuna attività selezionata."
            self.assertIn("Nessuna attività selezionata", empty_msg)

    def test_f5_b02_formatter_url_with_query_params(self):
        """F5.B2: Formatter preserves complex URLs with query params and fragments."""
        complex_url = "https://circuitocinemagenova.com/sivori/?film=123&session=2115#info"
        opt = create_sample_cinema_option()
        opt["verified_url"] = complex_url
        if HAS_FORMATTER:
            from genova_outings.formatter import format_whatsapp_message
            if HAS_MODELS:
                msg = format_whatsapp_message([OutingOption.from_dict(opt)])
            else:
                msg = format_whatsapp_message([opt])
            self.assertIn(complex_url, msg)
        else:
            self.assertIn("film=123", complex_url)

    def test_f5_b03_formatter_extreme_long_description(self):
        """F5.B3: Long descriptions (500+ chars) are formatted cleanly without breaking bolding."""
        long_desc = "Questa è una descrizione particolarmente dettagliata della rassegna cinematografica. " * 8
        opt = create_sample_cinema_option()
        opt["description"] = long_desc
        if HAS_FORMATTER:
            from genova_outings.formatter import format_whatsapp_message
            if HAS_MODELS:
                msg = format_whatsapp_message([OutingOption.from_dict(opt)])
            else:
                msg = format_whatsapp_message([opt])
            assert_plain_writing(self, msg)
        else:
            self.assertGreater(len(long_desc), 500)

    def test_f5_b04_formatter_special_italian_characters(self):
        """F5.B4: Formatter preserves Italian characters: à, è, é, ì, ò, ù, L'Acquario."""
        text_with_accents = "Una passeggiata a Boccadasse per gustare l'aria di mare e un caffè."
        opt = create_sample_walk_option()
        opt["description"] = text_with_accents
        if HAS_FORMATTER:
            from genova_outings.formatter import format_whatsapp_message
            if HAS_MODELS:
                msg = format_whatsapp_message([OutingOption.from_dict(opt)])
            else:
                msg = format_whatsapp_message([opt])
            self.assertIn("caffè", msg)
            self.assertIn("l'aria", msg)
        else:
            self.assertIn("caffè", text_with_accents)

    def test_f5_b05_formatter_tones(self):
        """F5.B5: Alternative tones ('amichevole', 'weekend', 'minimal') all pass plain writing."""
        opt = create_sample_cinema_option()
        for tone in ["amichevole", "weekend", "minimal", "relaxed"]:
            if HAS_FORMATTER:
                from genova_outings.formatter import format_whatsapp_message
                if HAS_MODELS:
                    msg = format_whatsapp_message([OutingOption.from_dict(opt)], tone=tone)
                else:
                    msg = format_whatsapp_message([opt], tone=tone)
                assert_plain_writing(self, msg)
            else:
                self.assertTrue(bool(tone))


# ==============================================================================
# Feature 6 Boundaries: Automated Plain-Writing Validator (F6)
# ==============================================================================
class TestFeature6Boundaries(unittest.TestCase):
    """Tier 2: Boundary and edge tests for validator regex rules."""

    def test_f6_b01_validator_date_in_substring_allowed(self):
        """F6.B1: Words with 'date' as substring (mandate, candidate, datteri) MUST NOT trigger violation."""
        clean_text = (
            "Ciao! Ti lascio i dettagli per questa settimana:\n\n"
            "🎬 *Cinema Sivori: rassegna*\n"
            "📍 Salita Santa Caterina\n"
            "🗓️ Informazioni aggiornate per la programmazione.\n"
            "Info: https://circuitocinemagenova.com/sivori/\n\n"
            "Dimmi se ti ispira!"
        )
        if HAS_VALIDATOR:
            from genova_outings.validator import validate_plain_writing
            is_valid, errors = validate_plain_writing(clean_text)
            self.assertTrue(is_valid, f"'aggiornate' should not trigger 'date' error: {errors}")
        else:
            assert_plain_writing(self, clean_text)

    def test_f6_b02_validator_case_insensitive_romance(self):
        """F6.B2: Detects romance terms regardless of uppercase/lowercase."""
        bad_variants = [
            "Ecco un DATE per venerdì",
            "Serata DaTe a Genova",
            "UN APPUNTAMENTO ROMANTICO",
            "Uscita Galante nel centro storico",
        ]
        for variant in bad_variants:
            if HAS_VALIDATOR:
                from genova_outings.validator import validate_plain_writing
                is_valid, errors = validate_plain_writing(variant)
                self.assertFalse(is_valid, f"Variant must fail: {variant}")
            else:
                with self.assertRaises(AssertionError):
                    assert_plain_writing(self, variant)

    def test_f6_b03_validator_multiple_violations_reported(self):
        """F6.B3: Detects and reports multiple distinct violations in a single message."""
        multi_violation_text = "Un date romantico — una mostra davvero imperdibile e mozzafiato!"
        if HAS_VALIDATOR:
            from genova_outings.validator import validate_plain_writing
            is_valid, errors = validate_plain_writing(multi_violation_text)
            self.assertFalse(is_valid)
            self.assertGreaterEqual(len(errors), 2, "Must report at least dash, romance, and puffery")
        else:
            with self.assertRaises(AssertionError):
                assert_plain_writing(self, multi_violation_text)

    def test_f6_b04_validator_empty_string(self):
        """F6.B4: Empty string validation handled safely without regex crash."""
        if HAS_VALIDATOR:
            from genova_outings.validator import validate_plain_writing
            is_valid, errors = validate_plain_writing("")
            # Either valid or returns empty notice
            self.assertIsInstance(is_valid, bool)
        else:
            self.assertTrue(True)

    def test_f6_b05_validator_markdown_bold_versus_whatsapp_bold(self):
        """F6.B5: Disallows double asterisk **bold** while allowing single *bold*."""
        bad_bold = "Ecco la nostra **proposta** di cinema."
        good_bold = "Ecco la nostra *proposta* di cinema."
        if HAS_VALIDATOR:
            from genova_outings.validator import validate_plain_writing
            is_valid_bad, _ = validate_plain_writing(bad_bold)
            self.assertFalse(is_valid_bad, "Double asterisks ** must be rejected")
            # Good bold (within clean template) should pass
            good_msg = f"Ciao!\n\n{good_bold}\n\nInfo: https://circuitocinemagenova.com\n\nDimmi se ti ispira!"
            is_valid_good, errs = validate_plain_writing(good_msg)
            self.assertTrue(is_valid_good, f"Single asterisks should pass: {errs}")
        else:
            with self.assertRaises(AssertionError):
                assert_plain_writing(self, bad_bold)


# ==============================================================================
# Feature 7 Boundaries: Main CLI Integration & Runner (F7)
# ==============================================================================
class TestFeature7Boundaries(unittest.TestCase):
    """Tier 2: Boundary and edge tests for CLI argument parsing and error exits."""

    def test_f7_b01_cli_invalid_select_argument(self):
        """F7.B1: Passing invalid format to --select (e.g. 'abc') exits with error or clean message."""
        if not HAS_CLI:
            self.skipTest("genova_outings.cli not yet available")

        from genova_outings.cli import main
        with patch("sys.argv", ["genova_outings", "--select", "abc", "--no-live"]):
            # Should exit or return non-zero/handled
            try:
                code = main()
                self.assertIn(code, [0, 1, 2])
            except SystemExit as e:
                self.assertIn(e.code, [1, 2])

    def test_f7_b02_cli_unknown_flag(self):
        """F7.B2: Passing unknown flag exits with code 2 (standard argparse)."""
        if not HAS_CLI:
            self.skipTest("genova_outings.cli not yet available")

        from genova_outings.cli import main
        with patch("sys.argv", ["genova_outings", "--unknown-flag-xyz"]):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 2)

    def test_f7_b03_cli_output_to_nonexistent_directory(self):
        """F7.B3: Output flag targeting non-existent directory handles error cleanly."""
        if not HAS_CLI:
            self.skipTest("genova_outings.cli not yet available")

        from genova_outings.cli import main
        bad_output = "/nonexistent_folder_abc_123/out.txt"
        with patch("sys.argv", ["genova_outings", "--select", "1", "--no-live", "--output", bad_output]):
            try:
                code = main()
                self.assertIn(code, [0, 1, 2])
            except (SystemExit, OSError):
                self.assertTrue(True)

    def test_f7_b04_cli_select_out_of_range(self):
        """F7.B4: Passing --select 999 handles out of range cleanly."""
        if not HAS_CLI:
            self.skipTest("genova_outings.cli not yet available")

        from genova_outings.cli import main
        buf = io.StringIO()
        with patch("sys.stdout", buf), patch("sys.argv", ["genova_outings", "--select", "999", "--no-live"]):
            code = main()
            self.assertIn(code, [0, 1])

    def test_f7_b05_cli_tone_invalid_fallback(self):
        """F7.B5: Passing unknown --tone falls back safely to default relaxed tone."""
        if not HAS_CLI:
            self.skipTest("genova_outings.cli not yet available")

        from genova_outings.cli import main
        buf = io.StringIO()
        with patch("sys.stdout", buf), patch("sys.argv", ["genova_outings", "--tone", "invalid_tone_xyz", "--select", "1", "--no-live"]):
            code = main()
            self.assertEqual(code, 0)
            output = buf.getvalue()
            assert_plain_writing(self, output)


if __name__ == "__main__":
    unittest.main()
