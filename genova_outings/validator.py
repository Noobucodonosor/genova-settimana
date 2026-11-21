"""Automated plain writing and WhatsApp formatting validator for Genova Outings.

Enforces:
- Zero em-dashes (\u2014), en-dashes (\u2013), horizontal bars (\u2015), figure dashes (\u2012),
  small em-dashes (\ufe58), fullwidth hyphens (\uff0d).
- Zero occurrences of the word 'date' (\\bdate\\b) or romantic phrasing
  ('appuntamento romantico', 'uscita a due', 'serata galante', etc.).
- Zero marketing puffery / promotional buzzwords
  ('imperdibile', 'splendido', 'magico', 'esperienza unica', 'mozzafiato', etc.).
- Valid WhatsApp formatting: single asterisk bolding *text* (no **),
  no markdown links [text](url) (must be raw https://), no '#' headers.
"""

from __future__ import annotations

import re
from typing import List, Tuple


# Forbidden unicode dashes
PROHIBITED_DASH_RE = re.compile(r"[\u2012\u2013\u2014\u2015\ufe58\uff0d]")

# Banned romance / date framing keywords
ROMANCE_PATTERN = re.compile(
    r"\b(date|appuntament[oi]\s+romantic[oi]|serat[ae]\s+a\s+due|uscit[ae]\s+a\s+due|"
    r"galante|galanti|romantic[oai]|lume\s+di\s+candela|innamorat[oaie]|fidanzat[oaie]|"
    r"flirt|intimit[aà]|cenett[ae]\s+a\s+due)\b",
    re.IGNORECASE,
)

# Banned marketing buzzwords and puffery
PUFFERY_PATTERN = re.compile(
    r"\b(imperdibile|imperdibili|splendid[oai]|magic[oai]|esperienza\s+unica|"
    r"esperienze\s+uniche|mozzafiato|suggestiv[oai]|fiore\s+all\'?occhiello|"
    r"incantevole|incantevoli|immersiv[oai]|da\s+non\s+perdere|straordinari[oai]|"
    r"meraviglios[oai]|favolos[oai]|eccezionale|eccezionali|frizzante|frizzanti|"
    r"incredibile|incredibili|top)\b",
    re.IGNORECASE,
)

# Markdown link pattern [text](url)
MARKDOWN_LINK_PATTERN = re.compile(r"\[.+?\]\(.+?\)")

# Markdown header pattern
MARKDOWN_HEADER_PATTERN = re.compile(r"^#{1,6}\s", re.MULTILINE)


class PlainWritingValidator:
    """Class-based validator for plain-writing and WhatsApp syntax compliance."""

    @classmethod
    def validate(cls, text: str) -> List[Tuple[str, str]]:
        """Validate text against all plain writing and WhatsApp formatting rules.

        Returns a list of tuples: (error_code, detailed_message).
        """
        if not text:
            return []

        errors: List[Tuple[str, str]] = []

        # 1. Prohibited dashes check
        dash_matches = PROHIBITED_DASH_RE.findall(text)
        if dash_matches:
            errors.append(
                (
                    "FORBIDDEN_DASH",
                    f"Found prohibited long dashes ({len(dash_matches)}): {dash_matches}",
                )
            )

        # 2. Romantic framing / date check
        romance_matches = ROMANCE_PATTERN.findall(text)
        if romance_matches:
            errors.append(
                (
                    "ROMANTIC_FRAMING",
                    f"Found prohibited romantic/date keywords: {romance_matches}",
                )
            )

        # 3. Marketing buzzwords / puffery check
        puffery_matches = PUFFERY_PATTERN.findall(text)
        if puffery_matches:
            errors.append(
                (
                    "MARKETING_PUFFERY",
                    f"Found prohibited marketing buzzwords: {puffery_matches}",
                )
            )

        # 4. WhatsApp markdown bolding check: disallow double asterisks
        if "**" in text:
            errors.append(
                (
                    "DOUBLE_ASTERISKS",
                    "Found double asterisks '**'. WhatsApp uses single '*bold*'",
                )
            )

        # 5. WhatsApp markdown bolding check: balanced single asterisks
        asterisk_count = text.count("*")
        if asterisk_count % 2 != 0:
            errors.append(
                (
                    "UNBALANCED_ASTERISKS",
                    f"Unbalanced '*' markers for WhatsApp bolding ({asterisk_count} found)",
                )
            )

        # 6. Prohibit markdown headers
        if MARKDOWN_HEADER_PATTERN.search(text):
            errors.append(
                (
                    "MARKDOWN_HEADERS",
                    "Found markdown headers (#) not supported in WhatsApp",
                )
            )

        # 7. Prohibit markdown links
        if MARKDOWN_LINK_PATTERN.search(text):
            errors.append(
                (
                    "MARKDOWN_LINKS",
                    "Found markdown [text](url) links. WhatsApp requires raw URLs",
                )
            )

        return errors


def validate_plain_writing(text: str) -> Tuple[bool, List[str]]:
    """Validate text against all plain-writing rules and WhatsApp conventions.

    Returns:
        (is_valid, errors_list)
        is_valid: True if 100% compliant, False otherwise.
        errors_list: Empty list if valid, or list of human-readable violation descriptions.
    """
    raw_errors = PlainWritingValidator.validate(text)
    if not raw_errors:
        return True, []

    formatted_errors = [f"{code}: {msg}" for code, msg in raw_errors]
    return False, formatted_errors


def sanitize_for_whatsapp(text: str) -> str:
    """Sanitize arbitrary input text to conform to WhatsApp plain-writing rules.

    - Replaces em-dashes and long dashes with colons or commas.
    - Replaces Italian 'le date' with 'i giorni' and standalone 'date' with 'giorni'.
    - Replaces double asterisks '**' with single asterisks '*'.
    - Converts markdown links [title](url) to 'title: url'.
    - Strips markdown header hashes '#'.
    - Removes trailing punctuation from raw URLs.
    - Removes known puffery terms.
    - Cleans and normalizes redundant punctuation and whitespace.
    """
    if not text:
        return ""

    cleaned = str(text)

    # 1. Replace prohibited dashes with ': '
    cleaned = re.sub(r"\s*[\u2012\u2013\u2014\u2015\ufe58\uff0d]+\s*", ": ", cleaned)

    # 2. Convert markdown links [label](url) -> label: url
    cleaned = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1: \2", cleaned)

    # 3. Remove leading markdown header marks
    cleaned = re.sub(r"^#{1,6}\s*", "", cleaned, flags=re.MULTILINE)

    # 4. Convert double asterisks to single asterisks
    cleaned = cleaned.replace("**", "*")

    # 5. Replace Italian 'le date' and word 'date'
    cleaned = re.sub(r"\ble\s+date\b", "i giorni", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bdate\b", "giorni", cleaned, flags=re.IGNORECASE)

    # 6. Replace explicit romantic phrases
    cleaned = re.sub(
        r"\b(appuntament[oi]\s+romantic[oi]|serat[ae]\s+a\s+due|uscit[ae]\s+a\s+due|cenett[ae]\s+a\s+due)\b",
        "uscita informale",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"\blume\s+di\s+candela\b", "atmosfera serale", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\b(galante|galanti|romantic[oai])\b", "accogliente", cleaned, flags=re.IGNORECASE)

    # 7. Remove marketing puffery keywords
    cleaned = PUFFERY_PATTERN.sub("", cleaned)

    # 8. Clean redundant colons and whitespace
    cleaned = re.sub(r":(?:\s*:)+", ":", cleaned)
    cleaned = re.sub(r"\s+([,.:;])", r"\1", cleaned)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)

    # 9. Clean trailing punctuation from URLs
    def _strip_url_trailing(match: re.Match[str]) -> str:
        url = match.group(0)
        trailing = ""
        while url and url[-1] in ".,;:!?)":
            trailing = url[-1] + trailing
            url = url[:-1]
        return url + trailing

    cleaned = re.sub(r"https?://[^\s]+", _strip_url_trailing, cleaned)

    return cleaned.strip()


# Compatibility alias
sanitize_plain_writing = sanitize_for_whatsapp
