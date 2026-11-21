"""Tests for WhatsApp formatter parity between formatter.py and export_static.py (TASK-UX-01)."""

import unittest
from genova_outings import export_static


class TestWhatsappParity(unittest.TestCase):
    def test_export_static_message_includes_verified_url_and_plain_writing(self):
        self.assertIn("function cleanPlain(", export_static.PAGE)
        self.assertIn("Info: ${safeHref}", export_static.PAGE)
        self.assertIn("Dimmi se ti ispira", export_static.PAGE)
        self.assertNotIn("—", export_static.PAGE.split("function message()")[1].split("function bar()")[0])


if __name__ == "__main__":
    unittest.main()
