#!/usr/bin/env python3
"""ETL pipeline generating normalized JSON datasets in data/ and site/data/ (TASK-GS-BE-01)."""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from genova_outings.catalog import get_weekly_catalog
from genova_outings.export_static import _dedupe
from genova_outings.html_utils import get_data_dir
from genova_outings.programme import attach_programmes
from genova_outings.validator import sanitize_plain_writing

HTML_TAG_RE = re.compile(r"<[^>]+>")
MULTI_PIPE_RE = re.compile(r"\|[^|]*\|")


def clean_scraping_text(value: Any) -> str:
    """Strip HTML tags, HTML entities, scraping pipes, and normalize whitespace."""
    if value is None:
        return ""
    text = html.unescape(str(value))
    text = HTML_TAG_RE.sub(" ", text)
    # Replace pipe separators from scraped snippets with clean comma separation
    text = re.sub(r"\s*\|\s*", ", ", text)
    text = sanitize_plain_writing(text)
    text = re.sub(r"(?:,\s*){2,}", ", ", text).strip(" ,")
    return re.sub(r"\s+", " ", text).strip()


def make_summary(text: str, max_len: int = 160) -> str:
    """Create a clean <=160 char summary without cutting mid-word."""
    cleaned = clean_scraping_text(text)
    if len(cleaned) <= max_len:
        return cleaned
    clipped = cleaned[: max_len - 3].rsplit(" ", 1)[0].rstrip(" ,;:-")
    if not clipped:
        clipped = cleaned[: max_len - 3]
    return f"{clipped}..."


def validate_events(events: List[Dict[str, Any]]) -> List[str]:
    """Validate normalized events; return list of blocking errors."""
    errors: List[str] = []
    seen_ids = set()
    seen_keys = set()

    for idx, ev in enumerate(events):
        eid = str(ev.get("id") or "").strip()
        title = str(ev.get("title") or "").strip()
        venue = str(ev.get("venue") or "").strip()
        summary = str(ev.get("summary") or "").strip()
        category = str(ev.get("category") or "").strip()

        if not eid or not title or not venue:
            errors.append(f"Row {idx}: missing id/title/venue")
        if eid in seen_ids:
            errors.append(f"Row {idx}: duplicate id '{eid}'")
        seen_ids.add(eid)

        dedupe_key = (title.lower(), venue.lower(), category.lower())
        if dedupe_key in seen_keys:
            errors.append(f"Row {idx}: duplicate event {dedupe_key}")
        seen_keys.add(dedupe_key)

        if len(summary) > 160:
            errors.append(f"Row {idx} ({eid}): summary exceeds 160 chars ({len(summary)})")

        for field_name, val in (("title", title), ("venue", venue), ("summary", summary)):
            if HTML_TAG_RE.search(val):
                errors.append(f"Row {idx} ({eid}): residual HTML tag in {field_name}")
            if MULTI_PIPE_RE.search(val) or "|" in val:
                errors.append(f"Row {idx} ({eid}): dirty pipe separator in {field_name}")

    return errors


def build_events(live_verify: bool = False) -> List[Dict[str, Any]]:
    """Build normalized weekly events list."""
    options = get_weekly_catalog(live_verify=live_verify)
    if live_verify:
        attach_programmes(options)
    options = _dedupe(options)
    options.sort(key=lambda o: (o.category.value, o.title.lower(), o.id))

    events: List[Dict[str, Any]] = []
    seen_keys = set()
    for o in options:
        title = clean_scraping_text(o.title)
        venue = clean_scraping_text(o.venue)
        key = (title.lower(), venue.lower(), o.category.value.lower())
        if key in seen_keys:
            continue
        seen_keys.add(key)

        showtimes = [
            {
                "titolo": clean_scraping_text(p.get("titolo", "")),
                "quando": clean_scraping_text(p.get("quando", "")),
            }
            for p in (o.raw_metadata.get("programma") or [])
            if p.get("titolo")
        ]
        events.append({
            "id": o.id,
            "title": title,
            "venue": venue,
            "address": clean_scraping_text(o.address or venue),
            "district": clean_scraping_text((o.zone or "").replace("_", " ").title()),
            "category": o.category.value,
            "summary": make_summary(o.description or o.day_time, max_len=160),
            "showtimes": showtimes,
            "day_time": clean_scraping_text(o.day_time),
            "url": (o.verified_url or "").strip(),
            "outdoor": bool(o.is_weather_dependent),
            "time_slot": o.time_slot or "flessibile",
            "tags": [clean_scraping_text(t) for t in (o.tags or []) if t],
        })
    return events


def build_esercenti(data_dir: Path) -> List[Dict[str, Any]]:
    """Build normalized esercenti dataset."""
    src = data_dir / "esercenti_genova_provincia_db.json"
    if not src.exists():
        return []
    raw = json.loads(src.read_text(encoding="utf-8"))
    out: List[Dict[str, Any]] = []
    for row in raw:
        out.append({
            "nome": clean_scraping_text(row.get("nome")),
            "comune": clean_scraping_text(row.get("comune")),
            "quartiere": clean_scraping_text(row.get("quartiere_o_zona")),
            "macro_settore": clean_scraping_text(row.get("macro_settore")),
            "categoria": clean_scraping_text(row.get("categoria_specifica")),
            "indipendente": bool(row.get("indipendente", True)),
            "indirizzo": clean_scraping_text(row.get("indirizzo")),
            "telefono": clean_scraping_text(row.get("telefono")),
            "url": str(row.get("sito_o_social") or "").strip(),
            "orari": clean_scraping_text(row.get("orari")),
            "cosa_trovi": make_summary(row.get("cosa_trovi_qui") or "", max_len=160),
            "personaggio_via": clean_scraping_text(row.get("personaggio_via")),
            "lat": row.get("lat"),
            "lon": row.get("lon"),
        })
    out.sort(key=lambda r: (r["comune"].lower(), r["nome"].lower(), r["indirizzo"].lower()))
    return out


def build_odonomastica(data_dir: Path) -> List[Dict[str, Any]]:
    """Build normalized odonomastica dataset from integral OSM+Wikidata CSV."""
    src = data_dir / "toponimi_personaggi_genova_integrale.csv"
    if not src.exists():
        return []
    out: List[Dict[str, Any]] = []
    seen = set()
    with open(src, "r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            toponimo = clean_scraping_text(row.get("toponimo"))
            tipo = clean_scraping_text(row.get("tipo"))
            personaggio = clean_scraping_text(row.get("personaggio_o_casata"))
            categoria = clean_scraping_text(row.get("descrizione_categoria"))
            key = (toponimo.lower(), personaggio.lower())
            if not toponimo or key in seen:
                continue
            seen.add(key)
            out.append({
                "toponimo": toponimo,
                "tipo": tipo,
                "personaggio": personaggio,
                "categoria": categoria,
            })
    out.sort(key=lambda r: (r["toponimo"].lower(), r["personaggio"].lower()))
    return out


def build_dashboard(data_dir: Path) -> List[Dict[str, Any]]:
    """Build normalized compact dashboard dataset from dashboard_items.json."""
    src = data_dir / "dashboard_items.json"
    if not src.exists():
        return []
    items = json.loads(src.read_text(encoding="utf-8"))

    def sort_key(x: Dict[str, Any]):
        score = 0
        if x.get("sito_web"):
            score -= 4
        if x.get("telefono"):
            score -= 2
        if "Bottega Storica" in x.get("sottocategoria", ""):
            score -= 5
        orari = x.get("orari_apertura", "")
        if orari and not orari.startswith("Consultare") and not orari.startswith("Aperto tutti i giorni per visite"):
            score -= 4
        if x.get("personaggio"):
            score -= 1
        return (score, x.get("comune", ""), x.get("nome", ""))

    out: List[Dict[str, Any]] = []
    for idx, it in enumerate(sorted(items, key=sort_key), 1):
        out.append({
            "id": idx,
            "c": clean_scraping_text(it.get("comune")),
            "n": clean_scraping_text(it.get("nome")),
            "m": clean_scraping_text(it.get("macro_categoria")),
            "s": clean_scraping_text(it.get("sottocategoria")),
            "a": clean_scraping_text(it.get("indirizzo")),
            "t": clean_scraping_text(it.get("telefono")),
            "w": str(it.get("sito_web") or "").strip(),
            "o": clean_scraping_text(it.get("orari_apertura")),
            "e": clean_scraping_text(it.get("eventi_e_servizi_al_pubblico", ""))[:260],
            "d": it.get("days_open") or [],
            "h": it.get("hours_range") or [],
            "sun": 1 if it.get("open_sunday") else 0,
            "eve": 1 if it.get("open_evening") else 0,
            "f1": 1 if it.get("free_first_sunday") else 0,
            "mo": it.get("seasonal_months") or [],
            "p": clean_scraping_text(it.get("personaggio")),
        })
    return out


def build_bussola(data_dir: Path) -> Dict[str, Any]:
    """Load bussola payload if present in data_dir."""
    src = data_dir / "tempo_libero_payload.json"
    if not src.exists():
        return {}
    return json.loads(src.read_text(encoding="utf-8"))


def run_build(
    data_dir: Optional[Path] = None,
    live_verify: bool = False,
    mirror_to_site: bool = True,
) -> Dict[str, int]:
    """Run full ETL build, validate events, and write JSON files."""
    base = data_dir or get_data_dir()
    events = build_events(live_verify=live_verify)
    errors = validate_events(events)
    if errors:
        raise ValueError("Event validation failed:\n" + "\n".join(errors[:20]))

    esercenti = build_esercenti(base)
    odonomastica = build_odonomastica(base)
    dashboard = build_dashboard(base)
    bussola = build_bussola(base)

    targets = [base / "data"]
    if mirror_to_site:
        targets.append(base / "site" / "data")

    for out_dir in targets:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "events.json").write_text(
            json.dumps(events, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        (out_dir / "esercenti.json").write_text(
            json.dumps(esercenti, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        (out_dir / "odonomastica.json").write_text(
            json.dumps(odonomastica, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        if dashboard:
            (out_dir / "dashboard.json").write_text(
                json.dumps(dashboard, ensure_ascii=False) + "\n", encoding="utf-8"
            )
        if bussola:
            (out_dir / "bussola.json").write_text(
                json.dumps(bussola, ensure_ascii=False) + "\n", encoding="utf-8"
            )

    return {
        "events": len(events),
        "esercenti": len(esercenti),
        "odonomastica": len(odonomastica),
        "dashboard": len(dashboard),
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Build normalized JSON datasets in data/ and site/data/.")
    parser.add_argument("--live", action="store_true", help="Run live HTTP verification and programme scraping")
    parser.add_argument("--no-site-mirror", action="store_true", help="Do not mirror JSON into site/data/")
    args = parser.parse_args(argv)
    try:
        counts = run_build(live_verify=args.live, mirror_to_site=not args.no_site_mirror)
        print(
            f"Built data/*.json: {counts['events']} events, "
            f"{counts['esercenti']} esercenti, {counts['odonomastica']} odonomastica."
        )
        return 0
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
