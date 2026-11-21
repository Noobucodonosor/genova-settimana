"""Legge la programmazione attuale dai siti ufficiali dei locali.

Ogni estrattore restituisce una lista di dict {"titolo": str, "quando": str},
limitata ai prossimi 7 giorni quando il sito riporta le date. Se un sito non
risponde o cambia formato, la funzione restituisce una lista vuota: la scheda
resta valida, senza programma.
"""

from __future__ import annotations

import html
import json
import logging
import re
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from typing import Callable, Dict, List, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 Chrome/124 Safari/537.36"
MAX_ITEMS = 8
MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio",
        "agosto", "settembre", "ottobre", "novembre", "dicembre"]
GIORNI = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]

_cache: Dict[str, List[Dict[str, str]]] = {}


def _get(url: str, timeout: float = 10.0) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    last_exc: Optional[Exception] = None
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", errors="ignore")
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_exc = exc
            if attempt == 0:
                time.sleep(0.8)
    raise last_exc  # type: ignore[misc]


def _txt(fragment: str) -> str:
    s = re.sub(r"<[^>]+>", " ", fragment)
    s = html.unescape(s).replace("\u2013", "-").replace("\u2014", "-")
    return re.sub(r"\s+", " ", s).strip()


def _month(name: str) -> Optional[int]:
    n = name.lower()[:3]
    for i, m in enumerate(MESI, 1):
        if m.startswith(n):
            return i
    return None


def _in_window(d: date, today: date) -> bool:
    return today <= d <= today + timedelta(days=7)


def _fmt(d: date) -> str:
    return f"{GIORNI[d.weekday()]} {d.day} {MESI[d.month - 1]}"


def _mkdate(day: int, month: int, today: date) -> Optional[date]:
    try:
        d = date(today.year, month, day)
    except ValueError:
        return None
    if d < today - timedelta(days=60):  # dicembre -> gennaio
        d = date(today.year + 1, month, day)
    return d


# ---------------------------------------------------------------- estrattori

def circuito_cinema(url: str, today: date) -> List[Dict[str, str]]:
    """circuitocinemagenova.com: titoli + orari per giorno (tab data-day)."""
    page = _get(url)
    labels = {k: v.strip() for k, v in re.findall(r'data-day="(\d+)"[^>]*>\s*([^<]+)<', page)}
    out = []
    for block in page.split('class="single-film"')[1:]:
        m = re.search(r'class="titolo_film"[^>]*>(.*?)</p>', block, re.S)
        if not m:
            continue
        title = _txt(m.group(1)).title()
        days = []
        for dk, inner in re.findall(r"class='day_block' data-day='(\d+)'>(.*?)</div>", block, re.S):
            times = re.findall(r"\b\d{1,2}:\d{2}\b", inner)
            if times:
                days.append(f"{labels.get(dk, '')} {' '.join(times)}".strip())
        if days:
            out.append({"titolo": title, "quando": "; ".join(days[:3])})
    return out


def nickelodeon(url: str, today: date) -> List[Dict[str, str]]:
    """cineclubnickelodeon.it: tab per giorno con h3 titolo e orari."""
    page = _get(url)
    # Il sito etichetta i tab "Giorno N" e li rinomina via JS: Giorno 1 = oggi.
    labels = {str(i): _fmt(today + timedelta(days=i - 1)) for i in range(1, 8)}
    out, seen = [], {}
    for tab, body in re.findall(r'class="jet-tabs__content[^"]*" data-tab="(\d+)"(.*?)(?=class="jet-tabs__content|\Z)', page, re.S):
        for h3, orari in re.findall(r"<h3>(.*?)</h3>\s*<span class=\"orari\">(.*?)</span>", body, re.S):
            title = _txt(h3).title()
            when = f"{labels.get(tab, '')} {_txt(orari)}".strip()
            if title in seen:
                if len(seen[title]["quando"]) < 90:
                    seen[title]["quando"] += f"; {when}"
                continue
            seen[title] = {"titolo": title, "quando": when}
            out.append(seen[title])
    return out


def count_basie(url: str, today: date) -> List[Dict[str, str]]:
    """countbasie.it: lista mensile, blocchi Giorno | Mese | GG | titolo."""
    out = []
    for offset in (0, 1):
        y, m = today.year, today.month + offset
        if m > 12:
            y, m = y + 1, 1
        try:
            page = _get(f"https://www.countbasie.it/programmazione/{y}/{m:02d}/lista-eventi.html")
        except Exception:
            continue
        page = re.sub(r"<script.*?</script>|<style.*?</style>", "", page, flags=re.S)
        flat = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " | ", page)))
        pat = r"(?:Luned|Marted|Mercoled|Gioved|Venerd|Sabato|Domenica)\S* \|[ |]*([A-Z][a-z]+) \|[ |]*(\d{1,2}) \|(.*?)Leggi tutto"
        for mese, gg, rest in re.findall(pat, flat):
            mm = _month(mese)
            d = _mkdate(int(gg), mm, today) if mm else None
            if not d or not _in_window(d, today):
                continue
            parts = [re.sub(r'["\s>]+$', "", p).strip() for p in rest.split("|")]
            parts = [p for p in parts if len(p) > 2 and "[...]" not in p]
            if not parts:
                continue
            title = " ".join(parts[:2]) if len(parts) > 1 and len(parts[0]) < 30 else parts[0]
            out.append({"titolo": title, "quando": _fmt(d)})
    return out


def tribe_events(url: str, today: date) -> List[Dict[str, str]]:
    """WordPress The Events Calendar (es. Teatro Sociale di Camogli)."""
    base = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
    end = today + timedelta(days=7)
    data = json.loads(_get(f"{base}/wp-json/tribe/events/v1/events?per_page=20"
                           f"&start_date={today.isoformat()}&end_date={end.isoformat()}"))
    out = []
    for ev in data.get("events", []):
        try:
            d = date.fromisoformat(ev["start_date"][:10])
        except Exception:
            continue
        if _in_window(d, today):
            out.append({"titolo": _txt(ev.get("title", "")), "quando": f"{_fmt(d)} ore {ev['start_date'][11:16]}"})
    return out


def teatro_nazionale(url: str, today: date) -> List[Dict[str, str]]:
    """teatronazionalegenova.it: EventBox con Title, Date (GG o GG - GG Mese), Location."""
    page = _get("https://www.teatronazionalegenova.it/")
    sala = urlparse(url).path.rstrip("/").split("/")[-1].replace("-", " ") if "spettacolo_sala" in url else ""
    sala_token = sala.split()[-1].lower() if sala else ""
    out = []
    for title, dt, loc in re.findall(r'<p class="Title">(.*?)</p>\s*<p class="Date">(.*?)</p>\s*<p class="Location">(.*?)</p>', page, re.S):
        title, dt, loc = _txt(title), _txt(dt), _txt(loc)
        loc_low = loc.lower()
        if sala_token and sala_token not in loc_low and not (sala_token == "modena" and "gustavo modena" in loc_low):
            continue
        m = re.match(r"(\d{1,2})(?:\s*-\s*(\d{1,2}))?\s+(\w+)", dt)
        mm = _month(m.group(3)) if m else None
        if not mm:
            continue
        start = _mkdate(int(m.group(1)), mm, today)
        stop = _mkdate(int(m.group(2) or m.group(1)), mm, today)
        if start and stop and start <= today + timedelta(days=7) and stop >= today:
            out.append({"titolo": title, "quando": f"{dt}, {loc}"})
    return out


def carlo_felice(url: str, today: date) -> List[Dict[str, str]]:
    """carlofelice.it: slide con heading (titolo) e description (data)."""
    page = _get("https://carlofelice.it/")
    out, seen = [], set()
    for title, desc in re.findall(r'elementor-slide-heading">(.*?)</div><div class="elementor-slide-description">(.*?)</div>', page, re.S):
        title, desc = _txt(title), _txt(desc)
        m = re.search(r"(?:Dal{1,2}[’' ]\s*(\d{1,2})\s+al\s+)?(\d{1,2})\s+(\w+)\s+(\d{4})", desc)
        mm = _month(m.group(3)) if m else None
        if not mm or title in seen:
            continue
        stop = _mkdate(int(m.group(2)), mm, today)
        start = _mkdate(int(m.group(1)), mm, today) if m.group(1) else stop
        if start and stop and start <= today + timedelta(days=7) and stop >= today:
            seen.add(title)
            out.append({"titolo": title.replace("_", " "), "quando": desc})
    return out


def _safe_date(year: int, month: int, day: int) -> Optional[date]:
    try:
        return date(year, month, day)
    except ValueError:
        return None


def parse_range(text: str, today: date) -> tuple[Optional[date], Optional[date]]:
    """Estrae (inizio, fine) da testi tipo '25 Set — 08 Dic 2026', 'Dal 12 novembre 2026 al 28
    febbraio 2027', '4-5 Novembre 2026', '13 novembre 2026', '26.11.2026'."""
    t = text.lower().replace("\u2014", "-").replace("\u2013", "-")
    m = re.search(r"\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b", t)
    if m:
        d = _safe_date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        return (d, d) if d else (None, None)
    # "4-5 novembre" / "13 - 14 nov 2026": un mese per due giorni
    m = re.search(r"\b(\d{1,2})\s*-\s*(\d{1,2})\s+([a-z]{3,9})\.?(?:\s+(\d{4}))?", t)
    if m and _month(m.group(3)):
        mm = _month(m.group(3))
        if m.group(4):
            yr = int(m.group(4))
            return _safe_date(yr, mm, int(m.group(1))), _safe_date(yr, mm, int(m.group(2)))
        return _mkdate(int(m.group(1)), mm, today), _mkdate(int(m.group(2)), mm, today)
    toks = [
        (int(d), _month(mo), int(yr) if yr else None)
        for d, mo, yr in re.findall(r"\b(\d{1,2})\s+([a-z]{3,9})\.?(?:\s+(\d{4}))?\b", t)
        if _month(mo)
    ]
    if not toks:
        return None, None
    d1, m1, y1 = toks[0]
    d2, m2, y2 = toks[-1]
    if y1 is None and y2 is not None:
        y1 = y2 if (m1, d1) <= (m2, d2) else y2 - 1
    start = _safe_date(y1, m1, d1) if y1 is not None else _mkdate(d1, m1, today)
    end = _safe_date(y2, m2, d2) if y2 is not None else _mkdate(d2, m2, today)
    if start and end and end < start and y2 is None:
        end = _safe_date(end.year + 1, end.month, end.day)
    return start, end


def _span_label(start: date, end: date, today: date) -> str:
    if start == end:
        return _fmt(start)
    if start <= today:
        return f"in corso fino {'all\'' if end.day in (8, 11) else 'al '}{end.day} {MESI[end.month - 1]}"
    first = f"{GIORNI[start.weekday()]} {start.day}" + ("" if start.month == end.month else f" {MESI[start.month - 1]}")
    return f"da {first} a {_fmt(end)}"


def _keep(start, end, today) -> bool:
    return bool(start and end and start <= today + timedelta(days=7) and end >= today)


def palazzo_ducale(url: str, today: date, hint: str = "") -> List[Dict[str, str]]:
    """palazzoducale.genova.it: mostre in corso (titolo + sala + periodo)."""
    page = _get("https://palazzoducale.genova.it/mostre/")
    out, seen = [], set()
    for title, info in re.findall(r'submenu-item-title">(.*?)</p>\s*<p class="submenu-item-info">(.*?)</p>', page, re.S):
        title = _txt(title)
        parts = re.split(r"<br\s*/?>", info)
        where = _txt(parts[0]) if len(parts) > 1 else ""
        start, end = parse_range(_txt(parts[-1]), today)
        if title in seen or not _keep(start, end, today):
            continue
        seen.add(title)
        out.append({"titolo": title, "quando": f"{_span_label(start, end, today)}, {where}".strip(", ")})
    return out


def galata(url: str, today: date) -> List[Dict[str, str]]:
    """galatamuseodelmare.it: blocchi tipologia / data / titolo."""
    page = _get("https://www.galatamuseodelmare.it/")
    out = []
    for tipo, when, title in re.findall(
            r'class="tipologia">(.*?)</p>\s*<p class="data">(.*?)</p>.*?class="titolo">(.*?)</h3>', page, re.S):
        start, end = parse_range(_txt(when), today)
        if _keep(start, end, today):
            out.append({"titolo": _txt(title), "quando": f"{_txt(tipo)}, {_span_label(start, end, today)}"})
    return out


_BIBLIO_KEYS = ["berio", "de amicis", "lercari", "guerrazzi", "cervetto", "bruschi", "saffi", "gallino",
                "brocchi", "campanella", "benzi", "firpo", "podestà", "piersantelli", "palasciano", "servitana"]


def biblioteche_genova(url: str, today: date, hint: str = "") -> List[Dict[str, str]]:
    """bibliotechedigenova.it/eventi: incontri e presentazioni, filtrati sulla biblioteca della scheda."""
    page = _get("https://www.bibliotechedigenova.it/eventi")
    key = next((k for k in _BIBLIO_KEYS if k in f"{hint} {url}".lower().replace("-", " ")), "")
    out = []
    for title, rest in re.findall(r"class='cs-titolo'><a[^>]*>(.*?)</a>(.*?)class='cs-icons'", page, re.S):
        dates = [_txt(x) for x in re.findall(r"class='cs-data'>(.*?)</div>", rest, re.S)]
        where = _txt((re.findall(r"class='cs-body'>(.*?)</div>", rest, re.S) or [""])[0])
        if key and key not in where.lower():
            continue
        start, end = parse_range(dates[0] if dates else "", today)
        if not _keep(start, end, today):
            continue
        ora = f" {dates[1]}" if len(dates) > 1 else ""
        out.append({"titolo": _txt(title), "quando": f"{_fmt(start)}{ora}" + ("" if key else f", {where}")})
    return out


def politeama(url: str, today: date) -> List[Dict[str, str]]:
    """politeamagenovese.it: griglia con artista (el-3), titolo (el-4), data (el-1)."""
    page = _get("https://www.politeamagenovese.it/")
    out, seen = [], set()
    for post in set(re.findall(r"eg-post-(\d+)", page)):
        f = {n: _txt(v) for n, v in re.findall(
            rf'eg-teatro-element-(\d) eg-post-{post}[^"]*">(.*?)</div>', page, re.S)}
        if "1" not in f:
            continue
        start, end = parse_range(f["1"], today)
        title = " : ".join(x for x in (f.get("3"), f.get("4")) if x).replace(" : ", ", ")
        if title and title not in seen and _keep(start, end, today):
            seen.add(title)
            out.append({"titolo": title, "quando": f["1"], "_d": start.isoformat()})
    out.sort(key=lambda x: x.pop("_d"))
    return out


def teatro_tosse(url: str, today: date, hint: str = "") -> List[Dict[str, str]]:
    """teatrodellatosse.it/eventi: blocchi Hevent con mese, giorni, sala e titolo."""
    page = _get("https://www.teatrodellatosse.it/eventi/")
    want_claque = "claque" in f"{hint} {url}".lower()
    out = []
    for block in page.split('class="Hevent"')[1:]:
        months = [_txt(m) for m in re.findall(r'EventDate_Month[^>]*>(.*?)</span>', block, re.S)]
        days = re.findall(r"(?:<span>|EventDate_Day[^>]*>)(\d{1,2})</span>", block.split("Titles")[0])
        title = _txt((re.findall(r'class="Title notranslate"[^>]*>(.*?)</span>', block, re.S) or [""])[0])
        loc = _txt((re.findall(r'EventLocation[^>]*>(.*?)</p>', block, re.S) or [""])[0])
        if not (months and days and title):
            continue
        if want_claque and "claque" not in loc.lower():
            continue
        mm1, mm2 = _month(months[0]), _month(months[-1])
        start = _mkdate(int(days[0]), mm1, today) if mm1 else None
        end = _mkdate(int(days[-1]), mm2, today) if mm2 else None
        if _keep(start, end, today):
            out.append({"titolo": title, "quando": f"{_span_label(start, end, today)}, {loc}".strip(", ")})
    return out


def crazy_bull(url: str, today: date) -> List[Dict[str, str]]:
    """crazybullgenova.it/eventi: card <article class='event-card'> con datetime ISO e titolo."""
    page = _get("https://www.crazybullgenova.it/eventi")
    out, seen = [], set()
    for card in re.findall(r'<article[^>]+class="[^"]*event-card[^"]*"[^>]*>(.*?)</article>', page, re.S):
        m_dt = re.search(r'datetime="(\d{4}-\d{2}-\d{2})', card)
        m_title = re.search(r"<h3[^>]*>(.*?)</h3>", card, re.S)
        if not (m_dt and m_title):
            continue
        try:
            d = date.fromisoformat(m_dt.group(1))
        except ValueError:
            continue
        if not _in_window(d, today):
            continue
        title = _txt(m_title.group(1))
        if not title or title in seen:
            continue
        seen.add(title)
        m_time = re.search(r'class="event-card-time"[^>]*>(?:<span[^>]*>[^<]*</span>)?\s*([^<]+)<', card)
        tm = _txt(m_time.group(1)) if m_time else ""
        when = f"{_fmt(d)} {tm}".strip()
        out.append({"titolo": title, "quando": when})
    return out


def genova_tango(url: str, today: date) -> List[Dict[str, str]]:
    """genovatango.com/eventi/: card milonghe ed eventi tango con <p class='event-date'> e <h3>."""
    page = _get("https://www.genovatango.com/eventi/")
    out, seen = [], set()
    weekday_re = re.compile(
        r"\b(luned[iì]|marted[iì]|mercoled[iì]|gioved[iì]|venerd[iì]|sabato|domenica)\b",
        re.IGNORECASE,
    )
    for card in re.findall(r'<article[^>]+class="[^"]*event-card[^"]*"[^>]*>(.*?)</article>', page, re.S):
        m_dt = re.search(r'<p[^>]+class="[^"]*event-date[^"]*"[^>]*>(.*?)</p>', card, re.S)
        m_title = re.search(r"<h3[^>]*>(.*?)</h3>", card, re.S)
        if not (m_dt and m_title):
            continue
        raw_dt = _txt(m_dt.group(1))
        cleaned_dt = re.sub(r"\s+", " ", weekday_re.sub("", raw_dt)).strip()
        start, end = parse_range(cleaned_dt, today)
        if not _keep(start, end, today):
            continue
        title = _txt(m_title.group(1))
        if not title or title in seen:
            continue
        seen.add(title)
        m_ore = re.search(r"\b(\d{1,2}:\d{2}(?:\s*-\s*\d{1,2}:\d{2})?)\b", raw_dt)
        when = _span_label(start, end, today)
        if m_ore:
            when = f"{when} ore {m_ore.group(1)}"
        out.append({"titolo": title, "quando": when})
    return out


EXTRACTORS: List[tuple[str, Callable[..., List[Dict[str, str]]]]] = [
    ("circuitocinemagenova.com", circuito_cinema),
    ("cineclubnickelodeon.it", nickelodeon),
    ("countbasie.it", count_basie),
    ("crazybullgenova.it", crazy_bull),
    ("genovatango.com", genova_tango),
    ("teatrosocialecamogli.it", tribe_events),
    ("teatronazionalegenova.it", teatro_nazionale),
    ("carlofelice", carlo_felice),
    ("palazzoducale.genova.it", lambda u, t, h="": palazzo_ducale(u, t, h)),
    ("galatamuseodelmare.it", lambda u, t, h="": galata(u, t)),
    ("bibliotechedigenova.it", lambda u, t, h="": biblioteche_genova(u, t, h)),
    ("politeamagenovese.it", lambda u, t, h="": politeama(u, t)),
    ("teatrodellatosse.it", lambda u, t, h="": teatro_tosse(u, t, h)),
]


def fetch_programme(url: str, today: Optional[date] = None, hint: str = "") -> List[Dict[str, str]]:
    """Programma dei prossimi 7 giorni per un URL, o [] se non disponibile.

    hint: nome del locale, usato dai siti che raggruppano più sedi (biblioteche, Tosse).
    """
    if not url:
        return []
    today = today or date.today()
    key = f"{url}|{hint}|{today.isoformat()}"
    if key in _cache:
        return _cache[key]
    result: List[Dict[str, str]] = []
    for host, fn in EXTRACTORS:
        if host in url:
            try:
                result = (fn(url, today, hint) if hint and fn.__name__ == "<lambda>" else fn(url, today))[:MAX_ITEMS]
            except Exception:
                result = []
            break
    _cache[key] = result
    return result


def has_extractor(url: str) -> bool:
    return any(h in (url or "") for h, _ in EXTRACTORS)


# ------------------------------------------------ eventi nei luoghi (musei ecc.)
# Ogni gruppo: parole che identificano lo stesso luogo nel titolo della scheda
# e nel nome del luogo o nel titolo dell'evento.
VENUE_GROUPS: List[List[str]] = [
    ["strada nuova", "palazzo rosso", "palazzo bianco", "palazzo tursi"],
    ["chiossone", "arte orientale"],
    ["d'albertis", "culture del mondo"],
    ["lanterna"],
    ["staglieno"],
    ["galata", "museo del mare"],
    ["acquario"],
    ["gam ", "galleria d'arte moderna", "frugone", "wolfsoniana", "polo museale di nervi"],
    ["sant'agostino"],
    ["palazzo spinola", "spinola di pellicceria"],
    ["palazzo reale"],
    ["mazzini"],
    ["boccadasse"],
    ["castelletto"],
    ["pallavicini"],
    ["righi", "forti di genova", "parco delle mura"],
    ["porto antico"],
    ["ducale"],
    ["diocesano", "san lorenzo"],
    ["villa serra"],
    ["camogli"],
    ["sestri levante", "musel"],
    ["chiavari", "palazzo rocca"],
    ["rapallo", "merletto"],
    ["santa margherita", "villa durazzo"],
    ["portofino", "castello brown"],
    ["estoril", "estoril beach club"],
    ["casa mia", "casamia"],
    ["menodue", "meno due"],
    ["mako", "discoteca mako"],
    ["giardini luzzati"],
    ["mog", "mercato orientale"],
    ["buridda"],
]


def _has_venue_keyword(text: str, kw: str) -> bool:
    return bool(re.search(rf"(?<![a-z0-9]){re.escape(kw.strip())}(?![a-z0-9])", text))


def _groups_for(text: str) -> List[List[str]]:
    t = (text or "").lower()
    return [g for g in VENUE_GROUPS if any(_has_venue_keyword(t, k) for k in g)]


def musei_genova_events(today: date) -> List[Dict[str, str]]:
    """museidigenova.it/it/mostre-ed-eventi: data inizio, data fine, museo, titolo."""
    page = _get("https://www.museidigenova.it/it/mostre-ed-eventi")
    out = []
    pat = (r'<h2 class="fs-30[^"]*">(\d{1,2})\s*<span[^>]*>(\w+)</span>\s*(\d{4})</h2>\s*'
           r'<h3 class="fs-30[^"]*">(\d{1,2})\s*<span[^>]*>(\w+)</span>\s*(\d{4})</h3>'
           r'.*?tipologia_evento[^>]*>(.*?)</p>(.*?)<h4[^>]*>\s*<a[^>]*>(.*?)<i')
    for d1, m1, y1, d2, m2, y2, tipo, luogo, title in re.findall(pat, page, re.S):
        try:
            start = date(int(y1), _month(m1), int(d1))
            end = date(int(y2), _month(m2), int(d2))
        except (TypeError, ValueError):
            continue
        if _keep(start, end, today):
            out.append({"luogo": _txt(luogo), "titolo": _txt(title),
                        "quando": _span_label(start, end, today)})
    return out


def palazzo_reale_events(today: date) -> List[Dict[str, str]]:
    """Musei Nazionali di Genova (Palazzo Reale e Spinola): API eventi WordPress."""
    out = []
    for site, luogo in (("palazzorealegenova", "Palazzo Reale"), ("palazzospinola", "Palazzo Spinola")):
        try:
            data = json.loads(_get(f"https://{site}.cultura.gov.it/wp-json/wp/v2/ett_event?per_page=30"))
        except Exception:
            continue
        for ev in data:
            try:
                d = date.fromisoformat(ev["date"][:10])
            except Exception:
                continue
            if not _in_window(d, today):
                continue
            title = _txt(ev["title"]["rendered"])
            extra = _txt(ev.get("excerpt", {}).get("rendered", ""))[:90]
            if len(title) < 25 and extra:
                title = f"{title[:1].upper()}{title[1:]}: {extra.rstrip('. ')}"
            out.append({"luogo": luogo, "titolo": title, "quando": _fmt(d)})
    return out


def visitgenoa_events(today: date, pages: int = 3) -> List[Dict[str, str]]:
    """Agenda cittadina visitgenoa.it: periodo e titolo (il luogo spesso è nel titolo)."""
    out = []
    for p in range(pages):
        try:
            page = _get(f"https://www.visitgenoa.it/it/eventi?page={p}")
        except Exception:
            break
        for d1, d2, title in re.findall(
                r'<span class="fs-14">(\d{2}/\d{2}/\d{4})(?:\s*-\s*(\d{2}/\d{2}/\d{4}))?<br>\s*</span>(.*?)</h4>', page, re.S):
            try:
                start = date(*reversed([int(x) for x in d1.split("/")]))
                end = date(*reversed([int(x) for x in (d2 or d1).split("/")]))
            except ValueError:
                continue
            if _keep(start, end, today):
                out.append({"luogo": "", "titolo": _txt(title), "quando": _span_label(start, end, today)})
    return out


def _iter_jsonld_events(payload) -> List[Dict]:
    items = payload if isinstance(payload, list) else [payload]
    out: List[Dict] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        graph = item.get("@graph")
        if isinstance(graph, list):
            out.extend(x for x in graph if isinstance(x, dict))
        else:
            out.append(item)
    return out


def _is_schema_event(ev: Dict) -> bool:
    t = ev.get("@type")
    types = t if isinstance(t, list) else [t]
    return any(isinstance(x, str) and x.endswith("Event") for x in types)


def xceed_genova_events(today: date) -> List[Dict[str, str]]:
    """Serate club e discoteche a Genova via JSON-LD Schema.org Event su xceed.me."""
    page = _get("https://xceed.me/it/genova/events")
    out, seen = [], set()
    for block in re.findall(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', page, re.S):
        try:
            payload = json.loads(block)
        except ValueError:
            continue
        for ev in _iter_jsonld_events(payload):
            if not _is_schema_event(ev):
                continue
            start_raw = str(ev.get("startDate") or "")
            if len(start_raw) < 10:
                continue
            try:
                d = date.fromisoformat(start_raw[:10])
            except ValueError:
                continue
            if not _in_window(d, today):
                continue
            loc = ev.get("location")
            luogo = _txt(loc.get("name", "")) if isinstance(loc, dict) else ""
            raw_title = _txt(str(ev.get("name") or "").replace("|", "-"))
            if not raw_title or raw_title in seen:
                continue
            seen.add(raw_title)
            m_time = re.search(r"T(\d{2}:\d{2})", start_raw)
            when = f"{_fmt(d)} {m_time.group(1)}" if m_time else _fmt(d)
            out.append({"luogo": luogo, "titolo": raw_title, "quando": when})
    return out


def build_venue_events(today: date) -> List[Dict[str, str]]:
    events: List[Dict[str, str]] = []
    for fn in (musei_genova_events, palazzo_reale_events, visitgenoa_events, xceed_genova_events):
        try:
            events.extend(fn(today))
        except Exception:
            pass
    return events


def match_venue_events(card_text: str, events: List[Dict[str, str]]) -> List[Dict[str, str]]:
    groups = _groups_for(card_text)
    if not groups:
        return []
    out, seen = [], set()
    for ev in events:
        hay = f"{ev['luogo']} {ev['titolo']}".lower()
        if any(_has_venue_keyword(hay, k) for g in groups for k in g) and ev["titolo"] not in seen:
            seen.add(ev["titolo"])
            q = ev["quando"] + (f", {ev['luogo']}" if ev["luogo"] and ev["luogo"].lower() not in card_text.lower() else "")
            out.append({"titolo": ev["titolo"], "quando": q})
    return out[:MAX_ITEMS]


def attach_programmes(options, today: Optional[date] = None, workers: int = 8) -> int:
    """Scrive raw_metadata['programma'] sulle opzioni coperte. Restituisce quante ne hanno uno."""
    targets = [o for o in options if has_extractor(o.verified_url)]
    pairs = sorted({(o.verified_url, f"{o.venue} {o.title}") for o in targets})
    with ThreadPoolExecutor(max_workers=workers) as ex:
        list(ex.map(lambda p: fetch_programme(p[0], today, p[1]), pairs))
    n = 0
    empty_urls = []
    for o in targets:
        prog = fetch_programme(o.verified_url, today, f"{o.venue} {o.title}")
        if prog:
            o.raw_metadata["programma"] = prog
            n += 1
        else:
            empty_urls.append(o.verified_url)
    if empty_urls:
        unique_empty = sorted(set(empty_urls))
        logger.warning(
            "Programme extractors returned 0 events for %d/%d target URLs: %s",
            len(unique_empty),
            len(pairs),
            ", ".join(unique_empty[:10]),
        )
    # Eventi nei luoghi (visite guidate, laboratori, concerti nei musei, tour)
    events = build_venue_events(today or date.today())
    for o in options:
        extra = match_venue_events(f"{o.venue} {o.title}", events)
        if not extra:
            continue
        have = o.raw_metadata.get("programma") or []
        titles = {p["titolo"] for p in have}
        merged = have + [e for e in extra if e["titolo"] not in titles]
        if not have:
            n += 1
        o.raw_metadata["programma"] = merged[:MAX_ITEMS]
    return n
