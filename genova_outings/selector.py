"""Interactive selection interface for Genova Weekly Informal Outings.

Provides:
- Numbered terminal REPL selector with checkbox toggling ([ ] / [*]).
- Commands: numbers (1,3), toggle (+2, -1), all, none, cat <category>, preview, done, quit.
- Programmatic selection helpers for CLI flags (--select 1,2, --all, --category cinema).
"""

from __future__ import annotations

import sys
from typing import Any, Dict, List, Optional, Sequence, Set, Union

from genova_outings.formatter import format_whatsapp_message
from genova_outings.models import OutingCategory, OutingOption, WeeklyCatalog


def parse_selection_indices(selection_str: str, total_count: int) -> List[int]:
    """Parse a user selection string (e.g. '1,3', '1 2 5') into 0-based indices.

    Ignores out-of-range, negative, zero, and non-numeric inputs safely.

    Args:
        selection_str: String containing numbers separated by commas or spaces.
        total_count: Total number of available options.

    Returns:
        List of 0-based indices in ascending order without duplicates.
    """
    if not selection_str or not isinstance(selection_str, str):
        return []

    tokens = selection_str.replace(",", " ").split()
    valid_indices: Set[int] = set()

    for token in tokens:
        cleaned = token.strip()
        if cleaned.isdigit():
            val = int(cleaned)
            # 1-based indexing for end users: 1 <= val <= total_count
            if 1 <= val <= total_count:
                valid_indices.add(val - 1)

    return sorted(valid_indices)


def select_by_indices(
    options: Sequence[OutingOption], indices: Sequence[int]
) -> List[OutingOption]:
    """Retrieve options corresponding to 0-based indices."""
    res: List[OutingOption] = []
    for idx in indices:
        if 0 <= idx < len(options):
            res.append(options[idx])
    return res


def select_by_category(
    options: Sequence[OutingOption], category_query: str
) -> List[OutingOption]:
    """Filter options matching a category string or synonym."""
    if not category_query:
        return list(options)
    target_category = OutingCategory.from_str(category_query)
    return [opt for opt in options if opt.category == target_category]


def filter_and_select(
    options: Sequence[OutingOption],
    select_str: Optional[str] = None,
    category_str: Optional[str] = None,
    select_all: bool = False,
) -> List[OutingOption]:
    """Headless filtering and selection helper for CLI arguments."""
    pool = list(options)
    if category_str:
        pool = select_by_category(pool, category_str)

    if select_all:
        return pool

    if select_str:
        indices = parse_selection_indices(select_str, len(pool))
        return select_by_indices(pool, indices)

    return pool


def run_terminal_selector(
    catalog: Union[WeeklyCatalog, List[Union[OutingOption, Dict[str, Any]]]],
    stream_out=None,
) -> List[OutingOption]:
    """Run an interactive numbered terminal checkbox selector.

    Args:
        catalog: WeeklyCatalog or list of OutingOption items.
        stream_out: Output stream (defaults to sys.stdout).

    Returns:
        List of selected OutingOption objects.
    """
    out = stream_out or sys.stdout

    # Extract OutingOption items
    if isinstance(catalog, WeeklyCatalog):
        items: List[OutingOption] = catalog.activities
        label = catalog.week_label
    elif isinstance(catalog, list):
        items = [
            item if isinstance(item, OutingOption) else OutingOption.from_dict(item)
            for item in catalog
        ]
        label = "Settimana Corrente"
    else:
        items = []
        label = "Settimana Corrente"

    if not items:
        out.write("Nessuna attività disponibile nel catalogo.\n")
        return []

    selected_indices: Set[int] = set()  # 1-based indices

    def display_list():
        out.write("\n" + "=" * 74 + "\n")
        out.write(f"COSA FACCIAMO GENOVA: CATALOGO SETTIMANALE ({label})\n")
        out.write("=" * 74 + "\n")
        for idx, item in enumerate(items, 1):
            mark = "[*]" if idx in selected_indices else "[ ]"
            cat_name = (
                item.category.value.upper()
                if isinstance(item.category, OutingCategory)
                else str(item.category).upper()
            )
            cat_tag = f"[{cat_name}]"
            loc = f"{item.venue} ({item.zone})" if item.zone else item.venue
            out.write(f"{mark} {idx:2d}. {cat_tag:<14} {item.title}\n")
            out.write(f"         📍 {loc} | 🗓️ {item.day_time}\n")
            if item.verified_url:
                out.write(f"         🔗 {item.verified_url}\n")
        out.write("-" * 74 + "\n")
        out.write(f"Selezionati: {len(selected_indices)} su {len(items)}\n")
        out.write(
            "Comandi: [n,n...] toggle | +n aggiungi | -n togli | all | none | "
            "cat <nome> | preview | done | quit\n"
        )
        out.write("-" * 74 + "\n")
        out.flush()

    display_list()

    while True:
        try:
            cmd = input("Scelta > ").strip()
        except (EOFError, KeyboardInterrupt):
            out.write("\nSelezione annullata.\n")
            out.flush()
            return []

        if not cmd:
            continue

        lower_cmd = cmd.lower()

        if lower_cmd in ("quit", "q", "exit"):
            return []

        if lower_cmd in ("done", "ok"):
            if not selected_indices:
                out.write(
                    "Nessuna attività selezionata. Digita i numeri (es. 1,3) oppure 'all'.\n"
                )
                out.flush()
                continue
            return [items[i - 1] for i in sorted(selected_indices)]

        if lower_cmd == "all":
            selected_indices = set(range(1, len(items) + 1))
            display_list()
            continue

        if lower_cmd in ("none", "clear"):
            selected_indices.clear()
            display_list()
            continue

        if lower_cmd.startswith("cat "):
            query = lower_cmd[4:].strip()
            target_cat = OutingCategory.from_str(query)
            matched = [
                idx
                for idx, it in enumerate(items, 1)
                if it.category == target_cat or query in it.category.value.lower()
            ]
            if matched:
                selected_indices.update(matched)
                display_list()
            else:
                out.write(f"Nessuna categoria corrispondente a '{query}'.\n")
                out.flush()
            continue

        if lower_cmd == "preview":
            selected_items = [items[i - 1] for i in sorted(selected_indices)]
            out.write("\n" + "=" * 25 + " ANTEPRIMA MESSAGGIO WHATSAPP " + "=" * 25 + "\n")
            out.write(format_whatsapp_message(selected_items) + "\n")
            out.write("=" * 80 + "\n")
            out.flush()
            continue

        if lower_cmd == "show":
            display_list()
            continue

        # Parse numeric tokens and toggle commands (+2, -1, 1, 3)
        parts = cmd.replace(",", " ").split()
        modified = False
        for p in parts:
            if p.startswith("+") and p[1:].isdigit():
                val = int(p[1:])
                if 1 <= val <= len(items):
                    selected_indices.add(val)
                    modified = True
            elif p.startswith("-") and p[1:].isdigit():
                val = int(p[1:])
                selected_indices.discard(val)
                modified = True
            elif p.isdigit():
                val = int(p)
                if 1 <= val <= len(items):
                    if val in selected_indices:
                        selected_indices.remove(val)
                    else:
                        selected_indices.add(val)
                    modified = True

        if modified:
            display_list()


def interactive_select(
    catalog: Union[WeeklyCatalog, List[Union[OutingOption, Dict[str, Any]]]],
    stream_out=None,
) -> List[OutingOption]:
    """Convenience alias for run_terminal_selector."""
    return run_terminal_selector(catalog, stream_out=stream_out)
