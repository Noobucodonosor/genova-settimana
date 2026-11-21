"""Unit tests for genova_outings/catalog.py.

Verifies:
1. get_weekly_catalog returns genuine, non-empty, verified OutingOption items.
2. Complete data hygiene: zero em-dashes (\u2014) or en-dashes (\u2013) across all fields.
3. Strict negative check: Villa Croce is completely absent from the catalog.
4. Category filtering behaves accurately.
5. Richness of options across categories (cinema, mostra, passeggiata, biblioteca, musica, ritrovo).
6. Absence of placeholders, dummy strings, or hallucinations.
"""

import unittest
from pathlib import Path

from genova_outings.models import OutingCategory, OutingOption
from genova_outings.catalog import (
    AUTHORITATIVE_LIVE_OUTINGS,
    get_weekly_catalog,
    load_catalog_items,
    load_authoritative_live_options,
    load_local_tempo_libero,
    load_local_guida_aperti,
)


class TestCatalogExtraction(unittest.TestCase):
    """Test weekly catalog extraction, aggregation, and negative filtering."""

    @classmethod
    def setUpClass(cls):
        # Retrieve weekly catalog without live network blocking during CI
        cls.catalog = get_weekly_catalog(live_verify=False)

    def test_catalog_is_non_empty(self):
        self.assertGreater(len(self.catalog), 15, "Catalog should have at least 15 verified weekly options")

    def test_all_items_have_required_fields(self):
        for opt in self.catalog:
            self.assertIsInstance(opt, OutingOption)
            self.assertTrue(opt.id, "OutingOption must have an id")
            self.assertTrue(opt.title, f"Option {opt.id} must have a title")
            self.assertIsInstance(opt.category, OutingCategory)
            self.assertTrue(opt.venue, f"Option {opt.id} must have a venue")
            self.assertTrue(opt.zone, f"Option {opt.id} must have a zone")
            self.assertTrue(opt.day_time, f"Option {opt.id} must have day_time")
            self.assertTrue(opt.verified_url, f"Option {opt.id} must have verified_url")
            self.assertTrue(
                opt.verified_url.startswith("http://") or opt.verified_url.startswith("https://"),
                f"Option {opt.id} verified_url must start with http/https: {opt.verified_url}"
            )
            self.assertTrue(opt.description, f"Option {opt.id} must have a description")

    def test_data_hygiene_zero_long_dashes(self):
        """Plain-writing compliance: zero em-dashes (\u2014) or en-dashes (\u2013) across all fields including address."""
        for opt in self.catalog:
            for field_name, value in [
                ("title", opt.title),
                ("description", opt.description),
                ("day_time", opt.day_time),
                ("venue", opt.venue),
                ("address", opt.address),
            ]:
                self.assertNotIn("—", value, f"Em-dash found in {field_name} of {opt.id}: {value}")
                self.assertNotIn("–", value, f"En-dash found in {field_name} of {opt.id}: {value}")

    def test_strict_negative_check_villa_croce_excluded(self):
        """MANDATORY REQUIREMENT: Villa Croce is closed for PNRR works and MUST be excluded."""
        for opt in self.catalog:
            combined = f"{opt.venue} {opt.title} {opt.description} {opt.verified_url}".lower()
            self.assertNotIn(
                "villa croce",
                combined,
                f"Villa Croce must NOT appear in the weekly catalog! Found in: {opt.id} ({opt.venue})"
            )
            self.assertNotIn(
                "villa-croce",
                combined,
                f"Villa Croce URL slug must NOT appear in catalog! Found in: {opt.id} ({opt.verified_url})"
            )

    def test_permanently_closed_and_seasonal_venues_excluded(self):
        """Verify permanently closed Teatro Cantero and seasonal summer arenas are absent."""
        for opt in self.catalog:
            combined = f"{opt.venue} {opt.title} {opt.description} {opt.verified_url}".lower()
            self.assertNotIn("cantero", combined, f"Cantero must not appear in catalog: {opt.id}")
            self.assertNotIn("circuito sul mare", combined, f"Circuito sul mare must not appear in November: {opt.id}")

    def test_multi_exhibitions_at_same_venue_retained(self):
        """Verify distinct exhibitions at Palazzo Ducale are both retained in the catalog."""
        ducale_mostre = [o for o in self.catalog if o.category == OutingCategory.MOSTRA and "ducale" in o.venue.lower()]
        titles = [o.title for o in ducale_mostre]
        self.assertTrue(
            any("impressionisti" in t.lower() for t in titles),
            f"Impressionisti exhibition missing from Palazzo Ducale in {titles}"
        )
        self.assertTrue(
            any("world press photo" in t.lower() for t in titles),
            f"World Press Photo exhibition missing from Palazzo Ducale in {titles}"
        )

    def test_category_filtering(self):
        cinemas = get_weekly_catalog(live_verify=False, category="cinema")
        self.assertGreater(len(cinemas), 0)
        for c in cinemas:
            self.assertEqual(c.category, OutingCategory.CINEMA)

        # Test category synonyms
        cinemas_film = get_weekly_catalog(live_verify=False, category="film")
        self.assertEqual(len(cinemas), len(cinemas_film))

        cinemas_essai = get_weekly_catalog(live_verify=False, category="cinema d'essai")
        self.assertEqual(len(cinemas), len(cinemas_essai))

        mostre = get_weekly_catalog(live_verify=False, category=OutingCategory.MOSTRA)
        self.assertGreater(len(mostre), 0)
        for m in mostre:
            self.assertEqual(m.category, OutingCategory.MOSTRA)

        walks = get_weekly_catalog(live_verify=False, category="passeggiata")
        self.assertGreater(len(walks), 0)
        for w in walks:
            self.assertEqual(w.category, OutingCategory.PASSEGGIATA)

    def test_representation_across_all_categories(self):
        """Ensure rich informal alternatives across all core categories."""
        present_categories = {opt.category for opt in self.catalog}
        self.assertIn(OutingCategory.CINEMA, present_categories)
        self.assertIn(OutingCategory.MOSTRA, present_categories)
        self.assertIn(OutingCategory.PASSEGGIATA, present_categories)
        self.assertIn(OutingCategory.BIBLIOTECA, present_categories)
        self.assertIn(OutingCategory.MUSICA, present_categories)
        self.assertIn(OutingCategory.RITROVO, present_categories)

    def test_source_diversity(self):
        """Ensure catalog combines both live web endpoints and local datasets."""
        sources = {opt.source_type for opt in self.catalog}
        self.assertIn("live_web", sources)
        self.assertIn("verified_local", sources)

    def test_no_placeholders_or_dummy_data(self):
        """Ensure zero placeholder strings in the catalog."""
        import re
        patterns = [
            re.compile(r"\blorem ipsum\b", re.IGNORECASE),
            re.compile(r"\btodo\b", re.IGNORECASE),
            re.compile(r"\bplaceholder\b", re.IGNORECASE),
            re.compile(r"\btest venue\b", re.IGNORECASE),
            re.compile(r"\bsample title\b", re.IGNORECASE),
        ]
        for opt in self.catalog:
            combined = f"{opt.title} {opt.description}"
            for pat in patterns:
                self.assertFalse(
                    bool(pat.search(combined)),
                    f"Placeholder pattern '{pat.pattern}' detected in option {opt.id}: {combined}"
                )

    def test_authoritative_live_options_count(self):
        live_opts = load_authoritative_live_options()
        self.assertGreaterEqual(len(live_opts), 18)
        # Check that Cinema Sivori, Palazzo Ducale, and Count Basie are among live options
        venues = [o.venue for o in live_opts]
        self.assertIn("Cinema Sivori", venues)
        self.assertIn("Palazzo Ducale", venues)
        self.assertIn("Count Basie Jazz Club", venues)


if __name__ == "__main__":
    unittest.main()
