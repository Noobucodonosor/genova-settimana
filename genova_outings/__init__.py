"""Genova Weekly Informal Outings package.

Core package for extracting, live-verifying, and selecting informal leisure
and cultural alternatives in Genova and provincia.
"""

from genova_outings.models import (
    OutingCategory,
    OutingOption,
    WeeklyCatalog,
)
from genova_outings.verifier import (
    VerificationResult,
    Verifier,
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
)
from genova_outings.catalog import (
    AUTHORITATIVE_LIVE_OUTINGS,
    get_weekly_catalog,
    load_catalog_items,
)
from genova_outings.validator import (
    PlainWritingValidator,
    sanitize_for_whatsapp,
    sanitize_plain_writing,
    validate_plain_writing,
)
from genova_outings.formatter import (
    CATEGORY_EMOJIS,
    format_whatsapp_message,
)
from genova_outings.selector import (
    filter_and_select,
    interactive_select,
    parse_selection_indices,
    run_terminal_selector,
    select_by_category,
    select_by_indices,
)
from genova_outings.web_ui import (
    create_web_server,
    start_web_ui,
)

__version__ = "1.0.0"

__all__ = [
    # Models
    "OutingCategory",
    "OutingOption",
    "WeeklyCatalog",
    # Verifier
    "VerificationResult",
    "Verifier",
    "clean_url",
    "check_url_reachability",
    "get_verified_url_fallback",
    "is_blacklisted_venue",
    "is_civic_museum_closed_on_day",
    "is_weather_dependent_venue",
    "probe_url_reachability",
    "sanitize_text",
    "verify_outing",
    "verify_venue",
    # Catalog
    "AUTHORITATIVE_LIVE_OUTINGS",
    "get_weekly_catalog",
    "load_catalog_items",
    # Validator & Sanitizer
    "PlainWritingValidator",
    "sanitize_for_whatsapp",
    "sanitize_plain_writing",
    "validate_plain_writing",
    # Formatter
    "CATEGORY_EMOJIS",
    "format_whatsapp_message",
    # Selector
    "filter_and_select",
    "interactive_select",
    "parse_selection_indices",
    "run_terminal_selector",
    "select_by_category",
    "select_by_indices",
    # Web UI
    "create_web_server",
    "start_web_ui",
]
