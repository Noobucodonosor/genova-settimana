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
    ("sivori", re.compile(r"\bsivori\b")),
)


def _norm_ascii(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text or "")
    ascii_only = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", ascii_only).strip().lower()


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
    """Produce a clean human-friendly editorial title free of scraping suffixes."""
    cleaned = _ROBOTIC_SUFFIX_RE.sub("", (title or "").strip()).strip(" :-")
    cleaned = re.sub(r"\s+", " ", cleaned)
    v_norm = _norm_ascii(venue or cleaned)
    v_core = _STRIP_PREFIX_RE.sub("", v_norm).strip()
    if v_core in _CANONICAL_CINEMA_NAMES and _norm_ascii(cleaned) in {v_core, _norm_ascii(_CANONICAL_CINEMA_NAMES[v_core])}:
        return _CANONICAL_CINEMA_NAMES[v_core]
    if _norm_ascii(cleaned) in _CANONICAL_CINEMA_NAMES:
        return _CANONICAL_CINEMA_NAMES[_norm_ascii(cleaned)]
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
        # Merge programme entries across all duplicates for this venue
        seen_prog = set()
        combined_prog = []
        for ent in sorted(entries, key=quality, reverse=True):
            for p in ent.raw_metadata.get("programma") or []:
                pk = (_norm_ascii(p.get("titolo", "")), _norm_ascii(p.get("quando", "")))
                if pk not in seen_prog and p.get("titolo"):
                    seen_prog.add(pk)
                    combined_prog.append(p)
        if combined_prog:
            best.raw_metadata["programma"] = combined_prog[:8]
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
    padding: 40px 0 20px;
  }
  h1 {
    font-family: var(--serif);
    font-weight: 400;
    font-size: clamp(28px, 5vw, 36px);
    line-height: 1.15;
    letter-spacing: -0.02em;
    margin: 0 0 8px;
  }
  .sub {
    margin: 0 0 24px;
    color: var(--muted);
    font-size: 14px;
    letter-spacing: 0.01em;
  }
  .ask {
    width: 100%;
    border: 0;
    border-bottom: 1px solid var(--line);
    background: transparent;
    padding: 10px 0;
    font: 16px/1.4 var(--sans);
    color: var(--ink);
    outline: none;
    border-radius: 0;
  }
  .ask:focus { border-bottom-color: var(--ink); }
  .ask::placeholder { color: #8c8881; }
  .pills {
    display: flex;
    flex-wrap: wrap;
    flex-wrap: balance;
    gap: 8px;
    margin-top: 18px;
  }
  .pill {
    border: 1px solid var(--line);
    background: transparent;
    color: var(--muted);
    border-radius: 999px;
    padding: 5px 13px;
    font: 13px/1.4 var(--sans);
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
    gap: 18px;
    padding: 20px 4px;
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
    margin-bottom: 4px;
  }
  .t {
    font-family: var(--serif);
    font-size: 19px;
    line-height: 1.3;
    font-weight: 400;
    color: var(--ink);
  }
  .m {
    color: var(--muted);
    font-size: 14px;
    margin-top: 4px;
  }
  .d {
    font-size: 14px;
    color: #3a3834;
    margin-top: 6px;
  }
  .prog {
    margin: 10px 0 0;
    padding: 0;
    list-style: none;
    font-size: 14px;
  }
  .prog li {
    padding: 3px 0;
    color: var(--ink);
  }
  .prog li span { color: var(--muted); }
  .more-prog, .more-places {
    border: 0;
    background: transparent;
    padding: 4px 0;
    margin-top: 4px;
    font: 13px var(--sans);
    color: var(--muted);
    text-decoration: underline;
    text-underline-offset: 3px;
    cursor: pointer;
  }
  .more-prog:hover, .more-places:hover { color: var(--ink); }
  .more-places-wrap {
    padding: 22px 0 8px;
    text-align: left;
  }
  .src {
    display: inline-block;
    margin-top: 8px;
    font-size: 13px;
    color: var(--accent);
    text-decoration: none;
  }
  .src:hover { text-decoration: underline; }
  .card input[type="checkbox"] {
    width: 18px;
    height: 18px;
    margin-top: 6px;
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
    padding: 12px 20px calc(12px + env(safe-area-inset-bottom));
    display: none;
    z-index: 20;
  }
  .bar.show { display: block; }
  .bar-in {
    max-width: 680px;
    margin: 0 auto;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 10px;
  }
  .bar-meta {
    flex: 1;
    display: flex;
    align-items: baseline;
    gap: 12px;
    min-width: 120px;
  }
  .count { font-size: 14px; color: var(--ink); font-weight: 500; }
  .edit-link {
    border: 0;
    background: transparent;
    padding: 0;
    font: 13px var(--sans);
    color: var(--muted);
    text-decoration: underline;
    cursor: pointer;
  }
  .bar-actions { display: flex; gap: 8px; }
  .btn {
    border: 1px solid var(--line);
    border-radius: 999px;
    padding: 8px 15px;
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
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>Questa settimana a Genova</h1>
    <p class="sub">__RANGE__ · Cinema, mostre, musica e teatri</p>
    <input id="q" class="ask" type="search" placeholder="Cerca un posto, un film, o scrivi stasera, piove, ballare..." autocomplete="off" aria-label="Cerca cosa fare a Genova">
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
  </div>
  <div class="bar-in">
    <div class="bar-meta">
      <span class="count" id="count"></span>
      <button class="edit-link" id="togglePreview" type="button">Modifica</button>
    </div>
    <div class="bar-actions">
      <button class="btn cp" id="copy" type="button">Copia testo</button>
      <button class="btn wa" id="send" type="button">Manda su WhatsApp</button>
    </div>
  </div>
</div>

<script>
let DATA = __DATA__;
const LABEL = __LABELS__;
const MACRO_CATS = [
  { id: "tutto", label: "Tutto" },
  { id: "cinema", label: "Cinema" },
  { id: "mostra", label: "Mostre" },
  { id: "musica_teatro", label: "Musica e teatro" },
  { id: "altro_macro", label: "Altro" }
];
const _params = new URLSearchParams(window.location.search);
let cat = _params.get("cat") || "tutto";
let query = _params.get("q") || "";
let showAlwaysOpen = false;
const expandedProg = new Set();
const SEL_KEY = "genova_civica_sel_v1";
const sel = new Set((() => {
  try { return JSON.parse(localStorage.getItem(SEL_KEY) || "[]"); } catch { return []; }
})());
function persistSel() {
  try { localStorage.setItem(SEL_KEY, JSON.stringify(Array.from(sel))); } catch {}
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

const STOP = new Set(["stasera","oggi","domani","dove","vado","andiamo","andare","cosa","facciamo","fare","ce","c","e","a","in","di","da","per","con","su","tra","fra","il","lo","la","i","gli","le","un","uno","una","mi","ti","ci","si","vi","che","chi","qualcosa","consigli","consiglio","vorrei","voglio","posto","posti","genova","settimana","questa","questo","nel","nella","nei","nelle","al","allo","alla","ai","agli","alle","del","dello","della","dei","degli","delle","se","o","oppure","ma","anche","po","bel","bella","bello","sera","pomeriggio","mattina","notte"]);
const DAYS = ["domenica","lunedi","martedi","mercoledi","giovedi","venerdi","sabato"];

const INTENTS = [
  { name:"ballare", triggers:["ballare","ballo","balla","danzare","danza","discoteca","dj","djset","club","milonga","tango","swing","lindy","blues dance","salsa","latino","caraibico","pista","movida"], boostTerms:["ballare","ballo","swing","lindy","blues dance","milonga","tango","dj","claque","count basie","luzzati","zenaswingers","circolo vega","mog"], cats:["musica","ritrovo"], banner:"Locali e serate dove ballare:" },
  { name:"bere", triggers:["bere","aperitivo","aperitivi","calice","vino","birra","cocktail","drink","pub","enoteca","spritz","caruggi","vicoli","chiacchierare"], boostTerms:["aperitivo","vino","birra","cocktail","bar","luzzati","mog","mercato orientale","carmine","caruggi","ritrovo","caff","sciamadda","viganotti"], cats:["ritrovo","musica","laboratorio"], banner:"Aperitivi e locali nei caruggi:" },
  { name:"pioggia", triggers:["piove","pioggia","diluvia","coperto","interno","freddo","brutto tempo","chiuso"], boostTerms:["indoor","cinema","mostra","museo","palazzo","biblioteca","teatro","mercato"], cats:["cinema","mostra","biblioteca","musica","laboratorio"], indoorOnly:true, banner:"Proposte al coperto:" },
  { name:"cinema", triggers:["film","cinema","proiezione","proiezioni","pellicola","sottotitoli","lingua originale","sala"], boostTerms:["cinema","sivori","america","odeon","nickelodeon","film","proiezioni"], cats:["cinema"], banner:"Cinema in programmazione:" },
  { name:"mostra", triggers:["mostra","mostre","museo","musei","arte","quadri","fotografia","esposizione","palazzo","rolli"], boostTerms:["mostra","museo","palazzo","ducale","strada nuova","reale","spinola","galata","castello","nervi"], cats:["mostra"], banner:"Mostre e musei:" },
  { name:"passeggiata", triggers:["passeggiata","passeggiare","camminare","mare","vista","panorama","tramonto","aperto","sole","parco","borgo","boccadasse","nervi","castelletto","righi","trekking"], boostTerms:["passeggiata","mare","belvedere","boccadasse","nervi","castelletto","righi","acquedotto","parco","borgo"], cats:["passeggiata","altro"], banner:"Passeggiate e percorsi all'aperto:" },
  { name:"mangiare", triggers:["mangiare","cena","cenare","pranzo","focaccia","farinata","cioccolato","dolce","gelato","bottega","assaggiare","fame","sciamadda"], boostTerms:["farinata","cioccolato","confetteria","mog","mercato","friggitoria","forno","pasticceria","bottega"], cats:["laboratorio","ritrovo"], banner:"Botteghe storiche e sapori:" }
];

function analyzeQuery(qRaw) {
  const nq = norm(qRaw);
  if (!nq) return null;
  const matchedIntents = INTENTS.filter(it => it.triggers.some(t => nq.includes(norm(t))));
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

  if (info.matchedIntents.length > 0) {
    let score = 0;
    for (const it of info.matchedIntents) {
      if (it.indoorOnly && d.outdoor) return 0;
      let intentHits = 0;
      for (const term of it.boostTerms) if (hay.includes(norm(term))) intentHits += 4;
      if (it.cats.includes(d.category)) intentHits += 2;
      if (intentHits === 0) return 0;
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
  if ((d.programma || []).length > 0) score += 2;
  return score;
}

function matchesMacroCat(itemCat, macroId) {
  if (macroId === "tutto") return true;
  if (macroId === "cinema") return itemCat === "cinema";
  if (macroId === "mostra") return itemCat === "mostra";
  if (macroId === "musica_teatro") return itemCat === "musica";
  if (macroId === "altro_macro") return !["cinema", "mostra", "musica"].includes(itemCat);
  return itemCat === macroId;
}

function renderPills() {
  document.getElementById("pills").innerHTML = MACRO_CATS.map(c =>
    `<button class="pill ${c.id === cat ? 'on' : ''}" data-k="${c.id}" type="button">${c.label}</button>`
  ).join("");
  document.querySelectorAll(".pill").forEach(b => b.onclick = () => {
    cat = b.dataset.k;
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

  if (info) {
    const scored = pool.map(d => ({ d, s: scoreItem(d, info) })).filter(x => x.s > 0).sort((a, b) => b.s - a.s);
    pool = scored.map(x => x.d);
    ansEl.textContent = pool.length
      ? (info.matchedIntents.length ? info.matchedIntents[0].banner : `${pool.length} proposte trovate`)
      : `Nessuna proposta per "${query.trim()}".`;
    ansEl.classList.add("show");
  } else {
    ansEl.classList.remove("show");
    const withProg = pool.filter(d => (d.programma || []).length > 0);
    const alwaysOpen = pool.filter(d => (d.programma || []).length === 0);
    if (!showAlwaysOpen && withProg.length > 0) {
      hiddenAlwaysOpen = alwaysOpen.length;
      pool = withProg;
    }
  }

  document.getElementById("list").innerHTML = pool.map(d => {
    const progs = d.programma || [];
    const showAll = expandedProg.has(d.id);
    const shown = showAll ? progs : progs.slice(0, 3);
    const progHtml = shown.length
      ? `<ul class="prog">${shown.map(p => `<li>${esc(p.titolo)} <span>${esc(p.quando)}</span></li>`).join("")}</ul>`
        + (progs.length > 3 ? `<button type="button" class="more-prog" data-more="${esc(d.id)}">${showAll ? "Mostra meno" : `Vedi tutto il programma (+${progs.length - 3})`}</button>` : "")
      : "";
    const safeHref = /^https?:\/\//i.test(String(d.url || "").trim()) ? d.url.trim() : "";
    const catName = LABEL[d.category] || d.category;
    return `<label class="card ${sel.has(d.id)?'sel':''}" data-id="${esc(d.id)}" role="checkbox" aria-checked="${sel.has(d.id)?'true':'false'}" tabindex="0">
      <div class="card-content">
        <div class="cat-kicker">${esc(catName)}</div>
        <div class="t">${esc(d.title)}</div>
        <div class="m">${esc(d.place)}</div>
        ${d.day_time ? `<div class="m">${esc(d.day_time)}</div>` : ""}
        ${(!progs.length && d.description) ? `<div class="d">${esc(d.description)}</div>` : ""}
        ${progHtml}
        ${safeHref ? `<a class="src" href="${esc(safeHref)}" target="_blank" rel="noopener">Sito ufficiale</a>` : ""}
      </div>
      <input type="checkbox" ${sel.has(d.id)?'checked':''} aria-label="Scegli ${esc(d.title)}">
    </label>`;
  }).join("");

  const moreWrap = document.getElementById("moreWrap");
  if (!info && (hiddenAlwaysOpen > 0 || showAlwaysOpen)) {
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

  document.querySelectorAll(".card").forEach(c => {
    const toggle = () => {
      const id = c.dataset.id;
      sel.has(id) ? sel.delete(id) : sel.add(id);
      persistSel();
      render(); bar();
    };
    c.onclick = e => {
      if (e.target.tagName === "A" || e.target.tagName === "BUTTON") return;
      if (e.target.tagName === "INPUT") {
        // Checkbox inside label already toggles via browser; sync state cleanly
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
      if (e.target.tagName === "A" || e.target.tagName === "BUTTON" || e.target.tagName === "INPUT") return;
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
    const p = (d.programma || [])[0];
    const when = p ? `${cleanPlain(p.titolo)}, ${cleanPlain(p.quando)}` : cleanPlain(d.day_time);
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
    options.sort(
        key=lambda o: (
            CAT_ORDER.index(o.category.value) if o.category.value in CAT_ORDER else 99,
            0 if o.raw_metadata.get("programma") else 1,
            o.title,
        )
    )
    data = []
    for o in options:
        place = o.venue
        zone = (o.zone or "").replace("_", " ").title()
        data.append({
            "id": o.id,
            "category": o.category.value,
            "title": o.title,
            "place": ", ".join(x for x in (o.address or place, zone) if x),
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
    rng = f"Dal {today.day} {MESI[today.month-1]} al {end.day} {MESI[end.month-1]}"
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
