"""Unit tests for shared html_utils helpers (TASK-ARCH-02)."""

import unittest
from pathlib import Path

from genova_outings.html_utils import (
    OPEN_DATA_ATTRIBUTION_TEXT,
    get_data_dir,
    load_json_file,
    safe_json_for_script,
)


class TestHtmlUtils(unittest.TestCase):
    def test_safe_json_for_script_escapes_script_close(self):
        raw = {"title": "Test </script><script>alert(1)</script>"}
        encoded = safe_json_for_script(raw)
        self.assertNotIn("<", encoded)
        self.assertIn("\\u003c/script>", encoded)

    def test_get_data_dir_and_load_json_file(self):
        root = get_data_dir()
        self.assertEqual(root, Path(__file__).resolve().parent.parent)
        cfg = load_json_file("data/config/closed_venues.json")
        self.assertIn("blacklisted_substrings", cfg)

    def test_attribution_constant_present(self):
        self.assertIn("OpenStreetMap contributors", OPEN_DATA_ATTRIBUTION_TEXT)
        self.assertIn("ODbL 1.0", OPEN_DATA_ATTRIBUTION_TEXT)


if __name__ == "__main__":
    unittest.main()
