"""Tests for scripts/build_data.py ETL and blocking validator (TASK-GS-BE-01)."""

import json
import tempfile
import unittest
from pathlib import Path

from scripts import build_data


class TestBuildDataETL(unittest.TestCase):
    def test_clean_scraping_text_and_summary_limit(self):
        dirty = "<b>Mostra</b> | Orari: 10-18 | Biglietto 10€ — testo lungo " + ("parola " * 30)
        cleaned = build_data.clean_scraping_text(dirty)
        self.assertNotIn("<b>", cleaned)
        self.assertNotIn("|", cleaned)
        self.assertNotIn("—", cleaned)
        summary = build_data.make_summary(dirty, max_len=160)
        self.assertLessEqual(len(summary), 160)

    def test_validator_rejects_dirty_pipes_html_and_duplicates(self):
        bad_events = [
            {
                "id": "e1",
                "title": "Evento <b>Uno</b>",
                "venue": "Sala | A | B",
                "summary": "x" * 165,
                "category": "mostra",
            },
            {
                "id": "e1",
                "title": "Evento <b>Uno</b>",
                "venue": "Sala | A | B",
                "summary": "ok",
                "category": "mostra",
            },
        ]
        errors = build_data.validate_events(bad_events)
        self.assertTrue(any("duplicate id" in e for e in errors))
        self.assertTrue(any("summary exceeds 160" in e for e in errors))
        self.assertTrue(any("residual HTML tag" in e for e in errors))
        self.assertTrue(any("dirty pipe" in e for e in errors))

    def test_run_build_generates_deterministic_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            (tmp / "esercenti_genova_provincia_db.json").write_text(
                json.dumps([
                    {
                        "nome": "Bottega <i>Storica</i>",
                        "comune": "Genova",
                        "quartiere_o_zona": "Centro",
                        "macro_settore": "Alimentari",
                        "categoria_specifica": "Panificio",
                        "indipendente": True,
                        "indirizzo": "Via Roma 1",
                        "telefono": "010123",
                        "sito_o_social": "https://example.org",
                        "orari": "08-19",
                        "cosa_trovi_qui": "Pane | Focaccia | Dolci",
                        "personaggio_via": "Mazzini",
                        "lat": 44.4,
                        "lon": 8.9,
                    }
                ]),
                encoding="utf-8",
            )
            (tmp / "toponimi_personaggi_genova_integrale.csv").write_text(
                "toponimo,tipo,personaggio_o_casata,descrizione_categoria\n"
                "Via Garibaldi,Via,Giuseppe Garibaldi,Risorgimento\n",
                encoding="utf-8",
            )
            counts = build_data.run_build(data_dir=tmp, live_verify=False, mirror_to_site=True)
            self.assertGreater(counts["events"], 0)
            self.assertEqual(counts["esercenti"], 1)
            self.assertEqual(counts["odonomastica"], 1)
            for folder in (tmp / "data", tmp / "site" / "data"):
                self.assertTrue((folder / "events.json").exists())
                self.assertTrue((folder / "esercenti.json").exists())
                self.assertTrue((folder / "odonomastica.json").exists())
            es = json.loads((tmp / "data" / "esercenti.json").read_text(encoding="utf-8"))
            self.assertEqual(es[0]["nome"], "Bottega Storica")
            self.assertNotIn("|", es[0]["cosa_trovi"])

    def test_build_events_uses_editorial_category_and_programme_order(self):
        from unittest.mock import patch
        from genova_outings.models import OutingCategory, OutingOption

        opts = [
            OutingOption(
                id="a_altro",
                title="Abbazia Antica",
                category=OutingCategory.ALTRO,
                venue="Abbazia Antica",
                zone="levante",
                day_time="Sempre",
                description="Abbazia",
                verified_url="https://example.org/abbazia",
            ),
            OutingOption(
                id="c_no_prog",
                title="Cinema Alpha",
                category=OutingCategory.CINEMA,
                venue="Cinema Alpha",
                zone="centro",
                day_time="Sera",
                description="Sala",
                verified_url="https://example.org/alpha",
            ),
            OutingOption(
                id="c_with_prog",
                title="Cinema Zeta",
                category=OutingCategory.CINEMA,
                venue="Cinema Zeta",
                zone="centro",
                day_time="Sera",
                description="Sala",
                verified_url="https://example.org/zeta",
                raw_metadata={"programma": [{"titolo": "Film", "quando": "21:00"}]},
            ),
            OutingOption(
                id="m_mostra",
                title="Mostra Arte",
                category=OutingCategory.MOSTRA,
                venue="Palazzo",
                zone="centro",
                day_time="10-19",
                description="Mostra",
                verified_url="https://example.org/mostra",
            ),
        ]
        with patch("scripts.build_data.get_weekly_catalog", return_value=opts):
            events = build_data.build_events(live_verify=False)
        self.assertEqual(
            [e["id"] for e in events],
            ["c_with_prog", "c_no_prog", "m_mostra", "a_altro"],
        )


if __name__ == "__main__":
    unittest.main()
