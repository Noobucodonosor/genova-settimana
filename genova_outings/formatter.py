"""WhatsApp message formatter for Genova Weekly Informal Outings.

Generates copy-paste ready WhatsApp messages in natural informal Italian,
strictly complying with plain-writing guidelines:
- Zero em-dashes (\u2014) or en-dashes (\u2013).
- Zero mentions of 'date' or romantic framing.
- Zero promotional marketing puffery.
- WhatsApp markdown bolding (*titolo*) and clean raw URLs.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Union

from genova_outings.models import OutingCategory, OutingOption
from genova_outings.validator import (
    sanitize_for_whatsapp,
    sanitize_plain_writing,
    validate_plain_writing,
)


CATEGORY_EMOJIS: Dict[OutingCategory, str] = {
    OutingCategory.CINEMA: "🎬",
    OutingCategory.MOSTRA: "🏛️",
    OutingCategory.PASSEGGIATA: "🌿",
    OutingCategory.BIBLIOTECA: "📚",
    OutingCategory.LABORATORIO: "🎭",
    OutingCategory.MUSICA: "🎶",
    OutingCategory.RITROVO: "☕",
    OutingCategory.ALTRO: "📍",
}


def _clean_field(val: Optional[str]) -> str:
    """Sanitize and strip string field."""
    if not val:
        return ""
    return sanitize_for_whatsapp(str(val))


def _clean_url(url: Optional[str]) -> str:
    """Ensure URL is clean and free of trailing punctuation."""
    if not url:
        return ""
    cleaned = str(url).strip().strip("'\"<>[]()")
    return cleaned.rstrip(".,;:!?)")


def _get_emoji_for_category(category: Any) -> str:
    """Resolve discrete category emoji."""
    if isinstance(category, OutingCategory):
        return CATEGORY_EMOJIS.get(category, "📍")
    cat_enum = OutingCategory.from_str(str(category))
    return CATEGORY_EMOJIS.get(cat_enum, "📍")


def format_whatsapp_message(
    selected_options: List[Union[OutingOption, Dict[str, Any]]],
    tone: str = "amichevole",
    layout: str = "card",
    include_closing: bool = True,
) -> str:
    """Format a list of selected outings into a WhatsApp-ready Italian message.

    Args:
        selected_options: List of OutingOption objects or equivalent dicts.
        tone: 'amichevole' (default), 'relaxed', 'weekend', 'minimal'.
        layout: 'card' (default) or 'compact'.
        include_closing: Whether to append closing conversational signoff.

    Returns:
        Formatted WhatsApp message compliant with plain-writing rules.
    """
    if not selected_options:
        return "Nessuna attività selezionata."

    # Convert dictionaries to OutingOption objects if needed
    normalized_options: List[OutingOption] = []
    for opt in selected_options:
        if isinstance(opt, OutingOption):
            normalized_options.append(opt)
        elif isinstance(opt, dict):
            normalized_options.append(OutingOption.from_dict(opt))

    count = len(normalized_options)
    norm_tone = (tone or "amichevole").lower().strip()

    # Determine friendly informal opener
    if norm_tone == "minimal":
        intro = "Ecco le opzioni in programma questa settimana a Genova:"
    elif norm_tone == "weekend":
        intro = "Se hai voglia di fare un salto nel weekend, ho visto queste cose a Genova:"
    else:
        # Default: 'amichevole' / 'relaxed' / fallback
        if count == 1:
            intro = "Ciao! Ho visto questa cosa a Genova questa settimana che sembra interessante se ti va di fare un salto:"
        else:
            intro = "Ciao! Ti lascio un paio di idee carine per questa settimana a Genova se ti va di fare un salto:"

    lines: List[str] = [intro, ""]

    if layout == "card":
        for opt in normalized_options:
            emoji = _get_emoji_for_category(opt.category)
            clean_title = _clean_field(opt.title)
            # Remove any existing asterisks to avoid double-bolding
            clean_title = clean_title.replace("*", "").strip()

            lines.append(f"{emoji} *{clean_title}*")

            # Location line: venue, address, zone
            venue = _clean_field(opt.venue)
            address = _clean_field(opt.address)
            zone = _clean_field(opt.zone)

            loc_parts: List[str] = []
            if venue:
                loc_parts.append(venue)
            if address and address.lower() not in venue.lower():
                loc_parts.append(address)

            loc_str = ", ".join(loc_parts)
            if zone:
                loc_str = f"{loc_str} ({zone})" if loc_str else f"({zone})"

            if loc_str:
                lines.append(f"📍 {loc_str}")

            # Schedule / Day time
            day_time = _clean_field(opt.day_time or opt.days_display)
            if day_time:
                lines.append(f"🗓️ {day_time}")

            # Description
            desc = _clean_field(opt.description)
            if desc:
                lines.append(desc)

            # Current programme (first 4 entries) when available
            prog = (opt.raw_metadata or {}).get("programma") or []
            if prog:
                lines.append("In programma:")
                for p in prog[:4]:
                    t = _clean_field(p.get("titolo", "")).replace("*", "")
                    q = _clean_field(p.get("quando", ""))
                    if t:
                        lines.append(f"  • _{t}_, {q}" if q else f"  • _{t}_")

            # Clean raw URL
            url = _clean_url(opt.verified_url or opt.source_url)
            if url:
                lines.append(f"Info: {url}")

            lines.append("")
    else:
        # Compact layout
        for opt in normalized_options:
            emoji = _get_emoji_for_category(opt.category)
            clean_title = _clean_field(opt.title).replace("*", "").strip()
            url = _clean_url(opt.verified_url or opt.source_url)
            zone_str = f" ({_clean_field(opt.zone)})" if opt.zone else ""
            day_str = f", {_clean_field(opt.day_time)}" if opt.day_time else ""
            desc = _clean_field(opt.description)

            url_part = f" Info: {url}" if url else ""
            lines.append(f"• {emoji} *{clean_title}*{zone_str}: {desc}{day_str}.{url_part}")
        lines.append("")

    # Conversational friendly closer
    if include_closing:
        if count == 1:
            lines.append("Dimmi se ti ispira!")
        else:
            lines.append("Dimmi se ti ispira qualcosa!")

    message = "\n".join(lines).strip()

    # Automated validation check & auto-remediation safeguard
    is_valid, _ = validate_plain_writing(message)
    if not is_valid:
        message = sanitize_for_whatsapp(message)

    return message
