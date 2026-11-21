"""Offline unit tests for export_static.py (TASK-QA-01)."""

import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from genova_outings import export_static
from genova_outings.models import OutingCategory, OutingOption


class TestExportStaticOffline(unittest.TestCase):
    def test_dedupe_prefers_richer_programme_entry(self):
        a = OutingOption(
            id="a1",
            title="Cinema Sivori",
            category=OutingCategory.CINEMA,
            venue="Cinema Sivori",
            zone="centro",
            day_time="Ogni sera",
            description="Breve",
            verified_url="https://www.circuitocinemagenova.com/sale/sivori/",
            raw_metadata={},
        )
        b = OutingOption(
            id="a2",
            title="Cinema Sivori (programma)",
            category=OutingCategory.CINEMA,
            venue="Cinema Sivori",
            zone="centro",
            day_time="Ogni sera",
            description="Breve",
            verified_url="https://www.circuitocinemagenova.com/sale/sivori",
            raw_metadata={"programma": [{"titolo": "Film", "quando": "21:00"}]},
        )
        res = export_static._dedupe([a, b])
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].id, "a2")

    def test_build_writes_clean_index_html(self):
        opt = OutingOption(
            id="c1",
            title="Cinema Sivori",
            category=OutingCategory.CINEMA,
            venue="Cinema Sivori",
            zone="centro",
            day_time="Sabato 21:00",
            description="Proiezione serale.",
            verified_url="https://www.circuitocinemagenova.com/",
            raw_metadata={"programma": [{"titolo": "La Chimera", "quando": "Sab 21:00"}]},
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            with patch("genova_outings.export_static.get_weekly_catalog", return_value=[opt]), \
                 patch("genova_outings.export_static.attach_programmes", return_value=1):
                target = export_static.build(out_dir)
            self.assertTrue(target.exists())
            content = target.read_text(encoding="utf-8")
            self.assertIn("Cinema Sivori", content)
            self.assertIn("La Chimera", content)
            for placeholder in ("__DATA__", "__LABELS__", "__RANGE__", "__UPDATED__"):
                self.assertNotIn(placeholder, content)

    @unittest.skipUnless(shutil.which("node"), "Node.js not installed")
    def test_js_score_item_runtime_no_reference_error_or_global_leak(self):
        m = re.search(
            r"(const norm = .*?function scoreItem\(d, info\) \{.*?\n\})",
            export_static.PAGE,
            re.S,
        )
        self.assertIsNotNone(m, "Could not locate JS search/score block in export_static.PAGE")
        js_snippet = m.group(1)

        sample_data = [
            {
                "id": "casa_mia_club_genova",
                "category": "musica",
                "title": "Casa Mia Club: Discoteca, Serate Clubbing e Dj Set",
                "place": "Via XII Ottobre 182r, Centro",
                "day_time": "Venerdì e sabato ore 23:30-04:30",
                "description": "Club sotterraneo con piste da ballo e dj set.",
                "programma": [{"titolo": "Saturday Night", "quando": "sabato 21 novembre 23:30"}],
                "tags": ["indoor", "ballare", "discoteca", "club", "dj"],
                "outdoor": False,
                "time_slot": "sera",
            },
            {
                "id": "teatro_carlo_felice",
                "category": "musica",
                "title": "Teatro Carlo Felice: Stagione Lirica",
                "place": "Passo Eugenio Montale 4, Centro",
                "day_time": "Venerdì ore 20:00",
                "description": "Opera lirica e concerti sinfonici.",
                "programma": [{"titolo": "La Traviata", "quando": "sabato 21 novembre 20:00"}],
                "tags": ["indoor", "opera", "teatro"],
                "outdoor": False,
                "time_slot": "sera",
            },
            {
                "id": "circuito_cinema_sivori",
                "category": "cinema",
                "title": "Cinema Sivori",
                "place": "Salita Santa Caterina 12, Centro",
                "day_time": "Tutti i giorni ore 16:00 / 18:30 / 21:15",
                "description": "Cinema d'essai in centro.",
                "programma": [{"titolo": "La Chimera", "quando": "sabato 21 novembre 21:15"}],
                "tags": ["indoor", "cinema", "essai"],
                "outdoor": False,
                "time_slot": "sera",
            },
            {
                "id": "borgo_boccadasse",
                "category": "passeggiata",
                "title": "Borgo di Boccadasse",
                "place": "Piazza Nettuno, Albaro",
                "day_time": "Sempre accessibile h24",
                "description": "Passeggiata sul mare e pista ciclabile.",
                "programma": [],
                "tags": ["outdoor", "mare"],
                "outdoor": True,
                "time_slot": "flessibile",
            },
            {
                "id": "teatro_sociale_camogli",
                "category": "musica",
                "title": "Teatro Sociale",
                "place": "Piazza Giacomo Matteotti 5, Camogli",
                "day_time": "Secondo stagione teatrale",
                "description": "Stagione di prosa e concerti a Camogli.",
                "programma": [],
                "tags": ["indoor", "teatro"],
                "outdoor": False,
                "time_slot": "sera",
            },
            {
                "id": "cineclub_nickelodeon",
                "category": "cinema",
                "title": "Cineclub Nickelodeon",
                "place": "Via della Consolazione 5r, Centro",
                "day_time": "Tutti i giorni ore 17:00 / 21:00",
                "description": "Cineclub storico di Genova.",
                "programma": [],
                "tags": ["indoor", "cinema"],
                "outdoor": False,
                "time_slot": "sera",
            },
            {
                "id": "club_amici_del_cinema",
                "category": "cinema",
                "title": "Club Amici del Cinema",
                "place": "Via Carlo Rolando 15, Sampierdarena",
                "day_time": "Tutti i giorni ore 18:00 / 21:00",
                "description": "Storica sala d'essai.",
                "programma": [],
                "tags": ["indoor", "cinema"],
                "outdoor": False,
                "time_slot": "sera",
            },
        ]

        runner = f"""
{js_snippet}
const DATA = {json.dumps(sample_data)};
const queries = ["ballare", "ballare stasera piove", "cinema", "cineclub", "sivori", "piove", "stasera"];
const results = {{}};
for (const q of queries) {{
  const info = analyzeQuery(q);
  const scored = DATA.map(d => ({{ id: d.id, s: scoreItem(d, info) }})).filter(x => x.s > 0).sort((a, b) => b.s - a.s);
  results[q] = scored.map(x => x.id);
}}
console.log(JSON.stringify({{ results, leakedScore: "score" in globalThis }}));
"""
        proc = subprocess.run(
            ["node", "-e", runner],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, f"Node failed: {proc.stderr}")
        out = json.loads(proc.stdout)
        self.assertFalse(out["leakedScore"], "scoreItem leaked global 'score'")
        self.assertEqual(out["results"]["ballare"], ["casa_mia_club_genova"])
        self.assertEqual(out["results"]["ballare stasera piove"], ["casa_mia_club_genova"])
        self.assertNotIn("teatro_carlo_felice", out["results"]["ballare"])
        self.assertNotIn("teatro_sociale_camogli", out["results"]["ballare"])
        self.assertNotIn("cineclub_nickelodeon", out["results"]["ballare"])
        self.assertNotIn("club_amici_del_cinema", out["results"]["ballare"])
        self.assertNotIn("borgo_boccadasse", out["results"]["ballare"])
        self.assertIn("circuito_cinema_sivori", out["results"]["cinema"])
        self.assertEqual(out["results"]["cineclub"], ["cineclub_nickelodeon"])
        self.assertEqual(out["results"]["sivori"], ["circuito_cinema_sivori"])
        self.assertNotIn("borgo_boccadasse", out["results"]["piove"])
        self.assertGreater(len(out["results"]["piove"]), 0)
        self.assertGreater(len(out["results"]["stasera"]), 0)

        # Verify Stasera date/time filter, round-robin mixing, and orphaned selection pruning
        tonight_script = f"""
{js_snippet}
const m2 = {json.dumps(sample_data)};
const satNight = new Date(2026, 10, 21, 19, 0, 0);
const daytimeLib = {{
  id: "bib_daytime",
  category: "biblioteca",
  title: "Biblioteca De Amicis",
  day_time: "Lun-Sab",
  time_slot: "mattina",
  programma: [{{ titolo: "BIBI Convegno", quando: "sabato 21 novembre ore 9-16" }}]
}};
const tomorrowEvent = {{
  id: "genova_tango_cba",
  category: "musica",
  title: "Genova Tango",
  day_time: "Domenica ore 21:00",
  time_slot: "sera",
  programma: [{{ titolo: "La Milonga", quando: "da domenica 22 a lunedì 23 novembre ore 21:00-01:00" }}]
}};
const s1 = getTonightProgs(m2[0], satNight);
const sDay = getTonightProgs(daytimeLib, satNight);
const sTom = getTonightProgs(tomorrowEvent, satNight);
console.log(JSON.stringify({{ s1: s1.length, sDay: sDay.length, sTom: sTom.length }}));
"""
        proc2 = subprocess.run(["node", "-e", tonight_script], capture_output=True, text=True, check=False)
        self.assertEqual(proc2.returncode, 0, f"Node tonight test failed: {proc2.stderr}")
        out2 = json.loads(proc2.stdout)
        self.assertEqual(out2["s1"], 1)
        self.assertEqual(out2["sDay"], 0)
        self.assertEqual(out2["sTom"], 0)

    def test_editorial_cleanup_programme_variants_and_places(self):
        self.assertEqual(
            export_static._clean_editorial_title("Casa Mia Club: Discoteca, Serate Clubbing e Dj Set", "Casa Mia Club"),
            "Casa Mia Club",
        )
        self.assertEqual(
            export_static._clean_editorial_title("Palazzo Ducale: Mostra Impressionisti", "Palazzo Ducale"),
            "Palazzo Ducale: Mostra Impressionisti",
        )
        self.assertEqual(
            export_static._format_place("Via XX Settembre 75r (Piazza della Corte)", "centro / via_xx_settembre"),
            "Via XX Settembre 75r (Piazza della Corte), Centro",
        )
        self.assertEqual(
            export_static._format_place("Corso Italia 28r", "albaro / corso_italia"),
            "Corso Italia 28r, Albaro",
        )
        progs = export_static._clean_programme_list([
            {"titolo": "SATURDAY ROYALE - ESTORIL BEACH CLUB", "quando": "sabato 21 novembre 18.30"},
            {"titolo": "Scrooge E Gli Spiriti Del Natale", "quando": "oggi 18:30 21:00"},
            {"titolo": "Ebenezer - Scrooge E Gli Spiriti Del Natale - V.O.", "quando": "domenica 21:00"},
            {"titolo": "Zustissia - Al Cinema Con Te'", "quando": "martedì 15.30"},
        ])
        self.assertEqual(len(progs), 3)
        self.assertEqual(progs[0]["titolo"], "Saturday Royale - Estoril Beach Club")
        self.assertEqual(progs[0]["quando"], "sabato 21 novembre 18:30")
        self.assertIn("V.O. domenica 21:00", progs[1]["quando"])
        self.assertEqual(progs[2]["titolo"], "Zustissia - Al Cinema Con Te")
        self.assertEqual(progs[2]["quando"], "martedì 15:30")


if __name__ == "__main__":
    unittest.main()
