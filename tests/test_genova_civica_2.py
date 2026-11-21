"""Verification tests for Genova Civica 2.0 upgrades."""

import io
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

from genova_outings import export_static, html_utils, programme


class TestGenovaCivica2(unittest.TestCase):
    def test_shared_nav_includes_storie_and_pwa_assets_exist(self):
        nav = html_utils.render_shared_nav("storie")
        self.assertIn("storie.html", nav)
        self.assertIn("Storie dalle Strade", nav)
        root = Path(__file__).resolve().parent.parent
        self.assertTrue((root / "site" / "manifest.webmanifest").exists())
        self.assertTrue((root / "site" / "sw.js").exists())

    def test_async_html_pages_stay_lightweight(self):
        root = Path(__file__).resolve().parent.parent
        for name in ("esercenti.html", "dashboard.html", "storie.html"):
            target = root / "site" / name
            self.assertTrue(target.exists(), name)
            self.assertLess(target.stat().st_size, 64 * 1024, f"{name} exceeded 64 KB")

    def test_export_static_minimal_magazine_design_and_dedupe(self):
        for marker in (
            "Questa settimana a Genova",
            "genova_civica_sel_v1",
            "Mostra anche luoghi sempre aperti",
            "Copia testo",
            "Manda su WhatsApp",
            "Modifica",
        ):
            self.assertIn(marker, export_static.PAGE)
        for removed in ("gc-nav", "toneSel", "zoneSel", "api.open-meteo.com", "saveIcs"):
            self.assertNotIn(removed, export_static.PAGE)

        from genova_outings.models import OutingCategory, OutingOption
        a = OutingOption(
            id="s1",
            title="Sìvori: Programmazione Spettacoli",
            category=OutingCategory.CINEMA,
            venue="Sìvori",
            zone="centro",
            day_time="Ogni sera",
            description="Cinema",
            verified_url="https://circuitocinemagenova.com/sivori/",
            raw_metadata={"programma": [{"titolo": "Film A", "quando": "21:00"}]},
        )
        b = OutingOption(
            id="s2",
            title="Cinema Sivori: Rassegna d'Essai",
            category=OutingCategory.CINEMA,
            venue="Cinema Sivori",
            zone="centro",
            day_time="Ogni sera",
            description="Cinema d'essai storico",
            verified_url="https://circuitocinemagenova.com/sivori/",
            raw_metadata={"programma": [{"titolo": "Film B", "quando": "18:30"}]},
        )
        deduped = export_static._dedupe([a, b])
        self.assertEqual(len(deduped), 1)
        self.assertEqual(deduped[0].title, "Cinema Sivori")
        self.assertEqual(deduped[0].category, OutingCategory.CINEMA)
        self.assertEqual(len(deduped[0].raw_metadata["programma"]), 2)

    def test_dedupe_category_priority_aliases_and_shared_portals(self):
        from genova_outings.models import OutingCategory, OutingOption

        sivori_musica = OutingOption(
            id="tl_273_musica",
            title="Cinema Sivori",
            category=OutingCategory.MUSICA,
            venue="Cinema Sivori",
            zone="centro",
            day_time="Ogni sera",
            description="Descrizione lunga da payload secondario per test categoria",
            verified_url="https://circuitocinemagenova.com/sivori/",
            source_type="verified_local",
            raw_metadata={"programma": [{"titolo": "Film B", "quando": "21:00"}]},
        )
        sivori_cinema = OutingOption(
            id="circuito_cinema_sivori",
            title="Cinema Sivori: Rassegna d'Essai e Prime Visioni",
            category=OutingCategory.CINEMA,
            venue="Cinema Sivori",
            zone="centro",
            day_time="Ogni sera",
            description="Sala cinema d'essai",
            verified_url="https://circuitocinemagenova.com/sivori/",
            source_type="live_web",
        )
        teatro_short = OutingOption(
            id="tl_89_musica",
            title="Teatro Sociale",
            category=OutingCategory.MUSICA,
            venue="Teatro Sociale",
            zone="levante",
            day_time="Venerdì e sabato",
            description="Teatro",
            verified_url="https://www.teatrosocialecamogli.it",
        )
        teatro_full = OutingOption(
            id="tl_35_musica",
            title="Teatro Sociale di Camogli: Concerti & Aperitivo nei Palchi",
            category=OutingCategory.MUSICA,
            venue="Teatro Sociale di Camogli",
            zone="levante",
            day_time="Fine settimana",
            description="Storico teatro ottocentesco a Camogli",
            verified_url="https://www.teatrosocialecamogli.it/",
        )
        nervi_a = OutingOption(
            id="tl_26_mostra",
            title="Polo Museale di Nervi (GAM, Raccolte Frugone & Wolfsoniana)",
            category=OutingCategory.MOSTRA,
            venue="Polo Museale di Nervi",
            zone="levante",
            day_time="Mar-Dom",
            description="Musei di Nervi",
            verified_url="https://www.museidigenova.it/it/gam-galleria-darte-moderna",
        )
        nervi_b = OutingOption(
            id="polo_museale_nervi_gam",
            title="Polo Museale di Nervi: Galleria d'Arte Moderna e Parchi",
            category=OutingCategory.MOSTRA,
            venue="GAM Galleria d'Arte Moderna",
            zone="levante",
            day_time="Mar-Dom",
            description="GAM",
            verified_url="https://www.museidigenova.it/it/gam-galleria-darte-moderna",
            source_type="live_web",
        )
        parchi_a = OutingOption(
            id="tl_25_passeggiata",
            title="Parchi di Nervi, Roseto & Passeggiata Anita Garibaldi",
            category=OutingCategory.PASSEGGIATA,
            venue="Parchi di Nervi, Roseto & Passeggiata Anita Garibaldi",
            zone="levante",
            day_time="Tutti i giorni",
            description="Parchi e scogliera",
            verified_url="https://www.visitgenoa.it/it/parchi-di-nervi",
        )
        parchi_b = OutingOption(
            id="passeggiata_nervi_anita_garibaldi",
            title="Passeggiata Anita Garibaldi: Scogliera e Parchi di Nervi",
            category=OutingCategory.PASSEGGIATA,
            venue="Passeggiata di Nervi",
            zone="levante",
            day_time="Tutti i giorni",
            description="Passeggiata sul mare",
            verified_url="https://www.visitgenoa.it/it/parchi-di-nervi-1",
            source_type="live_web",
        )
        bib_berio = OutingOption(
            id="tl_29_biblioteca",
            title="Biblioteca Civica Berio",
            category=OutingCategory.BIBLIOTECA,
            venue="Biblioteca Civica Berio",
            zone="centro",
            day_time="Lun-Sab",
            description="Berio",
            verified_url="https://www.bibliotechedigenova.it/",
        )
        bib_berio_dup = OutingOption(
            id="biblioteca_civica_berio",
            title="Biblioteca Civica Berio: Chiostro del Seicento e Spazio Lettura",
            category=OutingCategory.BIBLIOTECA,
            venue="Biblioteca Civica Berio",
            zone="centro",
            day_time="Lun-Sab",
            description="Berio",
            verified_url="https://www.bibliotechedigenova.it/berio",
            source_type="live_web",
        )
        bib_de_amicis = OutingOption(
            id="tl_30_biblioteca",
            title="Biblioteca De Amicis al Porto Antico",
            category=OutingCategory.BIBLIOTECA,
            venue="Biblioteca De Amicis al Porto Antico",
            zone="porto_antico",
            day_time="Lun-Sab",
            description="De Amicis",
            verified_url="https://www.bibliotechedigenova.it/",
        )
        bib_de_amicis_dup = OutingOption(
            id="biblioteca_de_amicis",
            title="Biblioteca De Amicis: Spazio Lettura sul Mare al Porto Antico",
            category=OutingCategory.BIBLIOTECA,
            venue="Biblioteca De Amicis",
            zone="porto_antico",
            day_time="Lun-Sab",
            description="De Amicis",
            verified_url="https://www.bibliotechedigenova.it/de-amicis",
            source_type="live_web",
        )

        merged = export_static._dedupe([
            sivori_musica,
            sivori_cinema,
            teatro_short,
            teatro_full,
            nervi_a,
            nervi_b,
            parchi_a,
            parchi_b,
            bib_berio,
            bib_berio_dup,
            bib_de_amicis,
            bib_de_amicis_dup,
        ])
        self.assertEqual(len(merged), 6)
        by_title = {item.title: item for item in merged}
        self.assertEqual(by_title["Cinema Sivori"].category, OutingCategory.CINEMA)
        self.assertEqual(len(by_title["Cinema Sivori"].raw_metadata["programma"]), 1)
        self.assertIn("Teatro Sociale di Camogli", by_title)
        self.assertIn("Biblioteca Civica Berio", by_title)
        self.assertIn("Biblioteca De Amicis", by_title)

    def test_programme_get_retries_once_on_transient_timeout(self):
        class DummyResp:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def read(self):
                return b"<html>ok</html>"

        with patch("urllib.request.urlopen", side_effect=[TimeoutError("slow"), DummyResp()]) as m, \
             patch("time.sleep"):
            out = programme._get("https://example.org/", timeout=1.0)
        self.assertEqual(out, "<html>ok</html>")
        self.assertEqual(m.call_count, 2)


if __name__ == "__main__":
    unittest.main()
