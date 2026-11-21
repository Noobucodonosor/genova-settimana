"""Unit tests for genova_outings/verifier.py.

Verifies:
1. Negative filters: explicitly blacklisting Villa Croce (closed for PNRR works) and other non-informal venues.
2. Plain-writing text sanitization (zero em/en dashes, no 'date' word).
3. HTTP reachability probing and caching.
4. Weather dependency detection.
5. verify_outing pipeline behavior.
"""

import unittest
from unittest.mock import patch, MagicMock
from genova_outings.models import OutingCategory, OutingOption
from genova_outings.verifier import (
    clean_url,
    check_url_reachability,
    get_verified_url_fallback,
    is_blacklisted_venue,
    is_civic_museum_closed_on_day,
    is_weather_dependent_venue,
    probe_url_reachability,
    sanitize_text,
    verify_outing,
    verify_venue,
    VerificationResult,
)


class TestNegativeFilters(unittest.TestCase):
    """Test blacklist logic, specifically Villa Croce and non-informal institutions."""

    def test_villa_croce_blacklisted_variations(self):
        # Explicit mandatory check: Villa Croce closed for PNRR works
        self.assertTrue(is_blacklisted_venue("Museo d'Arte Contemporanea di Villa Croce"))
        self.assertTrue(is_blacklisted_venue("Museo d'arte contemporanea Villa Croce"))
        self.assertTrue(is_blacklisted_venue("Villa Croce"))
        self.assertTrue(is_blacklisted_venue("Biblioteca del Museo civico di Arte contemporanea di Villa Croce"))
        self.assertTrue(is_blacklisted_venue("Mostra temporanea", url="https://museidigenova.it/it/museo-darte-contemporanea-di-villa-croce"))

    def test_croce_medical_and_sports_filtered(self):
        # Non-informal venues with 'croce' in their name
        self.assertTrue(is_blacklisted_venue("Pubblica Assistenza Croce Verde Sestri Ponente"))
        self.assertTrue(is_blacklisted_venue("Croce Rossa Italiana"))
        self.assertTrue(is_blacklisted_venue("Croce Bianca Bolzaneto"))
        self.assertTrue(is_blacklisted_venue("Stadio Beppe Croce"))
        self.assertTrue(is_blacklisted_venue("Stadio Giuseppe Sivori"))

    def test_non_informal_institutions_filtered(self):
        self.assertTrue(is_blacklisted_venue("Ospedale Policlinico San Martino"))
        self.assertTrue(is_blacklisted_venue("Tribunale di Genova"))
        self.assertTrue(is_blacklisted_venue("Liceo Artistico Emanuele Luzzati"))
        self.assertTrue(is_blacklisted_venue("Cimitero Monumentale di Staglieno"))

    def test_closure_notices_in_description_filtered(self):
        self.assertTrue(is_blacklisted_venue(
            "Galleria Civica",
            description="Chiuso al pubblico fino a data da destinarsi per lavori PNRR."
        ))
        self.assertTrue(is_blacklisted_venue(
            "Spazio Espositivo",
            description="Attività sospesa per restauro della sede."
        ))

    def test_permanently_closed_venues_filtered(self):
        # Teatro Cantero in Chiavari closed permanently in Dec 2017
        self.assertTrue(is_blacklisted_venue("Cinema Teatro Cantero"))
        self.assertTrue(is_blacklisted_venue("Teatro Cantero"))
        self.assertTrue(is_blacklisted_venue("Film al Cantero", url="http://www.cantero.it"))

    def test_summer_arenas_in_november_filtered(self):
        # Seasonal summer-only open air cinemas
        self.assertTrue(is_blacklisted_venue("Circuito sul mare"))
        self.assertTrue(is_blacklisted_venue("Arena Sturla"))
        self.assertTrue(is_blacklisted_venue("Cinema Estivo", url="https://circuitocinemagenova.com/circuito-sul-mare/"))

    def test_legitimate_venues_not_blacklisted(self):
        # Genuine active leisure venues must NOT be blacklisted
        self.assertFalse(is_blacklisted_venue("Cinema Sivori"))
        self.assertFalse(is_blacklisted_venue("Cinema America"))
        self.assertFalse(is_blacklisted_venue("Cineclub Nickelodeon"))
        self.assertFalse(is_blacklisted_venue("Palazzo Ducale"))
        self.assertFalse(is_blacklisted_venue("Biblioteca Civica Berio"))
        self.assertFalse(is_blacklisted_venue("Spianata Castelletto"))
        self.assertFalse(is_blacklisted_venue("Count Basie Jazz Club"))
        self.assertFalse(is_blacklisted_venue("La Claque in Agorà"))


class TestSanitization(unittest.TestCase):
    """Test text sanitization and plain-writing compliance."""

    def test_sanitize_em_dash(self):
        raw = "Palazzo Ducale — Grandi Mostre & Torre Grimaldina"
        cleaned = sanitize_text(raw)
        self.assertNotIn("—", cleaned)
        self.assertNotIn("–", cleaned)
        self.assertIn("Palazzo Ducale: Grandi Mostre & Torre Grimaldina", cleaned)

    def test_sanitize_en_dash(self):
        raw = "Orari autunnali: 16:00 – 18:30"
        cleaned = sanitize_text(raw)
        self.assertNotIn("–", cleaned)
        self.assertNotIn("—", cleaned)

    def test_sanitize_banned_date_word(self):
        raw = "Ecco le date per la mostra di novembre"
        cleaned = sanitize_text(raw)
        self.assertNotIn("date", cleaned.lower())
        self.assertIn("giorni", cleaned)

    def test_clean_url(self):
        self.assertEqual(clean_url("https://example.com/test."), "https://example.com/test")
        self.assertEqual(clean_url("https://circuitocinemagenova.com/sivori/;"), "https://circuitocinemagenova.com/sivori/")
        self.assertEqual(clean_url("www.cineclubnickelodeon.it"), "https://www.cineclubnickelodeon.it")

    def test_clean_url_robustness(self):
        self.assertEqual(clean_url('"https://circuitocinemagenova.com/sivori/"'), "https://circuitocinemagenova.com/sivori/")
        self.assertEqual(clean_url("'<https://palazzoducale.genova.it/mostre/>'"), "https://palazzoducale.genova.it/mostre/")
        self.assertEqual(clean_url(12345), "")
        self.assertEqual(clean_url(None), "")

    def test_sanitize_extended_dashes_and_colons(self):
        # Figure dash and small em dash
        self.assertNotIn("\u2012", sanitize_text("Palazzo Ducale \u2012 Mostra"))
        self.assertNotIn("\ufe58", sanitize_text("Palazzo Ducale \ufe58 Mostra"))
        # Triple dashes must not produce double colons
        tri = sanitize_text("Palazzo Ducale ——— Mostra Fotografica")
        self.assertNotIn("::", tri)
        self.assertIn("Palazzo Ducale: Mostra Fotografica", tri)
        # Leading and trailing dashes stripped
        lead_trail = sanitize_text("— Grande Mostra —")
        self.assertFalse(lead_trail.startswith(":"))
        self.assertFalse(lead_trail.endswith(":"))
        self.assertEqual(lead_trail, "Grande Mostra")


class TestWeatherDependency(unittest.TestCase):
    """Test weather dependency tagging for outdoor venues."""

    def test_outdoor_promenades(self):
        self.assertTrue(is_weather_dependent_venue("Spianata Castelletto", OutingCategory.PASSEGGIATA))
        self.assertTrue(is_weather_dependent_venue("Passeggiata Anita Garibaldi", OutingCategory.PASSEGGIATA, "Nervi"))
        self.assertTrue(is_weather_dependent_venue("Borgo di Boccadasse", OutingCategory.PASSEGGIATA))
        self.assertTrue(is_weather_dependent_venue("Parco delle Mura e Righi", OutingCategory.PASSEGGIATA))

    def test_indoor_venues(self):
        self.assertFalse(is_weather_dependent_venue("Cinema Sivori", OutingCategory.CINEMA, "Centro"))
        self.assertFalse(is_weather_dependent_venue("Palazzo Ducale", OutingCategory.MOSTRA, "Centro"))
        self.assertFalse(is_weather_dependent_venue("Biblioteca Berio", OutingCategory.BIBLIOTECA, "Centro"))
        self.assertFalse(is_weather_dependent_venue("Count Basie Jazz Club", OutingCategory.MUSICA, "Centro"))


class TestVerificationPipeline(unittest.TestCase):
    """Test verify_outing and Verifier class."""

    def test_verify_valid_outing(self):
        valid_opt = OutingOption(
            id="sivori",
            title="Cinema Sivori: Programmazione",
            category=OutingCategory.CINEMA,
            venue="Cinema Sivori",
            zone="Centro",
            day_time="Mercoledì ore 21:00",
            verified_url="https://circuitocinemagenova.com/sivori/",
            description="Film in lingua originale.",
        )
        res = verify_outing(valid_opt, check_network=False)
        self.assertTrue(res.is_valid)
        self.assertEqual(res.checked_url, "https://circuitocinemagenova.com/sivori/")

    def test_verify_rejects_villa_croce(self):
        villa_croce = OutingOption(
            id="villa_croce_poi",
            title="Museo d'Arte Contemporanea Villa Croce",
            category=OutingCategory.MOSTRA,
            venue="Museo Villa Croce",
            zone="Carignano",
            day_time="Chiuso",
            verified_url="https://www.museidigenova.it/it/museo-darte-contemporanea-di-villa-croce",
            description="Museo civico.",
        )
        res = verify_outing(villa_croce, check_network=False)
        self.assertFalse(res.is_valid)
        self.assertIn("Villa Croce", res.reason)

    def test_verify_rejects_missing_url(self):
        no_url = OutingOption(
            id="no_url_opt",
            title="Posto senza URL",
            category=OutingCategory.RITROVO,
            venue="Locale Anonimo",
            zone="Centro",
            day_time="Sempre",
            verified_url="",
            description="Descrizione.",
        )
        res = verify_outing(no_url, check_network=False)
        self.assertFalse(res.is_valid)
        self.assertIn("verified_url", res.reason)

    def test_probe_url_reachability_mock(self):
        with patch("urllib.request.urlopen") as mock_open:
            mock_resp = MagicMock()
            mock_resp.status = 200
            mock_resp.__enter__.return_value = mock_resp
            mock_open.return_value = mock_resp

            ok, code, msg = probe_url_reachability("https://test.genova.it/api", use_cache=False)
            self.assertTrue(ok)
            self.assertEqual(code, 200)


class TestMuseumSchedule(unittest.TestCase):
    """Test civic museum day-of-week closure verification."""

    def test_monday_civic_museum_closed(self):
        self.assertTrue(is_civic_museum_closed_on_day("Musei di Strada Nuova", 0))
        self.assertTrue(is_civic_museum_closed_on_day("Musei di Strada Nuova", "lunedi"))
        self.assertTrue(is_civic_museum_closed_on_day("Musei di Strada Nuova", "monday"))
        self.assertTrue(is_civic_museum_closed_on_day("Palazzo Rosso", 0))
        self.assertTrue(is_civic_museum_closed_on_day("Castello D'Albertis", "lun"))

    def test_tuesday_through_sunday_civic_museum_open(self):
        # Days 1 through 6 are open
        for day in [1, 2, 3, 4, 5, 6]:
            self.assertFalse(
                is_civic_museum_closed_on_day("Musei di Strada Nuova", day),
                f"Musei di Strada Nuova should be OPEN on day {day}"
            )
        self.assertFalse(is_civic_museum_closed_on_day("Musei di Strada Nuova", "martedi"))
        self.assertFalse(is_civic_museum_closed_on_day("Musei di Strada Nuova", "sabato"))
        self.assertFalse(is_civic_museum_closed_on_day("Musei di Strada Nuova", "domenica"))

    def test_non_civic_museum_not_affected(self):
        self.assertFalse(is_civic_museum_closed_on_day("Cinema Sivori", 0))
        self.assertFalse(is_civic_museum_closed_on_day("Palazzo Ducale", 0))


class TestCompatibilityHelpers(unittest.TestCase):
    """Test compatibility exports expected by conftest and E2E suites."""

    def test_check_url_reachability(self):
        with patch("genova_outings.verifier.probe_url_reachability") as mock_probe:
            mock_probe.return_value = (True, 200, "OK")
            self.assertTrue(check_url_reachability("https://circuitocinemagenova.com/sivori/"))

            mock_probe.return_value = (False, 404, "Not Found")
            self.assertFalse(check_url_reachability("https://visitgenoa.it/404"))

    def test_verify_venue(self):
        # Blacklisted venue must return False
        self.assertFalse(verify_venue("https://www.museidigenova.it/it/museo-darte-contemporanea-di-villa-croce"))
        self.assertFalse(verify_venue("Villa Croce"))
        self.assertFalse(verify_venue("Cinema Teatro Cantero"))
        self.assertFalse(verify_venue("Circuito sul mare"))

    def test_get_verified_url_fallback(self):
        fb = get_verified_url_fallback("nonexistent_park", "https://dead-domain-123.com")
        self.assertTrue(fb.startswith("https://www.visitgenoa.it") or fb.startswith("https://"))


if __name__ == "__main__":
    unittest.main()
