"""Catalog aggregator and normalizer for Genova Weekly Informal Outings.

Aggregates verified leisure and cultural options for the current week from:
1. Local verified datasets (`tempo_libero_payload.json`, `guida_aperti_al_pubblico`,
   `dashboard_items.json`, `esercenti_genova_provincia_db`).
2. Authoritative live verified endpoints (Circuito Cinema, Cineclub Nickelodeon,
   Palazzo Ducale, Berio, De Amicis, Count Basie, La Claque, Giardini Luzzati, etc.).

Enforces:
- Negative filters (explicitly blacklists closed venues like Villa Croce).
- Plain-writing data hygiene (sanitizes em/en dashes, hype words, and romance terms).
- Category normalization to OutingCategory enum.
- Live reachability verification when requested.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Set

from genova_outings.models import OutingCategory, OutingOption
from genova_outings.verifier import (
    clean_url,
    is_blacklisted_venue,
    is_weather_dependent_venue,
    probe_url_reachability,
    probe_urls_batch,
    sanitize_text,
    verify_outing,
)

logger = logging.getLogger(__name__)

# Base directory for local datasets (portable across CI and local machines)
DEFAULT_DATA_DIR = Path(os.environ.get("GENOVA_DATA_DIR") or Path(__file__).resolve().parent.parent)


def _resolve_raw_file(data_dir: Path, filename: str) -> Path:
    """Resolve a raw dataset file from data/raw/ with fallback to data_dir root."""
    raw_candidate = data_dir / "data" / "raw" / filename
    return raw_candidate if raw_candidate.exists() else data_dir / filename

def _load_authoritative_outings(data_dir: Optional[Path] = None) -> List[Dict[str, object]]:
    """Load curated authoritative outings from data/config/authoritative_outings.json."""
    base = data_dir or DEFAULT_DATA_DIR
    cfg_path = base / "data" / "config" / "authoritative_outings.json"
    if not cfg_path.exists():
        return []
    try:
        items = json.loads(cfg_path.read_text(encoding="utf-8"))
        for item in items:
            if isinstance(item.get("category"), str):
                item["category"] = OutingCategory.from_str(item["category"])
        return items
    except Exception as exc:
        logger.warning("Failed to load %s: %s", cfg_path, exc)
        return []


def _is_within_validity(raw: Dict[str, object], ref_day: date) -> bool:
    """Return True if optional valid_from / valid_to ISO bounds include ref_day."""
    vf = raw.get("valid_from")
    vt = raw.get("valid_to")
    try:
        if vf and ref_day < date.fromisoformat(str(vf)):
            return False
        if vt and ref_day > date.fromisoformat(str(vt)):
            return False
    except ValueError:
        return True
    return True


AUTHORITATIVE_LIVE_OUTINGS: List[Dict[str, object]] = _load_authoritative_outings()

def _build_option_from_raw(
    id_val: str,
    title: str,
    category: OutingCategory,
    venue: str,
    zone: str,
    day_time: str,
    url: str,
    description: str,
    source_type: str = "verified_local",
    address: str = "",
    time_slot: str = "flessibile",
    cost_info: Optional[str] = None,
    is_free: bool = False,
    tags: Optional[List[str]] = None,
    raw_metadata: Optional[Dict[str, object]] = None,
) -> Optional[OutingOption]:
    """Factory helper that validates, sanitizes, and builds an OutingOption."""
    # Negative filtering check (Villa Croce, closed venues, non-informal institutions)
    if is_blacklisted_venue(venue, description, url):
        return None

    # Sanitize strings to remove long dashes and forbidden phrasing
    clean_t = sanitize_text(title)
    clean_d = sanitize_text(description)
    clean_dt = sanitize_text(day_time)
    clean_v = sanitize_text(venue)
    clean_addr = sanitize_text(address) if address else ""
    clean_u = clean_url(url)

    if not clean_u:
        return None

    weather_dep = is_weather_dependent_venue(clean_v, category, zone)

    return OutingOption(
        id=id_val,
        title=clean_t,
        category=category,
        venue=clean_v,
        zone=zone,
        day_time=clean_dt,
        verified_url=clean_u,
        description=clean_d,
        source_type=source_type,
        is_weather_dependent=weather_dep,
        address=clean_addr,
        time_slot=time_slot,
        cost_info=cost_info,
        is_free=is_free,
        tags=tags or [],
        raw_metadata=raw_metadata or {},
    )


def load_authoritative_live_options(
    today: Optional[date] = None,
    data_dir: Optional[Path] = None,
) -> List[OutingOption]:
    """Generate OutingOption instances from curated authoritative live entries."""
    ref_day = today or date.today()
    entries = _load_authoritative_outings(data_dir) if data_dir is not None else AUTHORITATIVE_LIVE_OUTINGS
    results: List[OutingOption] = []
    for raw in entries:
        if not _is_within_validity(raw, ref_day):
            continue
        opt = _build_option_from_raw(
            id_val=str(raw["id"]),
            title=str(raw["title"]),
            category=raw["category"],  # type: ignore
            venue=str(raw["venue"]),
            zone=str(raw["zone"]),
            day_time=str(raw["day_time"]),
            url=str(raw["verified_url"]),
            description=str(raw["description"]),
            source_type="live_web",
            address=str(raw.get("address", "")),
            time_slot=str(raw.get("time_slot", "flessibile")),
            cost_info=raw.get("cost_info"),  # type: ignore
            is_free=bool(raw.get("is_free", False)),
            tags=raw.get("tags"),  # type: ignore
            raw_metadata={"live_source": "spec_miner_verified"},
        )
        if opt:
            results.append(opt)
    return results


def load_local_tempo_libero(data_dir: Path) -> List[OutingOption]:
    """Extract informal options from tempo_libero_payload.json."""
    path = _resolve_raw_file(data_dir, "tempo_libero_payload.json")
    if not path.exists():
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except Exception as e:
        logger.warning("Could not read tempo_libero_payload.json: %s", e)
        return []

    results: List[OutingOption] = []
    places = payload.get("places", [])

    # Curate high-quality tier 1 flagships and selected informal venues
    for p in places:
        # We only accept Tier 1 flagships or specific informal botteghe / biblioteche
        tier = p.get("tier", 2)
        tipo = p.get("tipo", "")
        if tier != 1 and tipo not in ("bottega", "biblioteca", "teatro"):
            continue

        nome = p.get("nome", "")
        url = p.get("url", "")
        if not url:
            continue

        # Map tipo to OutingCategory
        if tipo == "bottega":
            cat = OutingCategory.RITROVO if "caff" in nome.lower() or "confetteria" in nome.lower() or "cioccolato" in nome.lower() or "friggitoria" in nome.lower() or "barberia" in nome.lower() else OutingCategory.LABORATORIO
        elif tipo == "biblioteca":
            cat = OutingCategory.BIBLIOTECA
        elif tipo in ("museo", "dimora"):
            cat = OutingCategory.MOSTRA
        elif tipo == "teatro":
            cat = OutingCategory.MUSICA
        elif tipo == "natura":
            cat = OutingCategory.PASSEGGIATA
        else:
            cat = OutingCategory.ALTRO

        desc = p.get("pitch", "") or p.get("personaggio", "")
        orari = p.get("orari", "") or "Orari standard da verificare sul sito ufficiale"
        zona = p.get("zona", "Genova")

        slug_id = f"tl_{p.get('id', '')}_{cat.value}"

        opt = _build_option_from_raw(
            id_val=slug_id,
            title=nome,
            category=cat,
            venue=nome.split("—")[0].split("(")[0].strip(),
            zone=zona.capitalize(),
            day_time=orari,
            url=url,
            description=desc,
            source_type="verified_local",
            address=p.get("trasporto_info", ""),
            time_slot="pomeriggio",
            cost_info=p.get("costo"),
            is_free=bool(p.get("free", False)),
            tags=[tipo, zona],
            raw_metadata=p,
        )
        if opt:
            results.append(opt)

    return results


def load_local_guida_aperti(data_dir: Path) -> List[OutingOption]:
    """Extract verified informal cinemas, theatres, and open cultural sites from guida."""
    path = _resolve_raw_file(data_dir, "guida_aperti_al_pubblico_provincia_genova.json")
    if not path.exists():
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            guida = json.load(f)
    except Exception as e:
        logger.warning("Could not read guida_aperti_al_pubblico_provincia_genova.json: %s", e)
        return []

    results: List[OutingOption] = []
    seen_names: Set[str] = set()

    for item in guida:
        subcat = str(item.get("sottocategoria", "")).lower()
        macro = str(item.get("macro_categoria", ""))
        url = str(item.get("sito_web", "")).strip()
        nome = str(item.get("nome", "")).strip()

        if not url or url.lower() in ("no_url", "none", ""):
            continue
        if not (url.startswith("http://") or url.startswith("https://")):
            continue

        # Keep cinemas and theatres with active schedules
        if subcat in ("cinema", "theatre", "teatro") or "3." in macro:
            norm_name = nome.lower()
            if norm_name in seen_names:
                continue

            orari = item.get("orari_apertura", "")
            cat = OutingCategory.CINEMA if "cinema" in subcat or "cinema" in norm_name else OutingCategory.MUSICA
            desc = item.get("eventi_e_servizi_al_pubblico", "") or f"Programmazione spettacoli e proiezioni presso {nome}."
            comune = item.get("comune", "Genova")

            opt = _build_option_from_raw(
                id_val=f"guida_{len(results)}_{cat.value}",
                title=f"{nome}: Programmazione Spettacoli",
                category=cat,
                venue=nome,
                zone=comune,
                day_time=orari if orari else "Consultare la programmazione settimanale sul sito ufficiale",
                url=url,
                description=desc,
                source_type="verified_local",
                address=item.get("indirizzo", ""),
                time_slot="sera",
                tags=[subcat, comune],
                raw_metadata=item,
            )
            if opt:
                results.append(opt)
                seen_names.add(norm_name)

    return results


def load_local_esercenti_informali(data_dir: Path) -> List[OutingOption]:
    """Extract independent historic bookshops, vinyl shops, and traditional sciamadde."""
    path = _resolve_raw_file(data_dir, "esercenti_genova_provincia_db.json")
    if not path.exists():
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            esercenti = json.load(f)
    except Exception as e:
        logger.warning("Could not read esercenti_genova_provincia_db.json: %s", e)
        return []

    results: List[OutingOption] = []
    target_keywords = ["libreria", "dischi in vinile", "confetteria", "cioccolato", "farinata"]

    for item in esercenti:
        spec = str(item.get("categoria_specifica", "")).lower()
        desc_raw = str(item.get("cosa_trovi_qui", "")).lower()
        url = str(item.get("sito_o_social", "")).strip()

        if not url or not (url.startswith("http://") or url.startswith("https://")):
            continue

        is_target = any(kw in spec or kw in desc_raw for kw in target_keywords)
        if not is_target:
            continue

        nome = item.get("nome", "")
        comune = item.get("comune", "Genova")

        if "libreria" in spec or "libri" in desc_raw:
            cat = OutingCategory.BIBLIOTECA
        elif "dischi" in spec or "vinile" in desc_raw:
            cat = OutingCategory.MUSICA
        else:
            cat = OutingCategory.RITROVO

        orari = item.get("orari", "") or "Orari di apertura del locale"
        desc = item.get("cosa_trovi_qui", "") or f"Locale storico indipendente a {comune}."

        opt = _build_option_from_raw(
            id_val=f"es_{len(results)}_{cat.value}",
            title=f"{nome}: {spec.title()}",
            category=cat,
            venue=nome,
            zone=comune,
            day_time=orari,
            url=url,
            description=desc,
            source_type="verified_local",
            address=item.get("indirizzo", ""),
            time_slot="pomeriggio",
            tags=[spec],
            raw_metadata=item,
        )
        if opt:
            results.append(opt)

    return results


def load_catalog_items(data_dir: Optional[Path] = None) -> List[OutingOption]:
    """Aggregate all options from authoritative live sources and local datasets.

    Deduplicates candidates and strictly applies negative blacklist filters.
    """
    directory = data_dir or DEFAULT_DATA_DIR

    # 1. Start with high-priority authoritative live verified endpoints
    all_options: List[OutingOption] = load_authoritative_live_options()

    # 2. Append curated items from local datasets
    tl_options = load_local_tempo_libero(directory)
    all_options.extend(tl_options)

    guida_options = load_local_guida_aperti(directory)
    all_options.extend(guida_options)

    es_options = load_local_esercenti_informali(directory)
    all_options.extend(es_options)

    # 3. Deduplicate by (normalized venue, category)
    deduped: List[OutingOption] = []
    seen_keys: Set[Tuple[str, str]] = set()

    for opt in all_options:
        # Extra safety check against blacklisted closed venues (Villa Croce, Cantero, summer arenas, etc.)
        if is_blacklisted_venue(opt.venue, opt.description, opt.verified_url):
            continue

        norm_venue = "".join(ch for ch in opt.venue.lower() if ch.isalnum())
        title_slug = "".join(ch for ch in opt.title.lower() if ch.isalnum())
        key = (norm_venue, opt.category.value, title_slug)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        deduped.append(opt)

    return deduped


def get_weekly_catalog(
    live_verify: bool = True,
    category: Optional[str] = None,
    data_dir: Optional[Path] = None,
) -> List[OutingOption]:
    """Interface function: returns curated, verified list of active options for current week.

    Args:
        live_verify: If True, performs HTTP reachability probes and negative validation.
        category: Optional category filter (e.g. 'cinema', 'mostra', 'passeggiata', or synonyms like 'film').
        data_dir: Optional custom path to data directory.

    Returns:
        List of OutingOption objects meeting all plain-writing, accuracy, and reachability rules.
    """
    raw_catalog = load_catalog_items(data_dir=data_dir)

    # Filter by category if requested, supporting category synonyms
    target_cat: Optional[str] = None
    if category is not None:
        cat_str = str(category).strip()
        if cat_str:
            if isinstance(category, OutingCategory):
                target_cat = category.value
            else:
                target_cat = OutingCategory.from_str(cat_str).value

    # Pre-probe reachability in parallel if live_verify is requested
    if live_verify:
        candidate_urls = [
            opt.verified_url for opt in raw_catalog
            if not (target_cat and opt.category.value != target_cat)
        ]
        probe_urls_batch(candidate_urls, max_workers=16, timeout=3.0)

    verified_list: List[OutingOption] = []

    for option in raw_catalog:
        if target_cat and option.category.value != target_cat:
            continue

        if live_verify:
            # Run verifier with reachability prober
            vres = verify_outing(option, check_network=True)
            if not vres.is_valid:
                # Log rejection and omit
                logger.debug("Omitted invalid outing %s: %s", option.id, vres.reason)
                continue
            # Apply any sanitized title or description adjustments
            if vres.clean_title:
                option.title = vres.clean_title
            if vres.clean_description:
                option.description = vres.clean_description

        # Final sanity check: ensure no em/en dashes slip through in any text field
        option.title = sanitize_text(option.title)
        option.description = sanitize_text(option.description)
        option.day_time = sanitize_text(option.day_time)
        option.venue = sanitize_text(option.venue)
        option.address = sanitize_text(option.address)

        verified_list.append(option)

    return [o for o in verified_list if has_usable_schedule(o.day_time)]


_MONTH_NUM = {m: i for i, m in enumerate(
    ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio",
     "agosto", "settembre", "ottobre", "novembre", "dicembre"], 1)}
_OPEN_ACCESS = ("sempre", "tutti i giorni", "accesso libero", "alba", "tramonto")


def has_usable_schedule(day_time: str, today: Optional["date"] = None) -> bool:
    """True if day_time states real hours or open access and mentions no past date."""
    import re
    from datetime import date
    t = (day_time or "").lower()
    if not t or "verifica aperture" in t or "orari di apertura del locale" in t:
        return False
    today = today or date.today()
    for d, m in re.findall(r"\b(\d{1,2})\s+(" + "|".join(_MONTH_NUM) + r")\b", t):
        try:
            when = date(today.year, _MONTH_NUM[m], int(d))
        except ValueError:
            continue
        if when < today and (today - when).days < 200:
            return False
    return bool(re.search(r"\d{1,2}[:.]\d{2}|\bore\s+\d{1,2}\b", t)) or any(k in t for k in _OPEN_ACCESS)
