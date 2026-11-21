import json
import os as _os
_DATA_DIR = _os.environ.get("GENOVA_DATA_DIR") or _os.path.dirname(_os.path.abspath(__file__))

with open(f"{_DATA_DIR}/esercenti_genova_provincia_db.json") as f:
    records = json.load(f)

# Compact representation for instant client-side search across all 4,966 records
compact = []
for idx, r in enumerate(records, 1):
    compact.append({
        "i": idx,
        "c": r["comune"],
        "q": r["quartiere_o_zona"],
        "n": r["nome"],
        "m": r["macro_settore"],
        "s": r["categoria_specifica"],
        "ind": 1 if r["indipendente"] else 0,
        "a": r["indirizzo"],
        "t": r["telefono"],
        "w": r["sito_o_social"],
        "o": r["orari"],
        "k": r["cosa_trovi_qui"],
        "p": r["personaggio_via"],
        "la": r["lat"],
        "lo": r["lon"]
    })

payload_str = json.dumps(compact, ensure_ascii=False).replace("<", "\\u003c")

html_doc = """<!DOCTYPE html>
<html lang="it">
<head>
  <meta charset="UTF-8">
  <title>Genova & Provincia — Navigatore Esercenti, Artigiani e Negozi di Quartiere (4.966 Attività)</title>
  <style>__VANILLA_CSS__</style>
</head>
<body class="min-h-screen flex flex-col antialiased">
  __SHARED_NAV__

  <!-- Header -->
  <header class="border-b border-[var(--border)] bg-[var(--card)] px-6 py-4 sticky top-0 z-30 shadow-lg">
    <div class="max-w-[1600px] mx-auto space-y-3">
      <div class="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div class="flex items-center gap-2">
            <span class="px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-amber-500 text-slate-950">Motore di Ricerca Territoriale Anti-Amazon</span>
            <span class="text-xs text-[var(--muted-foreground)]">4.966 Esercenti Censiti • 4.459 Indipendenti • 25 Quartieri di Genova + 66 Comuni</span>
          </div>
          <h1 class="text-xl font-bold mt-1 text-[var(--foreground)]">Dove lo compro o lo riparo a Genova e Provincia?</h1>
        </div>

        <div class="flex flex-wrap items-center gap-3">
          <label class="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-emerald-500/40 bg-emerald-500/10 text-emerald-400 text-xs font-bold cursor-pointer select-none">
            <input id="chk-indep" type="checkbox" checked onchange="runSearch(1)" class="accent-emerald-500 w-4 h-4" />
            <span>Solo Esercenti Indipendenti / Artigiani (Escludi GDO & Catene)</span>
          </label>
          <label class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[var(--border)] bg-[var(--background)] text-xs font-medium cursor-pointer select-none">
            <input id="chk-contacts" type="checkbox" onchange="runSearch(1)" class="accent-amber-500" />
            <span>Con Telefono / Sito / Orari</span>
          </label>
        </div>
      </div>

      <!-- Search & Filters Row -->
      <div class="grid grid-cols-1 md:grid-cols-12 gap-2.5">
        <div class="md:col-span-5 relative">
          <input id="q-input" type="text" oninput="runSearch(1)"
            placeholder="Cosa ti serve oggi? (es. 'viti', 'chiavi', 'cerniera', 'tappezziere', 'riparazione pc', 'ricambi bici', 'cornici', 'pasta fresca'...)"
            class="w-full px-3.5 py-2 text-xs rounded-lg border border-amber-500/50 bg-[var(--background)] text-[var(--foreground)] placeholder:text-[var(--muted-foreground)] focus:outline-none focus:border-amber-400" />
        </div>
        <div class="md:col-span-3">
          <select id="sel-quartiere" onchange="runSearch(1)" class="w-full px-3 py-2 text-xs rounded-lg border border-[var(--border)] bg-[var(--background)] text-[var(--foreground)]">
            <option value="ALL">Tutte le Zone (25 Quartieri GE + 66 Comuni)</option>
          </select>
        </div>
        <div class="md:col-span-2">
          <select id="sel-macro" onchange="populateSubcats(); runSearch(1)" class="w-full px-3 py-2 text-xs rounded-lg border border-[var(--border)] bg-[var(--background)] text-[var(--foreground)]">
            <option value="ALL">Tutti i 9 Macro-Settori</option>
            <option value="1.">1. Ferramenta, Vernici, Elettricità & Casa (236)</option>
            <option value="2.">2. Elettronica, PC, Elettrodomestici & Tech (156)</option>
            <option value="3.">3. Merceria, Sartoria, Calzolai & Vestiti (879)</option>
            <option value="4.">4. Casalinghi, Tappezzeria, Arredo & Vivaismo (296)</option>
            <option value="5.">5. Cartolerie, Librerie, Belle Arti & Musica (266)</option>
            <option value="6.">6. Forni, Pastifici, Macellerie, Pescherie & Sfuso (1.168)</option>
            <option value="7.">7. Ciclofficine, Moto/Auto, Nautica, Pesca & Sport (310)</option>
            <option value="8.">8. Erboristerie, Farmacie, Ottici, Ortopedie & Animali (978)</option>
            <option value="9.">9. Altri Servizi di Prossimità & Studi (677)</option>
          </select>
        </div>
        <div class="md:col-span-2">
          <select id="sel-subcat" onchange="runSearch(1)" class="w-full px-3 py-2 text-xs rounded-lg border border-[var(--border)] bg-[var(--background)] text-[var(--foreground)]">
            <option value="ALL">Tutte le Categorie Specifiche</option>
          </select>
        </div>
      </div>

      <!-- Quick "Ho bisogno di..." Anti-Amazon Pills -->
      <div class="flex flex-wrap items-center gap-1.5 pt-1">
        <span class="text-xs font-bold text-amber-400 mr-1">🔥 Ricerche rapide Anti-Amazon:</span>
        <button onclick="quickNeed('Ferramenta', '1.')" class="px-2.5 py-1 rounded-md text-xs font-medium bg-[var(--content)] hover:bg-amber-500 hover:text-slate-950 transition">🔧 Ferramenta & Chiavi</button>
        <button onclick="quickNeed('Colorificio', '1.')" class="px-2.5 py-1 rounded-md text-xs font-medium bg-[var(--content)] hover:bg-amber-500 hover:text-slate-950 transition">🎨 Vernici & Colorifici</button>
        <button onclick="quickNeed('Materiale Elettrico', '1.')" class="px-2.5 py-1 rounded-md text-xs font-medium bg-[var(--content)] hover:bg-amber-500 hover:text-slate-950 transition">💡 Elettricità & Cavi</button>
        <button onclick="quickNeed('Falegnam', '1.')" class="px-2.5 py-1 rounded-md text-xs font-medium bg-[var(--content)] hover:bg-amber-500 hover:text-slate-950 transition">🪚 Falegnami & Vetrai</button>
        <button onclick="quickNeed('Computer', '2.')" class="px-2.5 py-1 rounded-md text-xs font-medium bg-[var(--content)] hover:bg-amber-500 hover:text-slate-950 transition">💻 Assistenza PC & Schede</button>
        <button onclick="quickNeed('Casalinghi', '4.')" class="px-2.5 py-1 rounded-md text-xs font-medium bg-[var(--content)] hover:bg-amber-500 hover:text-slate-950 transition">🍳 Casalinghi & Ricambi Moka</button>
        <button onclick="quickNeed('Tappezz', '4.')" class="px-2.5 py-1 rounded-md text-xs font-medium bg-[var(--content)] hover:bg-amber-500 hover:text-slate-950 transition">🛋️ Tappezzieri & Tendaggi</button>
        <button onclick="quickNeed('Cucito', '3.')" class="px-2.5 py-1 rounded-md text-xs font-medium bg-[var(--content)] hover:bg-amber-500 hover:text-slate-950 transition">🧵 Mercerie, Tessuti & Sarti</button>
        <button onclick="quickNeed('Calzolaio', '3.')" class="px-2.5 py-1 rounded-md text-xs font-medium bg-[var(--content)] hover:bg-amber-500 hover:text-slate-950 transition">👞 Calzolai & Pelletterie</button>
        <button onclick="quickNeed('Cartoleria', '5.')" class="px-2.5 py-1 rounded-md text-xs font-medium bg-[var(--content)] hover:bg-amber-500 hover:text-slate-950 transition">📎 Cartolerie & Copisterie</button>
        <button onclick="quickNeed('Biciclette', '7.')" class="px-2.5 py-1 rounded-md text-xs font-medium bg-[var(--content)] hover:bg-amber-500 hover:text-slate-950 transition">🚲 Ciclofficine & Ricambi Moto</button>
        <button onclick="quickNeed('Nautic', '7.')" class="px-2.5 py-1 rounded-md text-xs font-medium bg-[var(--content)] hover:bg-amber-500 hover:text-slate-950 transition">⚓ Forniture Nautiche & Pesca</button>
        <button onclick="quickNeed('Pastificio', '6.')" class="px-2.5 py-1 rounded-md text-xs font-medium bg-[var(--content)] hover:bg-amber-500 hover:text-slate-950 transition">🥟 Pastifici, Forni & Sciamadde</button>
        <button onclick="quickNeed('Erboristeria', '8.')" class="px-2.5 py-1 rounded-md text-xs font-medium bg-[var(--content)] hover:bg-amber-500 hover:text-slate-950 transition">🌿 Erboristerie & Ortopedie</button>
        <button onclick="resetAll()" class="px-2.5 py-1 rounded-md text-xs font-bold bg-red-500/20 text-red-300 hover:bg-red-500 hover:text-white transition">✕ Azzera Filtri</button>
      </div>
    </div>
  </header>

  <!-- Main Content -->
  <main class="flex-1 max-w-[1600px] w-full mx-auto p-6 space-y-4">

    <!-- Top Stats & Pagination Controls -->
    <div class="flex flex-wrap items-center justify-between gap-3 bg-[var(--card)] p-3.5 rounded-xl border border-[var(--border)]">
      <div id="status-bar" class="text-xs font-semibold text-[var(--foreground)]">Caricamento...</div>
      <div class="flex items-center gap-2">
        <button onclick="changePage(-1)" class="px-3 py-1 rounded-lg border border-[var(--border)] bg-[var(--background)] text-xs font-semibold hover:bg-[var(--content)]">← Pagina Prec.</button>
        <span id="page-num" class="text-xs font-mono px-2">1 / 1</span>
        <button onclick="changePage(1)" class="px-3 py-1 rounded-lg border border-[var(--border)] bg-[var(--background)] text-xs font-semibold hover:bg-[var(--content)]">Pagina Succ. →</button>
      </div>
    </div>

    <!-- Cards Grid -->
    <div id="grid" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3.5"></div>

  </main>

  <script>
    const DB = __PAYLOAD__;
    let currentMatches = [];
    let currentPage = 1;
    const PER_PAGE = 30;

    function initApp() {
      // Populate Quartieri / Comuni dropdown grouped nicely
      const qCounts = {};
      DB.forEach(r => { qCounts[r.q] = (qCounts[r.q] || 0) + 1; });
      const selQ = document.getElementById("sel-quartiere");
      const genovaQs = Object.keys(qCounts).filter(x => x.startsWith("Genova —")).sort();
      const provQs = Object.keys(qCounts).filter(x => !x.startsWith("Genova —")).sort();

      const grpGe = document.createElement("optgroup");
      grpGe.label = "Quartieri di Genova (25 Delegazioni)";
      genovaQs.forEach(q => {
        const opt = document.createElement("option");
        opt.value = q;
        opt.textContent = `${q.replace("Genova — ", "")} (${qCounts[q]})`;
        grpGe.appendChild(opt);
      });
      selQ.appendChild(grpGe);

      const grpPr = document.createElement("optgroup");
      grpPr.label = "Comuni della Provincia (66 Comuni)";
      provQs.forEach(q => {
        const opt = document.createElement("option");
        opt.value = q;
        opt.textContent = `${q.replace("Provincia — ", "")} (${qCounts[q]})`;
        grpPr.appendChild(opt);
      });
      selQ.appendChild(grpPr);

      populateSubcats();
      runSearch(1);
    }

    function populateSubcats() {
      const mac = document.getElementById("sel-macro").value;
      const selSub = document.getElementById("sel-subcat");
      selSub.innerHTML = '<option value="ALL">Tutte le Categorie Specifiche</option>';
      const subCounts = {};
      DB.forEach(r => {
        if (mac === "ALL" || r.m.startsWith(mac)) {
          subCounts[r.s] = (subCounts[r.s] || 0) + 1;
        }
      });
      Object.keys(subCounts).sort().forEach(s => {
        const opt = document.createElement("option");
        opt.value = s;
        opt.textContent = `${s} (${subCounts[s]})`;
        selSub.appendChild(opt);
      });
    }

    function quickNeed(term, macroPrefix) {
      document.getElementById("sel-macro").value = macroPrefix || "ALL";
      populateSubcats();
      document.getElementById("q-input").value = term;
      runSearch(1);
    }

    function resetAll() {
      document.getElementById("q-input").value = "";
      document.getElementById("sel-quartiere").value = "ALL";
      document.getElementById("sel-macro").value = "ALL";
      document.getElementById("chk-indep").checked = true;
      document.getElementById("chk-contacts").checked = false;
      populateSubcats();
      runSearch(1);
    }

    function runSearch(page) {
      currentPage = page || 1;
      const q = document.getElementById("q-input").value.trim().toLowerCase();
      const qZone = document.getElementById("sel-quartiere").value;
      const mac = document.getElementById("sel-macro").value;
      const sub = document.getElementById("sel-subcat").value;
      const onlyIndep = document.getElementById("chk-indep").checked;
      const onlyContacts = document.getElementById("chk-contacts").checked;

      const terms = q ? q.split(/\\s+/) : [];

      currentMatches = DB.filter(r => {
        if (onlyIndep && r.ind === 0) return false;
        if (onlyContacts && !r.t && !r.w && !r.o) return false;
        if (qZone !== "ALL" && r.q !== qZone) return false;
        if (mac !== "ALL" && !r.m.startsWith(mac)) return false;
        if (sub !== "ALL" && r.s !== sub) return false;
        if (terms.length > 0) {
          const hay = `${r.n} ${r.s} ${r.k} ${r.a} ${r.q} ${r.p}`.toLowerCase();
          for (const t of terms) {
            if (!hay.includes(t)) return false;
          }
        }
        return true;
      });

      renderGrid();
    }

    function renderGrid() {
      const grid = document.getElementById("grid");
      grid.innerHTML = "";

      const totalPages = Math.max(1, Math.ceil(currentMatches.length / PER_PAGE));
      if (currentPage > totalPages) currentPage = totalPages;

      const start = (currentPage - 1) * PER_PAGE;
      const slice = currentMatches.slice(start, start + PER_PAGE);

      document.getElementById("status-bar").innerHTML =
        `Trovati <span class="text-amber-400 font-bold">${currentMatches.length}</span> esercenti sul territorio — Mostrando ${slice.length > 0 ? start + 1 : 0}–${start + slice.length}`;
      document.getElementById("page-num").textContent = `Pag. ${currentPage} / ${totalPages}`;

      function esc(s) {
        return String(s ?? "").replace(/[&<>"']/g, m => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[m]));
      }
      function safeUrl(u) {
        const s = String(u ?? "").trim();
        return /^https?:\/\//i.test(s) ? s : "";
      }
      function safeTel(t) {
        return String(t ?? "").replace(/[^0-9+\-()\s]/g, "").trim();
      }

      slice.forEach(r => {
        const mapLink = r.la && r.lo
          ? `https://www.openstreetmap.org/?mlat=${encodeURIComponent(r.la)}&mlon=${encodeURIComponent(r.lo)}#map=18/${encodeURIComponent(r.la)}/${encodeURIComponent(r.lo)}`
          : `https://www.openstreetmap.org/search?query=${encodeURIComponent(r.n + " " + r.c)}`;
        const webHref = safeUrl(r.w);
        const telClean = safeTel(r.t);

        const card = document.createElement("div");
        card.className = "rounded-xl border border-[var(--border)] bg-[var(--card)] p-4 flex flex-col justify-between gap-3 hover:border-amber-500/60 transition";
        card.innerHTML = `
          <div class="space-y-1.5">
            <div class="flex items-start justify-between gap-2">
              <span class="text-xs font-bold text-amber-400">${esc(r.q)}</span>
              ${r.ind
                ? `<span class="px-2 py-0.5 rounded-full text-[11px] font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">Indipendente / Locale</span>`
                : `<span class="px-2 py-0.5 rounded-full text-[11px] font-medium bg-slate-700 text-slate-300">Catena / GDO</span>`
              }
            </div>
            <h3 class="text-base font-bold text-[var(--foreground)] leading-snug">${esc(r.n)}</h3>
            <div class="text-xs font-semibold text-blue-400">${esc(r.s)}</div>
            ${r.a ? `<div class="text-xs text-[var(--foreground)]">📍 ${esc(r.a)} (${esc(r.c)})</div>` : `<div class="text-xs text-[var(--muted-foreground)]">📍 ${esc(r.c)}</div>`}
            ${r.o ? `<div class="text-xs text-emerald-400 font-medium">🕒 Orari: ${esc(r.o)}</div>` : ""}
            <div class="p-2 rounded-lg bg-[var(--content)] border border-[var(--border)] text-xs text-[var(--muted-foreground)]">
              🔎 <strong class="text-[var(--foreground)]">Cosa trovi / Parole chiave:</strong> ${esc(r.k)}
            </div>
            ${r.p ? `<div class="text-[11px] text-slate-400">🏛️ Via intitolata a: <strong>${esc(r.p)}</strong></div>` : ""}
          </div>

          <div class="pt-2 border-t border-[var(--border)] flex flex-wrap items-center justify-between gap-2">
            <div class="flex items-center gap-2">
              ${telClean ? `<a href="tel:${esc(telClean)}" class="px-2.5 py-1 rounded bg-emerald-600/20 border border-emerald-500/40 text-emerald-300 text-xs font-mono font-semibold hover:bg-emerald-600 hover:text-white transition">📞 ${esc(r.t)}</a>` : `<span class="text-xs text-[var(--muted-foreground)]">Tel. non indicato</span>`}
              ${webHref ? `<a href="${esc(webHref)}" target="_blank" rel="noopener" class="px-2.5 py-1 rounded bg-amber-500 text-slate-950 text-xs font-bold hover:opacity-90">Sito / Social ↗</a>` : ""}
            </div>
            <a href="${esc(mapLink)}" target="_blank" rel="noopener" class="text-xs font-semibold text-[var(--muted-foreground)] hover:text-amber-400 underline">Mappa esatta ↗</a>
          </div>
        `;
        grid.appendChild(card);
      });
    }

    function changePage(delta) {
      const totalPages = Math.max(1, Math.ceil(currentMatches.length / PER_PAGE));
      const next = Math.min(totalPages, Math.max(1, currentPage + delta));
      if (next !== currentPage) {
        currentPage = next;
        renderGrid();
        window.scrollTo({ top: 0, behavior: "smooth" });
      }
    }

    initApp();
  </script>
  <footer class="px-6 py-4 border-t border-[var(--border)] text-center text-xs text-[var(--muted-foreground)]">
    Dati geografici e toponimi: © OpenStreetMap contributors (ODbL 1.0) · Wikidata (CC0).
  </footer>
</body>
</html>
"""

from genova_outings.vanilla_css import VANILLA_CSS
from genova_outings.html_utils import render_shared_nav
final_html = html_doc.replace("__VANILLA_CSS__", VANILLA_CSS).replace("__SHARED_NAV__", render_shared_nav("esercenti")).replace("__PAYLOAD__", payload_str)
with open(f"{_DATA_DIR}/navigatore_esercenti_genova_provincia.html", "w", encoding="utf-8") as f:
    f.write(final_html)

print("Generated /Users/dany/genova/navigatore_esercenti_genova_provincia.html! Size:", len(final_html)//1024, "KB")
