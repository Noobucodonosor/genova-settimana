"""Esporta una pagina statica (site/index.html) essenziale in stile rivista culturale.

Uso:  python3 -m genova_outings.export_static [cartella_uscita]
"""

import html
import re
import sys
import unicodedata
from copy import deepcopy
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlparse

from genova_outings.catalog import get_weekly_catalog
from genova_outings.html_utils import (
    OPEN_DATA_ATTRIBUTION_TEXT,
    PWA_HEAD_HTML,
    PWA_SW_SCRIPT,
    safe_json_for_script,
)
from genova_outings.models import OutingCategory
from genova_outings.programme import attach_programmes

MESI = [
    "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
    "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre",
]

CAT_LABEL = {
    "cinema": "Cinema",
    "mostra": "Mostre",
    "musica": "Musica e teatro",
    "biblioteca": "Biblioteche",
    "passeggiata": "Passeggiate",
    "laboratorio": "Botteghe e sapori",
    "ritrovo": "Caffè e ritrovi",
    "altro": "Abbazie e borghi",
}
CAT_ORDER = list(CAT_LABEL)


def editorial_sort_key(o):
    """Canonical editorial sort order shared by export_static and scripts/build_data."""
    return (
        CAT_ORDER.index(o.category.value) if o.category.value in CAT_ORDER else 99,
        0 if o.raw_metadata.get("programma") else 1,
        (o.title or "").lower(),
        o.id,
    )

_ROBOTIC_SUFFIX_RE = re.compile(
    r":\s*(?:Programmazione Spettacoli|Proiezioni d['’]Autore|Cinema e Cultura|"
    r"Rassegna Cineforum e Cinema di Ricerca|Rassegna d['’]Essai(?:\s+e\s+Prime Visioni|\s+di\s+Quartiere)?|"
    r"Libreria\s*\([^)]+\))\s*$",
    re.IGNORECASE,
)

_CANONICAL_CINEMA_NAMES = {
    "sivori": "Cinema Sivori",
    "america": "Cinema America",
    "odeon": "Cinema Odeon",
    "nickelodeon": "Cineclub Nickelodeon",
}

_STRIP_PREFIX_RE = re.compile(
    r"^(?:cinema|cineclub|teatro|museo|biblioteca\s+civica|biblioteca\s+internazionale|"
    r"biblioteca\s+comunale|biblioteca|libreria)\s+",
    re.IGNORECASE,
)


_SHARED_PORTAL_HOSTS = frozenset({
    "bibliotechedigenova.it",
    "botteghestorichegenova.it",
    "museidigenova.it",
    "visitgenoa.it",
    "teatronazionalegenova.it",
    "circuitocinemagenova.com",
    "parcoantola.it",
    "parcobeigua.it",
    "parcoaveto.it",
    "cittametropolitana.genova.it",
    "chiavariturismo.it",
    "arenzanoturismo.it",
    "fondoambiente.it",
    "sites.google.com",
    "cultura.gov.it",
})

_CANONICAL_VENUE_PATTERNS = (
    ("polomusealedinervi", re.compile(r"polo\s+museale\s+di\s+nervi|gam[- ]galleria\s+d['’]?arte\s+moderna")),
    ("parchidinervi", re.compile(r"parchi[- ]di[- ]nervi|passeggiata\s+(?:anita\s+garibaldi|di\s+nervi)")),
    ("parcodellemura", re.compile(r"parco[- ](?:urbano[- ])?delle[- ]mura|funicolare\s+zecca")),
    ("teatrosocialecamogli", re.compile(r"teatro\s+sociale(?:\s+di\s+camogli)?\b|teatrosocialecamogli\.it")),
    ("berio", re.compile(r"biblioteca\s+(?:civica\s+)?berio\b")),
    ("deamicis", re.compile(r"biblioteca\s+de\s+amicis\b")),
    ("sivori", re.compile(r"\bsivori\b")),
)

_SEO_TAGLINE_RE = re.compile(
    r":\s*(?:Discoteca[^:]*|Concerti(?:\s+dal Vivo|\s+Indipendenti)?[^:]*|"
    r"Live Club[^:]*|Elettronica[^:]*|Serate\s+Social\s+Dance[^:]*|"
    r"Spazio\s+Comune[^:]*|Cocktail\s+Bar[^:]*|Milonga[^:]*|"
    r"Commedia\s+Genovese[^:]*|Opera,\s*Sinfonica[^:]*|"
    r"Chiostro\s+del\s+Seicento[^:]*|Spazio\s+Lettura[^:]*|"
    r"Cinema\s+e\s+Cultura)\s*$",
    re.IGNORECASE,
)

_TITLE_OVERRIDES = {
    "circolo vega e spazi sociali di ponente": "Circolo Vega",
    "genova tango - centro buenos aires": "Genova Tango",
    "teatro sociale": "Teatro Sociale di Camogli",
    "biblioteca civica berio & terrazza sull'antico seminario": "Biblioteca Civica Berio",
}

_ROMAN_STREET_RE = re.compile(r"\b(xx|xii|xi|xvi|xxv)\b", re.IGNORECASE)
_DOT_TIME_RE = re.compile(r"\b([01]?\d|2[0-3])\.([0-5]\d)\b")
_CON_TE_APOS_RE = re.compile(r"(?i)\bCon Te'(?!\w)")
_VM_CASE_RE = re.compile(r"\bVm(\d+)\b")
_CAPS_KEEP_UPPER = frozenset({"DJ", "VO", "VM18", "CBA", "MLOL", "BIBI", "GAM", "FAI", "IGP", "USA", "I", "II", "III", "IV"})
_MINOR_IT_WORDS = frozenset({"a", "con", "da", "dal", "dei", "del", "della", "delle", "dello", "di", "e", "ed", "gli", "i", "il", "in", "la", "le", "lo", "nel", "nella", "o", "per", "su", "sul", "sulla", "tra"})


def _norm_ascii(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text or "")
    ascii_only = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", ascii_only).strip().lower()


def _norm_alnum(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", _norm_ascii(text)))


def _normalize_district(zone: str, street: str = "") -> str:
    """Format district labels cleanly, keeping Roman numerals uppercase and omitting street repeats."""
    raw = (zone or "").replace("_", " ").strip().title()
    raw = _ROMAN_STREET_RE.sub(lambda m: m.group(1).upper(), raw)
    if not raw:
        return ""
    street_norm = _norm_ascii(street)
    kept = []
    for part in (p.strip() for p in raw.split("/") if p.strip()):
        p_norm = _norm_ascii(part)
        if street_norm and p_norm and p_norm in street_norm:
            continue
        kept.append(part)
    return " / ".join(kept)


def _format_place(street: str, zone: str) -> str:
    """Join street address and non-redundant district cleanly."""
    street_clean = _ROMAN_STREET_RE.sub(lambda m: m.group(1).upper(), (street or "").strip())
    district_clean = _normalize_district(zone, street=street_clean)
    if street_clean and district_clean:
        return f"{street_clean}, {district_clean}"
    return street_clean or district_clean


def _humanize_caps_segment(seg: str) -> str:
    letters = [ch for ch in seg if ch.isalpha()]
    if len(letters) < 5:
        return seg
    upper_ratio = sum(1 for ch in letters if ch.isupper()) / len(letters)
    if upper_ratio < 0.72:
        return seg
    words = seg.split(" ")
    out = []
    seen_word = False
    for w in words:
        if not w:
            continue
        bare = re.sub(r"^[^\w]+|[^\w]+$", "", w)
        if bare.upper() in _CAPS_KEEP_UPPER:
            out.append(w.upper())
        elif seen_word and bare.lower() in _MINOR_IT_WORDS:
            out.append(w.lower())
        elif re.match(r"^[A-Za-z]+['’][A-Za-z]+$", w):
            head, tail = re.split(r"['’]", w, maxsplit=1)
            out.append(f"{head.lower()}'{tail.capitalize()}")
        else:
            out.append(w[:1].upper() + w[1:].lower())
        if bare:
            seen_word = True
    return " ".join(out)


def _clean_programme_title(title: str) -> str:
    t = re.sub(r"\s+", " ", (title or "").strip())
    t = _CON_TE_APOS_RE.sub("Con Te", t)
    t = _VM_CASE_RE.sub(lambda m: f"VM{m.group(1)}", t)
    if ":" in t:
        head, tail = t.split(":", 1)
        t = f"{_humanize_caps_segment(head.strip())}: {_humanize_caps_segment(tail.strip())}"
    else:
        t = _humanize_caps_segment(t)
    t = re.sub(r"\bV\.o\.", "V.O.", t, flags=re.IGNORECASE)
    return t.strip()


def _clean_programme_quando(quando: str) -> str:
    q = re.sub(r"\s+", " ", (quando or "").strip())
    return _DOT_TIME_RE.sub(r"\1:\2", q)


def _clean_programme_list(items) -> list:
    """Normalize showtime formatting, de-shout ALL CAPS, and fold duplicate V.O. film variants."""
    cleaned = []
    seen = set()
    for p in items or []:
        t = _clean_programme_title(p.get("titolo", ""))
        q = _clean_programme_quando(p.get("quando", ""))
        if not t:
            continue
        key = (_norm_ascii(t), _norm_ascii(q))
        if key in seen:
            continue
        seen.add(key)
        cleaned.append({"titolo": t, "quando": q})

    base_items = []
    vo_items = []
    for item in cleaned:
        if re.search(r"(?:^|\s|-)v\.o\.?$", item["titolo"], re.IGNORECASE):
            vo_items.append(item)
        else:
            base_items.append(item)

    merged = [dict(x) for x in base_items]
    for vo in vo_items:
        vo_stripped = re.sub(r"\s*-?\s*v\.o\.?$", "", vo["titolo"], flags=re.IGNORECASE).strip(" :-")
        vo_norm = _norm_alnum(vo_stripped)
        matched = False
        for target in merged:
            t_norm = _norm_alnum(target["titolo"])
            if len(t_norm) >= 12 and t_norm in vo_norm:
                if vo["quando"]:
                    target["quando"] = f"{target['quando']}; V.O. {vo['quando']}" if target["quando"] else f"V.O. {vo['quando']}"
                matched = True
                break
        if not matched:
            merged.append(vo)
    return merged[:8]


def _url_dedupe_key(url: str) -> str:
    """Return a canonical URL key only when the URL uniquely identifies one venue."""
    if not url:
        return ""
    parsed = urlparse(url.strip())
    host = (parsed.netloc or "").lower().removeprefix("www.")
    if not host or host.startswith("comune.") or ".comune." in host:
        return ""
    path = re.sub(r"-\d+$", "", (parsed.path or "").rstrip("/").lower())
    if host in _SHARED_PORTAL_HOSTS:
        if path in ("", "/it", "/en", "/eventi", "/mostre", "/biblioteca"):
            return ""
        return f"url:{host}{path}"
    if path in ("", "/it", "/en", "/home", "/eventi", "/mostre", "/spettacoli", "/programma"):
        return f"host:{host}"
    return f"url:{host}{path}"


def _venue_dedupe_key(o) -> str:
    """Canonical venue key merging accented/prefixed/alias duplicates (e.g. Sivori / Cinema Sivori)."""
    haystack = _norm_ascii(f"{o.venue} {o.title} {o.verified_url}")
    for canonical, pattern in _CANONICAL_VENUE_PATTERNS:
        if pattern.search(haystack):
            return canonical
    url_key = _url_dedupe_key(o.verified_url or "")
    if url_key:
        return url_key
    raw = _norm_ascii(o.venue or o.title or o.id)
    raw = raw.split(":")[0].split("&")[0].split("(")[0].strip()
    core = _STRIP_PREFIX_RE.sub("", raw).strip()
    tokens = re.findall(r"[a-z0-9]+", core)
    if not tokens:
        tokens = re.findall(r"[a-z0-9]+", raw)
    slug = "".join(tokens[:2])[:22]
    return slug or o.id


def _clean_editorial_title(title: str, venue: str = "") -> str:
    """Produce a clean human-friendly editorial title free of scraping/SEO suffixes."""
    cleaned = _ROBOTIC_SUFFIX_RE.sub("", (title or "").strip()).strip(" :-")
    cleaned = _SEO_TAGLINE_RE.sub("", cleaned).strip(" :-")
    cleaned = re.sub(r"\s+", " ", cleaned)
    c_norm = _norm_ascii(cleaned)
    if c_norm in _TITLE_OVERRIDES:
        return _TITLE_OVERRIDES[c_norm]
    v_norm = _norm_ascii(venue or cleaned)
    v_core = _STRIP_PREFIX_RE.sub("", v_norm).strip()
    if v_core in _CANONICAL_CINEMA_NAMES and c_norm in {v_core, _norm_ascii(_CANONICAL_CINEMA_NAMES[v_core])}:
        return _CANONICAL_CINEMA_NAMES[v_core]
    if c_norm in _CANONICAL_CINEMA_NAMES:
        return _CANONICAL_CINEMA_NAMES[c_norm]
    return cleaned or (venue or "").strip()


def _dedupe(options):
    """Una sola voce per luogo: fonde i programmi e sceglie la scheda più curata."""
    grouped = {}
    for o in options:
        key = _venue_dedupe_key(o)
        grouped.setdefault(key, []).append(o)

    merged = []
    for entries in grouped.values():
        def quality(opt):
            progs = opt.raw_metadata.get("programma") or []
            is_https = 1 if (opt.verified_url or "").startswith("https://") else 0
            clean_t = _clean_editorial_title(opt.title, opt.venue)
            text_norm = _norm_ascii(f"{opt.title} {opt.venue}")
            wants_cinema = int(
                ("cinema" in text_norm or "cineclub" in text_norm)
                and opt.category == OutingCategory.CINEMA
            )
            is_live = 1 if opt.source_type == "live_web" else 0
            # Prefer matching Cinema category, real programme, live_web, https, and richer metadata
            return (
                wants_cinema,
                len(progs) > 0,
                len(progs),
                is_live,
                is_https,
                -int(bool(_ROBOTIC_SUFFIX_RE.search(opt.title or ""))),
                len(opt.description or ""),
                len(clean_t),
            )

        best = deepcopy(max(entries, key=quality))
        # Merge and clean programme entries across all duplicates for this venue
        raw_prog = []
        for ent in sorted(entries, key=quality, reverse=True):
            raw_prog.extend(ent.raw_metadata.get("programma") or [])
        cleaned_prog = _clean_programme_list(raw_prog)
        if cleaned_prog:
            best.raw_metadata["programma"] = cleaned_prog
        best.title = _clean_editorial_title(best.title, best.venue)
        merged.append(best)
    return merged


PAGE = r"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Questa settimana a Genova</title>
<meta name="description" content="Cinema, mostre, musica, teatri e idee per la settimana a Genova.">
__PWA_HEAD__
<style>
  :root {
    --bg: #faf8f4;
    --ink: #171717;
    --muted: #66635e;
    --line: #e5e0d8;
    --accent: #0f4c81;
    --sel: #f2f6fa;
    --serif: Georgia, "Iowan Old Style", "Palatino Linotype", Palatino, serif;
    --sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    background: var(--bg);
    color: var(--ink);
    font: 16px/1.55 var(--sans);
    -webkit-font-smoothing: antialiased;
    font-variant-numeric: tabular-nums;
  }
  .wrap {
    max-width: 680px;
    margin: 0 auto;
    padding: 0 20px;
  }
  header {
    padding: 20px 0 12px;
  }
  h1 {
    font-family: var(--serif);
    font-weight: 400;
    font-size: clamp(26px, 5vw, 34px);
    line-height: 1.15;
    letter-spacing: -0.02em;
    margin: 0 0 4px;
  }
  .sub {
    margin: 0 0 12px;
    color: var(--muted);
    font-size: 14px;
    letter-spacing: 0.01em;
  }
  .ask {
    width: 100%;
    border: 0;
    border-bottom: 1px solid var(--line);
    background: transparent;
    padding: 8px 0;
    font: 16px/1.4 var(--sans);
    color: var(--ink);
    outline: none;
    border-radius: 0;
  }
  .ask:focus { border-bottom-color: var(--ink); }
  .ask::placeholder { color: #8c8881; }
  .pills {
    display: flex;
    flex-wrap: nowrap;
    overflow-x: auto;
    scrollbar-width: none;
    -webkit-overflow-scrolling: touch;
    gap: 8px;
    margin-top: 12px;
  }
  .pills::-webkit-scrollbar { display: none; }
  .pill {
    flex: 0 0 auto;
    white-space: nowrap;
    min-height: 40px;
    border: 1px solid var(--line);
    background: transparent;
    color: var(--muted);
    border-radius: 999px;
    padding: 8px 14px;
    font: 13px/1.3 var(--sans);
    cursor: pointer;
    transition: border-color 140ms ease, color 140ms ease, background-color 140ms ease;
  }
  .pill:hover { border-color: var(--ink); color: var(--ink); }
  .pill.on {
    background: var(--ink);
    border-color: var(--ink);
    color: var(--bg);
  }
  main { padding-bottom: 130px; }
  .ans {
    margin: 10px 0 6px;
    font-size: 13px;
    color: var(--muted);
    display: none;
  }
  .ans.show { display: block; }
  .card {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 14px;
    padding: 16px 4px;
    border-bottom: 1px solid var(--line);
    cursor: pointer;
    transition: background-color 140ms ease;
  }
  .card:first-child { border-top: 1px solid var(--line); }
  .card.sel, .card:has(> input:checked) {
    background: var(--sel);
    box-shadow: inset 3px 0 0 var(--accent);
    padding-left: 12px;
  }
  .card-content { flex: 1; min-width: 0; }
  .cat-kicker {
    font-size: 11px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 3px;
  }
  .t-row {
    display: flex;
    align-items: baseline;
    gap: 6px;
  }
  .t {
    font-family: var(--serif);
    font-size: 19px;
    line-height: 1.28;
    font-weight: 400;
    color: var(--ink);
  }
  .src-ico {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 28px;
    min-height: 28px;
    color: var(--accent);
    text-decoration: none;
    font-size: 14px;
    border-radius: 6px;
    flex: 0 0 auto;
  }
  .src-ico:hover { background: var(--sel); }
  .m {
    color: var(--muted);
    font-size: 14px;
    margin-top: 3px;
  }
  .d {
    font-size: 14px;
    color: #3a3834;
    margin-top: 6px;
  }
  .prog {
    margin: 8px 0 0;
    padding: 0;
    list-style: none;
    font-size: 14px;
  }
  .prog li {
    padding: 2px 0;
    color: var(--ink);
  }
  .prog li span { color: var(--muted); }
  .more-prog, .more-places {
    min-height: 36px;
    border: 0;
    background: transparent;
    padding: 6px 0;
    margin-top: 2px;
    font: 13px var(--sans);
    color: var(--muted);
    text-decoration: underline;
    text-underline-offset: 3px;
    cursor: pointer;
  }
  .more-prog:hover, .more-places:hover { color: var(--ink); }
  .more-places-wrap {
    padding: 18px 0 8px;
    text-align: left;
  }
  .card input[type="checkbox"] {
    width: 20px;
    height: 20px;
    margin-top: 4px;
    flex: 0 0 auto;
    accent-color: var(--accent);
    cursor: pointer;
  }
  footer {
    color: var(--muted);
    font-size: 12px;
    padding: 18px 0 32px;
  }
  .bar {
    position: fixed;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(250, 248, 244, 0.96);
    backdrop-filter: blur(8px);
    border-top: 1px solid var(--line);
    padding: 10px 20px calc(10px + env(safe-area-inset-bottom));
    display: none;
    z-index: 20;
  }
  .bar.show { display: block; }
  .bar-in {
    max-width: 680px;
    margin: 0 auto;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
  }
  .bar-meta {
    display: flex;
    align-items: center;
    gap: 8px;
    min-width: 0;
  }
  .count { font-size: 14px; color: var(--ink); font-weight: 500; white-space: nowrap; }
  .edit-link {
    min-height: 44px;
    border: 0;
    background: transparent;
    padding: 8px 10px;
    font: 13px var(--sans);
    color: var(--muted);
    text-decoration: underline;
    text-underline-offset: 3px;
    cursor: pointer;
  }
  .bar-actions { display: flex; gap: 8px; flex: 0 0 auto; }
  .btn {
    min-height: 44px;
    border: 1px solid var(--line);
    border-radius: 999px;
    padding: 10px 18px;
    font: 500 14px/1.2 var(--sans);
    cursor: pointer;
  }
  .cp { background: #ffffff; color: var(--ink); }
  .wa { background: #128c7e; border-color: #128c7e; color: #ffffff; }
  .preview-box {
    max-width: 680px;
    margin: 0 auto 10px;
    display: none;
  }
  .preview-box.open { display: block; }
  .preview-edit {
    width: 100%;
    min-height: 115px;
    border: 1px solid var(--line);
    border-radius: 8px;
    padding: 10px;
    font: 14px/1.45 var(--sans);
    background: #ffffff;
    color: var(--ink);
    resize: vertical;
  }
  .preview-tools {
    display: flex;
    justify-content: flex-end;
    margin-top: 8px;
  }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>Questa settimana a Genova</h1>
    <p class="sub">__RANGE__</p>
    <input id="q" class="ask" type="search" placeholder="Cerca film, locali o 'ballare'" autocomplete="off" aria-label="Cerca cosa fare a Genova">
    <div class="pills" id="pills" role="tablist" aria-label="Categorie"></div>
  </header>
  <main>
    <div id="ans" class="ans"></div>
    <div id="list"></div>
    <div id="moreWrap" class="more-places-wrap"></div>
    <footer>Orari e programmi dai siti ufficiali (agg. __UPDATED__). __ATTRIBUTION__</footer>
  </main>
</div>

<div class="bar" id="bar">
  <div class="preview-box" id="previewBox">
    <textarea id="msgEdit" class="preview-edit" aria-label="Modifica il messaggio WhatsApp"></textarea>
    <div class="preview-tools">
      <button class="btn cp" id="copy" type="button">Copia testo</button>
    </div>
  </div>
  <div class="bar-in">
    <div class="bar-meta">
      <span class="count" id="count"></span>
      <button class="edit-link" id="togglePreview" type="button">Modifica</button>
    </div>
    <div class="bar-actions">
      <button class="btn wa" id="send" type="button">Manda su WhatsApp</button>
    </div>
  </div>
</div>

<script>
let DATA = __DATA__;
const LABEL = __LABELS__;
const MACRO_CATS = [
  { id: "stasera", label: "Stasera" },
  { id: "tutto", label: "Tutto" },
  { id: "cinema", label: "Cinema" },
  { id: "mostra", label: "Mostre" },
  { id: "musica_teatro", label: "Musica" }
];
const _params = new URLSearchParams(window.location.search);
let cat = _params.get("cat") || "tutto";
let query = _params.get("q") || "";
let showAlwaysOpen = false;
let showOpenTonight = false;
const expandedProg = new Set();
const SEL_KEY = "genova_civica_sel_v1";
const sel = new Set((() => {
  try { return JSON.parse(localStorage.getItem(SEL_KEY) || "[]"); } catch { return []; }
})());
function persistSel() {
  try { localStorage.setItem(SEL_KEY, JSON.stringify(Array.from(sel))); } catch {}
}
function pruneSel() {
  const valid = new Set(DATA.map(d => d.id));
  let changed = false;
  for (const id of Array.from(sel)) {
    if (!valid.has(id)) {
      sel.delete(id);
      changed = true;
    }
  }
  if (changed) persistSel();
}
function syncUrl() {
  if (!window.history || !window.history.replaceState) return;
  const p = new URLSearchParams();
  if (cat && cat !== "tutto") p.set("cat", cat);
  if (query && query.trim()) p.set("q", query.trim());
  const qs = p.toString();
  window.history.replaceState(null, "", qs ? `?${qs}` : window.location.pathname);
}
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const norm = s => String(s ?? "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
const escRe = s => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
const hasTerm = (text, term) => new RegExp(`(?:^|[^a-z0-9])${escRe(norm(term))}(?:$|[^a-z0-9])`).test(text);

const STOP = new Set(["stasera","oggi","domani","dove","vado","andiamo","andare","cosa","facciamo","fare","ce","c","e","a","in","di","da","per","con","su","tra","fra","il","lo","la","i","gli","le","un","uno","una","mi","ti","ci","si","vi","che","chi","qualcosa","consigli","consiglio","vorrei","voglio","posto","posti","genova","settimana","questa","questo","nel","nella","nei","nelle","al","allo","alla","ai","agli","alle","del","dello","della","dei","degli","delle","se","o","oppure","ma","anche","po","bel","bella","bello","sera","pomeriggio","mattina","notte"]);
const DAYS = ["domenica","lunedi","martedi","mercoledi","giovedi","venerdi","sabato"];
const MONTHS = ["gennaio","febbraio","marzo","aprile","maggio","giugno","luglio","agosto","settembre","ottobre","novembre","dicembre"];
const MONTH_IDX = Object.fromEntries(MONTHS.map((m, i) => [m, i]));

function extractHours(cl) {
  const hrs = [];
  for (const m of cl.matchAll(/\b(\d{1,2}):\d{2}\b/g)) {
    const h = Number(m[1]);
    if (h >= 0 && h <= 23) hrs.push(h <= 4 ? h + 24 : h);
  }
  for (const m of cl.matchAll(/\bore\s+(\d{1,2})(?::\d{2})?(?:\s*[-–]\s*(\d{1,2})(?::\d{2})?)?\b/g)) {
    const h1 = Number(m[1]);
    if (h1 >= 0 && h1 <= 23) hrs.push(h1 <= 4 ? h1 + 24 : h1);
    if (m[2]) {
      const h2 = Number(m[2]);
      if (h2 >= 0 && h2 <= 23) hrs.push(h2 <= 4 ? h2 + 24 : h2);
    }
  }
  return hrs;
}

function monthDayKey(mIdx, day, baseM) {
  let y = 0;
  if (baseM >= 10 && mIdx <= 2) y = 1;
  else if (baseM <= 1 && mIdx >= 10) y = -1;
  return y * 400 + mIdx * 32 + day;
}

function clauseMatchesTonight(cl, itemCat, itemTimeSlot, now) {
  const td = now.getDate();
  const tm = now.getMonth();
  const dow = DAYS[now.getDay()];
  const todayK = tm * 32 + td;

  const hrs = extractHours(cl);
  if (hrs.length > 0 && Math.max(...hrs) < 18) return false;
  if (hrs.length === 0 && /\b(mattina|pomeriggio)\b/.test(cl)) return false;
  if (hrs.length === 0 && !["cinema", "musica", "ritrovo"].includes(itemCat) && itemTimeSlot !== "sera") return false;

  if (/\boggi\b|\bstasera\b/.test(cl)) return true;
  if (new RegExp(`\\b${dow}\\s+${td}\\b`).test(cl)) return true;

  let hasRange = false;
  const rmShort = cl.match(/\b(\d{1,2})\s*[-–]\s*(\d{1,2})\s+([a-z]+)\b/);
  if (rmShort && MONTH_IDX[rmShort[3]] !== undefined) {
    hasRange = true;
    const mi = MONTH_IDX[rmShort[3]];
    if (mi === tm && td >= Number(rmShort[1]) && td <= Number(rmShort[2])) return true;
  }

  const rmLong = cl.match(/\bdal?\s+(?:[a-z]+\s+)?(\d{1,2})(?:\s+([a-z]+))?\s+(?:al?|a)\s+(?:[a-z]+\s+)?(\d{1,2})\s+([a-z]+)\b/);
  if (rmLong && MONTH_IDX[rmLong[4]] !== undefined) {
    hasRange = true;
    const m2 = MONTH_IDX[rmLong[4]];
    const m1 = rmLong[2] && MONTH_IDX[rmLong[2]] !== undefined ? MONTH_IDX[rmLong[2]] : m2;
    const k1 = monthDayKey(m1, Number(rmLong[1]), tm);
    const k2 = monthDayKey(m2, Number(rmLong[3]), tm);
    if (todayK >= k1 && todayK <= k2) return true;
  }

  const rmUntil = cl.match(/\bfino\s+al\s+(\d{1,2})\s+([a-z]+)\b/);
  if (rmUntil && MONTH_IDX[rmUntil[2]] !== undefined) {
    hasRange = true;
    const k2 = monthDayKey(MONTH_IDX[rmUntil[2]], Number(rmUntil[1]), tm);
    if (todayK <= k2) return true;
  }

  if (!hasRange) {
    const single = cl.match(/\b(\d{1,2})\s+([a-z]+)\b/);
    if (single && MONTH_IDX[single[2]] !== undefined) {
      if (Number(single[1]) === td && MONTH_IDX[single[2]] === tm) return true;
    }
  }

  const hasDateWord = /\b(oggi|stasera|luned|marted|mercoled|gioved|venerd|sabat|domenic|gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre|dal?|fino)\b/.test(cl);
  if (!hasDateWord && hrs.length > 0 && Math.max(...hrs) >= 18) return true;
  return false;
}

function getTonightProgs(d, now = new Date()) {
  const progs = d.programma || [];
  return progs.filter(p => {
    const qn = norm(p && p.quando);
    if (!qn) return false;
    return qn.split(/\s*;\s*/).some(cl => clauseMatchesTonight(cl, d.category, d.time_slot, now));
  });
}

function isOpenTonightFallback(d, now = new Date()) {
  if (!["musica", "ritrovo", "cinema"].includes(d.category)) return false;
  const dow = DAYS[now.getDay()];
  const dt = norm(d.day_time);
  if (dt.includes(`${dow} chiuso`)) return false;
  if (d.time_slot === "sera") return true;
  return /\b(20|21|22|23|24|01|02|03|04)[:.]\d{2}\b|\bsera(le)?\b/.test(dt);
}

const INTENTS = [
  { name:"ballare", triggers:["ballare","ballo","balla","danzare","danza","discoteca","dj","djset","club","milonga","tango","swing","lindy","blues dance","salsa","latino","caraibico","pista","movida"], boostTerms:["ballare","ballo","discoteca","club","pista","swing","lindy","blues dance","milonga","tango","dj","count basie","luzzati","zenaswingers","circolo vega","mog","casa mia","menodue","mako","estoril","crazy bull","genova tango","buridda"], cats:["musica","ritrovo"], banner:"Locali e serate dove ballare:" },
  { name:"bere", triggers:["bere","aperitivo","aperitivi","calice","vino","birra","cocktail","drink","pub","enoteca","spritz","caruggi","vicoli","chiacchierare"], boostTerms:["aperitivo","vino","birra","cocktail","bar","luzzati","mog","mercato orientale","carmine","caruggi","ritrovo","caffe","caffetteria","sciamadda","viganotti"], cats:["ritrovo","musica","laboratorio"], banner:"Aperitivi e locali nei caruggi:" },
  { name:"pioggia", triggers:["piove","pioggia","diluvia","coperto","interno","freddo","brutto tempo","chiuso"], boostTerms:["indoor","cinema","mostra","museo","palazzo","biblioteca","teatro","mercato"], cats:["cinema","mostra","biblioteca","musica","laboratorio"], indoorOnly:true, banner:"Proposte al coperto:" },
  { name:"cinema", triggers:["film","cinema","proiezione","proiezioni","pellicola","sottotitoli","lingua originale","sala"], boostTerms:["cinema","cineclub","sivori","cinema america","odeon","nickelodeon","film","proiezioni"], cats:["cinema"], banner:"Cinema in programmazione:" },
  { name:"mostra", triggers:["mostra","mostre","museo","musei","arte","quadri","fotografia","esposizione","palazzo","rolli"], boostTerms:["mostra","museo","palazzo","ducale","strada nuova","reale","spinola","galata","castello","nervi"], cats:["mostra"], banner:"Mostre e musei:" },
  { name:"passeggiata", triggers:["passeggiata","passeggiare","camminare","mare","vista","panorama","tramonto","aperto","sole","parco","borgo","boccadasse","nervi","castelletto","righi","trekking"], boostTerms:["passeggiata","mare","belvedere","boccadasse","nervi","castelletto","righi","acquedotto","parco","borgo"], cats:["passeggiata","altro"], banner:"Passeggiate e percorsi all'aperto:" },
  { name:"mangiare", triggers:["mangiare","cena","cenare","pranzo","focaccia","farinata","cioccolato","dolce","gelato","bottega","assaggiare","fame","sciamadda"], boostTerms:["farinata","cioccolato","confetteria","mog","mercato","friggitoria","forno","pasticceria","bottega"], cats:["laboratorio","ritrovo"], banner:"Botteghe storiche e sapori:" }
];

function analyzeQuery(qRaw) {
  const nq = norm(qRaw);
  if (!nq) return null;
  const matchedIntents = INTENTS.filter(it => it.triggers.some(t => hasTerm(nq, t)));
  const now = new Date();
  let targetDay = null;
  if (/\boggi\b|\bstasera\b|\bstanotte\b/.test(nq)) targetDay = DAYS[now.getDay()];
  else if (/\bdomani\b/.test(nq)) targetDay = DAYS[(now.getDay() + 1) % 7];
  else {
    for (const d of DAYS) if (nq.includes(d)) { targetDay = d; break; }
  }
  const wantEvening = /\b(stasera|sera|serata|notte|tardi|dopo cena)\b/.test(nq);
  const wantWeekend = /\b(weekend|fine settimana)\b/.test(nq);
  const words = nq.split(/[^a-z0-9]+/).filter(w => w.length >= 2 && !STOP.has(w));
  return { nq, matchedIntents, targetDay, wantEvening, wantWeekend, words };
}

function scoreItem(d, info) {
  const progText = (d.programma || []).map(p => `${p.titolo} ${p.quando}`).join(" ");
  const hay = norm(`${d.title} ${d.place} ${d.description} ${d.day_time} ${(d.tags||[]).join(" ")} ${progText}`);
  const progHay = norm(progText);
  const dtHay = norm(d.day_time);
  let score = 0;

  if (info.matchedIntents.length > 0) {
    for (const it of info.matchedIntents) {
      if (it.indoorOnly && d.outdoor) return 0;
      let intentHits = 0;
      for (const term of it.boostTerms) if (hasTerm(hay, term)) intentHits += 4;
      if (it.cats.includes(d.category)) intentHits += 2;
      if (intentHits === 0) return 0;
      if (it.name === "ballare" && (!it.cats.includes(d.category) || intentHits < 6)) return 0;
      score += intentHits;
    }
    if (score === 0) return 0;
  }

  for (const w of info.words) {
    const isIntentWord = info.matchedIntents.some(it => it.triggers.some(tr => norm(tr).includes(w) || w.includes(norm(tr))));
    if (hay.includes(w)) score += 5;
    else if (!isIntentWord && info.matchedIntents.length === 0) return 0;
  }
  if (info.matchedIntents.length === 0 && info.words.length === 0) score = 2;
  if (info.targetDay) {
    if (progHay.includes(info.targetDay)) score += 6;
    if (dtHay.includes(info.targetDay) || dtHay.includes("tutti i giorni")) score += 2;
    if (dtHay.includes(`${info.targetDay} chiuso`)) return 0;
  }
  if (info.wantWeekend && (progHay.includes("venerdi") || progHay.includes("sabato") || progHay.includes("domenica"))) score += 5;
  if (info.wantEvening && (d.time_slot === "sera" || hay.includes("21:") || hay.includes("20:") || hay.includes("serale"))) score += 4;
  if ((d.programma || []).length > 0) score += 12;
  if (info.wantEvening && getTonightProgs(d).length > 0) score += 4;
  return score;
}

function matchesMacroCat(itemCat, macroId) {
  if (macroId === "tutto" || macroId === "stasera") return true;
  if (macroId === "cinema") return itemCat === "cinema";
  if (macroId === "mostra") return itemCat === "mostra";
  if (macroId === "musica_teatro") return itemCat === "musica";
  if (macroId === "altro_macro") return !["cinema", "mostra", "musica"].includes(itemCat);
  return itemCat === macroId;
}

function interleaveByCategory(items) {
  const order = ["musica", "cinema", "mostra", "ritrovo", "biblioteca", "passeggiata", "laboratorio", "altro"];
  const buckets = new Map(order.map(k => [k, []]));
  for (const item of items) {
    if (!buckets.has(item.category)) buckets.set(item.category, []);
    buckets.get(item.category).push(item);
  }
  const out = [];
  let added = true;
  while (added) {
    added = false;
    for (const arr of buckets.values()) {
      if (arr.length) {
        out.push(arr.shift());
        added = true;
      }
    }
  }
  return out;
}

function renderPills() {
  document.getElementById("pills").innerHTML = MACRO_CATS.map(c =>
    `<button class="pill ${c.id === cat ? 'on' : ''}" data-k="${c.id}" type="button">${c.label}</button>`
  ).join("");
  document.querySelectorAll(".pill").forEach(b => b.onclick = () => {
    cat = b.dataset.k;
    showAlwaysOpen = false;
    showOpenTonight = false;
    syncUrl();
    renderPills();
    render();
  });
}

function render() {
  const info = analyzeQuery(query);
  const ansEl = document.getElementById("ans");
  let pool = DATA.filter(d => matchesMacroCat(d.category, cat));
  let hiddenAlwaysOpen = 0;
  let hiddenTonightOpen = 0;

  if (info) {
    const scored = pool.map(d => ({ d, s: scoreItem(d, info) })).filter(x => x.s > 0).sort((a, b) => b.s - a.s);
    pool = scored.map(x => x.d);
    ansEl.textContent = pool.length
      ? (info.matchedIntents.length ? info.matchedIntents[0].banner : `${pool.length} proposte trovate`)
      : `Nessuna proposta per "${query.trim()}".`;
    ansEl.classList.add("show");
  } else if (cat === "stasera") {
    const tonightDated = interleaveByCategory(pool.filter(d => getTonightProgs(d).length > 0));
    const tonightOpen = pool.filter(d => getTonightProgs(d).length === 0 && isOpenTonightFallback(d));
    ansEl.textContent = tonightDated.length
      ? `${tonightDated.length} proposte con orario per stasera:`
      : "Nessun evento datato trovato per stasera.";
    ansEl.classList.add("show");
    if (showOpenTonight) {
      pool = tonightDated.concat(tonightOpen);
    } else {
      hiddenTonightOpen = tonightOpen.length;
      pool = tonightDated.length ? tonightDated : tonightOpen;
    }
  } else {
    ansEl.classList.remove("show");
    let withProg = pool.filter(d => (d.programma || []).length > 0);
    if (cat === "tutto") withProg = interleaveByCategory(withProg);
    const alwaysOpen = pool.filter(d => (d.programma || []).length === 0);
    if (!showAlwaysOpen && withProg.length > 0) {
      hiddenAlwaysOpen = alwaysOpen.length;
      pool = withProg;
    } else if (showAlwaysOpen) {
      pool = withProg.concat(alwaysOpen);
    }
  }

  const showKicker = Boolean(info) || cat === "tutto" || cat === "stasera";
  document.getElementById("list").innerHTML = pool.map(d => {
    const rawProgs = d.programma || [];
    const tonightProgs = (!info && cat === "stasera") ? getTonightProgs(d) : [];
    const progs = tonightProgs.length ? tonightProgs : rawProgs;
    const showAll = expandedProg.has(d.id);
    const shown = showAll ? progs : progs.slice(0, 2);
    const progHtml = shown.length
      ? `<ul class="prog">${shown.map(p => `<li>${esc(p.titolo)} <span>${esc(p.quando)}</span></li>`).join("")}</ul>`
        + (progs.length > 2 ? `<button type="button" class="more-prog" data-more="${esc(d.id)}">${showAll ? "Mostra meno" : `Vedi tutto (+${progs.length - 2})`}</button>` : "")
      : "";
    const safeHref = /^https?:\/\//i.test(String(d.url || "").trim()) ? d.url.trim() : "";
    const catName = LABEL[d.category] || d.category;
    return `<label class="card ${sel.has(d.id)?'sel':''}" data-id="${esc(d.id)}" role="checkbox" aria-checked="${sel.has(d.id)?'true':'false'}" tabindex="0">
      <div class="card-content">
        ${showKicker ? `<div class="cat-kicker">${esc(catName)}</div>` : ""}
        <div class="t-row"><span class="t">${esc(d.title)}</span>${safeHref ? `<a class="src-ico" href="${esc(safeHref)}" target="_blank" rel="noopener" title="Sito ufficiale" aria-label="Sito ufficiale di ${esc(d.title)}">↗</a>` : ""}</div>
        <div class="m">${esc(d.place)}</div>
        ${(!progs.length && d.day_time) ? `<div class="m">${esc(d.day_time)}</div>` : ""}
        ${(!progs.length && d.description) ? `<div class="d">${esc(d.description)}</div>` : ""}
        ${progHtml}
      </div>
      <input type="checkbox" ${sel.has(d.id)?'checked':''} title="Seleziona per WhatsApp" aria-label="Scegli ${esc(d.title)}">
    </label>`;
  }).join("");

  const moreWrap = document.getElementById("moreWrap");
  if (!info && cat === "stasera" && (hiddenTonightOpen > 0 || showOpenTonight)) {
    moreWrap.innerHTML = showOpenTonight
      ? `<button type="button" class="more-places" id="toggleOpenTonight">Mostra solo eventi con orario</button>`
      : `<button type="button" class="more-places" id="toggleOpenTonight">Mostra altri locali aperti stasera (+${hiddenTonightOpen})</button>`;
    document.getElementById("toggleOpenTonight").onclick = () => {
      showOpenTonight = !showOpenTonight;
      render();
    };
  } else if (!info && cat !== "stasera" && (hiddenAlwaysOpen > 0 || showAlwaysOpen)) {
    moreWrap.innerHTML = showAlwaysOpen
      ? `<button type="button" class="more-places" id="toggleAlwaysOpen">Mostra solo la programmazione della settimana</button>`
      : `<button type="button" class="more-places" id="toggleAlwaysOpen">Mostra anche luoghi sempre aperti (+${hiddenAlwaysOpen})</button>`;
    document.getElementById("toggleAlwaysOpen").onclick = () => {
      showAlwaysOpen = !showAlwaysOpen;
      render();
    };
  } else {
    moreWrap.innerHTML = "";
  }

  document.querySelectorAll(".more-prog").forEach(btn => {
    btn.onclick = e => {
      e.preventDefault();
      e.stopPropagation();
      const id = btn.dataset.more;
      expandedProg.has(id) ? expandedProg.delete(id) : expandedProg.add(id);
      render();
    };
  });

  document.querySelectorAll(".src-ico").forEach(a => {
    a.onclick = e => e.stopPropagation();
  });

  document.querySelectorAll(".card").forEach(c => {
    const toggle = () => {
      const id = c.dataset.id;
      sel.has(id) ? sel.delete(id) : sel.add(id);
      persistSel();
      render(); bar();
    };
    c.onclick = e => {
      if (e.target.closest("a, button")) return;
      if (e.target.tagName === "INPUT") {
        const id = c.dataset.id;
        e.target.checked ? sel.add(id) : sel.delete(id);
        persistSel();
        render(); bar();
        return;
      }
      e.preventDefault();
      toggle();
    };
    c.onkeydown = e => {
      if (e.target.closest("a, button") || e.target.tagName === "INPUT") return;
      if (e.key === " " || e.key === "Enter") {
        e.preventDefault();
        toggle();
      }
    };
  });
}

function cleanPlain(s) {
  return String(s || "").replace(/[\u2014\u2013\u2015]/g, "-").replace(/\s+/g, " ").trim();
}

function message() {
  const chosen = DATA.filter(d => sel.has(d.id));
  if (!chosen.length) return "";
  const head = chosen.length === 1
    ? "Ho visto questa cosa a Genova questa settimana, se ti va:"
    : "Ti lascio un paio di idee per questa settimana a Genova:";
  const body = chosen.map(d => {
    const progs = (d.programma || []).slice(0, 3);
    const when = progs.length
      ? progs.map(p => `- ${cleanPlain(p.titolo)} (${cleanPlain(p.quando)})`).join("\n  ")
      : cleanPlain(d.day_time);
    const safeHref = /^https?:\/\//i.test(String(d.url || "").trim()) ? String(d.url).trim().replace(/[.,;:!?)]+$/, "") : "";
    const lines = [`• *${cleanPlain(d.title)}*`, `  ${cleanPlain(d.place)}`, `  ${when}`];
    if (safeHref) lines.push(`  Info: ${safeHref}`);
    return lines.join("\n");
  }).join("\n\n");
  const tail = chosen.length === 1 ? "Dimmi se ti ispira!" : "Dimmi se ti ispira qualcosa!";
  return `${head}\n\n${body}\n\n${tail}`;
}

function getMessageText() {
  const box = document.getElementById("previewBox");
  const ed = document.getElementById("msgEdit");
  if (box && box.classList.contains("open") && ed && ed.value.trim()) {
    return ed.value;
  }
  return message();
}

function bar() {
  const n = sel.size;
  document.getElementById("bar").classList.toggle("show", n > 0);
  document.getElementById("count").textContent = n === 1 ? "1 scelta" : `${n} scelte`;
  const ed = document.getElementById("msgEdit");
  if (ed) ed.value = message();
}

const qIn = document.getElementById("q");
qIn.oninput = e => {
  query = e.target.value;
  if (query && cat !== "tutto") { cat = "tutto"; renderPills(); }
  syncUrl();
  render();
};

document.getElementById("togglePreview").onclick = () => {
  const box = document.getElementById("previewBox");
  box.classList.toggle("open");
  if (box.classList.contains("open")) document.getElementById("msgEdit").value = message();
};
document.getElementById("send").onclick = () => window.open("https://wa.me/?text=" + encodeURIComponent(getMessageText()), "_blank");
document.getElementById("copy").onclick = async () => {
  try { await navigator.clipboard.writeText(getMessageText()); document.getElementById("copy").textContent = "Copiato"; }
  catch { prompt("Copia il testo:", getMessageText()); }
  setTimeout(() => document.getElementById("copy").textContent = "Copia testo", 1500);
};

if (query) qIn.value = query;
pruneSel();
renderPills(); render(); bar();

if (location.protocol.startsWith("http")) {
  fetch("./data/events.json")
    .then(r => r.ok ? r.json() : null)
    .then(rows => {
      if (!Array.isArray(rows) || !rows.length) return;
      DATA = rows.map(r => ({
        id: r.id,
        category: r.category,
        title: r.title,
        place: [r.address || r.venue, r.district].filter(Boolean).join(", "),
        day_time: r.day_time || "",
        description: r.summary || "",
        url: r.url || "",
        programma: r.showtimes || [],
        tags: r.tags || [],
        outdoor: Boolean(r.outdoor),
        time_slot: r.time_slot || "flessibile"
      }));
      pruneSel();
      renderPills(); render(); bar();
    })
    .catch(() => {});
}
</script>
__PWA_SW__
</body>
</html>
"""


def build(out_dir: Path) -> Path:
    options = get_weekly_catalog(live_verify=True)
    attach_programmes(options)
    options = _dedupe(options)
    options.sort(key=editorial_sort_key)
    data = []
    for o in options:
        data.append({
            "id": o.id,
            "category": o.category.value,
            "title": o.title,
            "place": _format_place(o.address or o.venue, o.zone),
            "day_time": o.day_time,
            "description": o.description,
            "url": o.verified_url,
            "programma": o.raw_metadata.get("programma") or [],
            "tags": o.tags or [],
            "outdoor": bool(o.is_weather_dependent),
            "time_slot": o.time_slot or "flessibile",
        })
    today = date.today()
    end = today + timedelta(days=7)
    if today.month == end.month:
        rng = f"{today.day}–{end.day} {MESI[today.month-1]}"
    else:
        rng = f"{today.day} {MESI[today.month-1]} – {end.day} {MESI[end.month-1]}"
    page = (
        PAGE.replace("__PWA_HEAD__", PWA_HEAD_HTML)
        .replace("__PWA_SW__", PWA_SW_SCRIPT)
        .replace("__ATTRIBUTION__", html.escape(OPEN_DATA_ATTRIBUTION_TEXT))
        .replace("__DATA__", safe_json_for_script(data))
        .replace("__LABELS__", safe_json_for_script(CAT_LABEL))
        .replace("__RANGE__", html.escape(rng))
        .replace("__UPDATED__", f"{today.day} {MESI[today.month-1]} {today.year}")
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / "index.html"
    target.write_text(page, encoding="utf-8")
    print(f"{len(data)} schede, {sum(1 for d in data if d['programma'])} con programma -> {target}")
    return target


if __name__ == "__main__":
    build(Path(sys.argv[1] if len(sys.argv) > 1 else "site"))
