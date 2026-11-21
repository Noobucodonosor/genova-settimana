"""Portability and HTTP cache TTL tests for TASK-PORT-01."""

import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from genova_outings import catalog, verifier


class TestPortabilityAndCacheTTL(unittest.TestCase):
    def test_no_hardcoded_user_home_in_package(self):
        pkg_dir = Path(catalog.__file__).resolve().parent
        for py in pkg_dir.glob("*.py"):
            self.assertNotIn("/Users/dany", py.read_text(encoding="utf-8"), py.name)

    def test_default_data_dir_exists_and_is_relative_to_repo(self):
        self.assertTrue(catalog.DEFAULT_DATA_DIR.exists())
        self.assertEqual(catalog.DEFAULT_DATA_DIR, Path(__file__).resolve().parent.parent)

    def test_crawled_cache_respects_ttl(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_file = Path(tmpdir) / "crawled_urls_cache.json"
            cache_file.write_text(
                json.dumps({"https://example.org": {"status": "OK", "http_code": 200}}),
                encoding="utf-8",
            )
            old_time = time.time() - (10 * 86400)
            os.utime(cache_file, (old_time, old_time))

            verifier._CRAWLED_CACHE_LOADED = False
            verifier._CRAWLED_CACHE_DATA = {}
            with patch.dict(os.environ, {"GENOVA_DATA_DIR": tmpdir, "GENOVA_CACHE_TTL_DAYS": "7"}):
                data = verifier._load_crawled_cache()
                self.assertEqual(data, {})

            verifier._CRAWLED_CACHE_LOADED = False
            verifier._CRAWLED_CACHE_DATA = {}
            with patch.dict(os.environ, {"GENOVA_DATA_DIR": tmpdir, "GENOVA_CACHE_TTL_DAYS": "30"}):
                data = verifier._load_crawled_cache()
                self.assertIn("https://example.org", data)

            verifier._CRAWLED_CACHE_LOADED = False
            verifier._CRAWLED_CACHE_DATA = {}


if __name__ == "__main__":
    unittest.main()
