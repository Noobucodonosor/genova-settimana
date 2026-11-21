"""Tests for keyboard accessibility and programme extractor telemetry (TASK-A11Y-01)."""

import logging
import unittest
from datetime import date
from unittest.mock import patch

from genova_outings import export_static, programme, web_ui
from genova_outings.models import OutingCategory, OutingOption


class TestA11yAndTelemetry(unittest.TestCase):
    def test_cards_have_keyboard_accessibility_and_aria_roles(self):
        self.assertIn("setAttribute('role', 'checkbox')", web_ui.HTML_TEMPLATE)
        self.assertIn('role="checkbox"', export_static.PAGE)
        for template in (web_ui.HTML_TEMPLATE, export_static.PAGE):
            self.assertIn("aria-checked", template)
            self.assertIn("tabindex", template)
            self.assertIn("keydown", template.lower())

    def test_attach_programmes_logs_warning_for_empty_extractors(self):
        opt = OutingOption(
            id="sivori",
            title="Cinema Sivori",
            category=OutingCategory.CINEMA,
            venue="Cinema Sivori",
            zone="centro",
            day_time="Ogni sera",
            description="Cinema",
            verified_url="https://www.circuitocinemagenova.com/sale/sivori/",
        )
        with patch("genova_outings.programme.fetch_programme", return_value=[]), \
             patch("genova_outings.programme.build_venue_events", return_value=[]), \
             self.assertLogs("genova_outings.programme", level=logging.WARNING) as cm:
            n = programme.attach_programmes([opt], today=date(2026, 11, 21), workers=1)
        self.assertEqual(n, 0)
        self.assertTrue(any("0 events" in msg for msg in cm.output))


if __name__ == "__main__":
    unittest.main()
