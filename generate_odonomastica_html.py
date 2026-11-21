#!/usr/bin/env python3
"""Static generator for Storie dalle Strade (odonomastica OSM + Wikidata)."""

import os
from pathlib import Path

from genova_outings.html_utils import (
    OPEN_DATA_ATTRIBUTION_TEXT,
    PWA_HEAD_HTML,
    PWA_SW_SCRIPT,
    get_data_dir,
    render_shared_nav,
)
from genova_outings.vanilla_css import VANILLA_CSS

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="it">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Storie dalle Strade — Genova Civica (2.293 Toponimi)</title>
  __PWA_HEAD__
  <style>__VANILLA_CSS__</style>
</head>
<body class="bg-[var(--background)] text-[var(--foreground)] antialiased min-h-screen flex flex-col">
  __SHARED_NAV__

  <header class="border-b border-[var(--border)] bg-[var(--card)] px-6 py-4">
    <div class="max-w-[1440px] mx-auto space-y-3">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 class="text-xl font-bold text-[var(--foreground)]">Storie dalle Strade di Genova</h1>
          <p class="text-xs text-[var(--muted-foreground)] mt-0.5">Archivio toponomastico OpenStreetMap + Wikidata (2.293 vie, piazze e personaggi storici).</p>
        </div>
        <span id="odo-count" class="text-xs font-semibold px-3 py-1 rounded-full bg-[var(--content)] border border-[var(--border)]">Caricamento...</span>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-12 gap-2.5">
        <div class="md:col-span-5">
          <input id="q-odo" type="search" oninput="runOdo(1)" placeholder="Cerca via, piazza, personaggio o categoria storica..."
            class="w-full px-3.5 py-2 text-xs rounded-lg border border-[var(--border)] bg-[var(--background)] text-[var(--foreground)]" />
        </div>
        <div class="md:col-span-3">
          <select id="sel-tipo" onchange="runOdo(1)" class="w-full px-3 py-2 text-xs rounded-lg border border-[var(--border)] bg-[var(--background)] text-[var(--foreground)]">
            <option value="ALL">Tutti i tipi di toponimo</option>
          </select>
        </div>
        <div class="md:col-span-4">
          <select id="sel-cat" onchange="runOdo(1)" class="w-full px-3 py-2 text-xs rounded-lg border border-[var(--border)] bg-[var(--background)] text-[var(--foreground)]">
            <option value="ALL">Tutte le categorie storiche</option>
          </select>
        </div>
      </div>
    </div>
  </header>

  <main class="flex-1 max-w-[1440px] w-full mx-auto p-6 space-y-4">
    <div class="flex flex-wrap items-center justify-between gap-3 bg-[var(--card)] p-3.5 rounded-xl border border-[var(--border)]">
      <div id="odo-status" class="text-xs font-semibold text-[var(--foreground)]">Caricamento archivio...</div>
      <div class="flex items-center gap-2">
        <button onclick="pageOdo(-1)" class="px-3 py-1 rounded-lg border border-[var(--border)] bg-[var(--background)] text-xs font-semibold">Precedenti</button>
        <span id="odo-page" class="text-xs font-mono px-2">Pag. 1 / 1</span>
        <button onclick="pageOdo(1)" class="px-3 py-1 rounded-lg border border-[var(--border)] bg-[var(--background)] text-xs font-semibold">Successivi</button>
      </div>
    </div>
    <div id="odo-grid" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3.5"></div>
  </main>

  <script>
    let ROWS = [];
    let MATCHES = [];
    let PAGE = 1;
    const PER_PAGE = 36;
    const esc = s => String(s ?? "").replace(/[&<>"']/g, m => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[m]));

    async function bootOdo() {
      try {
        const resp = await fetch("./data/odonomastica.json");
        if (!resp.ok) throw new Error("HTTP " + resp.status);
        ROWS = await resp.json();
        const tipi = Array.from(new Set(ROWS.map(r => r.tipo).filter(Boolean))).sort();
        const cats = Array.from(new Set(ROWS.map(r => r.categoria).filter(Boolean))).sort();
        const sTipo = document.getElementById("sel-tipo");
        tipi.forEach(t => { const o = document.createElement("option"); o.value = t; o.textContent = t; sTipo.appendChild(o); });
        const sCat = document.getElementById("sel-cat");
        cats.forEach(c => { const o = document.createElement("option"); o.value = c; o.textContent = c; sCat.appendChild(o); });
        document.getElementById("odo-count").textContent = `${ROWS.length} toponimi`;
        runOdo(1);
      } catch (err) {
        document.getElementById("odo-status").textContent = "Archivio disponibile via HTTP/HTTPS (./data/odonomastica.json).";
      }
    }

    function runOdo(p) {
      PAGE = p || 1;
      const q = document.getElementById("q-odo").value.trim().toLowerCase();
      const t = document.getElementById("sel-tipo").value;
      const c = document.getElementById("sel-cat").value;
      MATCHES = ROWS.filter(r => {
        if (t !== "ALL" && r.tipo !== t) return false;
        if (c !== "ALL" && r.categoria !== c) return false;
        if (q) {
          const hay = `${r.toponimo} ${r.personaggio} ${r.categoria}`.toLowerCase();
          if (!hay.includes(q)) return false;
        }
        return true;
      });
      renderOdo();
    }

    function renderOdo() {
      const grid = document.getElementById("odo-grid");
      grid.innerHTML = "";
      const totalPages = Math.max(1, Math.ceil(MATCHES.length / PER_PAGE));
      if (PAGE > totalPages) PAGE = totalPages;
      const start = (PAGE - 1) * PER_PAGE;
      const slice = MATCHES.slice(start, start + PER_PAGE);
      document.getElementById("odo-status").textContent = `Trovati ${MATCHES.length} toponimi — Mostrando ${slice.length ? start + 1 : 0}–${start + slice.length}`;
      document.getElementById("odo-page").textContent = `Pag. ${PAGE} / ${totalPages}`;
      slice.forEach(r => {
        const card = document.createElement("article");
        card.className = "rounded-xl border border-[var(--border)] bg-[var(--card)] p-4 flex flex-col justify-between gap-2";
        const osmSearch = `https://www.openstreetmap.org/search?query=${encodeURIComponent(r.toponimo + " Genova")}`;
        card.innerHTML = `
          <div class="space-y-1">
            <div class="text-xs font-bold uppercase tracking-wider text-amber-500">${esc(r.tipo || "Toponimo")}</div>
            <h2 class="text-base font-bold text-[var(--foreground)]">${esc(r.toponimo)}</h2>
            <div class="text-sm font-semibold text-blue-400">${esc(r.personaggio)}</div>
            ${r.categoria ? `<p class="text-xs text-[var(--muted-foreground)]">${esc(r.categoria)}</p>` : ""}
          </div>
          <div class="pt-2 border-t border-[var(--border)] flex justify-between items-center text-xs">
            <a href="${esc(osmSearch)}" target="_blank" rel="noopener" class="underline text-[var(--primary)] font-semibold">Vedi su OpenStreetMap</a>
          </div>
        `;
        grid.appendChild(card);
      });
    }

    function pageOdo(delta) {
      const totalPages = Math.max(1, Math.ceil(MATCHES.length / PER_PAGE));
      const next = Math.min(totalPages, Math.max(1, PAGE + delta));
      if (next !== PAGE) {
        PAGE = next;
        renderOdo();
        window.scrollTo({ top: 0, behavior: "smooth" });
      }
    }

    bootOdo();
  </script>
  __PWA_SW__
  <footer class="px-6 py-4 border-t border-[var(--border)] text-center text-xs text-[var(--muted-foreground)]">
    __ATTRIBUTION__
  </footer>
</body>
</html>
"""


def build(out_dir: Path | None = None) -> Path:
    base = out_dir or (get_data_dir() / "site")
    base.mkdir(parents=True, exist_ok=True)
    html_out = (
        HTML_TEMPLATE.replace("__PWA_HEAD__", PWA_HEAD_HTML)
        .replace("__PWA_SW__", PWA_SW_SCRIPT)
        .replace("__VANILLA_CSS__", VANILLA_CSS)
        .replace("__SHARED_NAV__", render_shared_nav("storie"))
        .replace("__ATTRIBUTION__", OPEN_DATA_ATTRIBUTION_TEXT)
    )
    target = base / "storie.html"
    target.write_text(html_out, encoding="utf-8")
    print(f"Generated {target} ({len(html_out) // 1024} KB)")
    return target


if __name__ == "__main__":
    build()
