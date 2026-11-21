"""Adversarial stress-testing suite for Milestone 1: Core Catalog & Live Verification Engine.

Empirical verification of:
1. Negative closure stress: Villa Croce variations, obfuscation, closure phrases.
2. Dash & character sanitization stress: multi-dashes, various unicode dashes, URL punctuation.
3. Network & timeout resilience: 404, 500, NXDOMAIN, SSL, timeouts, malformed URLs.
4. Category filtering & boundary cases: None, empty strings, case mismatches, synonyms, bad types.
5. Concurrency stress: rapid parallel calls, thread safety of probe cache.
6. Logic flaws: civic museum weekday closures, coarse deduplication drops.
"""

import concurrent.futures
import threading
import unittest
from unittest.mock import patch
import urllib.error

from genova_outings.models import OutingCategory, OutingOption, WeeklyCatalog
from genova_outings.verifier import (
    clean_url,
    is_blacklisted_venue,
    is_civic_museum_closed_on_day,
    probe_url_reachability,
    probe_urls_batch,
    sanitize_text,
    verify_outing,
    _PROBE_CACHE,
)
from genova_outings.catalog import (
    get_weekly_catalog,
    load_catalog_items,
    load_authoritative_live_options,
)


class TestAdversarialNegativeClosure(unittest.TestCase):
    """Stress-test negative closure filtering against evasive variations."""

    def test_villa_croce_standard_variations_blocked(self):
        variations = [
            "Villa Croce",
            "villa croce",
            "VILLA CROCE",
            "vIlLa CrOcE",
            "Museo d'Arte Contemporanea Villa Croce",
            "Museo d'Arte Contemporanea di Villa Croce",
            "biblioteca villa croce",
            "via villa croce",
            "Parco di Villa Croce",
            "Villa Croce.",
            "Villa Croce, Genova",
            "(Villa Croce)",
            "[Villa Croce]",
        ]
        for name in variations:
            with self.subTest(name=name):
                self.assertTrue(
                    is_blacklisted_venue(name),
                    f"Failed to blacklist standard Villa Croce variation: {name!r}"
                )

    def test_villa_croce_obfuscation_bypasses(self):
        """VERIFY REMEDIATION:
        These variations must all be strictly blocked by the hardened is_blacklisted_venue regex.
        """
        bypasses = [
            ("Villa   Croce", "double/multiple spaces"),
            ("Villa\tCroce", "tab whitespace"),
            ("Villa\nCroce", "newline whitespace"),
            ("Villa - Croce", "dash with spaces"),
            ("Villa- Croce", "dash-space"),
            ("Villa -Croce", "space-dash"),
            ("Villa_Croce", "underscore"),
            ("villacroce", "concatenation"),
            ("Villa.Croce", "dot separator"),
            ("Villa/Croce", "slash separator"),
        ]
        for name, reason in bypasses:
            with self.subTest(name=name, reason=reason):
                self.assertTrue(
                    is_blacklisted_venue(name),
                    f"Expected {name!r} to be blocked ({reason})"
                )

    def test_villa_croce_url_slug_bypasses(self):
        """VERIFY REMEDIATION: URL slugs with underscores or URL encoding are blocked."""
        url_bypasses = [
            "https://genova.it/evento-villa_croce",
            "https://genova.it/evento/villa%20croce",
            "https://genova.it/evento?loc=villa+croce",
        ]
        for url in url_bypasses:
            with self.subTest(url=url):
                self.assertTrue(
                    is_blacklisted_venue("Mostra d'Arte", url=url),
                    f"URL {url!r} must be strictly blocked"
                )

    def test_verify_outing_admits_bypassed_villa_croce(self):
        """VERIFY REMEDIATION: verify_outing rejects Villa Croce option when obfuscated."""
        bypassed_opt = OutingOption(
            id="closed_croce_bypass",
            title="Mostra Contemporanea",
            category=OutingCategory.MOSTRA,
            venue="Villa - Croce",
            zone="Carignano",
            day_time="Sabato ore 16:00",
            verified_url="https://palazzoducale.genova.it/",
            description="Mostra a Villa_Croce.",
        )
        res = verify_outing(bypassed_opt, check_network=False)
        self.assertFalse(
            res.is_valid,
            "verify_outing must reject obfuscated Villa Croce"
        )


class TestAdversarialDashAndSanitization(unittest.TestCase):
    """Stress-test dash replacement and plain-writing text cleaning."""

    def test_unicode_dashes(self):
        text = "Palazzo Ducale \u2014 Mostra \u2013 Orari \u2015 Serale"
        cleaned = sanitize_text(text)
        self.assertNotIn("\u2014", cleaned)
        self.assertNotIn("\u2013", cleaned)
        self.assertNotIn("\u2015", cleaned)

    def test_triple_dash_leaves_double_colon(self):
        """VERIFY REMEDIATION: 3 or more dashes collapse cleanly into single colon with no '::'."""
        text = "Palazzo Ducale ——— Mostra Fotografica"
        cleaned = sanitize_text(text)
        self.assertNotIn("::", cleaned, "Triple dash must not produce double colon '::'")
        self.assertIn("Palazzo Ducale: Mostra Fotografica", cleaned)

    def test_leading_trailing_dashes_leave_colons(self):
        """VERIFY REMEDIATION: Leading/trailing dashes are stripped without leaving dangling colons."""
        text = "— Grande Mostra —"
        cleaned = sanitize_text(text)
        self.assertFalse(cleaned.startswith(":"), f"Unexpected leading colon in {cleaned!r}")
        self.assertFalse(cleaned.endswith(":"), f"Unexpected trailing colon in {cleaned!r}")
        self.assertEqual(cleaned, "Grande Mostra")

    def test_unsupported_unicode_dashes_slip_through(self):
        """VERIFY REMEDIATION: Figure dash (\u2012) and small em dash (\ufe58) are stripped."""
        text = "Palazzo Ducale \u2012 Mostra"
        cleaned = sanitize_text(text)
        self.assertNotIn("\u2012", cleaned, "Figure dash must be stripped by sanitize_text")
        self.assertIn("Palazzo Ducale: Mostra", cleaned)

    def test_imperative_date_mangling(self):
        """Plain writing prioritizes removing date terms."""
        text = "Date una mano ai volontari"
        cleaned = sanitize_text(text)
        self.assertTrue(cleaned.lower().startswith("giorni"))

    def test_clean_url_quoted_url_rejection(self):
        """VERIFY REMEDIATION: clean_url strips quotation marks and validates cleanly."""
        quoted_url = '"https://circuitocinemagenova.com/sivori/"'
        cleaned = clean_url(quoted_url)
        self.assertEqual(cleaned, "https://circuitocinemagenova.com/sivori/")
        opt = OutingOption("id", "Title", OutingCategory.CINEMA, "Cinema Sivori", "Centro", "Mercoledì ore 21:00", quoted_url, "Desc")
        vres = verify_outing(opt, check_network=False)
        self.assertTrue(vres.is_valid)

    def test_clean_url_non_string_crash(self):
        """VERIFY REMEDIATION: clean_url does not crash on non-string inputs."""
        self.assertEqual(clean_url(12345), "")
        self.assertEqual(clean_url(None), "")


class TestAdversarialNetworkResilience(unittest.TestCase):
    """Stress-test behavior under simulated and real network failures."""

    def test_dns_nxdomain(self):
        bad_url = "https://this-domain-definitely-does-not-exist-xyz987654321.genova.it"
        reachable, code, msg = probe_url_reachability(bad_url, timeout=1.5, use_cache=False)
        self.assertFalse(reachable)
        self.assertEqual(code, 0)

    def test_connection_refused(self):
        bad_url = "http://127.0.0.1:54321"
        reachable, code, msg = probe_url_reachability(bad_url, timeout=1.0, use_cache=False)
        self.assertFalse(reachable)
        self.assertEqual(code, 0)

    @patch("urllib.request.urlopen")
    def test_http_404_handled_gracefully(self, mock_urlopen):
        import io
        err = urllib.error.HTTPError(
            url="https://example.com/missing", code=404, msg="Not Found", hdrs={}, fp=io.BytesIO(b"")
        )
        mock_urlopen.side_effect = err
        reachable, code, msg = probe_url_reachability("https://example.com/missing", use_cache=False)
        err.close()
        self.assertFalse(reachable)
        self.assertEqual(code, 404)

    @patch("urllib.request.urlopen")
    def test_http_500_handled_gracefully(self, mock_urlopen):
        import io
        err = urllib.error.HTTPError(
            url="https://example.com/error", code=500, msg="Server Error", hdrs={}, fp=io.BytesIO(b"")
        )
        mock_urlopen.side_effect = err
        reachable, code, msg = probe_url_reachability("https://example.com/error", use_cache=False)
        err.close()
        self.assertFalse(reachable)
        self.assertEqual(code, 500)


class TestAdversarialCategoryFilteringAndSynonyms(unittest.TestCase):
    """Stress-test category filtering with edge cases, invalid inputs, and synonyms."""

    def test_synonym_filtering_defect(self):
        """VERIFY REMEDIATION: get_weekly_catalog resolves supported synonyms like 'film'."""
        cat_cinema = get_weekly_catalog(live_verify=False, category="cinema")
        cat_film = get_weekly_catalog(live_verify=False, category="film")
        self.assertGreater(len(cat_cinema), 0)
        self.assertGreater(len(cat_film), 0)
        self.assertEqual(len(cat_cinema), len(cat_film))

    def test_weekly_catalog_none_category_inconsistency(self):
        """VERIFY REMEDIATION: WeeklyCatalog.filter_by_category(None) returns all activities."""
        options = [
            OutingOption("1", "Film", OutingCategory.CINEMA, "V", "Z", "D", "https://a.com", "Desc"),
        ]
        wc = WeeklyCatalog(week_label="W1", generated_at="2026-11-04", activities=options)
        res_none = wc.filter_by_category(None)
        self.assertEqual(len(res_none), 1)


class TestAdversarialCivicMuseumLogicFlaw(unittest.TestCase):
    """Verify is_civic_museum_closed_on_day correctly distinguishes Monday closures."""

    def test_museum_closed_on_weekends_defect(self):
        # Civic museums in Genoa are ONLY closed on Mondays.
        self.assertTrue(is_civic_museum_closed_on_day("Musei di Strada Nuova", 0))
        self.assertTrue(is_civic_museum_closed_on_day("Musei di Strada Nuova", "lunedi"))
        for day in [1, 2, 3, 4, 5, 6]:  # Tuesday through Sunday: OPEN
            closed = is_civic_museum_closed_on_day("Musei di Strada Nuova", day)
            self.assertFalse(
                closed,
                f"Musei di Strada Nuova must be OPEN on day {day}"
            )


class TestAdversarialDeduplicationCollision(unittest.TestCase):
    """Verify refined deduplication key retains concurrent exhibitions at same venue."""

    def test_world_press_photo_dropped_by_dedup(self):
        live_options = load_authoritative_live_options()
        live_ids = [o.id for o in live_options]
        self.assertIn("ducale_mostra_impressionisti", live_ids)
        self.assertIn("ducale_world_press_photo", live_ids)

        cat_options = load_catalog_items()
        cat_ids = [o.id for o in cat_options]
        self.assertIn("ducale_mostra_impressionisti", cat_ids)
        self.assertIn(
            "ducale_world_press_photo",
            cat_ids,
            "World Press Photo 2026 must be retained alongside Impressionisti"
        )


class TestAdversarialConcurrency(unittest.TestCase):
    """Stress-test concurrent calls to probe_urls_batch and cache thread safety."""

    def test_batch_probe_rapid_concurrent_calls(self):
        test_urls = [
            "https://palazzoducale.genova.it/mostre/",
            "https://circuitocinemagenova.com/sivori/",
            "https://www.cineclubnickelodeon.it/",
            "https://www.portoantico.it/",
            "https://palazzoducale.genova.it/mostre/",
            "https://circuitocinemagenova.com/sivori/",
        ]

        def worker(thread_id):
            return probe_urls_batch(test_urls, max_workers=8, timeout=3.0)

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            futures = [pool.submit(worker, i) for i in range(16)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        self.assertEqual(len(results), 16)
        for res in results:
            self.assertIn("https://palazzoducale.genova.it/mostre/", res)
            reachable, code, msg = res["https://palazzoducale.genova.it/mostre/"]
            self.assertTrue(reachable)


if __name__ == "__main__":
    unittest.main()
