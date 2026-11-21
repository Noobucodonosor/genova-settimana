"""Esporta una pagina statica (un solo index.html) con le alternative della settimana.

Chi apre la pagina può filtrare per tipo, spuntare le proposte e inviare la scelta
su WhatsApp (wa.me/?text=..., senza numero: WhatsApp chiede a chi mandarlo).

Uso:  python3 -m genova_outings.export_static [cartella_uscita]
"""

import html
import json
import sys
from datetime import date, timedelta
from pathlib import Path

from genova_outings.catalog import get_weekly_catalog
from genova_outings.programme import attach_programmes

MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio",
        "agosto", "settembre", "ottobre", "novembre", "dicembre"]

CAT_LABEL = {
    "cinema": "🎬 Cinema", "mostra": "🏛️ Mostre e musei", "musica": "🎶 Musica, serate e teatro",
    "biblioteca": "📚 Biblioteche", "passeggiata": "🌿 Passeggiate", "laboratorio": "🏺 Botteghe e sapori",
    "ritrovo": "☕ Caffè e ritrovi", "altro": "⛪ Abbazie e borghi",
}
CAT_ORDER = list(CAT_LABEL)

PAGE = r"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cosa facciamo Genova</title>
<meta name="description" content="Cosa facciamo a Genova questa settimana: cinema, mostre, musica, dove ballare, biblioteche, botteghe e passeggiate.">
<style>
  :root { color-scheme: light dark; --bg:#f7f7f5; --card:#fff; --fg:#1c1c1c; --mut:#6b6b6b; --line:#e4e4e0; --acc:#1f6feb; --sel:#eaf2ff; }
  @media (prefers-color-scheme: dark) { :root { --bg:#141414; --card:#1e1e1e; --fg:#ececec; --mut:#9a9a9a; --line:#2e2e2e; --acc:#5b9dff; --sel:#1b2a40; } }
  * { box-sizing: border-box; }
  body { margin:0; font: 16px/1.45 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background:var(--bg); color:var(--fg); }
  header { padding: 22px 16px 10px; max-width: 760px; margin: 0 auto; }
  h1 { font-size: 24px; margin: 0 0 4px; letter-spacing: -0.02em; }
  .sub { color: var(--mut); font-size: 14px; margin: 0 0 14px; }
  .ask-box { position: relative; display: flex; align-items: center; background: var(--card); border: 1.5px solid var(--line); border-radius: 14px; padding: 4px 10px 4px 14px; box-shadow: 0 2px 6px rgba(0,0,0,0.04); }
  .ask-box:focus-within { border-color: var(--acc); box-shadow: 0 0 0 3px color-mix(in srgb, var(--acc) 18%, transparent); }
  .ask-in { flex: 1; border: 0; background: transparent; color: var(--fg); font-size: 16px; padding: 10px 0; outline: none; }
  .ask-in::placeholder { color: var(--mut); }
  .ask-clr { border: 0; background: var(--line); color: var(--fg); border-radius: 999px; width: 26px; height: 26px; font-size: 14px; cursor: pointer; display: none; align-items: center; justify-content: center; }
  .ask-clr.show { display: inline-flex; }
  .prompts { display: flex; gap: 6px; overflow-x: auto; padding: 10px 0 2px; scrollbar-width: none; }
  .pr { flex: 0 0 auto; border: 1px dashed var(--line); background: transparent; color: var(--mut); border-radius: 999px; padding: 5px 11px; font-size: 13px; cursor: pointer; }
  .pr:hover, .pr.on { border-style: solid; border-color: var(--acc); color: var(--acc); background: color-mix(in srgb, var(--acc) 8%, transparent); }
  nav { position: sticky; top: 0; z-index: 5; background: var(--bg); border-bottom: 1px solid var(--line); }
  .chips { display:flex; gap:6px; overflow-x:auto; padding:10px 16px; max-width:760px; margin:0 auto; scrollbar-width:none; }
  .chip { flex:0 0 auto; border:1px solid var(--line); background:var(--card); color:var(--fg); border-radius:999px; padding:6px 12px; font-size:14px; cursor:pointer; }
  .chip.on { background:var(--acc); border-color:var(--acc); color:#fff; }
  main { max-width:760px; margin:0 auto; padding: 12px 12px 140px; }
  .ans { background: color-mix(in srgb, var(--acc) 10%, var(--card)); border: 1px solid color-mix(in srgb, var(--acc) 35%, var(--line)); border-radius: 12px; padding: 11px 14px; margin-bottom: 12px; font-size: 14px; display: none; }
  .ans.show { display: block; }
  .card { display:flex; gap:12px; background:var(--card); border:1px solid var(--line); border-radius:14px; padding:14px; margin-bottom:10px; cursor:pointer; }
  .card.sel { border-color: var(--acc); background: var(--sel); }
  .card input { width:22px; height:22px; margin-top:2px; flex:0 0 auto; accent-color: var(--acc); }
  .t { font-weight: 650; font-size: 16px; }
  .m { color: var(--mut); font-size: 14px; margin-top: 3px; }
  .d { font-size: 14px; margin-top: 6px; }
  .prog { margin-top:8px; padding:8px 10px; border-left:3px solid var(--acc); background: color-mix(in srgb, var(--acc) 8%, transparent); border-radius:6px; font-size:14px; }
  .prog b { font-weight:600; }
  .prog ul { margin:4px 0 0; padding-left:18px; }
  .prog li span { color: var(--mut); }
  .src { display:inline-block; margin-top:8px; font-size:13px; color: var(--acc); text-decoration:none; }
  .bar { position:fixed; left:0; right:0; bottom:0; background:var(--card); border-top:1px solid var(--line); padding:12px 16px calc(12px + env(safe-area-inset-bottom)); display:none; }
  .bar.show { display:block; }
  .bar-in { max-width:760px; margin:0 auto; display:flex; gap:8px; align-items:center; }
  .count { flex:1; font-size:14px; color: var(--mut); }
  .btn { border:0; border-radius:10px; padding:11px 14px; font-size:15px; font-weight:600; cursor:pointer; }
  .wa { background:#25d366; color:#fff; }
  .cp { background: var(--line); color: var(--fg); }
  footer { color: var(--mut); font-size: 12px; text-align:center; padding: 8px 16px 0; }
</style>
</head>
<body>
<header>
  <h1>Cosa facciamo Genova</h1>
  <p class="sub">__RANGE__. Scrivi cosa ti va di fare o spunta quello che ti ispira per mandarlo su WhatsApp.</p>
  <div class="ask-box">
    <input id="q" class="ask-in" type="search" placeholder="Chiedi qui, es: stasera dove vado a ballare? o se piove?" autocomplete="off" aria-label="Cerca o chiedi cosa fare a Genova">
    <button id="qclr" class="ask-clr" type="button" aria-label="Cancella ricerca">✕</button>
  </div>
  <div class="prompts" id="prompts">
    <button class="pr" type="button" data-q="stasera dove vado a ballare?">💃 Stasera dove vado a ballare?</button>
    <button class="pr" type="button" data-q="cosa c'è stasera?">🌙 Cosa c'è stasera?</button>
    <button class="pr" type="button" data-q="dove andiamo se piove?">🌧️ Se piove dove andiamo?</button>
    <button class="pr" type="button" data-q="bere qualcosa o aperitivo nei caruggi">🍷 Bere qualcosa nei caruggi</button>
    <button class="pr" type="button" data-q="film al cinema">🎬 Che film danno?</button>
    <button class="pr" type="button" data-q="passeggiata vista mare">🌊 Vista mare</button>
  </div>
</header>
<nav><div class="chips" id="chips"></div></nav>
<main>
  <div id="ans" class="ans"></div>
  <div id="list"></div>
</main>
<footer>Orari e programmi letti dai siti ufficiali il __UPDATED__. Prima di andare conviene ricontrollare sul sito del posto.</footer>
<div class="bar" id="bar"><div class="bar-in">
  <span class="count" id="count"></span>
  <button class="btn cp" id="copy">Copia</button>
  <button class="btn wa" id="send">Invia su WhatsApp</button>
</div></div>
<script>
const DATA = __DATA__;
const LABEL = __LABELS__;
let cat = "tutto";
let query = "";
const sel = new Set();
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const norm = s => String(s ?? "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");

const STOP = new Set(["stasera","oggi","domani","dove","vado","andiamo","andare","cosa","facciamo","fare","ce","c","e","a","in","di","da","per","con","su","tra","fra","il","lo","la","i","gli","le","un","uno","una","mi","ti","ci","si","vi","che","chi","qualcosa","consigli","consiglio","vorrei","voglio","posto","posti","genova","settimana","questa","questo","nel","nella","nei","nelle","al","allo","alla","ai","agli","alle","del","dello","della","dei","degli","delle","se","o","oppure","ma","anche","po","bel","bella","bello","sera","pomeriggio","mattina","notte"]);
const DAYS = ["domenica","lunedi","martedi","mercoledi","giovedi","venerdi","sabato"];

const INTENTS = [
  {
    name: "ballare",
    triggers: ["ballare","ballo","balla","danzare","danza","discoteca","dj","djset","club","milonga","tango","swing","lindy","blues dance","salsa","latino","caraibico","pista","movida"],
    boostTerms: ["ballare","ballo","swing","lindy","blues dance","milonga","tango","dj","claque","count basie","luzzati","zenaswingers","circolo vega","mog"],
    cats: ["musica","ritrovo"],
    banner: "Ecco i posti dove ballare o fare serata a Genova tra live club, swing e blues dance, milonga, dj set e piazze dei caruggi:"
  },
  {
    name: "bere",
    triggers: ["bere","aperitivo","aperitivi","calice","vino","birra","cocktail","drink","pub","enoteca","spritz","caruggi","vicoli","chiacchierare"],
    boostTerms: ["aperitivo","vino","birra","cocktail","bar","luzzati","mog","mercato orientale","carmine","caruggi","ritrovo","caff","sciamadda","viganotti"],
    cats: ["ritrovo","musica","laboratorio"],
    banner: "Ecco i posti per bere qualcosa, fare aperitivo o fermarsi nei caruggi:"
  },
  {
    name: "pioggia",
    triggers: ["piove","pioggia","diluvia","coperto","interno","freddo","brutto tempo","chiuso"],
    boostTerms: ["indoor","cinema","mostra","museo","palazzo","biblioteca","teatro","mercato"],
    cats: ["cinema","mostra","biblioteca","musica","laboratorio"],
    indoorOnly: true,
    banner: "Se piove o fa freddo, queste sono tutte proposte al coperto (cinema, mostre, teatri, mercati storici e botteghe):"
  },
  {
    name: "cinema",
    triggers: ["film","cinema","proiezione","proiezioni","pellicola","sottotitoli","lingua originale","sala"],
    boostTerms: ["cinema","sivori","america","odeon","nickelodeon","film","proiezioni"],
    cats: ["cinema"],
    banner: "Ecco i cinema e cineclub con i film in programmazione questa settimana:"
  },
  {
    name: "mostra",
    triggers: ["mostra","mostre","museo","musei","arte","quadri","fotografia","esposizione","palazzo","rolli"],
    boostTerms: ["mostra","museo","palazzo","ducale","strada nuova","reale","spinola","galata","castello","nervi"],
    cats: ["mostra"],
    banner: "Ecco le mostre e i musei aperti con le esposizioni e visite in corso:"
  },
  {
    name: "passeggiata",
    triggers: ["passeggiata","passeggiare","camminare","mare","vista","panorama","tramonto","aperto","sole","parco","borgo","boccadasse","nervi","castelletto","righi","trekking"],
    boostTerms: ["passeggiata","mare","belvedere","boccadasse","nervi","castelletto","righi","acquedotto","parco","borgo"],
    cats: ["passeggiata","altro"],
    banner: "Ecco le passeggiate panoramiche, i borghi sul mare e i percorsi all'aperto:"
  },
  {
    name: "mangiare",
    triggers: ["mangiare","cena","cenare","pranzo","focaccia","farinata","cioccolato","dolce","gelato","bottega","assaggiare","fame","sciamadda"],
    boostTerms: ["farinata","cioccolato","confetteria","mog","mercato","friggitoria","forno","pasticceria","bottega"],
    cats: ["laboratorio","ritrovo"],
    banner: "Ecco botteghe storiche, sciamadde, cioccolaterie e posti dove mangiare qualcosa di tipico:"
  },
  {
    name: "musica_teatro",
    triggers: ["musica","concerto","concerti","live","jazz","teatro","spettacolo","spettacoli","stand up","comedy","opera"],
    boostTerms: ["concerto","jazz","live","teatro","tosse","claque","count basie","modena","duse","camogli","carlo felice","politeama"],
    cats: ["musica"],
    banner: "Ecco concerti dal vivo, jazz club e spettacoli a teatro di questa settimana:"
  }
];

function analyzeQuery(raw) {
  const q = norm(raw).replace(/[?!.,;:()"']/g, " ").replace(/\s+/g, " ").trim();
  if (!q) return null;

  const todayIdx = new Date().getDay();
  const todayName = DAYS[todayIdx];
  const tomorrowName = DAYS[(todayIdx + 1) % 7];

  let targetDay = null;
  let wantEvening = /\b(stasera|sera|serata|notte|dopocena)\b/.test(q);
  if (/\b(stasera|oggi)\b/.test(q)) targetDay = todayName;
  else if (/\bdomani\b/.test(q)) targetDay = tomorrowName;
  else {
    for (const d of DAYS) {
      if (q.includes(d)) { targetDay = d; break; }
    }
  }
  const wantWeekend = /\b(weekend|fine settimana)\b/.test(q);

  const matchedIntents = INTENTS.filter(it => it.triggers.some(tr => q.includes(norm(tr))));
  const words = q.split(" ").filter(w => w.length > 2 && !STOP.has(w));

  return { q, targetDay, wantEvening, wantWeekend, matchedIntents, words };
}

function scoreItem(d, info) {
  if (!info) return 1;
  const hay = norm([
    d.title, d.place, d.day_time, d.description, d.category,
    ...(d.tags || []),
    ...(d.programma || []).map(p => `${p.titolo} ${p.quando}`)
  ].join(" "));
  const progHay = norm((d.programma || []).map(p => `${p.titolo} ${p.quando}`).join(" "));
  const dtHay = norm(d.day_time);

  let score = 0;

  if (info.matchedIntents.length > 0) {
    for (const it of info.matchedIntents) {
      if (it.indoorOnly && d.outdoor) return 0;
      let intentHits = 0;
      for (const b of it.boostTerms) {
        if (hay.includes(norm(b))) intentHits += 3;
      }
      if ((d.tags || []).some(t => it.triggers.includes(norm(t)) || it.boostTerms.includes(norm(t)))) {
        intentHits += 8;
      }
      if (it.cats.includes(d.category)) intentHits += 2;
      if (it.name === "ballare" && intentHits < 3) continue;
      score += intentHits;
    }
    if (score === 0) return 0;
  }

  for (const w of info.words) {
    const isIntentWord = info.matchedIntents.some(it => it.triggers.some(tr => norm(tr).includes(w) || w.includes(norm(tr))));
    if (hay.includes(w)) {
      score += 5;
    } else if (!isIntentWord && info.matchedIntents.length === 0) {
      return 0;
    }
  }

  if (info.matchedIntents.length === 0 && info.words.length === 0) {
    // Query was only time-based like "cosa c'è stasera?" or "oggi"
    score = 2;
  }

  if (info.targetDay) {
    if (progHay.includes(info.targetDay)) score += 6;
    if (dtHay.includes(info.targetDay) || dtHay.includes("tutti i giorni")) score += 2;
    if (dtHay.includes(`${info.targetDay} chiuso`)) return 0;
  }
  if (info.wantWeekend) {
    if (progHay.includes("venerdi") || progHay.includes("sabato") || progHay.includes("domenica")) score += 5;
  }
  if (info.wantEvening) {
    if (d.time_slot === "sera" || hay.includes("21:") || hay.includes("20:") || hay.includes("24:00") || hay.includes("serale")) {
      score += 4;
    }
  }
  if ((d.programma || []).length > 0) score += 2;

  return score;
}

function chips() {
  const cats = ["tutto", ...Object.keys(LABEL).filter(k => DATA.some(d => d.category === k))];
  document.getElementById("chips").innerHTML = cats.map(k =>
    `<button class="chip ${k===cat?'on':''}" data-k="${k}">${k==="tutto" ? "Tutto" : LABEL[k]}</button>`).join("");
  document.querySelectorAll(".chip").forEach(b => b.onclick = () => { cat = b.dataset.k; chips(); render(); });
}

function render() {
  const info = analyzeQuery(query);
  const ansEl = document.getElementById("ans");
  let items = DATA.filter(d => cat === "tutto" || d.category === cat);

  if (info) {
    const scored = items
      .map(d => ({ d, s: scoreItem(d, info) }))
      .filter(x => x.s > 0)
      .sort((a, b) => b.s - a.s);
    items = scored.map(x => x.d);

    let msg = "";
    if (info.matchedIntents.length > 0) {
      msg = info.matchedIntents[0].banner;
    } else if (info.targetDay || info.wantEvening) {
      msg = `Ecco le proposte attive ${info.wantEvening ? "per la sera" : ""} (${items.length} trovate):`;
    } else {
      msg = `Risultati per "${query.trim()}" (${items.length} proposte):`;
    }
    ansEl.textContent = items.length ? msg : `Nessun risultato esatto per "${query.trim()}". Prova a cliccare su "Tutto" o a cercare ad esempio "ballare", "cinema", "piove" o "aperitivo".`;
    ansEl.classList.add("show");
  } else {
    ansEl.classList.remove("show");
  }

  document.getElementById("list").innerHTML = items.map(d => {
    const prog = (d.programma || []).length
      ? `<div class="prog"><b>In programma</b><ul>${d.programma.map(p => `<li>${esc(p.titolo)} <span>${esc(p.quando)}</span></li>`).join("")}</ul></div>` : "";
    return `<div class="card ${sel.has(d.id)?'sel':''}" data-id="${esc(d.id)}">
      <input type="checkbox" ${sel.has(d.id)?'checked':''} aria-label="Scegli ${esc(d.title)}">
      <div><div class="t">${esc(d.title)}</div>
        <div class="m">📍 ${esc(d.place)}</div>
        <div class="m">🗓️ ${esc(d.day_time)}</div>
        ${d.description ? `<div class="d">${esc(d.description)}</div>` : ""}
        ${prog}
        <a class="src" href="${esc(d.url)}" target="_blank" rel="noopener">Sito ufficiale</a>
      </div></div>`;
  }).join("");
  document.querySelectorAll(".card").forEach(c => c.onclick = e => {
    if (e.target.tagName === "A") return;
    const id = c.dataset.id;
    sel.has(id) ? sel.delete(id) : sel.add(id);
    render(); bar();
  });
}

function message() {
  const chosen = DATA.filter(d => sel.has(d.id));
  const head = chosen.length === 1 ? "Ho guardato la lista, questa mi ispira:" : "Ho guardato la lista, queste mi ispirano:";
  const body = chosen.map(d => {
    const p = (d.programma || [])[0];
    return `• *${d.title}*\n  ${d.place}` + (p ? `\n  ${p.titolo}, ${p.quando}` : `\n  ${d.day_time}`);
  }).join("\n\n");
  return `${head}\n\n${body}`;
}

function bar() {
  const n = sel.size;
  document.getElementById("bar").classList.toggle("show", n > 0);
  document.getElementById("count").textContent = n === 1 ? "1 scelta" : `${n} scelte`;
}

const qIn = document.getElementById("q");
const qClr = document.getElementById("qclr");
function setQuery(val) {
  query = val;
  qIn.value = val;
  qClr.classList.toggle("show", Boolean(val));
  document.querySelectorAll(".pr").forEach(b => b.classList.toggle("on", b.dataset.q === val));
  if (val && cat !== "tutto") { cat = "tutto"; chips(); }
  render();
}
qIn.oninput = e => setQuery(e.target.value);
qClr.onclick = () => { setQuery(""); qIn.focus(); };
document.querySelectorAll(".pr").forEach(b => b.onclick = () => setQuery(query === b.dataset.q ? "" : b.dataset.q));

document.getElementById("send").onclick = () => window.open("https://wa.me/?text=" + encodeURIComponent(message()), "_blank");
document.getElementById("copy").onclick = async () => {
  try { await navigator.clipboard.writeText(message()); document.getElementById("copy").textContent = "Copiato"; }
  catch { prompt("Copia il testo:", message()); }
  setTimeout(() => document.getElementById("copy").textContent = "Copia", 1500);
};
chips(); render(); bar();
</script>
</body>
</html>
"""


def _dedupe(options):
    """Una scheda per luogo+url: tiene quella con più programma o descrizione."""
    best = {}
    for o in options:
        v_slug = "".join(ch for ch in (o.venue or "").lower() if ch.isalnum())[:18]
        key = (o.verified_url.rstrip("/").lower(), o.category.value, v_slug)
        score = len(o.raw_metadata.get("programma") or []) * 10 + len(o.description or "")
        if key not in best or score > best[key][0]:
            best[key] = (score, o)
    return [v[1] for v in best.values()]


def build(out_dir: Path) -> Path:
    options = get_weekly_catalog(live_verify=True)
    attach_programmes(options)
    options = _dedupe(options)
    options.sort(key=lambda o: (CAT_ORDER.index(o.category.value) if o.category.value in CAT_ORDER else 99,
                                0 if o.raw_metadata.get("programma") else 1, o.title))
    data = []
    for o in options:
        place = o.venue if o.venue.lower() in o.title.lower() else o.venue
        zone = (o.zone or "").replace("_", " ").title()
        data.append({
            "id": o.id, "category": o.category.value, "title": o.title,
            "place": ", ".join(x for x in (o.address or place, zone) if x),
            "day_time": o.day_time, "description": o.description,
            "url": o.verified_url, "programma": o.raw_metadata.get("programma") or [],
            "tags": o.tags or [], "outdoor": bool(o.is_weather_dependent),
            "time_slot": o.time_slot or "flessibile",
        })
    today = date.today()
    end = today + timedelta(days=7)
    rng = f"Dal {today.day} {MESI[today.month-1]} al {end.day} {MESI[end.month-1]}"
    page = (PAGE.replace("__DATA__", json.dumps(data, ensure_ascii=False))
                .replace("__LABELS__", json.dumps(CAT_LABEL, ensure_ascii=False))
                .replace("__RANGE__", html.escape(rng))
                .replace("__UPDATED__", f"{today.day} {MESI[today.month-1]} {today.year}"))
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / "index.html"
    target.write_text(page, encoding="utf-8")
    print(f"{len(data)} schede, {sum(1 for d in data if d['programma'])} con programma -> {target}")
    return target


if __name__ == "__main__":
    build(Path(sys.argv[1] if len(sys.argv) > 1 else "site"))
