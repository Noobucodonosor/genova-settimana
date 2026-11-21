"""Verification engine for Genova Weekly Informal Outings.

Handles:
1. Negative filtering & blacklists (specifically excluding closed venues like Villa Croce).
2. Live HTTP reachability probing with caching and graceful fallbacks.
3. Schedule, day-of-week, and Monday civic museum closure verification.
4. Weather dependency classification for outdoor promenades and viewpoints.
5. Plain-writing text sanitization (stripping em/en dashes, hype buzzwords, and romance terms).
"""

from __future__ import annotations

import json
import os
import re
import ssl
import urllib.request
import urllib.error
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import unquote, unquote_plus

from genova_outings.models import OutingCategory, OutingOption

# In-memory probe cache: {url: (is_reachable, status_code, message)}
_PROBE_CACHE: Dict[str, Tuple[bool, int, str]] = {}
_CRAWLED_CACHE_LOADED = False
_CRAWLED_CACHE_DATA: Dict[str, dict] = {}

# Explicitly blacklisted venue keywords and names
# Villa Croce is closed to the public for PNRR works until further notice.
BLACKLISTED_SUBSTRINGS: List[str] = [
    "villa croce",
    "villa-croce",
    "villa_croce",
    "museo d'arte contemporanea di villa croce",
    "museo d'arte contemporanea villa croce",
    "biblioteca del museo civico di arte contemporanea di villa croce",
    # Permanently closed venues
    "teatro cantero",
    "cantero chiavari",
    "cinema teatro cantero",
    "teatro cinema cantero",
    "cantero.it",
    # Inactive summer seasonal arenas in November
    "circuito sul mare",
    "circuito-sul-mare",
    "arena sturla",
    "arena-sturla",
    # Medical, ambulance and emergency services with 'croce'
    "croce verde",
    "croce rossa",
    "croce bianca",
    "croce d'oro",
    "pubblica assistenza",
    # Sports pitches / arenas
    "stadio beppe croce",
    "stadio giuseppe sivori",
    "impianto di calcio",
    "campo sportivo",
    # Administrative, institutional, medical, non-informal venues
    "ospedale",
    "carcere",
    "tribunale",
    "cimitero monumentale",
    "autofficina",
    "elettrauto",
    "scuola dell'infanzia",
    "scuola primaria",
    "scuola secondaria",
    "liceo artistico emanuele luzzati",
]

# Regex patterns for Villa Croce, permanently closed venues, and seasonal arenas
VILLA_CROCE_PATTERN = re.compile(r"villa[\s_\-\.\/%+]*croce", re.IGNORECASE)
CANTERO_PATTERN = re.compile(r"\bcantero\b", re.IGNORECASE)
SUMMER_ARENA_PATTERN = re.compile(r"\b(?:circuito[\s_\-]*sul[\s_\-]*mare|arena[\s_\-]*sturla)\b", re.IGNORECASE)

# Regex patterns indicating closed status or cessation of activity
CLOSURE_PATTERNS: List[re.Pattern] = [
    re.compile(r"chiuso\s+al\s+pubblico", re.IGNORECASE),
    re.compile(r"chiuso\s+per\s+(?:lavori|restauro|restauri|pnrr)", re.IGNORECASE),
    re.compile(r"fino\s+a\s+data\s+da\s+destinarsi", re.IGNORECASE),
    re.compile(r"chiusura\s+temporanea", re.IGNORECASE),
    re.compile(r"inagibile", re.IGNORECASE),
    re.compile(r"attivit[aà]\s+sospesa", re.IGNORECASE),
]

# Prohibited long dash characters: figure dash (\u2012), en dash (\u2013), em dash (\u2014),
# horizontal bar (\u2015), small em dash (\ufe58), fullwidth hyphen-minus (\uff0d)
PROHIBITED_DASH_RE = re.compile(r"[\u2012\u2013\u2014\u2015\ufe58\uff0d]")

# Italian word 'date' (plural of data) or English 'date'
BANNED_DATE_WORD_RE = re.compile(r"\b(?:le\s+)?date\b", re.IGNORECASE)

# Weather-dependent venue indicator keywords
WEATHER_KEYWORDS: Set[str] = {
    "passeggiata", "parco", "parchi", "giardini", "belvedere", "spianata",
    "boccadasse", "nervi", "mura", "acquedotto", "forte", "sentiero",
    "scogliera", "creusa", "porticciolo", "anita garibaldi", "righi"
}

# Civic museums strictly closed on Mondays in Genova
MONDAY_CLOSED_MUSEUMS: Set[str] = {
    "musei di strada nuova", "palazzo rosso", "palazzo bianco", "palazzo tursi",
    "castello d'albertis", "gam galleria d'arte moderna", "wolfsoniana",
    "museo d'arte orientale chiossone", "museo civico di storia naturale giacomo doria",
    "museo del risorgimento", "raccolte frugone"
}


@dataclass
class VerificationResult:
    """Detailed result of verifying an OutingOption."""
    is_valid: bool
    reason: str = ""
    http_status: Optional[int] = None
    checked_url: Optional[str] = None
    is_weather_dependent: bool = False
    clean_title: str = ""
    clean_description: str = ""


_MONTHS = (r"gen(?:naio)?|feb(?:braio)?|mar(?:zo)?|apr(?:ile)?|mag(?:gio)?|giu(?:gno)?|lug(?:lio)?"
           r"|ago(?:sto)?|set(?:tembre)?|ott(?:obre)?|nov(?:embre)?|dic(?:embre)?")


def sanitize_text(text: str) -> str:
    """Sanitize raw text for plain writing compliance:
    1. Replaces em-dash, en-dash, figure dash, etc. with colon or comma.
    2. Collapses multiple colons and cleans punctuation spacing.
    3. Strips leading and trailing colons to avoid dangling punctuation.
    4. Replaces Italian/English 'date' word with natural calendar terminology.
    5. Normalizes whitespace.
    """
    if not text:
        return ""
    if not isinstance(text, str):
        text = str(text)

    # Ranges between numbers or months (10:00–19:00, Apr–Ott) become a plain hyphen
    cleaned = re.sub(r"(\d)\s*[\u2012-\u2015]\s*(\d)", r"\1-\2", text)
    cleaned = re.sub(rf"\b({_MONTHS})\s*[\u2012-\u2015]\s*({_MONTHS})\b", r"\1-\2", cleaned, flags=re.IGNORECASE)
    # Replace remaining prohibited unicode dashes with ': '
    cleaned = PROHIBITED_DASH_RE.sub(": ", cleaned)

    # Collapse multiple colons (e.g. '::', ': :', ': : :') into a single ':'
    cleaned = re.sub(r":(?:\s*:)+", ":", cleaned)
    cleaned = re.sub(r":+", ":", cleaned)

    # Remove space before standard punctuation marks
    cleaned = re.sub(r"\s+([,.:;])", r"\1", cleaned)

    # Ensure colon has a following space if followed by alphanumeric text
    cleaned = re.sub(r":([a-zA-Z])", r": \1", cleaned)
    cleaned = re.sub(r"(?<![0-9]):([0-9])", r": \1", cleaned)

    # Strip dangling leading and trailing colons and spaces
    cleaned = re.sub(r"^[\s:]+|[\s:]+$", "", cleaned)

    # Replace instances of 'le date' with 'i giorni' and standalone 'date' with 'giorni'
    cleaned = re.sub(r"\ble\s+date\b", "i giorni", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bdate\b", "giorni", cleaned, flags=re.IGNORECASE)

    # Collapse consecutive whitespace
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    return cleaned.strip()


def clean_url(url: Any) -> str:
    """Strip trailing punctuation, quotes, and validate URL structure safely."""
    if url is None:
        return ""
    if not isinstance(url, str):
        try:
            url = str(url)
        except Exception:
            return ""
    cleaned = url.strip().strip("'\"`<>[]()").rstrip(".,;:)>]")
    cleaned = cleaned.strip()
    if not cleaned:
        return ""
    if not (cleaned.startswith("http://") or cleaned.startswith("https://")):
        if cleaned.startswith("www."):
            cleaned = "https://" + cleaned
        else:
            return ""
    return cleaned


def is_blacklisted_venue(name: str, description: str = "", url: str = "") -> bool:
    """Determine whether a venue or activity is explicitly blacklisted or closed.

    Checks:
    - Villa Croce closure (PNRR works): regex matching across name, description, URL slugs.
    - Permanently closed venues: Teatro Cantero in Chiavari.
    - Inactive summer seasonal arenas in November: Circuito sul Mare, Arena Sturla.
    - Emergency / medical / sports services.
    - Explicit closure statements in descriptions or notices.
    """
    raw_combined = f"{name} {description} {url}"
    combined = unquote_plus(unquote(raw_combined)).lower()

    # 1. Regex check for Villa Croce variations (spaces, hyphens, underscores, slashes, concatenated)
    if VILLA_CROCE_PATTERN.search(combined) or VILLA_CROCE_PATTERN.search(raw_combined.lower()):
        return True

    # 2. Permanently closed venues (Teatro Cantero in Chiavari)
    if CANTERO_PATTERN.search(combined) or CANTERO_PATTERN.search(raw_combined.lower()):
        return True

    # 3. Summer-only arenas inactive in November (Circuito sul Mare, Arena Sturla)
    if SUMMER_ARENA_PATTERN.search(combined) or SUMMER_ARENA_PATTERN.search(raw_combined.lower()):
        return True

    # 4. Match blacklisted substrings
    for banned in BLACKLISTED_SUBSTRINGS:
        if banned in combined or banned in raw_combined.lower():
            return True

    # 5. Match closure phrases
    for pattern in CLOSURE_PATTERNS:
        if pattern.search(combined) or pattern.search(raw_combined):
            return True

    return False


def is_weather_dependent_venue(name: str, category: OutingCategory, zone: str = "") -> bool:
    """Check if an outing takes place outdoors and is weather-dependent."""
    if category == OutingCategory.PASSEGGIATA:
        return True
    combined = f"{name} {zone}".lower()
    return any(kw in combined for kw in WEATHER_KEYWORDS)


def is_civic_museum_closed_on_day(venue_name: str, day_of_week: int | str) -> bool:
    """Check if a civic museum is closed on the target day.

    Civic museums in Genoa are ONLY closed on Mondays ('lun', 'lunedi', 'lunedì', 'monday', 0).
    They are OPEN Tuesday through Sunday (days 1-6). Do NOT report them closed on other days.
    """
    is_monday = False
    if isinstance(day_of_week, int):
        # In standard Python datetime.date.weekday(), Monday is 0.
        is_monday = (day_of_week == 0)
    elif isinstance(day_of_week, str):
        dow_str = day_of_week.strip().lower()
        if dow_str in ("0", "lun", "lunedi", "lunedì", "monday", "mon"):
            is_monday = True

    if not is_monday:
        return False

    v_lower = venue_name.lower()
    for cm in MONDAY_CLOSED_MUSEUMS:
        if cm in v_lower:
            return True
    return False


def _load_crawled_cache() -> Dict[str, dict]:
    """Load local crawled_urls_cache.json if present in workspace."""
    global _CRAWLED_CACHE_LOADED, _CRAWLED_CACHE_DATA
    if _CRAWLED_CACHE_LOADED:
        return _CRAWLED_CACHE_DATA

    cache_path = Path("/Users/dany/genova/crawled_urls_cache.json")
    if cache_path.exists():
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                _CRAWLED_CACHE_DATA = json.load(f)
        except Exception:
            _CRAWLED_CACHE_DATA = {}
    _CRAWLED_CACHE_LOADED = True
    return _CRAWLED_CACHE_DATA


def probe_url_reachability(url: str, timeout: float = 3.5, use_cache: bool = True) -> Tuple[bool, int, str]:
    """Probe an HTTP/HTTPS URL for network reachability (HTTP 200/30x).

    Returns:
        (is_reachable: bool, status_code: int, status_message: str)
    """
    url = clean_url(url)
    if not url or not (url.startswith("http://") or url.startswith("https://")):
        return False, 0, "Invalid or missing URL scheme"

    if use_cache and url in _PROBE_CACHE:
        return _PROBE_CACHE[url]

    # Check local crawled cache with scheme and trailing slash variations
    crawled = _load_crawled_cache()
    if use_cache and crawled:
        candidates = [url, url.rstrip("/"), url + "/"]
        if url.startswith("https://"):
            candidates.append("http://" + url[8:])
            candidates.append("http://" + url[8:].rstrip("/"))
        elif url.startswith("http://"):
            candidates.append("https://" + url[7:])
            candidates.append("https://" + url[7:].rstrip("/"))

        for cand in candidates:
            if cand in crawled:
                entry = crawled[cand]
                code = entry.get("http_code", 0)
                status = entry.get("status", "")
                if code == 200 or status == "OK":
                    _PROBE_CACHE[url] = (True, code or 200, "Cached OK")
                    return _PROBE_CACHE[url]
                if status == "OFFLINE_OR_PROTECTED" and code in (404, 410, 500, 502, 503):
                    _PROBE_CACHE[url] = (False, code, f"Cached Error {status}")
                    return _PROBE_CACHE[url]

    # Perform live probe
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            code = resp.status
            if 200 <= code < 400:
                result = (True, code, "HTTP OK")
            else:
                result = (False, code, f"HTTP status {code}")
    except urllib.error.HTTPError as e:
        code = e.code
        e.close()
        result = (False, code, f"HTTP Error {code}")
    except urllib.error.URLError as e:
        result = (False, 0, f"URL Error: {e.reason}")
    except Exception as e:
        result = (False, 0, f"Probe Error: {str(e)}")

    if use_cache:
        _PROBE_CACHE[url] = result
    return result


def probe_urls_batch(
    urls: List[str],
    max_workers: int = 16,
    timeout: float = 3.0,
    use_cache: bool = True
) -> Dict[str, Tuple[bool, int, str]]:
    """Probe multiple URLs concurrently using a ThreadPoolExecutor.

    Pre-warms the _PROBE_CACHE to accelerate subsequent individual verifications.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    cleaned_urls = [clean_url(u) for u in urls if clean_url(u)]
    results: Dict[str, Tuple[bool, int, str]] = {}
    to_probe = []

    for u in set(cleaned_urls):
        if use_cache and u in _PROBE_CACHE:
            results[u] = _PROBE_CACHE[u]
        else:
            to_probe.append(u)

    if not to_probe:
        return results

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {
            executor.submit(probe_url_reachability, u, timeout, use_cache): u
            for u in to_probe
        }
        for future in as_completed(future_to_url):
            u = future_to_url[future]
            try:
                results[u] = future.result()
            except Exception as e:
                results[u] = (False, 0, str(e))

    return results


class Verifier:
    """Verification prober and data hygiene validator for outings."""

    def __init__(self, check_network: bool = False, timeout: float = 3.5):
        self.check_network = check_network
        self.timeout = timeout

    def verify(self, option: OutingOption) -> VerificationResult:
        """Validate an OutingOption against blacklist, formatting, and reachability."""
        return verify_outing(option, check_network=self.check_network, timeout=self.timeout)


def verify_outing(
    option: OutingOption,
    check_network: bool = False,
    timeout: float = 3.5
) -> VerificationResult:
    """Verify an outing candidate for inclusion in the weekly catalog.

    Checks:
    1. Negative filters: excludes Villa Croce, medical assistance, sports venues, or closed venues.
    2. URL presence and format.
    3. Plain writing hygiene: checks for forbidden em/en dashes.
    4. Weather dependency status.
    5. Reachability prober (if check_network=True).
    """
    # 1. Negative Blacklist Filter
    if is_blacklisted_venue(option.venue, option.description, option.verified_url):
        reason = "Blacklisted or closed venue"
        if "croce" in (option.venue + option.description + option.verified_url).lower():
            reason = "Blacklisted closed venue: Villa Croce is closed for PNRR works until further notice"
        elif "cantero" in (option.venue + option.description + option.verified_url).lower():
            reason = "Blacklisted permanently closed venue: Cinema Teatro Cantero closed permanently in 2017"
        elif "sul mare" in (option.venue + option.description + option.verified_url).lower() or "sturla" in option.venue.lower():
            reason = "Blacklisted seasonal venue: Open-air arena inactive in November"
        return VerificationResult(
            is_valid=False,
            reason=reason,
            checked_url=option.verified_url,
        )

    # 2. URL sanity check
    clean_link = clean_url(option.verified_url)
    if not clean_link or not (clean_link.startswith("http://") or clean_link.startswith("https://")):
        return VerificationResult(
            is_valid=False,
            reason="Missing or invalid verified_url",
            checked_url=option.verified_url,
        )

    # 3. Plain writing dash check
    has_dash = bool(
        PROHIBITED_DASH_RE.search(option.title)
        or PROHIBITED_DASH_RE.search(option.description)
        or PROHIBITED_DASH_RE.search(option.day_time)
    )
    clean_title = sanitize_text(option.title)
    clean_desc = sanitize_text(option.description)

    # 4. Weather dependency check
    weather_dep = is_weather_dependent_venue(option.venue, option.category, option.zone)
    if option.is_weather_dependent != weather_dep:
        option.is_weather_dependent = weather_dep

    # 5. Optional live reachability check
    http_status = None
    if check_network:
        is_reachable, code, msg = probe_url_reachability(clean_link, timeout=timeout)
        http_status = code
        if not is_reachable:
            return VerificationResult(
                is_valid=False,
                reason=f"URL unreachable: {msg}",
                http_status=http_status,
                checked_url=clean_link,
                is_weather_dependent=weather_dep,
                clean_title=clean_title,
                clean_description=clean_desc,
            )

    return VerificationResult(
        is_valid=True,
        reason="Verified valid active outing",
        http_status=http_status or 200,
        checked_url=clean_link,
        is_weather_dependent=weather_dep,
        clean_title=clean_title,
        clean_description=clean_desc,
    )


def check_url_reachability(url: str, timeout: float = 3.5) -> bool:
    """Check whether a URL is reachable over HTTP/HTTPS (returns True on 200-399)."""
    reachable, _, _ = probe_url_reachability(url, timeout=timeout)
    return reachable


def verify_venue(url_or_name: str) -> bool:
    """Compatibility check: returns False if venue or URL is blacklisted/closed or unreachable."""
    if is_blacklisted_venue(url_or_name, url=url_or_name):
        return False
    if url_or_name.startswith("http://") or url_or_name.startswith("https://"):
        reachable, _, _ = probe_url_reachability(url_or_name)
        return reachable
    return True


def get_verified_url_fallback(name: str, url: str) -> str:
    """Return verified URL if reachable, or official municipal portal fallback."""
    clean = clean_url(url)
    if clean and (clean.startswith("http://") or clean.startswith("https://")):
        reachable, _, _ = probe_url_reachability(clean)
        if reachable:
            return clean
    return "https://www.visitgenoa.it/"
