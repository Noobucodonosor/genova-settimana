"""Lightweight local Web UI for Genova Weekly Informal Outings.

Runs via Python standard library http.server on localhost:8765.
Provides:
- Embedded responsive single-page application with cards and checkboxes.
- Category filter pills and tone selector.
- Clickable official links.
- Real-time WhatsApp message preview bubble.
- 1-click clipboard copy (navigator.clipboard).
- JSON API endpoints: /api/catalog and /api/format.
"""

from __future__ import annotations

import json
import logging
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, List, Optional, Union

from genova_outings.catalog import get_weekly_catalog
from genova_outings.formatter import format_whatsapp_message
from genova_outings.models import OutingCategory, OutingOption, WeeklyCatalog

logger = logging.getLogger(__name__)

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="it">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Cosa facciamo Genova</title>
  <style>
    :root {
      --primary: #128c7e;
      --primary-dark: #075e54;
      --accent: #25d366;
      --bg: #f0f2f5;
      --card-bg: #ffffff;
      --text: #111b21;
      --text-muted: #667781;
      --border: #e9edef;
      --bubble-bg: #d9fdd3;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background-color: var(--bg);
      color: var(--text);
      line-height: 1.5;
      padding: 20px;
    }
    .container {
      max-width: 1200px;
      margin: 0 auto;
    }
    header {
      background: var(--card-bg);
      padding: 24px;
      border-radius: 12px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.08);
      margin-bottom: 20px;
    }
    h1 {
      font-size: 1.6rem;
      color: var(--primary-dark);
      margin-bottom: 6px;
    }
    .subtitle {
      color: var(--text-muted);
      font-size: 0.95rem;
      margin-bottom: 14px;
    }
    .search-box {
      display: flex;
      gap: 8px;
      align-items: center;
      background: var(--bg);
      border: 1.5px solid var(--border);
      border-radius: 10px;
      padding: 8px 14px;
      margin-bottom: 10px;
    }
    .search-box:focus-within {
      border-color: var(--primary);
      background: #fff;
    }
    .search-input {
      flex: 1;
      border: 0;
      background: transparent;
      font-size: 1rem;
      color: var(--text);
      outline: none;
    }
    .prompt-chips {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-bottom: 6px;
    }
    .prompt-chip {
      background: transparent;
      border: 1px dashed #cbd5e1;
      border-radius: 999px;
      padding: 4px 11px;
      font-size: 0.82rem;
      color: var(--text-muted);
      cursor: pointer;
    }
    .prompt-chip:hover, .prompt-chip.active {
      border-style: solid;
      border-color: var(--primary);
      color: var(--primary-dark);
      background: #e6f4f1;
    }
    .answer-banner {
      background: #e6f4f1;
      border: 1px solid #b2dfdb;
      color: #004d40;
      padding: 10px 14px;
      border-radius: 8px;
      font-size: 0.9rem;
      margin-bottom: 12px;
      display: none;
    }
    .answer-banner.show {
      display: block;
    }
    .toolbar {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      align-items: center;
      margin-top: 16px;
      padding-top: 16px;
      border-top: 1px solid var(--border);
    }
    .filter-pills {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }
    .pill {
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 6px 14px;
      font-size: 0.85rem;
      cursor: pointer;
      transition: all 0.2s ease;
    }
    .pill.active {
      background: var(--primary);
      color: #fff;
      border-color: var(--primary);
    }
    .tone-select {
      padding: 6px 12px;
      border-radius: 8px;
      border: 1px solid var(--border);
      background: var(--card-bg);
      font-size: 0.9rem;
    }
    .btn-action {
      background: #f0f2f5;
      border: 1px solid #d1d7db;
      padding: 6px 14px;
      border-radius: 8px;
      font-size: 0.85rem;
      cursor: pointer;
    }
    .btn-action:hover {
      background: #e9edef;
    }
    .main-grid {
      display: grid;
      grid-template-columns: 1fr 420px;
      gap: 20px;
      align-items: start;
    }
    @media (max-width: 900px) {
      .main-grid { grid-template-columns: 1fr; }
    }
    .catalog-list {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    .card {
      background: var(--card-bg);
      border-radius: 10px;
      padding: 16px;
      box-shadow: 0 1px 2px rgba(0,0,0,0.06);
      display: flex;
      gap: 14px;
      cursor: pointer;
      border: 2px solid transparent;
      transition: border-color 0.15s ease, transform 0.15s ease;
    }
    .card:hover {
      transform: translateY(-1px);
    }
    .card.selected {
      border-color: var(--accent);
      background-color: #f7fdf9;
    }
    .card-checkbox {
      margin-top: 4px;
      width: 20px;
      height: 20px;
      cursor: pointer;
      accent-color: var(--primary);
    }
    .card-body {
      flex: 1;
    }
    .card-title {
      font-weight: 600;
      font-size: 1.05rem;
      margin-bottom: 4px;
    }
    .card-meta {
      font-size: 0.85rem;
      color: var(--text-muted);
      margin-bottom: 6px;
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }
    .card-prog { margin-top: 8px; padding: 8px 10px; border-left: 3px solid #2563eb; background: rgba(37,99,235,0.06); border-radius: 6px; font-size: 13px; }
    .card-prog-h { font-weight: 600; margin-bottom: 4px; }
    .card-prog ul { margin: 0; padding-left: 16px; }
    .card-prog li { margin: 2px 0; }
    .card-prog li span { color: #64748b; }
    .card-desc {
      font-size: 0.9rem;
      color: #3b4a54;
      margin-bottom: 8px;
    }
    .card-link {
      color: var(--primary);
      text-decoration: none;
      font-size: 0.85rem;
      font-weight: 500;
      display: inline-block;
    }
    .card-link:hover {
      text-decoration: underline;
    }
    .preview-panel {
      position: sticky;
      top: 20px;
      background: var(--card-bg);
      border-radius: 12px;
      padding: 20px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    .preview-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
    }
    .preview-header h2 {
      font-size: 1.15rem;
      color: var(--primary-dark);
    }
    .preview-bubble {
      background: var(--bubble-bg);
      border-radius: 8px;
      padding: 14px;
      font-size: 0.9rem;
      white-space: pre-wrap;
      font-family: inherit;
      min-height: 200px;
      max-height: 500px;
      overflow-y: auto;
      border: 1px solid #c7f3be;
      margin-bottom: 14px;
    }
    .btn-copy {
      width: 100%;
      background: var(--primary);
      color: #fff;
      border: none;
      border-radius: 8px;
      padding: 12px;
      font-size: 1rem;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      justify-content: center;
      align-items: center;
      gap: 8px;
      transition: background-color 0.2s ease;
    }
    .btn-copy:hover {
      background: var(--primary-dark);
    }
    .toast {
      position: fixed;
      bottom: 24px;
      right: 24px;
      background: #111b21;
      color: #fff;
      padding: 12px 20px;
      border-radius: 8px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.2);
      font-size: 0.9rem;
      opacity: 0;
      transform: translateY(10px);
      transition: all 0.3s ease;
      pointer-events: none;
      z-index: 1000;
    }
    .toast.show {
      opacity: 1;
      transform: translateY(0);
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>Cosa facciamo Genova</h1>
      <p class="subtitle">Scrivi cosa ti va di fare o spunta le proposte di tuo interesse per generare il messaggio WhatsApp.</p>

      <div class="search-box">
        <input id="searchInput" class="search-input" type="search" placeholder="Chiedi qui, es: stasera dove vado a ballare? o se piove?" autocomplete="off" aria-label="Cerca o chiedi cosa fare a Genova">
      </div>
      <div class="prompt-chips" id="promptChips">
        <button class="prompt-chip" type="button" data-q="stasera dove vado a ballare?">💃 Stasera dove vado a ballare?</button>
        <button class="prompt-chip" type="button" data-q="cosa c'è stasera?">🌙 Cosa c'è stasera?</button>
        <button class="prompt-chip" type="button" data-q="dove andiamo se piove?">🌧️ Se piove dove andiamo?</button>
        <button class="prompt-chip" type="button" data-q="bere qualcosa o aperitivo nei caruggi">🍷 Bere qualcosa nei caruggi</button>
        <button class="prompt-chip" type="button" data-q="film al cinema">🎬 Che film danno?</button>
      </div>

      <div class="toolbar">
        <div class="filter-pills" id="pillsContainer">
          <button class="pill active" data-cat="all">Tutte</button>
          <button class="pill" data-cat="cinema">🎬 Cinema</button>
          <button class="pill" data-cat="mostra">🏛️ Mostre</button>
          <button class="pill" data-cat="passeggiata">🌿 Passeggiate</button>
          <button class="pill" data-cat="biblioteca">📚 Biblioteche</button>
          <button class="pill" data-cat="laboratorio">🎭 Laboratori</button>
          <button class="pill" data-cat="musica">🎶 Musica e serate</button>
          <button class="pill" data-cat="ritrovo">☕ Ritrovi</button>
        </div>

        <div style="margin-left: auto; display: flex; gap: 8px; align-items: center;">
          <select id="toneSelect" class="tone-select" aria-label="Tono del messaggio">
            <option value="amichevole">Tono: Amichevole</option>
            <option value="weekend">Tono: Weekend</option>
            <option value="minimal">Tono: Minimal</option>
          </select>
          <button class="btn-action" id="selectAllBtn">Seleziona tutti</button>
          <button class="btn-action" id="clearAllBtn">Deseleziona</button>
        </div>
      </div>
    </header>

    <div class="main-grid">
      <div>
        <div id="answerBanner" class="answer-banner"></div>
        <div class="catalog-list" id="catalogList">
          <p style="padding: 20px; color: var(--text-muted);">Caricamento catalogo settimanale...</p>
        </div>
      </div>

      <div class="preview-panel">
        <div class="preview-header">
          <h2>Anteprima WhatsApp</h2>
          <span id="selectedCount" style="font-size: 0.85rem; color: var(--text-muted);">0 selezionate</span>
        </div>
        <div class="preview-bubble" id="whatsappPreview">Nessuna attività selezionata.</div>
        <button class="btn-copy" id="copyBtn">
          📋 Copia Messaggio WhatsApp
        </button>
      </div>
    </div>
  </div>

  <div class="toast" id="toast">Messaggio copiato negli appunti!</div>

  <script>
    let catalogItems = [];
    let selectedIds = new Set();
    let currentFilter = 'all';
    let currentQuery = '';

    const norm = s => String(s ?? '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
    const STOP = new Set(["stasera","oggi","domani","dove","vado","andiamo","andare","cosa","facciamo","fare","ce","c","e","a","in","di","da","per","con","su","tra","fra","il","lo","la","i","gli","le","un","uno","una","mi","ti","ci","si","vi","che","chi","qualcosa","consigli","consiglio","vorrei","voglio","posto","posti","genova","settimana","questa","questo","nel","nella","nei","nelle","al","allo","alla","ai","agli","alle","del","dello","della","dei","degli","delle","se","o","oppure","ma","anche","po","bel","bella","bello","sera","pomeriggio","mattina","notte"]);
    const INTENTS = [
      {
        name: "ballare",
        triggers: ["ballare","ballo","balla","danzare","danza","discoteca","dj","club","milonga","tango","swing","lindy","blues dance","salsa","latino","pista","movida"],
        boostTerms: ["ballare","ballo","swing","lindy","blues","milonga","tango","dj","claque","count basie","luzzati","zenaswingers","circolo vega","mog"],
        cats: ["musica","ritrovo"],
        banner: "Ecco i posti dove ballare o fare serata a Genova tra live club, swing e blues dance, milonga, dj set e piazze dei caruggi:"
      },
      {
        name: "bere",
        triggers: ["bere","aperitivo","calice","vino","birra","cocktail","drink","pub","enoteca","caruggi","vicoli"],
        boostTerms: ["aperitivo","vino","birra","cocktail","luzzati","mog","mercato orientale","caruggi","ritrovo"],
        cats: ["ritrovo","musica","laboratorio"],
        banner: "Ecco i posti per bere qualcosa, fare aperitivo o fermarsi nei caruggi:"
      },
      {
        name: "pioggia",
        triggers: ["piove","pioggia","diluvia","coperto","interno","freddo","brutto tempo"],
        boostTerms: ["indoor","cinema","mostra","museo","palazzo","biblioteca","teatro","mercato"],
        cats: ["cinema","mostra","biblioteca","musica","laboratorio"],
        indoorOnly: true,
        banner: "Se piove o fa freddo, queste sono tutte proposte al coperto:"
      },
      {
        name: "cinema",
        triggers: ["film","cinema","proiezione","proiezioni","lingua originale"],
        boostTerms: ["cinema","sivori","america","odeon","nickelodeon","film"],
        cats: ["cinema"],
        banner: "Ecco i cinema e cineclub con i film in programmazione questa settimana:"
      },
      {
        name: "mostra",
        triggers: ["mostra","mostre","museo","musei","arte","quadri","fotografia","palazzo"],
        boostTerms: ["mostra","museo","palazzo","ducale","strada nuova","reale","spinola","galata","castello"],
        cats: ["mostra"],
        banner: "Ecco le mostre e i musei aperti con le esposizioni in corso:"
      }
    ];

    function filterByQuery(items, rawQuery) {
      const q = norm(rawQuery).replace(/[?!.,;:()"']/g, ' ').replace(/\s+/g, ' ').trim();
      const banner = document.getElementById('answerBanner');
      if (!q) {
        banner.classList.remove('show');
        return items;
      }
      const matchedIntents = INTENTS.filter(it => it.triggers.some(tr => q.includes(norm(tr))));
      const words = q.split(' ').filter(w => w.length > 2 && !STOP.has(w));
      const wantEvening = /\b(stasera|sera|serata|notte)\b/.test(q);

      const scored = items.map(item => {
        const prog = (item.raw_metadata && item.raw_metadata.programma) || [];
        const hay = norm([
          item.title, item.venue, item.zone, item.day_time, item.description, item.category,
          ...(item.tags || []),
          ...prog.map(p => `${p.titolo} ${p.quando}`)
        ].join(' '));
        let score = 0;
        if (matchedIntents.length > 0) {
          for (const it of matchedIntents) {
            if (it.indoorOnly && item.is_weather_dependent) return { item, score: 0 };
            let hits = 0;
            for (const b of it.boostTerms) { if (hay.includes(norm(b))) hits += 3; }
            if ((item.tags || []).some(t => it.triggers.includes(norm(t)) || it.boostTerms.includes(norm(t)))) hits += 8;
            if (it.cats.includes((item.category || '').toLowerCase())) hits += 2;
            if (it.name === 'ballare' && hits < 3) continue;
            score += hits;
          }
          if (score === 0) return { item, score: 0 };
        }
        for (const w of words) {
          const isIntentWord = matchedIntents.some(it => it.triggers.some(tr => norm(tr).includes(w) || w.includes(norm(tr))));
          if (hay.includes(w)) score += 5;
          else if (!isIntentWord && matchedIntents.length === 0) return { item, score: 0 };
        }
        if (matchedIntents.length === 0 && words.length === 0) score = 2;
        if (wantEvening && (item.time_slot === 'sera' || hay.includes('21:') || hay.includes('20:') || hay.includes('24:00'))) score += 4;
        if (prog.length > 0) score += 2;
        return { item, score };
      }).filter(x => x.score > 0).sort((a, b) => b.score - a.score);

      const res = scored.map(x => x.item);
      banner.textContent = res.length
        ? (matchedIntents.length ? matchedIntents[0].banner : `Proposte trovate per "${rawQuery.trim()}" (${res.length}):`)
        : `Nessun risultato esatto per "${rawQuery.trim()}". Prova a cliccare su "Tutte" o a cercare "ballare", "cinema", "piove".`;
      banner.classList.add('show');
      return res;
    }

    async function init() {
      try {
        const resp = await fetch('/api/catalog');
        const data = await resp.json();
        catalogItems = data.activities || [];
        renderCatalog();
        updatePreview();
      } catch (err) {
        document.getElementById('catalogList').innerHTML =
          '<p style="color: red; padding: 20px;">Errore durante il caricamento del catalogo.</p>';
      }
    }

    function esc(s) {
      return String(s ?? '').replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
    }

    function safeUrl(u) {
      const s = String(u ?? '').trim();
      return /^https?:\/\//i.test(s) ? s : '';
    }

    function renderCatalog() {
      const container = document.getElementById('catalogList');
      container.innerHTML = '';

      let filtered = currentFilter === 'all'
        ? catalogItems
        : catalogItems.filter(item => {
            const cat = (item.category || '').toLowerCase();
            return cat === currentFilter;
          });
      filtered = filterByQuery(filtered, currentQuery);

      if (filtered.length === 0) {
        container.innerHTML = '<p style="padding: 20px; color: var(--text-muted);">Nessuna attività in questa categoria.</p>';
        return;
      }

      filtered.forEach(item => {
        const card = document.createElement('div');
        const isChecked = selectedIds.has(item.id);
        card.className = 'card' + (isChecked ? ' selected' : '');

        const loc = item.zone ? `${item.venue} (${item.zone})` : item.venue;
        const href = safeUrl(item.verified_url);

        card.innerHTML = `
          <input type="checkbox" class="card-checkbox" ${isChecked ? 'checked' : ''} aria-label="Seleziona ${esc(item.title)}">
          <div class="card-body">
            <div class="card-title">${esc(item.title)}</div>
            <div class="card-meta">
              <span>📍 ${esc(loc)}</span>
              ${item.day_time ? `<span>🗓️ ${esc(item.day_time)}</span>` : ''}
            </div>
            ${item.description ? `<div class="card-desc">${esc(item.description)}</div>` : ''}
            ${(item.raw_metadata && item.raw_metadata.programma && item.raw_metadata.programma.length) ? `<div class="card-prog"><div class="card-prog-h">In programma nei prossimi 7 giorni</div><ul>${item.raw_metadata.programma.map(p => `<li><b>${esc(p.titolo)}</b> <span>${esc(p.quando)}</span></li>`).join('')}</ul></div>` : ''}
            ${href ? `<a class="card-link" href="${esc(href)}" target="_blank" rel="noopener">Fonte ufficiale &rarr;</a>` : ''}
          </div>
        `;

        card.addEventListener('click', (e) => {
          if (e.target.tagName === 'A') return;
          const chk = card.querySelector('.card-checkbox');
          if (e.target !== chk) {
            chk.checked = !chk.checked;
          }
          if (chk.checked) {
            selectedIds.add(item.id);
            card.classList.add('selected');
          } else {
            selectedIds.delete(item.id);
            card.classList.remove('selected');
          }
          updatePreview();
        });

        container.appendChild(card);
      });
    }

    async function updatePreview() {
      document.getElementById('selectedCount').innerText = `${selectedIds.size} selezionate`;
      const tone = document.getElementById('toneSelect').value;

      try {
        const resp = await fetch('/api/format', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            selected_ids: Array.from(selectedIds),
            tone: tone
          })
        });
        const data = await resp.json();
        document.getElementById('whatsappPreview').innerText = data.message || 'Nessuna attività selezionata.';
      } catch (err) {
        document.getElementById('whatsappPreview').innerText = 'Errore anteprima.';
      }
    }

    // Search box and quick prompt chips
    const searchInput = document.getElementById('searchInput');
    function applySearchQuery(val) {
      currentQuery = val;
      searchInput.value = val;
      document.querySelectorAll('.prompt-chip').forEach(b => b.classList.toggle('active', b.dataset.q === val));
      if (val && currentFilter !== 'all') {
        currentFilter = 'all';
        document.querySelectorAll('.pill').forEach(b => b.classList.toggle('active', b.dataset.cat === 'all'));
      }
      renderCatalog();
    }
    searchInput.addEventListener('input', (e) => applySearchQuery(e.target.value));
    document.querySelectorAll('.prompt-chip').forEach(btn => {
      btn.addEventListener('click', () => {
        applySearchQuery(currentQuery === btn.dataset.q ? '' : btn.dataset.q);
      });
    });

    // Filter pills
    document.querySelectorAll('.pill').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.pill').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentFilter = btn.dataset.cat;
        renderCatalog();
      });
    });

    document.getElementById('toneSelect').addEventListener('change', updatePreview);

    document.getElementById('selectAllBtn').addEventListener('click', () => {
      catalogItems.forEach(i => selectedIds.add(i.id));
      renderCatalog();
      updatePreview();
    });

    document.getElementById('clearAllBtn').addEventListener('click', () => {
      selectedIds.clear();
      renderCatalog();
      updatePreview();
    });

    // Copy to clipboard
    document.getElementById('copyBtn').addEventListener('click', async () => {
      const text = document.getElementById('whatsappPreview').innerText;
      if (!text || text === 'Nessuna attività selezionata.') return;

      try {
        await navigator.clipboard.writeText(text);
        showToast('Messaggio WhatsApp copiato negli appunti!');
      } catch (err) {
        showToast('Copia manuale: seleziona il testo.');
      }
    });

    function showToast(msg) {
      const toast = document.getElementById('toast');
      toast.innerText = msg;
      toast.classList.add('show');
      setTimeout(() => toast.classList.remove('show'), 2500);
    }

    init();
  </script>
</body>
</html>
"""


class OutingsWebHandler(BaseHTTPRequestHandler):
    """HTTP request handler serving catalog and formatting API."""

    def __init__(self, *args, catalog: Optional[WeeklyCatalog] = None, **kwargs):
        self.catalog = catalog or get_weekly_catalog(live_verify=False)
        super().__init__(*args, **kwargs)

    def log_message(self, format, *args):
        """Suppress standard access logs in test runs."""
        pass

    def _send_json(self, status: int, data: Any):
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        origin = self.headers.get("Origin", "")
        if origin.startswith(("http://127.0.0.1", "http://localhost")):
            self.send_header("Access-Control-Allow-Origin", origin)
        self.end_headers()
        self.wfile.write(payload)

    def _send_html(self, status: int, html_str: str):
        payload = html_str.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path in ("/", "/index.html"):
            self._send_html(200, HTML_TEMPLATE)
            return

        if path == "/api/catalog":
            cat_dict = self.catalog.to_dict() if isinstance(self.catalog, WeeklyCatalog) else {
                "week_label": "Settimana Corrente",
                "activities": [
                    a.to_dict() if isinstance(a, OutingOption) else a for a in self.catalog
                ],
            }
            self._send_json(200, cat_dict)
            return

        self.send_error(404, "Not Found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/format":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
            except (TypeError, ValueError):
                self.send_error(400, "Invalid Content-Length")
                return
            if content_length < 0 or content_length > 1_048_576:
                self.send_error(413, "Payload Too Large")
                return
            body_bytes = self.rfile.read(content_length)
            try:
                data = json.loads(body_bytes.decode("utf-8"))
            except Exception:
                data = {}

            selected_ids = set(data.get("selected_ids", []))
            tone = data.get("tone", "amichevole")

            # Collect matching options
            items: List[OutingOption] = (
                self.catalog.activities
                if isinstance(self.catalog, WeeklyCatalog)
                else [
                    it if isinstance(it, OutingOption) else OutingOption.from_dict(it)
                    for it in self.catalog
                ]
            )

            chosen = [it for it in items if it.id in selected_ids]
            message = format_whatsapp_message(chosen, tone=tone)
            self._send_json(200, {"message": message, "count": len(chosen)})
            return

        self.send_error(404, "Not Found")


def create_web_server(
    catalog: Optional[Union[WeeklyCatalog, List[OutingOption]]] = None,
    host: str = "127.0.0.1",
    port: int = 8765,
) -> HTTPServer:
    """Create and return an initialized HTTPServer instance.

    Args:
        catalog: Optional pre-loaded catalog.
        host: Hostname to bind (default '127.0.0.1').
        port: Port to bind (default 8765, 0 for ephemeral).

    Returns:
        HTTPServer instance ready to serve.
    """
    actual_catalog = catalog or get_weekly_catalog(live_verify=False)

    class CustomHandler(OutingsWebHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, catalog=actual_catalog, **kwargs)

    server = HTTPServer((host, port), CustomHandler)
    return server


def start_web_ui(
    catalog: Optional[Union[WeeklyCatalog, List[OutingOption]]] = None,
    host: str = "127.0.0.1",
    port: int = 8765,
    open_browser: bool = False,
) -> None:
    """Start the lightweight web UI and serve forever or until interrupted."""
    server = create_web_server(catalog=catalog, host=host, port=port)
    actual_port = server.server_port
    url = f"http://{host}:{actual_port}"
    print(f"\n🌐 Interfaccia Web avviata su {url}")
    print("Premi Ctrl+C nel terminale per arrestare il server.\n")

    if open_browser:
        try:
            import webbrowser
            webbrowser.open(url)
        except Exception:
            pass

    try:
        server.serve_forever()
    except (KeyboardInterrupt, SystemExit):
        print("\nArresto del server Web in corso...")
    finally:
        server.server_close()
        print("Server Web arrestato.")
