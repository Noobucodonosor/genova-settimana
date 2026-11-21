"""Unit tests for genova_outings.selector module.

Tests interactive terminal selection, checkbox toggling logic, category selection,
index parsing, and headless CLI filtering helpers.
"""

import io
import unittest
from unittest.mock import patch

from genova_outings.models import OutingCategory, OutingOption, WeeklyCatalog
from genova_outings.selector import (
    filter_and_select,
    interactive_select,
    parse_selection_indices,
    run_terminal_selector,
    select_by_category,
    select_by_indices,
)


class TestSelector(unittest.TestCase):
    """Test suite for selector functions."""

    def setUp(self):
        self.item1 = OutingOption(
            id="item_cinema",
            title="Cinema Sivori: rassegna cinema d'autore",
            category=OutingCategory.CINEMA,
            venue="Cinema Sivori",
            zone="Centro",
            day_time="Mercoledì alle 21:15",
            verified_url="https://circuitocinemagenova.com/sivori/",
            description="Proiezione film in VO con sottotitoli.",
        )
        self.item2 = OutingOption(
            id="item_mostra",
            title="Palazzo Ducale: mostra impressionisti",
            category=OutingCategory.MOSTRA,
            venue="Palazzo Ducale",
            zone="Centro",
            day_time="Gio-Dom 10:00-19:00",
            verified_url="https://palazzoducale.genova.it/mostre/",
            description="Opere esposte al Sottoporticato.",
        )
        self.item3 = OutingOption(
            id="item_walk",
            title="Spianata Castelletto: belvedere",
            category=OutingCategory.PASSEGGIATA,
            venue="Belvedere Luigi Montaldo",
            zone="Castelletto",
            day_time="Tutti i giorni",
            verified_url="https://www.visitgenoa.it/it/spianata-castelletto_",
            description="Passeggiata panoramica con ascensore Liberty.",
        )
        self.items = [self.item1, self.item2, self.item3]
        self.catalog = WeeklyCatalog(
            week_label="Settimana 4-10 Nov",
            generated_at="2026-11-04T10:00:00Z",
            activities=self.items,
        )

    def test_parse_selection_indices_valid(self):
        """Parses comma and space separated 1-based numbers to 0-based indices."""
        self.assertEqual(parse_selection_indices("1,3", 3), [0, 2])
        self.assertEqual(parse_selection_indices("1 2", 3), [0, 1])
        self.assertEqual(parse_selection_indices("2, 1, 3", 3), [0, 1, 2])

    def test_parse_selection_indices_boundaries_and_invalid(self):
        """Safely handles out-of-range, negative, zero, and letters."""
        self.assertEqual(parse_selection_indices("999", 3), [])
        self.assertEqual(parse_selection_indices("0", 3), [])
        self.assertEqual(parse_selection_indices("-1,-5", 3), [])
        self.assertEqual(parse_selection_indices("abc, xyz", 3), [])
        self.assertEqual(parse_selection_indices("", 3), [])
        self.assertEqual(parse_selection_indices("1, 999, foo, 2", 3), [0, 1])

    def test_select_by_indices(self):
        """Returns options corresponding to indices."""
        selected = select_by_indices(self.items, [0, 2])
        self.assertEqual(len(selected), 2)
        self.assertEqual(selected[0].id, "item_cinema")
        self.assertEqual(selected[1].id, "item_walk")

    def test_select_by_category(self):
        """Filters options matching category or synonym."""
        cinemas = select_by_category(self.items, "cinema")
        self.assertEqual(len(cinemas), 1)
        self.assertEqual(cinemas[0].category, OutingCategory.CINEMA)

        # Synonym 'film'
        cinemas_syn = select_by_category(self.items, "film")
        self.assertEqual(len(cinemas_syn), 1)

    def test_filter_and_select_headless(self):
        """Combined category and index selection helper."""
        # select_all
        all_opts = filter_and_select(self.items, select_all=True)
        self.assertEqual(len(all_opts), 3)

        # select_str
        subset = filter_and_select(self.items, select_str="1,3")
        self.assertEqual(len(subset), 2)

        # category + select
        cat_subset = filter_and_select(self.items, category_str="mostra", select_str="1")
        self.assertEqual(len(cat_subset), 1)
        self.assertEqual(cat_subset[0].id, "item_mostra")

    def test_terminal_selector_toggle_and_done(self):
        """Simulates user toggling 1,3 and entering done."""
        buf = io.StringIO()
        with patch("builtins.input", side_effect=["1,3", "done"]):
            result = run_terminal_selector(self.catalog, stream_out=buf)
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0].id, "item_cinema")
            self.assertEqual(result[1].id, "item_walk")

    def test_terminal_selector_all_command(self):
        """Simulates user selecting 'all' then 'done'."""
        buf = io.StringIO()
        with patch("builtins.input", side_effect=["all", "done"]):
            result = run_terminal_selector(self.catalog, stream_out=buf)
            self.assertEqual(len(result), 3)

    def test_terminal_selector_cat_command(self):
        """Simulates user using 'cat cinema' then 'done'."""
        buf = io.StringIO()
        with patch("builtins.input", side_effect=["cat cinema", "done"]):
            result = run_terminal_selector(self.catalog, stream_out=buf)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0].id, "item_cinema")

    def test_terminal_selector_quit_command(self):
        """Simulates user typing 'quit'."""
        buf = io.StringIO()
        with patch("builtins.input", side_effect=["quit"]):
            result = run_terminal_selector(self.catalog, stream_out=buf)
            self.assertEqual(result, [])

    def test_terminal_selector_add_and_remove_syntax(self):
        """Simulates user using +1 and -1 syntax."""
        buf = io.StringIO()
        with patch("builtins.input", side_effect=["+1", "+2", "-1", "done"]):
            result = run_terminal_selector(self.catalog, stream_out=buf)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0].id, "item_mostra")

    def test_terminal_selector_eof_handling(self):
        """Handles EOFError cleanly without crash."""
        buf = io.StringIO()
        with patch("builtins.input", side_effect=EOFError):
            result = run_terminal_selector(self.catalog, stream_out=buf)
            self.assertEqual(result, [])

    def test_interactive_select_alias(self):
        """interactive_select calls run_terminal_selector."""
        buf = io.StringIO()
        with patch("builtins.input", side_effect=["1", "done"]):
            result = interactive_select(self.items, stream_out=buf)
            self.assertEqual(len(result), 1)

    def test_web_server_endpoints(self):
        """Test local web server endpoints GET /, GET /api/catalog, POST /api/format."""
        import json
        import threading
        import urllib.request
        from genova_outings.web_ui import create_web_server

        server = create_web_server(catalog=self.catalog, port=0)
        port = server.server_port
        t = threading.Thread(target=server.serve_forever)
        t.daemon = True
        t.start()
        try:
            # 1. GET /
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/") as resp:
                self.assertEqual(resp.status, 200)
                html = resp.read().decode("utf-8")
                self.assertIn("Cosa facciamo Genova", html)
                self.assertIn("stasera dove vado a ballare?", html)

            # 2. GET /api/catalog
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/catalog") as resp:
                self.assertEqual(resp.status, 200)
                cat_data = json.loads(resp.read().decode("utf-8"))
                self.assertIn("activities", cat_data)
                self.assertEqual(len(cat_data["activities"]), 3)

            # 3. POST /api/format
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/api/format",
                data=json.dumps({"selected_ids": ["item_cinema"], "tone": "amichevole"}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req) as resp:
                self.assertEqual(resp.status, 200)
                fmt_data = json.loads(resp.read().decode("utf-8"))
                self.assertIn("message", fmt_data)
                self.assertEqual(fmt_data["count"], 1)
                self.assertIn("Cinema Sivori", fmt_data["message"])
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
