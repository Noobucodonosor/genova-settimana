"""Security regression tests for TASK-SEC-01 (XSS, inline JSON, TLS, CORS, Content-Length)."""

import http.client
import json
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from genova_outings import export_static, verifier, web_ui
from genova_outings.models import OutingCategory, OutingOption


class TestSecurityHardening(unittest.TestCase):
    def test_web_ui_template_has_xss_and_url_guards(self):
        self.assertIn("function esc(", web_ui.HTML_TEMPLATE)
        self.assertIn("function safeUrl(", web_ui.HTML_TEMPLATE)
        self.assertIn("${esc(item.title)}", web_ui.HTML_TEMPLATE)
        self.assertIn("${esc(href)}", web_ui.HTML_TEMPLATE)

    def test_export_static_escapes_inline_json_and_validates_urls(self):
        src = Path(export_static.__file__).read_text(encoding="utf-8")
        self.assertTrue(
            '.replace("<", "\\\\u003c")' in src or "safe_json_for_script" in src
        )
        self.assertIn("/^https?:\\/\\//i.test", export_static.PAGE)

    def test_verifier_does_not_disable_tls_verification(self):
        src = Path(verifier.__file__).read_text(encoding="utf-8")
        self.assertNotIn("CERT_NONE", src)
        self.assertNotIn("check_hostname = False", src)

    def test_provincial_generators_escape_inline_json_and_have_xss_guards(self):
        root = Path(__file__).resolve().parent.parent
        for fname in (
            "build_bussola_html.py",
            "generate_dashboard_html.py",
            "generate_navigatore_esercenti.py",
        ):
            src = (root / fname).read_text(encoding="utf-8")
            self.assertIn('.replace("<", "\\\\u003c")', src, fname)
            self.assertIn("^https?://", src.replace("\\/", "/"), fname)

    def test_web_ui_server_cors_and_content_length_limits(self):
        opt = OutingOption(
            id="sec-1",
            title="Test",
            category=OutingCategory.MOSTRA,
            venue="Palazzo Ducale",
            zone="centro",
            day_time="Sabato 10:00",
            description="Mostra di test.",
            verified_url="https://palazzoducale.genova.it/",
        )
        server = web_ui.create_web_server(catalog=[opt], host="127.0.0.1", port=0)
        port = server.server_address[1]
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        try:
            # 1. Arbitrary Origin should NOT receive Access-Control-Allow-Origin: *
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
            conn.request("GET", "/api/catalog", headers={"Origin": "https://evil.example"})
            resp = conn.getresponse()
            resp.read()
            self.assertIsNone(resp.getheader("Access-Control-Allow-Origin"))
            conn.close()

            # 2. Localhost Origin is allowed
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
            conn.request("GET", "/api/catalog", headers={"Origin": f"http://localhost:{port}"})
            resp = conn.getresponse()
            resp.read()
            self.assertEqual(resp.getheader("Access-Control-Allow-Origin"), f"http://localhost:{port}")
            conn.close()

            # 3. Oversized Content-Length -> 413
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
            conn.request("POST", "/api/format", body=b"{}", headers={"Content-Length": "2000000"})
            resp = conn.getresponse()
            resp.read()
            self.assertEqual(resp.status, 413)
            conn.close()
        finally:
            server.shutdown()
            server.server_close()
            t.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
