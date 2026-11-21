"""Unit tests for genova_outings.validator module.

Tests automated plain-writing rules, prohibited dash detection, date/romance detection,
puffery detection, WhatsApp markdown syntax validation, and sanitization helpers.
"""

import unittest
from genova_outings.validator import (
    PlainWritingValidator,
    sanitize_for_whatsapp,
    sanitize_plain_writing,
    validate_plain_writing,
)


class TestValidatorPlainWriting(unittest.TestCase):
    """Test suite for PlainWritingValidator and validate_plain_writing."""

    def test_compliant_informal_message_passes(self):
        """Clean message passes validation with zero errors."""
        msg = (
            "Ciao! Ho visto questa cosa a Genova questa settimana che sembra interessante:\n\n"
            "🎬 *Cinema Sivori: rassegna cinema d'autore*\n"
            "📍 Salita Santa Caterina 12 (Centro)\n"
            "🗓️ Mercoledì alle 21:15\n"
            "Proiezione in lingua originale con sottotitoli in italiano.\n"
            "Info: https://circuitocinemagenova.com/sivori/\n\n"
            "Dimmi se ti ispira!"
        )
        is_valid, errors = validate_plain_writing(msg)
        self.assertTrue(is_valid, f"Compliant message should pass, got errors: {errors}")
        self.assertEqual(errors, [])

    def test_detects_prohibited_dashes(self):
        """Detects various unicode dashes (em-dash, en-dash, horizontal bar, figure dash)."""
        dashes = [
            ("\u2014", "em-dash"),
            ("\u2013", "en-dash"),
            ("\u2015", "horizontal bar"),
            ("\u2012", "figure dash"),
            ("\ufe58", "small em-dash"),
            ("\uff0d", "fullwidth hyphen-minus"),
        ]
        for char, name in dashes:
            text = f"Mostra d'arte {char} Palazzo Ducale"
            is_valid, errors = validate_plain_writing(text)
            self.assertFalse(is_valid, f"Failed to detect {name} ({ord(char):04x})")
            raw_errors = PlainWritingValidator.validate(text)
            error_codes = [code for code, _ in raw_errors]
            self.assertIn("FORBIDDEN_DASH", error_codes)

    def test_detects_date_word_case_insensitive(self):
        """Detects standalone word 'date' with word boundaries in all cases."""
        bad_examples = [
            "Ecco un date carino per stasera",
            "Questo è un DATE speciale",
            "Serata Date a Genova",
            "Organizziamo un DaTe informale",
        ]
        for bad in bad_examples:
            is_valid, errors = validate_plain_writing(bad)
            self.assertFalse(is_valid, f"Failed to reject: {bad}")
            raw = PlainWritingValidator.validate(bad)
            codes = [c for c, _ in raw]
            self.assertIn("ROMANTIC_FRAMING", codes)

    def test_date_as_substring_is_allowed(self):
        """Words containing 'date' as a substring (aggiornate, candidate, mandate, datteri) must PASS."""
        valid_examples = [
            "Informazioni aggiornate per la programmazione.",
            "Opzioni candidate per il pomeriggio.",
            "Mandate un messaggio se interessati.",
            "Degustazione con noci e datteri.",
        ]
        for val in valid_examples:
            raw = PlainWritingValidator.validate(val)
            romance_codes = [c for c, _ in raw if c == "ROMANTIC_FRAMING"]
            self.assertEqual(
                romance_codes,
                [],
                f"Substring false alarm on: '{val}'",
            )

    def test_detects_romantic_framing(self):
        """Detects explicit romantic framing phrases."""
        bad_examples = [
            "Un appuntamento romantico al tramonto",
            "Una romantica uscita a due nei caruggi",
            "Serata galante sul mare",
            "Cenetta a due a Boccadasse",
            "Cena a lume di candela",
        ]
        for bad in bad_examples:
            is_valid, _ = validate_plain_writing(bad)
            self.assertFalse(is_valid, f"Romantic phrase should fail: {bad}")

    def test_detects_marketing_puffery(self):
        """Detects marketing buzzwords and promotional puffery."""
        puffery_words = [
            "imperdibile",
            "mozzafiato",
            "esperienza unica",
            "splendido",
            "magico",
            "suggestivo",
            "incantevole",
            "fiore all'occhiello",
            "immersivo",
            "da non perdere",
            "straordinario",
            "meraviglioso",
            "favoloso",
            "eccezionale",
            "incredibile",
            "top",
        ]
        for word in puffery_words:
            bad_text = f"Una proposta {word} per il weekend."
            is_valid, _ = validate_plain_writing(bad_text)
            self.assertFalse(is_valid, f"Puffery '{word}' should fail")

    def test_detects_invalid_whatsapp_syntax(self):
        """Detects double asterisks, markdown links, headers, and unbalanced asterisks."""
        # Double asterisks
        bad_bold = "**Titolo in grassetto standard**"
        is_valid, _ = validate_plain_writing(bad_bold)
        self.assertFalse(is_valid)

        # Markdown header
        bad_header = "# Titolo Sezione"
        is_valid, _ = validate_plain_writing(bad_header)
        self.assertFalse(is_valid)

        # Markdown link
        bad_link = "Info: [Palazzo Ducale](https://palazzoducale.genova.it)"
        is_valid, _ = validate_plain_writing(bad_link)
        self.assertFalse(is_valid)

        # Unbalanced single asterisks
        bad_unbalanced = "*Titolo senza chiusura"
        is_valid, _ = validate_plain_writing(bad_unbalanced)
        self.assertFalse(is_valid)

    def test_multiple_violations_reported_together(self):
        """Reports all distinct violations present in text."""
        multi_bad = "# Sezione Weekend\nUn date romantico — una mostra **imperdibile** e mozzafiato!"
        raw_errors = PlainWritingValidator.validate(multi_bad)
        codes = [c for c, _ in raw_errors]
        self.assertIn("FORBIDDEN_DASH", codes)
        self.assertIn("ROMANTIC_FRAMING", codes)
        self.assertIn("MARKETING_PUFFERY", codes)
        self.assertIn("DOUBLE_ASTERISKS", codes)
        self.assertIn("MARKDOWN_HEADERS", codes)
        self.assertGreaterEqual(len(codes), 4)

    def test_empty_string_handled_safely(self):
        """Empty string returns valid with no errors."""
        is_valid, errors = validate_plain_writing("")
        self.assertTrue(is_valid)
        self.assertEqual(errors, [])


class TestSanitizer(unittest.TestCase):
    """Test suite for sanitize_for_whatsapp and sanitize_plain_writing."""

    def test_sanitize_replaces_dashes(self):
        """Replaces long dashes with colons."""
        raw = "Mostra fotografica — Palazzo Reale – Sala da ballo"
        cleaned = sanitize_for_whatsapp(raw)
        self.assertNotIn("—", cleaned)
        self.assertNotIn("–", cleaned)
        self.assertIn(":", cleaned)

    def test_sanitize_removes_double_asterisks(self):
        """Converts double asterisks to single asterisks."""
        raw = "**Cinema Sivori**"
        cleaned = sanitize_for_whatsapp(raw)
        self.assertNotIn("**", cleaned)
        self.assertEqual(cleaned, "*Cinema Sivori*")

    def test_sanitize_converts_markdown_links(self):
        """Converts [title](url) to title: url."""
        raw = "Consulta [Circuito Cinema](https://circuitocinemagenova.com)"
        cleaned = sanitize_for_whatsapp(raw)
        self.assertNotIn("[", cleaned)
        self.assertNotIn("](", cleaned)
        self.assertIn("Circuito Cinema: https://circuitocinemagenova.com", cleaned)

    def test_sanitize_replaces_date_and_le_date(self):
        """Replaces 'le date' with 'i giorni' and 'date' with 'giorni'."""
        raw = "Ecco le date della mostra e il date speciale"
        cleaned = sanitize_for_whatsapp(raw)
        import re
        self.assertIsNone(re.search(r"\bdate\b", cleaned, re.IGNORECASE))
        self.assertIn("i giorni", cleaned)

    def test_sanitize_strips_url_trailing_punctuation(self):
        """Strips trailing dots and commas from URLs."""
        raw = "Info su https://circuitocinemagenova.com/sivori/."
        cleaned = sanitize_for_whatsapp(raw)
        self.assertTrue(cleaned.endswith("https://circuitocinemagenova.com/sivori/."))
        # Verify the URL portion does not keep the dot internally attached to the protocol host
        # The URL itself should end with slash
        self.assertIn("https://circuitocinemagenova.com/sivori/", cleaned)

    def test_sanitize_strips_puffery_buzzwords(self):
        """Removes puffery terms without leaving double spaces."""
        raw = "Una mostra imperdibile con vista mozzafiato da Spianata"
        cleaned = sanitize_for_whatsapp(raw)
        self.assertNotIn("imperdibile", cleaned.lower())
        self.assertNotIn("mozzafiato", cleaned.lower())
        self.assertNotIn("  ", cleaned)

    def test_compatibility_alias(self):
        """sanitize_plain_writing is identical to sanitize_for_whatsapp."""
        raw = "Film — Mercoledì"
        self.assertEqual(sanitize_plain_writing(raw), sanitize_for_whatsapp(raw))


if __name__ == "__main__":
    unittest.main()
