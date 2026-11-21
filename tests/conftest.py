"""Conftest and shared test helpers for Genova Weekly Informal Outings E2E test suite.
Compatible with standard library unittest and pytest.
"""

import os
import sys
import re
import json
import unittest
from typing import Any, Dict, List, Optional

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Dataset file paths in workspace
TEMPO_LIBERO_PAYLOAD_PATH = os.path.join(PROJECT_ROOT, "tempo_libero_payload.json")
TEMPO_LIBERO_DATASET_PATH = os.path.join(PROJECT_ROOT, "tempo_libero_dataset.json")
GUIDA_APERTI_PATH = os.path.join(PROJECT_ROOT, "guida_aperti_al_pubblico_provincia_genova.json")
DASHBOARD_ITEMS_PATH = os.path.join(PROJECT_ROOT, "dashboard_items.json")
ESERCENTI_PATH = os.path.join(PROJECT_ROOT, "esercenti_genova_provincia_db.json")

# Dynamic feature detection flags for genova_outings package
def check_import(module_name: str, attr_name: Optional[str] = None) -> bool:
    try:
        mod = __import__(module_name, fromlist=[attr_name] if attr_name else [])
        if attr_name:
            return hasattr(mod, attr_name)
        return True
    except (ImportError, AttributeError):
        return False

_check_import = check_import

HAS_GENOVA_OUTINGS = check_import("genova_outings")
HAS_MODELS = check_import("genova_outings.models", "OutingOption")
HAS_CATALOG = check_import("genova_outings.catalog", "get_weekly_catalog")
HAS_VERIFIER = check_import("genova_outings.verifier", "verify_venue")
HAS_SELECTOR = check_import("genova_outings.selector", "run_terminal_selector")
HAS_FORMATTER = check_import("genova_outings.formatter", "format_whatsapp_message")
HAS_VALIDATOR = check_import("genova_outings.validator", "validate_plain_writing")
HAS_CLI = check_import("genova_outings.cli", "main")

# Prohibited patterns strictly defined by ORIGINAL_REQUEST.md & Plain Writing rules
DASH_PATTERN = re.compile(r"[\u2014\u2013\u2015]")
ROMANCE_PATTERN = re.compile(
    r"\b(date|appuntament[oi]\s+romantic[oi]|serat[ae]\s+a\s+due|uscit[ae]\s+a\s+due|"
    r"galante|romantic[oai]|lume\s+di\s+candela|innamorat[oaie]|fidanzat[oaie]|"
    r"flirt|intimit[aà]|cenett[ae]\s+a\s+due)\b",
    re.IGNORECASE,
)
PUFFERY_PATTERN = re.compile(
    r"\b(imperdibile|imperdibili|splendid[oai]|magic[oai]|esperienza\s+unica|"
    r"esperienze\s+uniche|mozzafiato|suggestiv[oai]|fiore\s+all\'?occhiello|"
    r"incantevole|incantevoli|immersiv[oai]|da\s+non\s+perdere|straordinari[oai]|"
    r"meraviglios[oai]|favolos[oai]|eccezionale|frizzante|incredibile|top)\b",
    re.IGNORECASE,
)


def assert_plain_writing(test_case: unittest.TestCase, text: str) -> None:
    """Rigorous assertion helper verifying that text complies 100% with plain writing rules:
    - Zero em-dashes (\\u2014) or en-dashes (\\u2013)
    - Zero romantic / date terms ('date', 'appuntamento romantico', etc.)
    - Zero promotional hype / buzzwords ('imperdibile', 'splendido', 'magico', 'mozzafiato', etc.)
    - Valid WhatsApp formatting (balanced *, no **, no # markdown headers, no [text](url) links)
    """
    test_case.assertIsInstance(text, str, "Output must be a string")
    test_case.assertTrue(len(text) > 0, "Output string must not be empty")

    # 1. Dash assertion
    dash_matches = DASH_PATTERN.findall(text)
    test_case.assertEqual(
        dash_matches,
        [],
        f"Plain-writing violation: prohibited long dashes found in output: {dash_matches}",
    )

    # 2. Romance / Date assertion
    romance_matches = ROMANCE_PATTERN.findall(text)
    test_case.assertEqual(
        romance_matches,
        [],
        f"Plain-writing violation: prohibited romantic / date keywords found: {romance_matches}",
    )

    # 3. Buzzword / Puffery assertion
    puffery_matches = PUFFERY_PATTERN.findall(text)
    test_case.assertEqual(
        puffery_matches,
        [],
        f"Plain-writing violation: prohibited marketing buzzwords found: {puffery_matches}",
    )

    # 4. WhatsApp markdown bolding check (*bold* touching characters, balanced asterisks)
    asterisk_count = text.count("*")
    test_case.assertEqual(
        asterisk_count % 2,
        0,
        f"WhatsApp formatting violation: unbalanced '*' bolding markers ({asterisk_count} found)",
    )
    test_case.assertNotIn(
        "**",
        text,
        "WhatsApp formatting violation: found '**' (standard markdown bold fails on WhatsApp)",
    )

    # 5. Prohibit markdown headers and markdown links
    test_case.assertIsNone(
        re.search(r"^#{1,6}\s", text, re.MULTILINE),
        "WhatsApp formatting violation: markdown headers (#) not supported in WhatsApp",
    )
    test_case.assertIsNone(
        re.search(r"\[.+?\]\(.+?\)", text),
        "WhatsApp formatting violation: markdown [text](url) links not supported in WhatsApp",
    )


def assert_real_genova_option(test_case: unittest.TestCase, option: Any) -> None:
    """Verifies that an outing option represents a genuine, verified Genova venue
    with non-empty fields, valid URL, and excludes closed venues (Villa Croce).
    """
    # Extract attributes whether dataclass or dictionary
    if isinstance(option, dict):
        opt_id = option.get("id", "")
        title = option.get("title", "")
        venue = option.get("venue", "")
        zone = option.get("zone", "")
        url = option.get("verified_url") or option.get("source_url") or ""
        desc = option.get("description", "")
        category = option.get("category", "")
    else:
        opt_id = getattr(option, "id", "")
        title = getattr(option, "title", "")
        venue = getattr(option, "venue", "")
        zone = getattr(option, "zone", "")
        url = getattr(option, "verified_url", "") or getattr(option, "source_url", "")
        desc = getattr(option, "description", "")
        category = getattr(option, "category", "")

    test_case.assertTrue(bool(opt_id), "Option id must be non-empty")
    test_case.assertTrue(bool(title), "Option title must be non-empty")
    test_case.assertTrue(bool(venue), "Option venue must be non-empty")
    test_case.assertTrue(bool(zone), "Option zone must be non-empty")
    test_case.assertTrue(bool(desc), "Option description must be non-empty")
    test_case.assertTrue(
        url.startswith("http://") or url.startswith("https://"),
        f"Verified URL must start with http:// or https:// (got: '{url}')",
    )

    # Sanity check: NO em/en dashes in title or description
    test_case.assertIsNone(
        DASH_PATTERN.search(title),
        f"Option title contains prohibited long dashes: '{title}'",
    )
    test_case.assertIsNone(
        DASH_PATTERN.search(desc),
        f"Option description contains prohibited long dashes: '{desc}'",
    )

    # Strict negative check: Villa Croce is closed for PNRR works
    full_text = f"{opt_id} {title} {venue} {url}".lower()
    test_case.assertNotIn(
        "villa croce",
        full_text,
        "Closed venue violation: Villa Croce is closed for PNRR works and must NOT be in catalog",
    )


def create_sample_cinema_option() -> Dict[str, Any]:
    """Returns an authoritative sample cinema option."""
    return {
        "id": "cinema_sivori_rassegna",
        "title": "Cinema Sivori: rassegna cinema d'autore",
        "category": "cinema",
        "venue": "Cinema Sivori",
        "zone": "Centro",
        "address": "Salita Santa Caterina 12",
        "day_time": "Mercoledì alle 21:15",
        "days_display": "Mercoledì alle 21:15",
        "verified_url": "https://circuitocinemagenova.com/sivori/",
        "source_url": "https://circuitocinemagenova.com/sivori/",
        "description": "Proiezione in lingua originale con sottotitoli in italiano nella storica sala del centro.",
        "source_type": "verified_local",
        "is_weather_dependent": False,
    }


def create_sample_mostra_option() -> Dict[str, Any]:
    """Returns an authoritative sample exhibition option."""
    return {
        "id": "palazzo_ducale_renoir",
        "title": "Palazzo Ducale: mostra impressionisti",
        "category": "mostra",
        "venue": "Palazzo Ducale",
        "zone": "Centro",
        "address": "Piazza Matteotti 9",
        "day_time": "Gio-Dom 10:00-19:00",
        "days_display": "Gio-Dom 10:00-19:00",
        "verified_url": "https://palazzoducale.genova.it/mostre/",
        "source_url": "https://palazzoducale.genova.it/mostre/",
        "description": "Dipinti di Renoir, Monet e Cézanne allestiti negli spazi del Sottoporticato.",
        "source_type": "live_web",
        "is_weather_dependent": False,
    }


def create_sample_walk_option() -> Dict[str, Any]:
    """Returns an authoritative sample scenic walk option."""
    return {
        "id": "spianata_castelletto_belvedere",
        "title": "Spianata Castelletto: sosta al belvedere",
        "category": "passeggiata",
        "venue": "Belvedere Luigi Montaldo",
        "zone": "Castelletto",
        "address": "Spianata Castelletto",
        "day_time": "Tutti i giorni, luce diurna o tramonto",
        "days_display": "Tutti i giorni, luce diurna o tramonto",
        "verified_url": "https://www.visitgenoa.it/it/spianata-castelletto_",
        "source_url": "https://www.visitgenoa.it/it/spianata-castelletto_",
        "description": "Vista panoramica sul centro storico e sul porto, raggiungibile con ascensore Liberty da Portello.",
        "source_type": "verified_local",
        "is_weather_dependent": True,
    }


def create_sample_library_option() -> Dict[str, Any]:
    """Returns an authoritative sample library reading space option."""
    return {
        "id": "biblioteca_civica_berio",
        "title": "Biblioteca Berio: lettura e chiostro",
        "category": "biblioteca",
        "venue": "Biblioteca Civica Berio",
        "zone": "Centro",
        "address": "Via del Seminario 16",
        "day_time": "Lun-Ven 08:00-19:00, Sab 08:00-13:00",
        "days_display": "Lun-Ven 08:00-19:00, Sab 08:00-13:00",
        "verified_url": "https://www.bibliotechedigenova.it/berio",
        "source_url": "https://www.bibliotechedigenova.it/berio",
        "description": "Sale studio affacciate sul chiostro seicentesco con bar interno e tavolini all'aperto.",
        "source_type": "verified_local",
        "is_weather_dependent": False,
    }


def create_sample_music_option() -> Dict[str, Any]:
    """Returns an authoritative sample live music option."""
    return {
        "id": "count_basie_live_jazz",
        "title": "Count Basie Jazz Club: concerto acustico",
        "category": "musica",
        "venue": "Count Basie Jazz Club",
        "zone": "Centro Storico",
        "address": "Vico Tana 20r",
        "day_time": "Venerdì e Sabato ore 21:15",
        "days_display": "Venerdì e Sabato ore 21:15",
        "verified_url": "https://www.countbasie.it/",
        "source_url": "https://www.countbasie.it/",
        "description": "Serata di musica dal vivo nei caruggi di Prè con ingresso riservato ai soci Arci.",
        "source_type": "live_web",
        "is_weather_dependent": False,
    }


def create_sample_options_list() -> List[Dict[str, Any]]:
    """Returns a curated list of sample options across categories."""
    return [
        create_sample_cinema_option(),
        create_sample_mostra_option(),
        create_sample_walk_option(),
        create_sample_library_option(),
        create_sample_music_option(),
    ]
