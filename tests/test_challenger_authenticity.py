"""Challenger 2 empirical verification suite for Milestone 1.

Focus:
1. Data authenticity & placeholder detection
2. Temporal validity & seasonal activity (Nov 2026)
3. Closed venue detection (Cinema Teatro Cantero)
4. Multi-exhibition deduplication retention (Palazzo Ducale)
5. Fallback performance (< 0.5s) and live verification reliability
"""

import re
import time
import unittest
from genova_outings import get_weekly_catalog, OutingCategory
from genova_outings.verifier import probe_url_reachability


class TestMilestone1AuthenticityAndPerformance(unittest.TestCase):
    """Empirical challenge tests targeting data integrity, temporality, and performance."""

    def test_fallback_performance_under_500ms(self):
        """Verify get_weekly_catalog(live_verify=False) executes in < 0.5s."""
        timings = []
        for _ in range(5):
            t0 = time.perf_counter()
            cat = get_weekly_catalog(live_verify=False)
            t1 = time.perf_counter()
            timings.append(t1 - t0)

        avg_time = sum(timings) / len(timings)
        max_time = max(timings)
        self.assertLess(
            max_time, 0.5,
            f"Fallback execution exceeded 0.5s: max={max_time:.4f}s, avg={avg_time:.4f}s"
        )
        self.assertGreater(len(cat), 120, f"Expected >120 catalog items (entries without verified hours are dropped), got {len(cat)}")

    def test_zero_strict_dummy_or_placeholder_strings(self):
        """Verify no test/dummy/todo/lorem/placeholder strings appear in any catalog field."""
        cat = get_weekly_catalog(live_verify=False)
        dummy_patterns = [
            re.compile(r"\btest\b", re.I),
            re.compile(r"\bdummy\b", re.I),
            re.compile(r"\btodo\b", re.I),
            re.compile(r"\blorem(?:\s+ipsum)?\b", re.I),
            re.compile(r"\bplaceholder\b", re.I),
            re.compile(r"\bsample\b", re.I),
            re.compile(r"\bfake\b", re.I),
            re.compile(r"\bfoo\b", re.I),
            re.compile(r"\btbd\b", re.I),
        ]
        fields = ["id", "title", "venue", "zone", "day_time", "verified_url", "description", "address", "cost_info"]

        violations = []
        for opt in cat:
            for f in fields:
                val = getattr(opt, f, "")
                if not val:
                    continue
                for pat in dummy_patterns:
                    matches = pat.findall(str(val))
                    if matches:
                        violations.append((opt.id, f, val, matches))

        self.assertEqual(violations, [], f"Found dummy/placeholder strings: {violations}")

    def test_no_closed_theatres_cantero(self):
        """Verify permanently closed venues (Teatro Cantero in Chiavari, closed Dec 2017) are excluded."""
        cat = get_weekly_catalog(live_verify=False)
        cantero_items = [o for o in cat if "cantero" in (o.id + o.venue + o.description).lower()]
        self.assertEqual(
            cantero_items, [],
            f"Found permanently closed Cinema Teatro Cantero in catalog: {[c.id for c in cantero_items]}"
        )

    def test_no_inactive_summer_only_arenas_in_november(self):
        """Verify inactive summer-only open-air cinemas (Circuito sul Mare) are excluded in November."""
        cat = get_weekly_catalog(live_verify=False)
        summer_items = [o for o in cat if "circuito sul mare" in o.venue.lower() or "circuito-sul-mare" in o.verified_url]
        self.assertEqual(
            summer_items, [],
            f"Found inactive summer arena in November catalog: {[s.id for s in summer_items]}"
        )

    def test_multi_exhibition_retention_at_same_venue(self):
        """Verify multiple distinct exhibitions at Palazzo Ducale (Impressionisti and World Press Photo) both exist."""
        cat = get_weekly_catalog(live_verify=False)
        ducale_mostre = [
            o for o in cat
            if o.category == OutingCategory.MOSTRA and "ducale" in o.venue.lower()
        ]
        # Should contain both Impressionisti and World Press Photo
        titles = [o.title for o in ducale_mostre]
        self.assertTrue(
            any("impressionisti" in t.lower() for t in titles),
            f"Missing Impressionisti exhibition at Palazzo Ducale in {titles}"
        )
        self.assertTrue(
            any("world press photo" in t.lower() for t in titles),
            f"World Press Photo 2026 was incorrectly deduplicated and dropped from Palazzo Ducale in {titles}"
        )

    def test_network_probe_resilience(self):
        """Verify probe_url_reachability handles non-existent domains and hanging timeouts gracefully."""
        # Non-existent domain
        t0 = time.perf_counter()
        reachable, code, _ = probe_url_reachability("http://this-does-not-exist-9876543210.org", timeout=1.0, use_cache=False)
        t1 = time.perf_counter()
        self.assertFalse(reachable)
        self.assertLess(t1 - t0, 2.0)

        # Hanging non-routable IP
        t0 = time.perf_counter()
        reachable, code, _ = probe_url_reachability("http://10.255.255.1:81/", timeout=1.0, use_cache=False)
        t1 = time.perf_counter()
        self.assertFalse(reachable)
        self.assertLess(t1 - t0, 2.0)


if __name__ == "__main__":
    unittest.main()
