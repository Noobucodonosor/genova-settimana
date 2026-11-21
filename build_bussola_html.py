import json

with open("/Users/dany/genova/tempo_libero_payload.json", "r", encoding="utf-8") as f:
    payload_json = f.read()

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="it">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Bussola del Tempo Libero — Genova & i 67 Comuni della Provincia</title>
  <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
  <style>
    * { box-sizing: border-box; }
    body { margin: 0; font-size: 14px; }
    .custom-scroll::-webkit-scrollbar { width: 6px; height: 6px; }
    .custom-scroll::-webkit-scrollbar-track { background: transparent; }
    .custom-scroll::-webkit-scrollbar-thumb { background: var(--border); border-radius: 999px; }
    .pill-active {
      background: var(--primary) !important;
      color: var(--primary-foreground) !important;
      border-color: var(--primary) !important;
      font-weight: 600;
    }
    .tab-active {
      background: var(--card);
      color: var(--foreground);
      box-shadow: 0 1px 3px rgba(0,0,0,0.14);
      font-weight: 600;
    }
    canvas { touch-action: none; }
  </style>
</head>
<body class="bg-[var(--background)] text-[var(--foreground)] antialiased selection:bg-[var(--primary)] selection:text-[var(--primary-foreground)]">

  <!-- TOP STICKY HEADER & PERSONAL COMPASS -->
  <header class="sticky top-0 z-30 bg-[var(--background)]/95 backdrop-blur border-b border-[var(--border)]">
    <div class="max-w-[1440px] mx-auto px-4 py-3 space-y-3">
      <!-- Row 1: Brand + Temporal Mode Switcher + Quick Actions -->
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-[var(--primary)] text-[var(--primary-foreground)] flex items-center justify-center font-bold text-lg shadow-sm">
            🧭
          </div>
          <div>
            <div class="flex items-center gap-2 flex-wrap">
              <h1 class="text-base sm:text-lg font-bold tracking-tight">Bussola del Tempo Libero</h1>
              <span class="text-xs px-2 py-0.5 rounded-full bg-[var(--card)] border border-[var(--border)] text-[var(--muted-foreground)]">
                Genova &amp; 67 Comuni
              </span>
            </div>
            <p class="text-xs text-[var(--muted-foreground)]">
              Decidi dove andare in base a punto di partenza, treno o auto, meteo, orari reali e personaggi storici
            </p>
          </div>
        </div>

        <!-- 3 Main Temporal Views -->
        <nav class="flex items-center p-1 rounded-xl bg-[var(--content)] border border-[var(--border)]" aria-label="Orizzonte temporale">
          <button id="tab-day" onclick="switchView('day')" class="px-3.5 py-1.5 rounded-lg text-xs sm:text-sm transition tab-active">
            📍 Giorno &amp; Mappa
          </button>
          <button id="tab-week" onclick="switchView('week')" class="px-3.5 py-1.5 rounded-lg text-xs sm:text-sm text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition">
            🗓️ Piano Settimana
          </button>
          <button id="tab-month" onclick="switchView('month')" class="px-3.5 py-1.5 rounded-lg text-xs sm:text-sm text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition">
            📅 Calendario Mese
          </button>
        </nav>

        <!-- Surprise Me & My Trip Drawer Button -->
        <div class="flex items-center gap-2">
          <button onclick="surpriseMe()" class="px-3 py-2 rounded-xl bg-[var(--card)] hover:bg-[var(--content)] border border-[var(--border)] text-xs font-medium transition flex items-center gap-1.5" title="Consigliami una combinazione aperta perfetta per i filtri attuali">
            <span>🎲</span>
            <span class="hidden sm:inline">Ispirami Ora</span>
          </button>
          <button onclick="toggleDrawer(true)" class="px-3.5 py-2 rounded-xl bg-[var(--primary)] text-[var(--primary-foreground)] text-xs sm:text-sm font-semibold shadow-sm hover:opacity-95 transition flex items-center gap-2">
            <span>🎒 Il Mio Programma</span>
            <span id="trip-count-badge" class="px-2 py-0.5 rounded-full bg-[var(--background)] text-[var(--foreground)] text-xs font-bold">0</span>
          </button>
        </div>
      </div>

      <!-- Row 2: Human Decision Filters (Origin, Transport, Weather/Mood, Zone, Search) -->
      <div class="grid grid-cols-1 md:grid-cols-12 gap-2.5 items-center pt-1">
        <!-- Parto da -->
        <div class="md:col-span-3 flex items-center gap-2 bg-[var(--card)] border border-[var(--border)] rounded-xl px-3 py-1.5">
          <span class="text-xs text-[var(--muted-foreground)] whitespace-nowrap">🏠 Parto da:</span>
          <select id="hub-select" onchange="onHubChange(this.value)" class="w-full bg-transparent text-xs font-semibold focus:outline-none truncate">
          </select>
        </div>

        <!-- Mezzo di trasporto -->
        <div class="md:col-span-3 flex items-center gap-1 bg-[var(--card)] border border-[var(--border)] rounded-xl p-1 overflow-x-auto custom-scroll">
          <button data-transport="all" onclick="setTransport('all')" class="transport-btn pill-active px-2.5 py-1 rounded-lg text-xs whitespace-nowrap transition">Tutti</button>
          <button data-transport="treno" onclick="setTransport('treno')" class="transport-btn px-2.5 py-1 rounded-lg text-xs text-[var(--muted-foreground)] hover:text-[var(--foreground)] whitespace-nowrap transition" title="Raggiungibili in Treno, Metro, Funicolare o Battello">🚆 Senza Auto</button>
          <button data-transport="auto" onclick="setTransport('auto')" class="transport-btn px-2.5 py-1 rounded-lg text-xs text-[var(--muted-foreground)] hover:text-[var(--foreground)] whitespace-nowrap transition" title="Valli, borghi e castelli raggiungibili in auto o moto">🚗 Valli in Auto</button>
          <button data-transport="vicino" onclick="setTransport('vicino')" class="transport-btn px-2.5 py-1 rounded-lg text-xs text-[var(--muted-foreground)] hover:text-[var(--foreground)] whitespace-nowrap transition" title="A meno di 25 minuti dal punto di partenza">&lt; 25 min</button>
        </div>

        <!-- Zona della Provincia -->
        <div class="md:col-span-3 flex items-center gap-2 bg-[var(--card)] border border-[var(--border)] rounded-xl px-3 py-1.5">
          <span class="text-xs text-[var(--muted-foreground)] whitespace-nowrap">🗺️ Zona:</span>
          <select id="zone-select" onchange="setZone(this.value)" class="w-full bg-transparent text-xs font-semibold focus:outline-none truncate">
            <option value="all">Tutta la Provincia (67 Comuni)</option>
            <option value="centro">Genova Centro, Caruggi &amp; Forti</option>
            <option value="genova_mare">Genova Mare (Pegli, Boccadasse, Nervi)</option>
            <option value="golfo_paradiso">Golfo Paradiso (Recco, Camogli, Uscio)</option>
            <option value="tigullio_occ">Tigullio Occ. (Portofino, S. Margherita, Rapallo, Zoagli)</option>
            <option value="tigullio_or">Tigullio Or., Fontanabuona, Graveglia &amp; Aveto</option>
            <option value="ponente_stura">Ponente &amp; Valle Stura (Mele, Arenzano, Campo Ligure)</option>
            <option value="polcevera_scrivia">Val Polcevera, Scrivia, Casella &amp; Parco Antola</option>
          </select>
        </div>

        <!-- Ricerca libera -->
        <div class="md:col-span-3 flex items-center gap-2 bg-[var(--card)] border border-[var(--border)] rounded-xl px-3 py-1.5">
          <span class="text-xs text-[var(--muted-foreground)]">🔍</span>
          <input id="search-input" type="text" oninput="onSearchInput(this.value)" placeholder="Cerca luogo, comune, bottega, personaggio..." class="w-full bg-transparent text-xs focus:outline-none placeholder:text-[var(--muted-foreground)]" />
          <button id="clear-search-btn" onclick="onSearchInput(''); document.getElementById('search-input').value='';" class="hidden text-xs text-[var(--muted-foreground)] hover:text-[var(--foreground)]">✕</button>
        </div>
      </div>

      <!-- Row 3: Mood & Weather Chips -->
      <div class="flex items-center gap-1.5 overflow-x-auto custom-scroll pb-0.5">
        <span class="text-xs text-[var(--muted-foreground)] mr-1 whitespace-nowrap">Che voglia hai?</span>
        <button data-mood="all" onclick="setMood('all')" class="mood-btn pill-active px-3 py-1 rounded-full border border-[var(--border)] bg-[var(--card)] text-xs whitespace-nowrap transition">✨ Tutto il meglio</button>
        <button data-mood="pioggia" onclick="setMood('pioggia')" class="mood-btn px-3 py-1 rounded-full border border-[var(--border)] bg-[var(--card)] text-xs whitespace-nowrap transition">🌧️ Piove / Al Coperto</button>
        <button data-mood="sole" onclick="setMood('sole')" class="mood-btn px-3 py-1 rounded-full border border-[var(--border)] bg-[var(--card)] text-xs whitespace-nowrap transition">☀️ Aria Aperta, Mare &amp; Trek</button>
        <button data-mood="bottega" onclick="setMood('bottega')" class="mood-btn px-3 py-1 rounded-full border border-[var(--border)] bg-[var(--card)] text-xs whitespace-nowrap transition">🏺 Botteghe Iper-Specifiche &amp; Sapori</button>
        <button data-mood="cultura" onclick="setMood('cultura')" class="mood-btn px-3 py-1 rounded-full border border-[var(--border)] bg-[var(--card)] text-xs whitespace-nowrap transition">🏰 Palazzi, Castelli &amp; Musei</button>
        <button data-mood="sera" onclick="setMood('sera')" class="mood-btn px-3 py-1 rounded-full border border-[var(--border)] bg-[var(--card)] text-xs whitespace-nowrap transition">🎭 Sera, Teatri &amp; Musica</button>
        <button data-mood="gratis" onclick="setMood('gratis')" class="mood-btn px-3 py-1 rounded-full border border-[var(--border)] bg-[var(--card)] text-xs whitespace-nowrap transition">🆓 Gratis</button>
        <button id="comune-filter-pill" onclick="clearComuneFilter()" class="hidden px-3 py-1 rounded-full border border-[var(--primary)] bg-[var(--primary)] text-[var(--primary-foreground)] text-xs font-semibold whitespace-nowrap transition"></button>
      </div>
    </div>
  </header>

  <!-- MAIN WORKSPACE -->
  <main class="max-w-[1440px] mx-auto px-4 py-4 space-y-5">

    <!-- ==========================================
         VIEW 1: OGGI / GIORNO SCELTO + MAPPA VIVA
         ========================================== -->
    <section id="view-day" class="space-y-4">

      <!-- Date, Time-of-Day & Live Status Bar -->
      <div class="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-3.5 flex flex-wrap items-center justify-between gap-3 shadow-sm">
        <div class="flex flex-wrap items-center gap-2">
          <span class="text-xs font-semibold text-[var(--muted-foreground)]">📅 Quando esci:</span>
          <div id="quick-dates" class="flex flex-wrap items-center gap-1.5"></div>
          <input id="date-picker" type="date" onchange="setSelectedDate(this.value)" class="px-2.5 py-1 rounded-lg bg-[var(--content)] border border-[var(--border)] text-xs font-medium focus:outline-none" />
        </div>

        <div class="flex flex-wrap items-center gap-2">
          <span class="text-xs font-semibold text-[var(--muted-foreground)]">⏰ Fascia:</span>
          <div class="flex items-center p-0.5 rounded-xl bg-[var(--content)] border border-[var(--border)]">
            <button data-slot="all" onclick="setTimeSlot('all')" class="slot-btn pill-active px-2.5 py-1 rounded-lg text-xs transition">Tutto il dì</button>
            <button data-slot="mattina" onclick="setTimeSlot('mattina')" class="slot-btn px-2.5 py-1 rounded-lg text-xs text-[var(--muted-foreground)] transition">🌅 09–13</button>
            <button data-slot="pomeriggio" onclick="setTimeSlot('pomeriggio')" class="slot-btn px-2.5 py-1 rounded-lg text-xs text-[var(--muted-foreground)] transition">☀️ 14–18</button>
            <button data-slot="sera" onclick="setTimeSlot('sera')" class="slot-btn px-2.5 py-1 rounded-lg text-xs text-[var(--muted-foreground)] transition">🌙 19–23</button>
          </div>

          <label class="flex items-center gap-1.5 text-xs cursor-pointer select-none px-2.5 py-1 rounded-lg bg-[var(--content)] border border-[var(--border)]">
            <input id="only-open-toggle" type="checkbox" checked onchange="toggleOnlyOpen(this.checked)" class="accent-[var(--primary)]" />
            <span>Solo aperti</span>
          </label>
        </div>
      </div>

      <!-- Day Special Banner (e.g. Salva-Lunedì, #DomenicalMuseo, Weekend Castelli) -->
      <div id="day-advice-banner" class="rounded-2xl border border-[var(--border)] bg-[var(--card)] px-4 py-3 flex flex-wrap items-center justify-between gap-2"></div>

      <!-- Ready-to-Go Curated Day Plans ("Gite & Giornate Chiavi in Mano") -->
      <div class="space-y-2.5">
        <div class="flex items-center justify-between gap-2">
          <div>
            <h2 class="text-sm sm:text-base font-bold flex items-center gap-2">
              <span>✨ Gite &amp; Giornate Pronte</span>
              <span id="itineraries-subtitle" class="text-xs font-normal text-[var(--muted-foreground)]"></span>
            </h2>
          </div>
          <button onclick="toggleItinerariesCollapse()" id="toggle-itin-btn" class="text-xs text-[var(--muted-foreground)] hover:text-[var(--foreground)] underline">
            Nascondi proposte pronte
          </button>
        </div>
        <div id="itineraries-strip" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3"></div>
      </div>

      <!-- Split View: Interactive Geographical Map (Left 7 cols) + Smart Ranked Places (Right 5 cols) -->
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-4 items-start">

        <!-- LEFT: Interactive Province & City GPS Map + Selected Place Inspector -->
        <div class="lg:col-span-7 space-y-3 lg:sticky lg:top-[168px]">
          <div class="bg-[var(--card)] border border-[var(--border)] rounded-2xl overflow-hidden shadow-sm">
            <!-- Map Toolbar -->
            <div class="px-3.5 py-2.5 border-b border-[var(--border)] flex flex-wrap items-center justify-between gap-2">
              <div class="flex flex-wrap items-center gap-1.5">
                <button onclick="setMapCamera('provincia')" class="px-2.5 py-1 rounded-lg bg-[var(--content)] hover:opacity-90 border border-[var(--border)] text-xs font-medium">🗺️ 67 Comuni</button>
                <button onclick="setMapCamera('genova')" class="px-2.5 py-1 rounded-lg bg-[var(--content)] hover:opacity-90 border border-[var(--border)] text-xs font-medium">🏛️ Genova &amp; Caruggi</button>
                <button onclick="setMapCamera('tigullio')" class="px-2.5 py-1 rounded-lg bg-[var(--content)] hover:opacity-90 border border-[var(--border)] text-xs font-medium">🌊 Golfo Paradiso &amp; Tigullio</button>
                <button onclick="setMapCamera('valli')" class="px-2.5 py-1 rounded-lg bg-[var(--content)] hover:opacity-90 border border-[var(--border)] text-xs font-medium">⛰️ Valli &amp; Castelli</button>
              </div>
              <div class="flex items-center gap-1">
                <button onclick="zoomMap(1.35)" class="w-7 h-7 rounded-lg bg-[var(--content)] border border-[var(--border)] text-sm font-bold flex items-center justify-center" title="Ingrandisci">+</button>
                <button onclick="zoomMap(0.74)" class="w-7 h-7 rounded-lg bg-[var(--content)] border border-[var(--border)] text-sm font-bold flex items-center justify-center" title="Riduci">−</button>
              </div>
            </div>

            <!-- Canvas Container -->
            <div class="relative w-full h-[390px] sm:h-[450px] select-none">
              <canvas id="geo-map" class="w-full h-full block cursor-grab active:cursor-grabbing"></canvas>
              <div id="map-tooltip" class="hidden pointer-events-none absolute z-20 px-2.5 py-1.5 rounded-xl bg-[var(--card)]/95 border border-[var(--border)] shadow-md text-xs max-w-[250px]"></div>
            </div>

            <!-- Map Legend -->
            <div class="px-3.5 py-2 border-t border-[var(--border)] bg-[var(--content)]/50 flex flex-wrap items-center justify-between gap-2 text-xs text-[var(--muted-foreground)]">
              <div class="flex flex-wrap items-center gap-3">
                <span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-full inline-block" style="background:#10b981"></span> Aperto</span>
                <span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-full inline-block" style="background:#f59e0b"></span> Altro orario</span>
                <span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-full inline-block" style="background:#94a3b8"></span> Chiuso</span>
                <span class="flex items-center gap-1.5"><span class="w-3 h-3 rounded-full inline-block border-2 border-amber-400" style="background:var(--primary)"></span> Tappa nel programma</span>
                <span class="flex items-center gap-1.5">--- Ferrovia</span>
              </div>
              <span>Trascina o usa la rotellina • Clicca un pin o un Comune</span>
            </div>

            <!-- Live Active Itinerary Mini-Bar right inside Map Card -->
            <div id="map-active-trip-bar" class="hidden px-3.5 py-2.5 border-t border-[var(--border)] bg-[var(--card)] flex flex-wrap items-center justify-between gap-2"></div>
          </div>

          <!-- Selected Place Detail & Nearby Pairing Card ("Già che sei lì...") -->
          <div id="place-inspector" class="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-4 shadow-sm">
          </div>
        </div>

        <!-- RIGHT: Filtered & Ranked Destination Cards -->
        <div class="lg:col-span-5 space-y-3">
          <div class="flex flex-wrap items-center justify-between gap-2 bg-[var(--card)] border border-[var(--border)] rounded-xl px-3.5 py-2.5">
            <div>
              <span id="results-count" class="text-sm font-bold">0 mete</span>
              <span id="results-context" class="text-xs text-[var(--muted-foreground)] ml-1"></span>
            </div>
            <div class="flex items-center gap-1.5">
              <span class="text-xs text-[var(--muted-foreground)]">Ordina:</span>
              <select id="sort-select" onchange="setSort(this.value)" class="bg-[var(--content)] border border-[var(--border)] rounded-lg px-2 py-1 text-xs font-medium focus:outline-none">
                <option value="smart">🌟 Imperdibili &amp; Aperti</option>
                <option value="travel">⚡ Più veloci da raggiungere</option>
                <option value="botteghe">🏺 Prima Botteghe &amp; Sapori</option>
                <option value="natura">🌿 Prima Natura &amp; Panorami</option>
              </select>
            </div>
          </div>

          <div id="places-list" class="space-y-2.5"></div>

          <button id="load-more-btn" onclick="loadMorePlaces()" class="hidden w-full py-2.5 rounded-xl bg-[var(--card)] hover:bg-[var(--content)] border border-[var(--border)] text-xs font-semibold transition">
            Mostra altre mete
          </button>
        </div>

      </div>
    </section>

    <!-- ==========================================
         VIEW 2: PIANO SETTIMANA (7 GIORNI LUN–DOM)
         ========================================== -->
    <section id="view-week" class="hidden space-y-4">
      <div class="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 class="text-base font-bold">🗓️ Strategia dei 7 Giorni — Genova &amp; Provincia</h2>
          <p class="text-xs text-[var(--muted-foreground)]">
            Confronta a colpo d'occhio aperture, consigli furbi (es. Salva-Lunedì, Lanterna e Filigrana dal Venerdì, Castelli domenicali) e assegna le tue uscite ai giorni liberi
          </p>
        </div>
        <div class="flex items-center gap-2">
          <button onclick="shiftWeek(-7)" class="px-3 py-1.5 rounded-xl bg-[var(--content)] border border-[var(--border)] text-xs font-medium hover:opacity-90">← Sett. Prec.</button>
          <span id="week-range-label" class="text-xs sm:text-sm font-bold px-2"></span>
          <button onclick="shiftWeek(7)" class="px-3 py-1.5 rounded-xl bg-[var(--content)] border border-[var(--border)] text-xs font-medium hover:opacity-90">Sett. Succ. →</button>
        </div>
      </div>

      <div id="week-grid" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-7 gap-3"></div>
    </section>

    <!-- ==========================================
         VIEW 3: CALENDARIO MESE & STAGIONI
         ========================================== -->
    <section id="view-month" class="hidden space-y-4">
      <div class="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-4 space-y-3">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 class="text-base font-bold">📅 Calendario Mensile, #DomenicalMuseo &amp; Appuntamenti</h2>
            <p class="text-xs text-[var(--muted-foreground)]">
              Clicca qualsiasi giorno del calendario per vedere eventi, sagre storiche, fioriture e aprire subito la mappa tarata su quella data
            </p>
          </div>
          <div class="flex items-center gap-2">
            <button onclick="shiftMonth(-1)" class="px-3 py-1.5 rounded-xl bg-[var(--content)] border border-[var(--border)] text-xs font-medium">← Mese Prec.</button>
            <span id="month-title-label" class="text-sm font-bold min-w-[140px] text-center"></span>
            <button onclick="shiftMonth(1)" class="px-3 py-1.5 rounded-xl bg-[var(--content)] border border-[var(--border)] text-xs font-medium">Mese Succ. →</button>
          </div>
        </div>
        <div id="month-pills" class="flex items-center gap-1.5 overflow-x-auto custom-scroll pb-1"></div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-12 gap-4 items-start">
        <!-- Real 7-col Calendar Grid -->
        <div class="lg:col-span-8 bg-[var(--card)] border border-[var(--border)] rounded-2xl overflow-hidden shadow-sm">
          <div class="grid grid-cols-7 border-b border-[var(--border)] bg-[var(--content)] text-center py-2 text-xs font-bold text-[var(--muted-foreground)]">
            <div>Lun</div><div>Mar</div><div>Mer</div><div>Gio</div><div>Ven</div><div>Sab</div><div>Dom</div>
          </div>
          <div id="calendar-cells" class="grid grid-cols-7"></div>
        </div>

        <!-- Selected Day & Month Highlights Sidebar -->
        <div id="month-day-detail" class="lg:col-span-4 bg-[var(--card)] border border-[var(--border)] rounded-2xl p-4 space-y-4 shadow-sm">
        </div>
      </div>
    </section>

    <footer class="pt-2 pb-6 text-center text-xs text-[var(--muted-foreground)]">
      Motore decisionale costruito su 67/67 Comuni della Città Metropolitana di Genova • 326 esperienze selezionate e geolocalizzate (filtrate da 4.251 luoghi aperti al pubblico estratti da OpenStreetMap, Wikidata e siti ufficiali) • Collegate a 5.540 toponimi di personaggi storici.
    </footer>

  </main>

  <!-- SLIDE-OVER DRAWER: IL MIO PROGRAMMA & LA STORIA DEI PERSONAGGI -->
  <div id="trip-drawer-backdrop" onclick="toggleDrawer(false)" class="hidden fixed inset-0 z-40 bg-black/40 backdrop-blur-xs"></div>
  <aside id="trip-drawer" class="hidden fixed top-0 right-0 z-50 h-full w-full max-w-[500px] bg-[var(--background)] border-l border-[var(--border)] shadow-2xl flex flex-col">
    <div class="p-4 border-b border-[var(--border)] bg-[var(--card)] flex items-center justify-between gap-2">
      <div>
        <h2 class="text-base font-bold flex items-center gap-2">
          <span>🎒 Il Mio Programma</span>
          <span id="drawer-date-badge" class="text-xs font-normal px-2 py-0.5 rounded-full bg-[var(--content)] border border-[var(--border)] text-[var(--muted-foreground)]"></span>
        </h2>
        <p class="text-xs text-[var(--muted-foreground)]">Tabella di marcia con verifica orari, tempi di spostamento e racconto</p>
      </div>
      <button onclick="toggleDrawer(false)" class="w-8 h-8 rounded-xl bg-[var(--content)] border border-[var(--border)] text-sm font-bold flex items-center justify-center">✕</button>
    </div>

    <div class="flex-1 overflow-y-auto custom-scroll p-4 space-y-4">
      <!-- Start Time & Route Optimizer Controls -->
      <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-3 flex flex-wrap items-center justify-between gap-2">
        <div class="flex items-center gap-2">
          <span class="text-xs text-[var(--muted-foreground)]">🕘 Orario partenza:</span>
          <select id="trip-start-hour" onchange="setTripStartHour(parseFloat(this.value))" class="bg-[var(--content)] border border-[var(--border)] rounded-lg px-2 py-1 text-xs font-semibold">
            <option value="8.5">08:30</option>
            <option value="9.5" selected>09:30</option>
            <option value="10.5">10:30</option>
            <option value="12.0">12:00 (Pranzo &amp; Pom.)</option>
            <option value="14.5">14:30 (Pomeriggio)</option>
            <option value="18.5">18:30 (Sera)</option>
          </select>
        </div>
        <div class="flex items-center gap-1.5">
          <button onclick="optimizeTripOrder()" class="px-2.5 py-1 rounded-lg bg-[var(--content)] hover:opacity-90 border border-[var(--border)] text-xs font-medium" title="Riordina le tappe per minimizzare gli spostamenti dal punto di partenza">
            ✨ Ottimizza giro
          </button>
          <button onclick="clearTripForActiveDate()" class="px-2.5 py-1 rounded-lg bg-[var(--content)] hover:opacity-90 border border-[var(--border)] text-xs text-[var(--muted-foreground)]">
            Svuota
          </button>
        </div>
      </div>

      <!-- Timeline Container -->
      <div id="drawer-timeline" class="space-y-2.5"></div>

      <!-- External Navigation & Copy Actions -->
      <div id="drawer-actions" class="hidden grid grid-cols-1 sm:grid-cols-2 gap-2">
        <a id="gmaps-route-link" href="#" target="_blank" rel="noopener" class="px-3.5 py-2.5 rounded-xl bg-[var(--primary)] text-[var(--primary-foreground)] text-xs font-semibold text-center shadow-sm hover:opacity-95 transition">
          🗺️ Apri Giro su Google Maps
        </a>
        <button onclick="copyTripText()" id="copy-trip-btn" class="px-3.5 py-2.5 rounded-xl bg-[var(--card)] border border-[var(--border)] text-xs font-semibold hover:bg-[var(--content)] transition">
          📋 Copia Tabella di Marcia
        </button>
      </div>

      <!-- Dynamic Story Woven from Historical Characters ("Il Filo Rosso dei Personaggi") -->
      <div id="drawer-story" class="hidden bg-[var(--card)] border border-[var(--border)] rounded-2xl p-4 space-y-2">
      </div>
    </div>
  </aside>

  <script>
    const DATA = __PAYLOAD_JSON__;

    //Accurate Ligurian Coastline GPS Polyline (West -> Genoa -> Portofino -> Sestri -> Moneglia)
    const COASTLINE = [
      [44.382, 8.560], [44.389, 8.643], [44.403, 8.685], [44.427, 8.751],
      [44.426, 8.818], [44.413, 8.855], [44.405, 8.904], [44.411, 8.926],
      [44.397, 8.948], [44.389, 8.975], [44.384, 9.015], [44.381, 9.045],
      [44.375, 9.075], [44.370, 9.108], [44.361, 9.143], [44.350, 9.153],
      [44.325, 9.147], [44.316, 9.175], [44.299, 9.218], [44.313, 9.212],
      [44.333, 9.215], [44.349, 9.233], [44.337, 9.267], [44.316, 9.321],
      [44.304, 9.352], [44.270, 9.394], [44.255, 9.406], [44.260, 9.424],
      [44.239, 9.489], [44.222, 9.540]
    ];

    // Real Railway Corridors for Map Context
    const RAIL_LINES = [
      // Coastal Line
      [[44.389,8.643],[44.403,8.685],[44.427,8.751],[44.427,8.818],[44.415,8.890],[44.417,8.922],[44.407,8.943],[44.383,9.044],[44.371,9.108],[44.362,9.143],[44.350,9.154],[44.333,9.214],[44.350,9.231],[44.337,9.267],[44.317,9.321],[44.307,9.346],[44.273,9.396],[44.241,9.490]],
      // Valle Stura (Genova - Campo Ligure - Rossiglione)
      [[44.427,8.751],[44.455,8.743],[44.505,8.712],[44.538,8.698],[44.561,8.671]],
      // Giovi / Valle Scrivia (Genova - Busalla - Ronco - Isola)
      [[44.417,8.922],[44.462,8.899],[44.525,8.915],[44.571,8.946],[44.608,8.953],[44.645,8.957]],
      // Trenino Genova - Casella
      [[44.416,8.942],[44.451,8.948],[44.478,8.945],[44.535,8.999]]
    ];

    const TIPO_META = {
      bottega:    { icon: "🏺", label: "Bottega & Sapori" },
      museo:      { icon: "🏛️", label: "Museo & Galleria" },
      dimora:     { icon: "🏰", label: "Villa, Palazzo o Castello" },
      natura:     { icon: "🌿", label: "Natura, Parco & Trek" },
      abbazia:    { icon: "⛪", label: "Abbazia, Chiostro & Santuario" },
      teatro:     { icon: "🎭", label: "Teatro & Spettacolo" },
      biblioteca: { icon: "📚", label: "Biblioteca Storica" }
    };

    const ZONE_LABELS = {
      centro: "Genova Centro & Caruggi",
      genova_mare: "Genova Mare (Pegli–Nervi)",
      golfo_paradiso: "Golfo Paradiso",
      tigullio_occ: "Portofino & Tigullio Occ.",
      tigullio_or: "Tigullio Or., Fontanabuona & Aveto",
      ponente_stura: "Ponente & Valle Stura",
      polcevera_scrivia: "Valli Polcevera, Scrivia & Antola"
    };

    const DAYS_IT = ["Domenica", "Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato"];
    const DAYS_SHORT = ["Dom", "Lun", "Mar", "Mer", "Gio", "Ven", "Sab"];
    const MONTHS_IT = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"];

    const PLACES_BY_ID = {};
    DATA.places.forEach(p => { PLACES_BY_ID[p.id] = p; });

    // Initialize default date to 2026-11-01 (or today if within 2026-2027)
    function getInitialDateStr() {
      const now = new Date();
      const y = now.getFullYear();
      const m = String(now.getMonth() + 1).padStart(2, "0");
      const d = String(now.getDate()).padStart(2, "0");
      return `${y}-${m}-${d}`;
    }

    const STATE = {
      view: "day",
      selectedDate: getInitialDateStr(),
      timeSlot: "all",
      onlyOpen: true,
      hubId: "ge_centro",
      customOrigin: null, // { nome, lat, lon, rail }
      transport: "all",
      mood: "all",
      zone: "all",
      comuneFilter: null,
      search: "",
      sort: "smart",
      visibleLimit: 20,
      selectedPlaceId: 1,
      itinerariesCollapsed: false,
      tripStartHour: 9.5,
      // Trips stored per YYYY-MM-DD so you can plan multiple days across the week/month!
      tripsByDate: {},
      weekMondayStr: null,
      calYear: 2026,
      calMonth: 11, // 1..12
      // Map camera (lat/lon bounding center & span)
      cam: { lat: 44.415, lon: 9.04, spanLon: 0.98 }
    };

    // Setup weekMonday & calendar month from initial date
    (function initDates() {
      const dt = parseDateStr(STATE.selectedDate);
      STATE.calYear = dt.getFullYear();
      STATE.calMonth = dt.getMonth() + 1;
      STATE.weekMondayStr = getMondayStr(dt);
      // Pre-load a starter 3-stop sample on initial date only if empty? Better start clean or with 0 so user sees badge update when clicking!
    })();

    function parseDateStr(s) {
      const [y, m, d] = s.split("-").map(Number);
      return new Date(y, m - 1, d, 12, 0, 0);
    }
    function fmtDateStr(dt) {
      return `${dt.getFullYear()}-${String(dt.getMonth() + 1).padStart(2, "0")}-${String(dt.getDate()).padStart(2, "0")}`;
    }
    function getMondayStr(dt) {
      const copy = new Date(dt.getFullYear(), dt.getMonth(), dt.getDate(), 12, 0, 0);
      const day = copy.getDay();
      const diff = (day === 0 ? -6 : 1 - day);
      copy.setDate(copy.getDate() + diff);
      return fmtDateStr(copy);
    }
    function fmtHumanDate(s) {
      const dt = parseDateStr(s);
      return `${DAYS_SHORT[dt.getDay()]} ${dt.getDate()} ${MONTHS_IT[dt.getMonth()].slice(0, 3)}`;
    }
    function fmtHour(h) {
      const hh = Math.floor(h);
      const mm = Math.round((h - hh) * 60);
      return `${String(hh).padStart(2, "0")}:${String(mm).padStart(2, "0")}`;
    }

    // Active Origin Hub
    function getOrigin() {
      if (STATE.customOrigin) return STATE.customOrigin;
      return DATA.hubs.find(h => h.id === STATE.hubId) || DATA.hubs[0];
    }

    // Haversine & Realistic Ligurian Travel Time Calculator
    function haversineKm(lat1, lon1, lat2, lon2) {
      const R = 6371;
      const dLat = (lat2 - lat1) * Math.PI / 180;
      const dLon = (lon2 - lon1) * Math.PI / 180;
      const a = Math.sin(dLat/2)**2 + Math.cos(lat1*Math.PI/180)*Math.cos(lat2*Math.PI/180)*Math.sin(dLon/2)**2;
      return 2 * R * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    }

    function calcTravel(fromObj, place) {
      const airKm = haversineKm(fromObj.lat, fromObj.lon, place.lat, place.lon);
      if (airKm < 1.8) {
        const walkMin = Math.max(4, Math.round(airKm * 15));
        return { km: airKm, min: walkMin, mode: "piedi", badge: `🚶 ${walkMin} min (${airKm.toFixed(1)} km)` };
      }
      // Mountain winding factor vs coastal highway/rail
      const isMountain = !place.treno && (place.zona === "polcevera_scrivia" || place.zona === "tigullio_or" || place.zona === "ponente_stura");
      const roadFactor = isMountain ? 1.58 : 1.30;
      const roadKm = airKm * roadFactor;
      const carSpeed = isMountain ? 38 : 48;
      const carMin = Math.max(8, Math.round(6 + (roadKm / carSpeed) * 60));

      if (place.treno && fromObj.rail) {
        const railMin = Math.max(10, Math.round(9 + (airKm * 1.22 / 44) * 60));
        if (STATE.transport === "auto") {
          return { km: roadKm, min: carMin, mode: "auto", badge: `🚗 ${carMin} min (${Math.round(roadKm)} km)` };
        }
        return { km: roadKm, min: railMin, carMin, mode: "treno", badge: `🚆 ${railMin} min • 🚗 ${carMin}m` };
      }
      return { km: roadKm, min: carMin, carMin, mode: "auto", badge: `🚗 ${carMin} min (${Math.round(roadKm)} km)` };
    }

    // Exact Schedule & Special Calendar Rule Evaluator
    function evalPlaceOnDate(place, dateStr, slotName) {
      const dt = parseDateStr(dateStr);
      const dow = dt.getDay(); // 0=Sun..6=Sat
      const dom = dt.getDate();
      const month = dt.getMonth() + 1;
      const isFirstSun = (dow === 0 && dom <= 7);
      const isThirdSun = (dow === 0 && dom >= 15 && dom <= 21);

      if (place.months && !place.months.includes(month)) {
        return { status: "closed", label: "Chiuso per stagione (riapre in primavera)", isFreeToday: place.free };
      }

      // Special Abbazia della Cervara rule (1st & 3rd Sun Mar-Oct)
      if (place.nome.includes("Cervara")) {
        if (isFirstSun || isThirdSun) {
          return { status: "open", label: "Apertura speciale 1ª/3ª Dom (su prenotazione)", isFreeToday: false };
        }
        return { status: "closed", label: "Aperta solo 1ª e 3ª Domenica (Mar–Ott)", isFreeToday: false };
      }

      let openToday = place.days.includes(dow);
      let freeToday = Boolean(place.free);

      // #DomenicalMuseo rule: State museums open & FREE on 1st Sunday!
      if (isFirstSun && place.free_1st_sun) {
        openToday = true;
        freeToday = true;
      }
      // December pre-Christmas Sunday openings for historic botteghe
      if (month === 12 && dow === 0 && place.tipo === "bottega" && place.tier === 1) {
        openToday = true;
      }

      if (!openToday) {
        return { status: "closed", label: `Chiuso di ${DAYS_IT[dow]}`, isFreeToday: freeToday };
      }

      // Check time slot overlap
      const slotWindows = {
        all: [0, 24],
        mattina: [8.5, 13.0],
        pomeriggio: [14.0, 18.5],
        sera: [19.0, 23.5]
      };
      const [wStart, wEnd] = slotWindows[slotName || "all"] || [0, 24];
      const matchesSlot = place.slots.some(([s1, s2]) => Math.max(s1, wStart) < Math.min(s2, wEnd));

      const slotText = place.slots.map(([s1, s2]) => `${fmtHour(s1)}–${fmtHour(s2)}`).join(", ");
      const freeSuffix = (isFirstSun && place.free_1st_sun && !place.free) ? " • 🆓 #DomenicalMuseo" : "";

      if (matchesSlot) {
        return { status: "open", label: `Aperto (${slotText})${freeSuffix}`, isFreeToday: freeToday };
      } else {
        return { status: "later", label: `Aperto oggi in fascia ${slotText}${freeSuffix}`, isFreeToday: freeToday };
      }
    }

    // Filter places according to active user controls
    function getFilteredPlaces(dateStr, slotName, ignoreOnlyOpen = false) {
      const origin = getOrigin();
      const q = STATE.search.trim().toLowerCase();

      return DATA.places.map(p => {
        const ev = evalPlaceOnDate(p, dateStr, slotName);
        const tr = calcTravel(origin, p);
        return { place: p, ev, tr };
      }).filter(({ place, ev, tr }) => {
        if (!ignoreOnlyOpen && STATE.onlyOpen && ev.status === "closed") return false;
        if (STATE.zone !== "all" && place.zona !== STATE.zone) return false;
        if (STATE.comuneFilter && place.comune !== STATE.comuneFilter) return false;

        if (STATE.transport === "treno" && !place.treno && tr.mode !== "piedi") return false;
        if (STATE.transport === "auto" && place.treno && place.zona === "centro") return false;
        if (STATE.transport === "vicino" && tr.min > 25) return false;

        if (STATE.mood === "pioggia" && place.indoor !== "in") return false;
        if (STATE.mood === "sole" && place.indoor === "in") return false;
        if (STATE.mood === "bottega" && place.tipo !== "bottega") return false;
        if (STATE.mood === "cultura" && !["museo", "dimora", "abbazia", "biblioteca"].includes(place.tipo)) return false;
        if (STATE.mood === "sera") {
          const openEve = place.slots.some(([s1, s2]) => s2 >= 19.5) || place.tipo === "teatro";
          if (!openEve) return false;
        }
        if (STATE.mood === "gratis" && !ev.isFreeToday) return false;

        if (q) {
          const hay = `${place.nome} ${place.comune} ${place.pitch} ${place.personaggio} ${TIPO_META[place.tipo].label}`.toLowerCase();
          if (!hay.includes(q)) return false;
        }
        return true;
      }).sort((a, b) => {
        // Always prioritize open over later over closed
        const stRank = { open: 0, later: 1, closed: 2 };
        if (stRank[a.ev.status] !== stRank[b.ev.status]) return stRank[a.ev.status] - stRank[b.ev.status];

        if (STATE.sort === "travel") return a.tr.min - b.tr.min;
        if (STATE.sort === "botteghe") {
          const ab = a.place.tipo === "bottega" ? 0 : 1;
          const bb = b.place.tipo === "bottega" ? 0 : 1;
          if (ab !== bb) return ab - bb;
        }
        if (STATE.sort === "natura") {
          const an = a.place.tipo === "natura" ? 0 : 1;
          const bn = b.place.tipo === "natura" ? 0 : 1;
          if (an !== bn) return an - bn;
        }
        if (a.place.tier !== b.place.tier) return a.place.tier - b.place.tier;
        return a.tr.min - b.tr.min;
      });
    }

    // Active Trip Helpers
    function getActiveTripIds() {
      if (!STATE.tripsByDate[STATE.selectedDate]) STATE.tripsByDate[STATE.selectedDate] = [];
      return STATE.tripsByDate[STATE.selectedDate];
    }

    function toggleStopInTrip(placeId, dateStr = STATE.selectedDate) {
      if (!STATE.tripsByDate[dateStr]) STATE.tripsByDate[dateStr] = [];
      const arr = STATE.tripsByDate[dateStr];
      const idx = arr.indexOf(placeId);
      if (idx >= 0) arr.splice(idx, 1);
      else arr.push(placeId);
      refreshAll();
    }

    function loadItineraryIntoDate(itinId, dateStr = STATE.selectedDate) {
      const it = DATA.itineraries.find(x => x.id === itinId);
      if (!it) return;
      STATE.tripsByDate[dateStr] = [...it.stops];
      if (it.id === "it_sera_teatro_genova") STATE.tripStartHour = 18.5;
      else if (STATE.tripStartHour > 15) STATE.tripStartHour = 9.5;
      document.getElementById("trip-start-hour").value = String(STATE.tripStartHour);
      STATE.selectedPlaceId = it.stops[0];
      focusCameraOnStops(it.stops);
      refreshAll();
      toggleDrawer(true);
    }

    function focusCameraOnStops(stopIds) {
      const pts = stopIds.map(id => PLACES_BY_ID[id]).filter(Boolean);
      if (!pts.length) return;
      const lats = pts.map(p => p.lat);
      const lons = pts.map(p => p.lon);
      const minLat = Math.min(...lats), maxLat = Math.max(...lats);
      const minLon = Math.min(...lons), maxLon = Math.max(...lons);
      STATE.cam.lat = (minLat + maxLat) / 2;
      STATE.cam.lon = (minLon + maxLon) / 2;
      STATE.cam.spanLon = Math.max(0.05, Math.min(1.0, Math.max(maxLon - minLon, (maxLat - minLat) * 1.7) * 2.1));
    }

    // ==========================================
    // UI RENDERERS
    // ==========================================
    function populateHubs() {
      const sel = document.getElementById("hub-select");
      sel.innerHTML = DATA.hubs.map(h => `<option value="${h.id}">${h.nome}</option>`).join("");
      sel.value = STATE.hubId;
    }

    function renderQuickDates() {
      const container = document.getElementById("quick-dates");
      const base = new Date();
      // Build 5 handy quick pills: Today, Tomorrow, Friday, Saturday, Sunday (or 1st Sun)
      const dates = [];
      const seen = new Set();
      for (let offset = 0; offset < 8; offset++) {
        const d = new Date(base.getFullYear(), base.getMonth(), base.getDate() + offset, 12, 0, 0);
        const s = fmtDateStr(d);
        const dow = d.getDay();
        if (offset <= 1 || dow === 5 || dow === 6 || dow === 0) {
          if (!seen.has(s) && dates.length < 5) {
            seen.add(s);
            let prefix = offset === 0 ? "Oggi • " : (offset === 1 ? "Domani • " : "");
            dates.push({ str: s, label: `${prefix}${DAYS_SHORT[dow]} ${d.getDate()} ${MONTHS_IT[d.getMonth()].slice(0,3)}` });
          }
        }
      }
      if (!seen.has(STATE.selectedDate)) {
        dates.unshift({ str: STATE.selectedDate, label: fmtHumanDate(STATE.selectedDate) });
      }
      container.innerHTML = dates.map(d => `
        <button onclick="setSelectedDate('${d.str}')" class="px-2.5 py-1 rounded-lg border border-[var(--border)] bg-[var(--content)] text-xs transition ${d.str === STATE.selectedDate ? 'pill-active' : 'text-[var(--muted-foreground)] hover:text-[var(--foreground)]'}">
          ${d.label}
        </button>
      `).join("");
      document.getElementById("date-picker").value = STATE.selectedDate;
    }

    function renderDayAdviceBanner() {
      const dt = parseDateStr(STATE.selectedDate);
      const dow = dt.getDay();
      const dom = dt.getDate();
      const month = dt.getMonth() + 1;
      const isFirstSun = (dow === 0 && dom <= 7);

      let icon = "🧭", title = "", desc = "";
      if (isFirstSun) {
        icon = "🆓";
        title = `È la 1ª Domenica del Mese (#DomenicalMuseo)!`;
        desc = `Ingresso gratuito a Palazzo Reale, Galleria Nazionale di Palazzo Spinola, Museo Archeologico di Chiavari e MuSel di Sestri Levante. Aperti anche la Fabbrica di Cioccolato Viganotti e Marescotti di Cavo!`;
      } else if (dow === 1) {
        icon = "🛟";
        title = `Strategia "Salva-Lunedì" attivata`;
        desc = `Il lunedì molti musei civici riposano, ma sono APERTI: Galata Museo del Mare + Sottomarino, Acquario, Museo Diocesano & Chiostro (coi Jeans del '500!), Villa Durazzo a S. Margherita, San Fruttuoso, Sa' Pesta a pranzo, Busellato e Romanengo pomeriggio.`;
      } else if (dow === 5) {
        icon = "🗼";
        title = `Venerdì: aprono le perle del fine settimana e i cartelloni serali`;
        desc = `Da oggi sono visitabili la Lanterna di Genova, il Museo della Carta a Mele e il Museo della Filigrana a Campo Ligure, oltre a mostre serali a Palazzo Ducale e spettacoli a teatro.`;
      } else if (dow === 6) {
        icon = "🏺";
        title = `Sabato: il giorno d'oro per unire Botteghe Artigiane e Gite in Provincia`;
        desc = `Tutte le botteghe storiche (chiuse la domenica) sono aperte, insieme alla Fonderia delle Campane di Avegno, ai Telai del Damasco di Lorsica, al Castello di Campo Ligure e alla Miniera di Gambatesa.`;
      } else if (dow === 0) {
        icon = "🏰";
        title = `Domenica tra Castelli, Riviere, Parchi Romantici & Cioccolato`;
        desc = month >= 4 && month <= 10
          ? `Domenica ideale per il Castello della Pietra a Vobbia, il Parco di Pegli, i Parchi di Nervi, il Trenino di Casella o il Golfo Paradiso in battello.`
          : `Ideale per ville e passeggiate sul mare (Nervi, Pegli, Camogli, S. Margherita, Sestri), musei di Strada Nuova e cioccolata storica da Viganotti o Cavo.`;
      } else {
        icon = "✨";
        title = `${DAYS_IT[dow]} senza folla: Caruggi, Palazzi dei Rolli, Orologi da Torre & Riviere`;
        desc = `Zero code nei Musei di Strada Nuova e Palazzo Reale, artigiani al lavoro nei laboratori dei caruggi, Orologi Trebino a Uscio, Marionette a Campomorone e treni costieri tranquillissimi.`;
      }

      document.getElementById("day-advice-banner").innerHTML = `
        <div class="flex items-start sm:items-center gap-3">
          <span class="text-xl">${icon}</span>
          <div>
            <div class="text-xs sm:text-sm font-bold">${title}</div>
            <p class="text-xs text-[var(--muted-foreground)] mt-0.5">${desc}</p>
          </div>
        </div>
      `;
    }

    function renderItinerariesStrip() {
      const strip = document.getElementById("itineraries-strip");
      const sub = document.getElementById("itineraries-subtitle");
      if (STATE.itinerariesCollapsed) {
        strip.classList.add("hidden");
        return;
      }
      strip.classList.remove("hidden");

      const dt = parseDateStr(STATE.selectedDate);
      const dow = dt.getDay();
      const dom = dt.getDate();
      const month = dt.getMonth() + 1;
      const isFirstSun = (dow === 0 && dom <= 7);
      const origin = getOrigin();

      const scored = DATA.itineraries.map(it => {
        const stops = it.stops.map(id => PLACES_BY_ID[id]).filter(Boolean);
        const openCount = stops.filter(p => evalPlaceOnDate(p, STATE.selectedDate, STATE.timeSlot).status !== "closed").length;
        const firstTravel = stops[0] ? calcTravel(origin, stops[0]) : { min: 0, badge: "" };
        let fit = openCount / Math.max(1, stops.length);
        if (it.id === "it_domenica_museo_rolli" && !isFirstSun) fit -= 0.5;
        if (it.id === "it_salva_lunedi" && dow === 1) fit += 0.5;
        if (STATE.zone !== "all" && it.zona === STATE.zone) fit += 0.4;
        if (STATE.transport === "treno" && (it.mezzo === "treno" || it.mezzo === "piedi")) fit += 0.25;
        if (STATE.transport === "auto" && it.mezzo === "auto") fit += 0.35;
        if (STATE.mood === "pioggia" && it.meteo === "pioggia") fit += 0.4;
        if (STATE.mood === "sole" && it.meteo === "sole") fit += 0.3;
        if (STATE.mood === "bottega" && stops.some(s => s.tipo === "bottega")) fit += 0.55;
        if (STATE.mood === "sera" && it.id === "it_sera_teatro_genova") fit += 0.8;
        const inSeason = it.months.includes(month);
        if (!inSeason) fit -= 1.0;
        return { it, stops, openCount, firstTravel, fit, inSeason };
      }).filter(({ it }) => {
        if (STATE.transport === "treno" && it.mezzo === "auto") return false;
        if (STATE.zone !== "all" && it.zona !== STATE.zone) return true; // still allow ranking, or filter if strict
        return true;
      }).sort((a, b) => {
        if (STATE.zone !== "all") {
          const az = a.it.zona === STATE.zone ? 0 : 1;
          const bz = b.it.zona === STATE.zone ? 0 : 1;
          if (az !== bz) return az - bz;
        }
        return b.fit - a.fit;
      }).slice(0, 4);

      sub.textContent = `• Selezionate per ${fmtHumanDate(STATE.selectedDate)} partendo da ${origin.nome.split("(")[0].trim()}`;

      strip.innerHTML = scored.map(({ it, stops, openCount, firstTravel }) => {
        const allOpen = openCount === stops.length;
        const statusChip = allOpen
          ? `<span class="text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-600">✅ ${openCount}/${stops.length} tappe aperte</span>`
          : `<span class="text-xs font-medium px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-600">⚠️ ${openCount}/${stops.length} aperte in questa data</span>`;

        const mezzoIcon = it.mezzo === "auto" ? "🚗 Auto" : (it.mezzo === "piedi" ? "🚶 A piedi" : "🚆 Treno/Mezzi");
        return `
          <div class="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-3.5 flex flex-col justify-between gap-2.5 shadow-sm hover:border-[var(--primary)] transition">
            <div class="space-y-1.5">
              <div class="flex items-center justify-between gap-1.5 flex-wrap">
                <span class="text-xs px-2 py-0.5 rounded-full bg-[var(--content)] border border-[var(--border)] font-medium">${it.badge}</span>
                ${statusChip}
              </div>
              <h3 class="text-sm font-bold leading-snug">${it.titolo}</h3>
              <p class="text-xs text-[var(--muted-foreground)] leading-relaxed">${it.sottotitolo}</p>
            </div>
            <div class="space-y-2 pt-1 border-t border-[var(--border)]">
              <div class="flex items-center justify-between text-xs text-[var(--muted-foreground)]">
                <span>${mezzoIcon} • ${it.durata}</span>
                <span>1ª tappa: ${firstTravel.min} min</span>
              </div>
              <div class="text-xs text-[var(--foreground)] truncate">
                ${stops.map((s, idx) => `${idx + 1}. ${s.nome.split("—")[0].split("(")[0].trim()}`).join(" → ")}
              </div>
              <button onclick="loadItineraryIntoDate('${it.id}')" class="w-full py-1.5 rounded-xl bg-[var(--content)] hover:bg-[var(--primary)] hover:text-[var(--primary-foreground)] border border-[var(--border)] text-xs font-semibold transition">
                Carica queste ${stops.length} tappe nel programma →
              </button>
            </div>
          </div>
        `;
      }).join("");
    }

    function renderPlacesList(filtered) {
      const countEl = document.getElementById("results-count");
      const ctxEl = document.getElementById("results-context");
      const listEl = document.getElementById("places-list");
      const moreBtn = document.getElementById("load-more-btn");
      const tripIds = getActiveTripIds();

      countEl.textContent = `${filtered.length} mete`;
      ctxEl.textContent = `per ${fmtHumanDate(STATE.selectedDate)}`;

      if (!filtered.length) {
        listEl.innerHTML = `
          <div class="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-6 text-center space-y-2">
            <div class="text-2xl">🔍</div>
            <div class="text-sm font-bold">Nessuna meta trovata con questi filtri</div>
            <p class="text-xs text-[var(--muted-foreground)]">Prova a disattivare "Solo aperti", cambiare zona o allargare il mezzo di trasporto.</p>
            <button onclick="resetFilters()" class="mt-2 px-3.5 py-1.5 rounded-xl bg-[var(--primary)] text-[var(--primary-foreground)] text-xs font-semibold">Reimposta filtri</button>
          </div>
        `;
        moreBtn.classList.add("hidden");
        return;
      }

      const slice = filtered.slice(0, STATE.visibleLimit);
      listEl.innerHTML = slice.map(({ place, ev, tr }) => {
        const meta = TIPO_META[place.tipo] || TIPO_META.museo;
        const inTripIdx = tripIds.indexOf(place.id);
        const isSelected = STATE.selectedPlaceId === place.id;

        const stColor = ev.status === "open"
          ? "bg-emerald-500/15 text-emerald-600"
          : (ev.status === "later" ? "bg-amber-500/15 text-amber-600" : "bg-[var(--content)] text-[var(--muted-foreground)]");

        const indoorBadge = place.indoor === "in" ? "🌧️ Al coperto" : (place.indoor === "out" ? "☀️ Aria aperta" : "🌤️ Misto");

        return `
          <article onclick="selectPlace(${place.id}, true)" class="bg-[var(--card)] border ${isSelected ? 'border-[var(--primary)] ring-1 ring-[var(--primary)]' : 'border-[var(--border)]'} rounded-2xl p-3.5 space-y-2 cursor-pointer hover:border-[var(--primary)] transition shadow-sm">
            <div class="flex items-start justify-between gap-2">
              <div class="space-y-0.5">
                <div class="flex items-center gap-1.5 flex-wrap">
                  <span class="text-xs font-semibold px-2 py-0.5 rounded-full bg-[var(--content)] border border-[var(--border)]">${meta.icon} ${ place.comune }</span>
                  <span class="text-xs font-medium px-2 py-0.5 rounded-full ${stColor}">${ev.status === 'open' ? '● ' : ''}${ev.label}</span>
                </div>
                <h3 class="text-sm font-bold pt-1 leading-snug">${place.nome}</h3>
              </div>
              ${place.tier === 1 ? '<span class="text-xs px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-600 font-semibold whitespace-nowrap">★ Top</span>' : ''}
            </div>

            <p class="text-xs text-[var(--muted-foreground)] leading-relaxed">${place.pitch}</p>

            <div class="flex flex-wrap items-center gap-2 text-xs text-[var(--muted-foreground)]">
              <span class="px-2 py-0.5 rounded-lg bg-[var(--content)] font-medium text-[var(--foreground)]">${tr.badge}</span>
              <span>${indoorBadge}</span>
              <span>• ⏱️ ~${place.durata_min} min</span>
              ${ev.isFreeToday ? '<span class="text-emerald-600 font-semibold">• 🆓 Gratis</span>' : ''}
            </div>

            ${place.personaggio ? `<div class="text-xs text-[var(--muted-foreground)] truncate">👤 <span class="font-medium text-[var(--foreground)]">${place.personaggio}</span></div>` : ''}

            <div class="pt-1.5 border-t border-[var(--border)] flex items-center justify-between gap-2" onclick="event.stopPropagation()">
              <div class="flex items-center gap-2">
                ${place.url ? `<a href="${place.url}" target="_blank" rel="noopener" class="text-xs underline text-[var(--muted-foreground)] hover:text-[var(--foreground)]">🌐 Sito</a>` : ''}
                <a href="https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(place.nome + ' ' + place.comune)}" target="_blank" rel="noopener" class="text-xs underline text-[var(--muted-foreground)] hover:text-[var(--foreground)]">🗺️ Mappa</a>
              </div>
              <button onclick="toggleStopInTrip(${place.id})" class="px-3 py-1 rounded-xl text-xs font-semibold transition ${inTripIdx >= 0 ? 'bg-emerald-500/20 text-emerald-600 border border-emerald-500/40' : 'bg-[var(--primary)] text-[var(--primary-foreground)]'}">
                ${inTripIdx >= 0 ? `✓ Tappa #${inTripIdx + 1}` : '+ Aggiungi'}
              </button>
            </div>
          </article>
        `;
      }).join("");

      if (filtered.length > STATE.visibleLimit) {
        moreBtn.classList.remove("hidden");
        moreBtn.textContent = `Mostra altre mete (${filtered.length - STATE.visibleLimit} rimanenti)`;
      } else {
        moreBtn.classList.add("hidden");
      }
    }

    function renderPlaceInspector() {
      const box = document.getElementById("place-inspector");
      const place = PLACES_BY_ID[STATE.selectedPlaceId] || DATA.places[0];
      if (!place) return;

      const origin = getOrigin();
      const ev = evalPlaceOnDate(place, STATE.selectedDate, STATE.timeSlot);
      const tr = calcTravel(origin, place);
      const meta = TIPO_META[place.tipo] || TIPO_META.museo;
      const tripIds = getActiveTripIds();
      const inTripIdx = tripIds.indexOf(place.id);

      // Find 3 closest OPEN places within 4 km to pair ("Già che sei lì vicino...")
      const nearby = DATA.places
        .filter(p => p.id !== place.id && evalPlaceOnDate(p, STATE.selectedDate, STATE.timeSlot).status !== "closed")
        .map(p => ({ p, d: haversineKm(place.lat, place.lon, p.lat, p.lon) }))
        .filter(x => x.d <= 4.5)
        .sort((a, b) => (a.p.tier - b.p.tier) || (a.d - b.d))
        .slice(0, 3);

      box.innerHTML = `
        <div class="space-y-3">
          <div class="flex flex-wrap items-start justify-between gap-2">
            <div>
              <div class="flex items-center gap-2 flex-wrap">
                <span class="text-xs font-bold px-2.5 py-0.5 rounded-full bg-[var(--content)] border border-[var(--border)]">${meta.icon} ${meta.label} • ${place.comune}</span>
                <span class="text-xs text-[var(--muted-foreground)]">${ZONE_LABELS[place.zona] || ''}</span>
              </div>
              <h3 class="text-base font-bold mt-1.5">${place.nome}</h3>
            </div>
            <button onclick="toggleStopInTrip(${place.id})" class="px-3.5 py-1.5 rounded-xl text-xs font-semibold transition ${inTripIdx >= 0 ? 'bg-emerald-500/20 text-emerald-600 border border-emerald-500/40' : 'bg-[var(--primary)] text-[var(--primary-foreground)]'}">
              ${inTripIdx >= 0 ? `✓ Nel programma (Tappa #${inTripIdx + 1})` : '+ Aggiungi alla Giornata'}
            </button>
          </div>

          <p class="text-xs sm:text-sm text-[var(--foreground)] leading-relaxed">${place.pitch}</p>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs bg-[var(--content)] rounded-xl p-3 border border-[var(--border)]">
            <div><span class="text-[var(--muted-foreground)]">🕒 Orari:</span> <span class="font-medium">${place.orari}</span></div>
            <div><span class="text-[var(--muted-foreground)]">🧭 Arrivo:</span> <span class="font-medium">${tr.badge} — ${place.trasporto_info}</span></div>
            <div><span class="text-[var(--muted-foreground)]">🎟️ Ingresso:</span> <span class="font-medium">${place.costo} (visita ~${place.durata_min} min)</span></div>
            <div><span class="text-[var(--muted-foreground)]">👤 Personaggio:</span> <span class="font-medium">${place.personaggio || 'Memoria storica locale'}</span></div>
          </div>

          <div class="flex flex-wrap items-center gap-3 text-xs">
            ${place.url ? `<a href="${place.url}" target="_blank" rel="noopener" class="px-3 py-1.5 rounded-lg bg-[var(--content)] border border-[var(--border)] font-medium hover:opacity-90">🌐 Sito Ufficiale ↗</a>` : ''}
            <a href="https://www.google.com/maps/dir/?api=1&origin=${origin.lat},${origin.lon}&destination=${place.lat},${place.lon}" target="_blank" rel="noopener" class="px-3 py-1.5 rounded-lg bg-[var(--content)] border border-[var(--border)] font-medium hover:opacity-90">🗺️ Indicazioni Stradali / Treno ↗</a>
            ${place.tel ? `<span class="text-[var(--muted-foreground)]">📞 ${place.tel}</span>` : ''}
            <button onclick="setCustomOriginFromPlace(${place.id})" class="ml-auto text-xs underline text-[var(--muted-foreground)] hover:text-[var(--foreground)]">Imposta come punto di partenza</button>
          </div>

          ${nearby.length ? `
            <div class="pt-2 border-t border-[var(--border)] space-y-1.5">
              <div class="text-xs font-semibold text-[var(--muted-foreground)]">📍 Già che sei lì vicino (aperti in questa data):</div>
              <div class="grid grid-cols-1 sm:grid-cols-3 gap-2">
                ${nearby.map(({ p, d }) => {
                  const added = tripIds.includes(p.id);
                  return `
                    <div onclick="selectPlace(${p.id}, true)" class="p-2 rounded-xl bg-[var(--content)] border border-[var(--border)] hover:border-[var(--primary)] cursor-pointer flex flex-col justify-between gap-1">
                      <div class="text-xs font-semibold leading-tight line-clamp-2">${TIPO_META[p.tipo].icon} ${p.nome}</div>
                      <div class="flex items-center justify-between text-xs text-[var(--muted-foreground)] pt-1">
                        <span>${d < 1 ? `${Math.round(d*1000)} m` : `${d.toFixed(1)} km`}</span>
                        <button onclick="event.stopPropagation(); toggleStopInTrip(${p.id})" class="font-semibold text-[var(--foreground)] hover:underline">${added ? '✓ Aggiunto' : '+ Abbina'}</button>
                      </div>
                    </div>
                  `;
                }).join("")}
              </div>
            </div>
          ` : ''}
        </div>
      `;
    }

    // ==========================================
    // INTERACTIVE HTML5 CANVAS GEOGRAPHICAL MAP
    // ==========================================
    let MAP_HIT_TARGETS = [];

    function projectLatLon(lat, lon, w, h) {
      const cosLat = Math.cos(44.41 * Math.PI / 180);
      const spanLon = STATE.cam.spanLon;
      const spanLat = (spanLon * cosLat) * (h / Math.max(1, w));
      const x = ((lon - (STATE.cam.lon - spanLon / 2)) / spanLon) * w;
      const y = (((STATE.cam.lat + spanLat / 2) - lat) / spanLat) * h;
      return [x, y];
    }

    function unprojectDelta(dx, dy, w, h) {
      const cosLat = Math.cos(44.41 * Math.PI / 180);
      const spanLon = STATE.cam.spanLon;
      const spanLat = (spanLon * cosLat) * (h / Math.max(1, w));
      return {
        dLon: -(dx / w) * spanLon,
        dLat: (dy / h) * spanLat
      };
    }

    function drawMap(filteredList) {
      const canvas = document.getElementById("geo-map");
      if (!canvas) return;
      const rect = canvas.getBoundingClientRect();
      if (rect.width < 10 || rect.height < 10) return;

      const dpr = window.devicePixelRatio || 1;
      canvas.width = Math.round(rect.width * dpr);
      canvas.height = Math.round(rect.height * dpr);
      const ctx = canvas.getContext("2d");
      ctx.scale(dpr, dpr);

      const w = rect.width;
      const h = rect.height;
      const isLight = document.documentElement.classList.contains("light");

      // Theme-adaptive map palette
      const seaFill = isLight ? "#e0f2fe" : "#0c1e2e";
      const landFill = isLight ? "#f8fafc" : "#17202b";
      const coastStroke = isLight ? "#38bdf8" : "#1e4976";
      const railStroke = isLight ? "rgba(100,116,139,0.45)" : "rgba(148,163,184,0.32)";
      const comuneDot = isLight ? "rgba(71,85,105,0.45)" : "rgba(148,163,184,0.40)";
      const labelColor = isLight ? "#334155" : "#cbd5e1";
      const labelHalo = isLight ? "rgba(255,255,255,0.88)" : "rgba(15,23,42,0.88)";

      // 1. Fill Sea Base
      ctx.fillStyle = seaFill;
      ctx.fillRect(0, 0, w, h);

      // 2. Draw Land Polygon north of Coastline
      ctx.beginPath();
      const [xStart, yStart] = projectLatLon(44.85, 8.35, w, h);
      ctx.moveTo(xStart, yStart);
      for (const [clat, clon] of COASTLINE) {
        const [cx, cy] = projectLatLon(clat, clon, w, h);
        ctx.lineTo(cx, cy);
      }
      const [xEnd, yEnd] = projectLatLon(44.85, 9.75, w, h);
      ctx.lineTo(xEnd, yEnd);
      ctx.closePath();
      ctx.fillStyle = landFill;
      ctx.fill();
      ctx.strokeStyle = coastStroke;
      ctx.lineWidth = 2;
      ctx.stroke();

      // Sea Watermark
      ctx.font = "600 12px sans-serif";
      ctx.fillStyle = isLight ? "rgba(2,132,199,0.45)" : "rgba(125,211,252,0.28)";
      const [sx, sy] = projectLatLon(44.27, 8.95, w, h);
      if (sy > 20 && sy < h - 10) ctx.fillText("MAR LIGURE", sx, sy);

      // 3. Draw Railway Corridors
      ctx.save();
      ctx.strokeStyle = railStroke;
      ctx.lineWidth = 1.6;
      ctx.setLineDash([4, 4]);
      for (const line of RAIL_LINES) {
        ctx.beginPath();
        line.forEach(([rlat, rlon], i) => {
          const [rx, ry] = projectLatLon(rlat, rlon, w, h);
          if (i === 0) ctx.moveTo(rx, ry);
          else ctx.lineTo(rx, ry);
        });
        ctx.stroke();
      }
      ctx.restore();

      MAP_HIT_TARGETS = [];

      // 4. Draw the 67 Municipality Markers & Collision-Free Labels (>= 12px)
      const majorComuni = new Set(["Genova", "Arenzano", "Campo Ligure", "Busalla", "Casella", "Vobbia", "Torriglia", "Recco", "Camogli", "Portofino", "Santa Margherita Ligure", "Rapallo", "Chiavari", "Sestri Levante", "Moneglia", "Santo Stefano d'Aveto", "Lorsica", "Tiglieto", "Ne"]);
      const showAllComuniLabels = STATE.cam.spanLon < 0.36;
      const placedBoxes = [];

      ctx.font = "500 12px sans-serif";
      for (const c of DATA.comuni) {
        const [cx, cy] = projectLatLon(c.lat, c.lon, w, h);
        if (cx < -20 || cx > w + 20 || cy < -20 || cy > h + 20) continue;

        ctx.beginPath();
        ctx.arc(cx, cy, STATE.comuneFilter === c.nome ? 5 : 2.5, 0, Math.PI * 2);
        ctx.fillStyle = STATE.comuneFilter === c.nome ? "#f59e0b" : comuneDot;
        ctx.fill();

        MAP_HIT_TARGETS.push({ type: "comune", x: cx, y: cy, r: 7, data: c });

        if (majorComuni.has(c.nome) || showAllComuniLabels) {
          const tw = ctx.measureText(c.nome).width;
          const box = { x1: cx + 6, y1: cy - 8, x2: cx + 8 + tw, y2: cy + 6 };
          const overlaps = placedBoxes.some(b => !(box.x2 < b.x1 || box.x1 > b.x2 || box.y2 < b.y1 || box.y1 > b.y2));
          if (!overlaps) {
            placedBoxes.push(box);
            ctx.lineWidth = 3;
            ctx.strokeStyle = labelHalo;
            ctx.strokeText(c.nome, cx + 6, cy + 4);
            ctx.fillStyle = labelColor;
            ctx.fillText(c.nome, cx + 6, cy + 4);
          }
        }
      }

      // 5. Draw Active Trip Route Polyline (Origin -> Stop 1 -> Stop 2 ...)
      const origin = getOrigin();
      const tripIds = getActiveTripIds();
      if (tripIds.length > 0) {
        ctx.save();
        ctx.beginPath();
        const [ox, oy] = projectLatLon(origin.lat, origin.lon, w, h);
        ctx.moveTo(ox, oy);
        tripIds.forEach(id => {
          const p = PLACES_BY_ID[id];
          if (p) {
            const [px, py] = projectLatLon(p.lat, p.lon, w, h);
            ctx.lineTo(px, py);
          }
        });
        ctx.strokeStyle = isLight ? "#2563eb" : "#60a5fa";
        ctx.lineWidth = 2.6;
        ctx.setLineDash([6, 4]);
        ctx.stroke();
        ctx.restore();
      }

      // 6. Draw Destination Pins
      const filteredIds = new Set(filteredList.map(x => x.place.id));
      // Draw Tier 2 first, then Tier 1, then Selected & Trip stops on top
      const drawOrder = [...filteredList].sort((a, b) => b.place.tier - a.place.tier);

      for (const { place, ev } of drawOrder) {
        if (tripIds.includes(place.id)) continue; // drawn on top layer
        const [px, py] = projectLatLon(place.lat, place.lon, w, h);
        if (px < -15 || px > w + 15 || py < -15 || py > h + 15) continue;

        const isSel = STATE.selectedPlaceId === place.id;
        const r = isSel ? 8.5 : (place.tier === 1 ? 6.2 : 4.4);
        const fill = ev.status === "open" ? "#10b981" : (ev.status === "later" ? "#f59e0b" : "#94a3b8");

        ctx.beginPath();
        ctx.arc(px, py, r, 0, Math.PI * 2);
        ctx.fillStyle = fill;
        ctx.fill();
        ctx.lineWidth = isSel ? 2.8 : 1.5;
        ctx.strokeStyle = isSel ? (isLight ? "#0f172a" : "#ffffff") : (isLight ? "#ffffff" : "#0f172a");
        ctx.stroke();

        MAP_HIT_TARGETS.push({ type: "place", x: px, y: py, r: r + 5, data: place, ev });
      }

      // 7. Draw Numbered Trip Stops on Top
      tripIds.forEach((id, idx) => {
        const place = PLACES_BY_ID[id];
        if (!place) return;
        const [px, py] = projectLatLon(place.lat, place.lon, w, h);
        ctx.beginPath();
        ctx.arc(px, py, 10.5, 0, Math.PI * 2);
        ctx.fillStyle = isLight ? "#1d4ed8" : "#3b82f6";
        ctx.fill();
        ctx.lineWidth = 2.5;
        ctx.strokeStyle = "#fbbf24";
        ctx.stroke();

        ctx.font = "bold 12px sans-serif";
        ctx.fillStyle = "#ffffff";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(String(idx + 1), px, py + 0.5);
        ctx.textAlign = "start";
        ctx.textBaseline = "alphabetic";

        MAP_HIT_TARGETS.push({ type: "place", x: px, y: py, r: 13, data: place, ev: evalPlaceOnDate(place, STATE.selectedDate, STATE.timeSlot) });
      });

      // 8. Draw Origin Hub Pin
      const [hx, hy] = projectLatLon(origin.lat, origin.lon, w, h);
      ctx.beginPath();
      ctx.arc(hx, hy, 9, 0, Math.PI * 2);
      ctx.fillStyle = isLight ? "#0f172a" : "#f8fafc";
      ctx.fill();
      ctx.lineWidth = 2;
      ctx.strokeStyle = "#38bdf8";
      ctx.stroke();
      ctx.font = "12px sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText("🏠", hx, hy);
      ctx.textAlign = "start";
      ctx.textBaseline = "alphabetic";
    }

    function setupMapInteractions() {
      const canvas = document.getElementById("geo-map");
      const tooltip = document.getElementById("map-tooltip");
      let dragging = false, moved = false, lastX = 0, lastY = 0;

      function findHit(mx, my) {
        // Search in reverse so top-most pins win
        for (let i = MAP_HIT_TARGETS.length - 1; i >= 0; i--) {
          const t = MAP_HIT_TARGETS[i];
          const dist = Math.hypot(mx - t.x, my - t.y);
          if (dist <= t.r) return t;
        }
        return null;
      }

      canvas.addEventListener("pointerdown", e => {
        dragging = true;
        moved = false;
        lastX = e.clientX;
        lastY = e.clientY;
        canvas.setPointerCapture(e.pointerId);
      });

      canvas.addEventListener("pointermove", e => {
        const rect = canvas.getBoundingClientRect();
        const mx = e.clientX - rect.left;
        const my = e.clientY - rect.top;

        if (dragging) {
          const dx = e.clientX - lastX;
          const dy = e.clientY - lastY;
          if (Math.abs(dx) > 2 || Math.abs(dy) > 2) moved = true;
          lastX = e.clientX;
          lastY = e.clientY;
          const d = unprojectDelta(dx, dy, rect.width, rect.height);
          STATE.cam.lon = Math.max(8.45, Math.min(9.60, STATE.cam.lon + d.dLon));
          STATE.cam.lat = Math.max(44.20, Math.min(44.68, STATE.cam.lat + d.dLat));
          tooltip.classList.add("hidden");
          drawMap(LAST_FILTERED);
          return;
        }

        const hit = findHit(mx, my);
        if (hit) {
          canvas.style.cursor = "pointer";
          tooltip.classList.remove("hidden");
          tooltip.style.left = `${Math.min(rect.width - 230, Math.max(8, mx + 12))}px`;
          tooltip.style.top = `${Math.max(8, my - 38)}px`;
          if (hit.type === "place") {
            const p = hit.data;
            tooltip.innerHTML = `<div class="font-bold">${TIPO_META[p.tipo].icon} ${p.nome}</div><div class="text-[var(--muted-foreground)]">${p.comune} • ${hit.ev.label}</div>`;
          } else {
            tooltip.innerHTML = `<div class="font-bold">📍 Comune di ${hit.data.nome}</div><div class="text-[var(--muted-foreground)]">${hit.data.elev} m s.l.m. • Clicca per filtrare</div>`;
          }
        } else {
          canvas.style.cursor = "grab";
          tooltip.classList.add("hidden");
        }
      });

      canvas.addEventListener("pointerup", e => {
        dragging = false;
        if (!moved) {
          const rect = canvas.getBoundingClientRect();
          const hit = findHit(e.clientX - rect.left, e.clientY - rect.top);
          if (hit) {
            if (hit.type === "place") {
              selectPlace(hit.data.id, false);
            } else if (hit.type === "comune") {
              setComuneFilter(hit.data.nome);
            }
          }
        }
      });

      canvas.addEventListener("wheel", e => {
        e.preventDefault();
        const factor = e.deltaY < 0 ? 1.22 : 0.82;
        zoomMap(factor);
      }, { passive: false });

      window.addEventListener("resize", () => {
        if (STATE.view === "day") drawMap(LAST_FILTERED);
      });

      // Re-draw canvas automatically if host theme toggles light/dark
      new MutationObserver(() => {
        if (STATE.view === "day") drawMap(LAST_FILTERED);
      }).observe(document.documentElement, { attributes: true, attributeFilter: ["class", "style"] });
    }

    function setMapCamera(preset) {
      if (preset === "provincia") STATE.cam = { lat: 44.42, lon: 9.04, spanLon: 0.98 };
      else if (preset === "genova") STATE.cam = { lat: 44.410, lon: 8.932, spanLon: 0.085 };
      else if (preset === "tigullio") STATE.cam = { lat: 44.315, lon: 9.285, spanLon: 0.36 };
      else if (preset === "valli") STATE.cam = { lat: 44.525, lon: 8.96, spanLon: 0.62 };
      drawMap(LAST_FILTERED);
    }

    function zoomMap(factor) {
      STATE.cam.spanLon = Math.max(0.025, Math.min(1.15, STATE.cam.spanLon / factor));
      drawMap(LAST_FILTERED);
    }

    // ==========================================
    // VIEW 2: 7-DAY WEEKLY PLANNER
    // ==========================================
    const WEEKDAY_STRATEGY = {
      1: { tag: "🛟 Salva-Lunedì", tip: "Porto Antico (Galata & Acquario), Chiostro S. Lorenzo, Villa Durazzo S. Margherita e San Fruttuoso aperti!" },
      2: { tag: "🏺 Caruggi & Rolli", tip: "Riaprono tutte le botteghe artigiane e i Musei di Strada Nuova senza la folla del weekend." },
      3: { tag: "🌿 Riviere & Ville", tip: "Mercoledì perfetto in treno per i Parchi di Pegli o Nervi, oppure Merletto e Funivia a Rapallo." },
      4: { tag: "📚 Cultura & Sera", tip: "Palazzi reali, Orologi da Torre a Uscio e primi concerti/aperitivi serali a teatro." },
      5: { tag: "🗼 Aprono le Perle", tip: "Aprono Lanterna, Museo della Carta a Mele, Filigrana a Campo Ligure e mostre fino alle 21." },
      6: { tag: "✨ Giorno Completo", tip: "L'unico giorno con Botteghe Storiche + Castelli + Campane di Avegno + Damaschi di Lorsica tutti aperti!" },
      0: { tag: "🏰 Gite & Castelli", tip: "Natura, Valli, Castello della Pietra (Apr-Ott), Cioccolato da Viganotti e #DomenicalMuseo (1ª dom)." }
    };

    function renderWeekView() {
      const mon = parseDateStr(STATE.weekMondayStr);
      const sun = new Date(mon.getFullYear(), mon.getMonth(), mon.getDate() + 6, 12, 0, 0);
      document.getElementById("week-range-label").textContent = `${fmtHumanDate(fmtDateStr(mon))} – ${fmtHumanDate(fmtDateStr(sun))} ${sun.getFullYear()}`;

      const grid = document.getElementById("week-grid");
      const cols = [];

      for (let i = 0; i < 7; i++) {
        const d = new Date(mon.getFullYear(), mon.getMonth(), mon.getDate() + i, 12, 0, 0);
        const dStr = fmtDateStr(d);
        const dow = d.getDay();
        const isFirstSun = (dow === 0 && d.getDate() <= 7);
        const strat = WEEKDAY_STRATEGY[dow];
        const openMatches = getFilteredPlaces(dStr, "all", false);
        const plannedIds = STATE.tripsByDate[dStr] || [];

        const topPicks = openMatches.slice(0, 4);

        cols.push(`
          <div class="bg-[var(--card)] border ${dStr === STATE.selectedDate ? 'border-[var(--primary)] ring-1 ring-[var(--primary)]' : 'border-[var(--border)]'} rounded-2xl p-3 flex flex-col justify-between gap-3 shadow-sm">
            <div class="space-y-2">
              <div class="flex items-center justify-between gap-1">
                <div>
                  <div class="text-xs font-bold uppercase text-[var(--muted-foreground)]">${DAYS_IT[dow]}</div>
                  <div class="text-sm font-bold">${d.getDate()} ${MONTHS_IT[d.getMonth()].slice(0,3)}</div>
                </div>
                <span class="text-xs px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-600 font-semibold">${openMatches.length} aperti</span>
              </div>

              <div class="p-2 rounded-xl bg-[var(--content)] border border-[var(--border)] space-y-0.5">
                <div class="text-xs font-bold">${isFirstSun ? '🆓 #DomenicalMuseo' : strat.tag}</div>
                <p class="text-xs text-[var(--muted-foreground)] leading-snug">${isFirstSun ? 'Palazzo Reale, Spinola e MuSel Sestri gratuiti!' : strat.tip}</p>
              </div>

              ${plannedIds.length ? `
                <div class="p-2 rounded-xl bg-amber-500/10 border border-amber-500/30 space-y-1">
                  <div class="text-xs font-bold text-amber-600">🎒 Il tuo piano (${plannedIds.length} tappe):</div>
                  ${plannedIds.map((pid, idx) => `<div class="text-xs truncate">${idx+1}. ${PLACES_BY_ID[pid]?.nome || ''}</div>`).join("")}
                </div>
              ` : ''}

              <div class="space-y-1.5 pt-1">
                <div class="text-xs font-semibold text-[var(--muted-foreground)]">Consigliati per te:</div>
                ${topPicks.map(({ place, tr }) => {
                  const inDay = plannedIds.includes(place.id);
                  return `
                    <div class="p-2 rounded-xl bg-[var(--content)]/70 border border-[var(--border)] space-y-1">
                      <div class="text-xs font-semibold leading-snug">${TIPO_META[place.tipo].icon} ${place.nome.split("—")[0].split("(")[0].trim()}</div>
                      <div class="flex items-center justify-between text-xs text-[var(--muted-foreground)]">
                        <span>${place.comune} • ${tr.min}m</span>
                        <button onclick="toggleStopInTrip(${place.id}, '${dStr}')" class="font-semibold text-[var(--foreground)] hover:underline">${inDay ? '✓' : '+ Metti'}</button>
                      </div>
                    </div>
                  `;
                }).join("")}
              </div>
            </div>

            <button onclick="jumpToDateInDayView('${dStr}')" class="w-full py-1.5 rounded-xl bg-[var(--content)] hover:bg-[var(--primary)] hover:text-[var(--primary-foreground)] border border-[var(--border)] text-xs font-semibold transition">
              Esplora in Mappa →
            </button>
          </div>
        `);
      }
      grid.innerHTML = cols.join("");
    }

    // ==========================================
    // VIEW 3: REAL MONTHLY CALENDAR & SEASONS
    // ==========================================
    function getEventsForDate(year, month, dom) {
      const dt = new Date(year, month - 1, dom, 12, 0, 0);
      const dow = dt.getDay();
      const isFirstSun = (dow === 0 && dom <= 7);
      const isThirdSun = (dow === 0 && dom >= 15 && dom <= 21);

      const list = [];
      for (const ev of DATA.monthly_events) {
        if (ev.month !== month) continue;
        if (ev.day_rule === "first_sun" && isFirstSun) list.push(ev);
        else if (ev.days && ev.days.includes(dom)) list.push(ev);
      }

      // Dynamic recurring Ligurian openings
      if ((dow === 5 || dow === 6 || dow === 0) && list.length < 2) {
        list.push({
          titolo: "Lanterna, Museo della Carta (Mele) & Filigrana (Campo Ligure)",
          comune: "Genova / Mele / Campo Ligure",
          tipo: "borgo",
          desc: "Aperture del fine settimana per il faro simbolo di Genova, la cartiera settecentesca e il museo orafo."
        });
      }
      if (dow === 0 && month >= 4 && month <= 10) {
        list.push({
          titolo: "Visite Guidate al Castello della Pietra nella Roccia",
          comune: "Vobbia (Parco Antola)",
          tipo: "borgo",
          desc: "Aperture domenicali ogni ora (10:30–16:30) della fortezza incastonata tra i torrioni di roccia."
        });
      }
      if ((isFirstSun || isThirdSun) && month >= 3 && month <= 10) {
        list.push({
          titolo: "Apertura Giardino Monumentale Abbazia della Cervara",
          comune: "Santa Margherita Ligure",
          tipo: "natura",
          desc: "1ª e 3ª domenica del mese: visite guidate su prenotazione all'abbazia a picco sul mare."
        });
      }
      return list;
    }

    function renderMonthView() {
      const y = STATE.calYear;
      const m = STATE.calMonth;
      document.getElementById("month-title-label").textContent = `${MONTHS_IT[m - 1]} ${y}`;

      // 12 Month quick pills starting from Nov 2026
      const pills = [];
      for (let i = 0; i < 12; i++) {
        const pm = ((10 + i) % 12) + 1;
        const py = 2026 + Math.floor((10 + i) / 12);
        const active = (py === y && pm === m);
        pills.push(`
          <button onclick="setCalendarMonth(${py}, ${pm})" class="px-3 py-1 rounded-full border border-[var(--border)] bg-[var(--content)] text-xs whitespace-nowrap transition ${active ? 'pill-active' : 'text-[var(--muted-foreground)] hover:text-[var(--foreground)]'}">
            ${MONTHS_IT[pm - 1].slice(0,3)} '${String(py).slice(2)}
          </button>
        `);
      }
      document.getElementById("month-pills").innerHTML = pills.join("");

      const firstDay = new Date(y, m - 1, 1, 12, 0, 0);
      const daysInMonth = new Date(y, m, 0).getDate();
      const startOffset = (firstDay.getDay() === 0 ? 6 : firstDay.getDay() - 1); // Monday=0..Sunday=6

      const cells = [];
      for (let b = 0; b < startOffset; b++) {
        cells.push(`<div class="min-h-[94px] border-b border-r border-[var(--border)] bg-[var(--content)]/30"></div>`);
      }

      for (let dom = 1; dom <= daysInMonth; dom++) {
        const dStr = `${y}-${String(m).padStart(2, "0")}-${String(dom).padStart(2, "0")}`;
        const evs = getEventsForDate(y, m, dom);
        const isSel = dStr === STATE.selectedDate;
        const planned = (STATE.tripsByDate[dStr] || []).length;

        cells.push(`
          <div onclick="selectCalendarDate('${dStr}')" class="min-h-[94px] p-2 border-b border-r border-[var(--border)] cursor-pointer transition hover:bg-[var(--content)]/60 flex flex-col justify-between ${isSel ? 'bg-[var(--primary)]/10 ring-2 ring-inset ring-[var(--primary)]' : ''}">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold ${isSel ? 'px-1.5 py-0.5 rounded-md bg-[var(--primary)] text-[var(--primary-foreground)]' : ''}">${dom}</span>
              ${planned ? `<span class="text-xs px-1.5 rounded-full bg-amber-500/20 text-amber-600 font-bold">🎒 ${planned}</span>` : ''}
            </div>
            <div class="space-y-1 mt-1">
              ${evs.slice(0, 2).map(e => {
                const badgeCls = e.tipo === "gratis"
                  ? "bg-emerald-500/15 text-emerald-600"
                  : (e.tipo === "evento" || e.tipo === "sapori" ? "bg-amber-500/15 text-amber-600" : "bg-[var(--content)] text-[var(--foreground)]");
                return `<div class="text-xs px-1.5 py-0.5 rounded-md truncate font-medium ${badgeCls}">${e.titolo}</div>`;
              }).join("")}
            </div>
          </div>
        `);
      }
      document.getElementById("calendar-cells").innerHTML = cells.join("");

      renderMonthDayDetail();
    }

    function renderMonthDayDetail() {
      const box = document.getElementById("month-day-detail");
      const dt = parseDateStr(STATE.selectedDate);
      const y = dt.getFullYear(), m = dt.getMonth() + 1, dom = dt.getDate();
      const evs = getEventsForDate(y, m, dom);
      const monthHighlights = DATA.monthly_events.filter(e => e.month === m);
      const openCount = getFilteredPlaces(STATE.selectedDate, "all", false).length;

      box.innerHTML = `
        <div class="space-y-2 pb-3 border-b border-[var(--border)]">
          <div class="text-xs font-semibold text-[var(--muted-foreground)] uppercase">Giorno Selezionato</div>
          <div class="text-lg font-bold">${DAYS_IT[dt.getDay()]} ${dom} ${MONTHS_IT[m - 1]} ${y}</div>
          <div class="text-xs text-emerald-600 font-semibold">● ${openCount} mete aperte compatibili coi tuoi filtri</div>
          <button onclick="jumpToDateInDayView('${STATE.selectedDate}')" class="w-full mt-1 py-2 rounded-xl bg-[var(--primary)] text-[var(--primary-foreground)] text-xs font-semibold shadow-sm hover:opacity-95 transition">
            📍 Apri Mappa &amp; Pianifica il ${dom} ${MONTHS_IT[m - 1].slice(0,3)} →
          </button>
        </div>

        <div class="space-y-2">
          <div class="text-xs font-bold uppercase text-[var(--muted-foreground)]">Cosa succede in questa data</div>
          ${evs.length ? evs.map(e => `
            <div class="p-3 rounded-xl bg-[var(--content)] border border-[var(--border)] space-y-1">
              <div class="text-xs font-bold">${e.titolo}</div>
              <div class="text-xs text-[var(--muted-foreground)]">📍 ${e.comune}</div>
              <p class="text-xs leading-relaxed">${e.desc}</p>
            </div>
          `).join("") : `<p class="text-xs text-[var(--muted-foreground)]">Giornata ideale per itinerari tra botteghe storiche, riviere in treno, parchi storici e musei senza affollamento.</p>`}
        </div>

        <div class="space-y-2 pt-2 border-t border-[var(--border)]">
          <div class="text-xs font-bold uppercase text-[var(--muted-foreground)]">Tutti gli Appuntamenti di ${MONTHS_IT[m - 1]}</div>
          ${monthHighlights.map(e => `
            <div class="text-xs py-1.5 border-b border-[var(--border)] last:border-0">
              <span class="font-semibold">${e.titolo}</span>
              <span class="text-[var(--muted-foreground)]"> — ${e.comune}</span>
            </div>
          `).join("")}
        </div>
      `;
    }

    // ==========================================
    // TRIP TIMELINE & HISTORICAL CHARACTER STORY
    // ==========================================
    function renderTripDrawer() {
      const tripIds = getActiveTripIds();
      const totalAllDays = Object.values(STATE.tripsByDate).reduce((acc, a) => acc + a.length, 0);
      document.getElementById("trip-count-badge").textContent = String(tripIds.length || totalAllDays);
      document.getElementById("drawer-date-badge").textContent = fmtHumanDate(STATE.selectedDate);

      const timelineEl = document.getElementById("drawer-timeline");
      const actionsEl = document.getElementById("drawer-actions");
      const storyEl = document.getElementById("drawer-story");
      const mapBar = document.getElementById("map-active-trip-bar");

      if (!tripIds.length) {
        if (mapBar) mapBar.classList.add("hidden");
        timelineEl.innerHTML = `
          <div class="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-6 text-center space-y-2">
            <div class="text-2xl">🗺️</div>
            <div class="text-sm font-bold">Nessuna tappa ancora scelta per ${fmtHumanDate(STATE.selectedDate)}</div>
            <p class="text-xs text-[var(--muted-foreground)]">
              Clicca <strong>"Carica tappe"</strong> su una delle Gite Pronte oppure premi <strong>"+ Aggiungi"</strong> sulle mete che ti ispirano: calcoleremo orari, spostamenti e il racconto dei personaggi!
            </p>
          </div>
        `;
        actionsEl.classList.add("hidden");
        storyEl.classList.add("hidden");
        return;
      }

      actionsEl.classList.remove("hidden");
      storyEl.classList.remove("hidden");

      const origin = getOrigin();
      let cursorHour = STATE.tripStartHour;
      let prevPoint = { lat: origin.lat, lon: origin.lon, rail: origin.rail, nome: origin.nome };

      const stepsHtml = [];
      const gmapsWaypoints = [`${origin.lat},${origin.lon}`];
      const storyCharacters = [];

      tripIds.forEach((id, idx) => {
        const place = PLACES_BY_ID[id];
        if (!place) return;
        const leg = calcTravel(prevPoint, place);
        cursorHour += leg.min / 60;
        const arrHour = cursorHour;
        const depHour = arrHour + place.durata_min / 60;
        cursorHour = depHour;
        prevPoint = { lat: place.lat, lon: place.lon, rail: place.treno, nome: place.nome };
        gmapsWaypoints.push(`${place.lat},${place.lon}`);

        // Validate arrival hour against date & place slots
        const dayEv = evalPlaceOnDate(place, STATE.selectedDate, "all");
        const inHourSlot = dayEv.status !== "closed" && place.slots.some(([s1, s2]) => arrHour >= s1 - 0.25 && arrHour <= s2 - 0.25);

        const checkBadge = dayEv.status === "closed"
          ? `<span class="text-xs text-amber-600 font-semibold">⚠️ ${dayEv.label}</span>`
          : (inHourSlot
              ? `<span class="text-xs text-emerald-600 font-semibold">✅ Aperto all'arrivo</span>`
              : `<span class="text-xs text-amber-600 font-semibold">🕒 Verifica fascia (${place.slots.map(([a,b])=>fmtHour(a)+'-'+fmtHour(b)).join(', ')})</span>`);

        if (place.personaggio) {
          storyCharacters.push({ comune: place.comune, luogo: place.nome.split("—")[0].split("(")[0].trim(), personaggio: place.personaggio });
        }

        stepsHtml.push(`
          <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-3 space-y-1.5">
            <div class="text-xs text-[var(--muted-foreground)] flex items-center justify-between">
              <span>↳ Spostamento: <strong>${leg.badge}</strong></span>
              <div class="flex items-center gap-1">
                ${idx > 0 ? `<button onclick="moveTripStop(${idx}, -1)" class="px-1.5 py-0.5 rounded bg-[var(--content)] text-xs" title="Sposta su">↑</button>` : ''}
                ${idx < tripIds.length - 1 ? `<button onclick="moveTripStop(${idx}, 1)" class="px-1.5 py-0.5 rounded bg-[var(--content)] text-xs" title="Sposta giù">↓</button>` : ''}
                <button onclick="toggleStopInTrip(${place.id})" class="px-1.5 py-0.5 rounded bg-[var(--content)] text-xs" title="Rimuovi">✕</button>
              </div>
            </div>
            <div class="flex items-baseline justify-between gap-2">
              <div class="text-sm font-bold">${idx + 1}. ${TIPO_META[place.tipo].icon} ${place.nome}</div>
            </div>
            <div class="flex flex-wrap items-center justify-between gap-2 text-xs">
              <span class="font-semibold px-2 py-0.5 rounded-md bg-[var(--content)]">${fmtHour(arrHour)} – ${fmtHour(depHour)} (${place.comune})</span>
              ${checkBadge}
            </div>
          </div>
        `);
      });

      timelineEl.innerHTML = stepsHtml.join("");
      const gmapsUrl = `https://www.google.com/maps/dir/${gmapsWaypoints.join("/")}`;
      document.getElementById("gmaps-route-link").href = gmapsUrl;

      if (mapBar) {
        mapBar.classList.remove("hidden");
        const chain = tripIds.map((id, i) => `${i + 1}. ${(PLACES_BY_ID[id]?.nome || "").split("—")[0].split("(")[0].trim()}`).join(" → ");
        mapBar.innerHTML = `
          <div class="text-xs truncate max-w-[65%]">
            <span class="font-bold">🎒 Giro attivo (${fmtHumanDate(STATE.selectedDate)}):</span>
            <span class="text-[var(--muted-foreground)] ml-1">${chain}</span>
          </div>
          <div class="flex items-center gap-2">
            <a href="${gmapsUrl}" target="_blank" rel="noopener" class="px-2.5 py-1 rounded-lg bg-[var(--content)] border border-[var(--border)] text-xs font-semibold hover:opacity-90">🗺️ Maps ↗</a>
            <button onclick="toggleDrawer(true)" class="px-2.5 py-1 rounded-lg bg-[var(--primary)] text-[var(--primary-foreground)] text-xs font-semibold">Orari &amp; Storia →</button>
          </div>
        `;
      }

      // Weave Custom Story from Characters along the User's Route!
      const uniqueComuni = [...new Set(tripIds.map(id => PLACES_BY_ID[id]?.comune).filter(Boolean))];
      let storyProse = "";
      if (storyCharacters.length) {
        const chapters = storyCharacters.map((c, i) => {
          const connector = i === 0 ? "Il cammino si apre" : (i === storyCharacters.length - 1 ? "Infine, l'ultima tappa conduce" : "Proseguendo lungo il percorso ci si imbatte");
          return `${connector} a <strong>${c.comune}</strong> presso <em>${c.luogo}</em>, nel segno di <strong>${c.personaggio}</strong>`;
        }).join(". ") + ".";
        storyProse = chapters;
      } else {
        storyProse = `Un itinerario attraverso ${uniqueComuni.join(", ")}, seguendo la trama delle antiche vie, delle botteghe e dei paesaggi della Provincia di Genova.`;
      }

      storyEl.innerHTML = `
        <div class="text-xs font-bold uppercase tracking-wide text-[var(--muted-foreground)] flex items-center gap-1.5">
          <span>📜</span>
          <span>Il Racconto dei Personaggi del Tuo Giro</span>
        </div>
        <p class="text-xs sm:text-sm leading-relaxed">${storyProse}</p>
        <p class="text-xs text-[var(--muted-foreground)] pt-1 border-t border-[var(--border)]">
          Intrecciato automaticamente dall'archivio dei ${DATA.meta.total_person_toponyms.toLocaleString('it-IT')} toponimi e monumenti intitolati a personaggi storici nei 67 Comuni.
        </p>
      `;
    }

    // ==========================================
    // CONTROLLERS & ACTIONS
    // ==========================================
    function switchView(v) {
      STATE.view = v;
      ["day", "week", "month"].forEach(name => {
        document.getElementById(`view-${name}`).classList.toggle("hidden", name !== v);
        document.getElementById(`tab-${name}`).classList.toggle("tab-active", name === v);
        document.getElementById(`tab-${name}`).classList.toggle("text-[var(--muted-foreground)]", name !== v);
      });
      refreshAll();
    }

    function onHubChange(hubId) {
      if (hubId !== "custom") {
        STATE.hubId = hubId;
        STATE.customOrigin = null;
      }
      refreshAll();
    }

    function setCustomOriginFromPlace(placeId) {
      const p = PLACES_BY_ID[placeId];
      if (!p) return;
      STATE.customOrigin = { id: "custom", nome: `${p.nome.slice(0,22)} (${p.comune})`, lat: p.lat, lon: p.lon, rail: p.treno };
      const sel = document.getElementById("hub-select");
      let opt = document.getElementById("custom-origin-opt");
      if (!opt) {
        opt = document.createElement("option");
        opt.id = "custom-origin-opt";
        opt.value = "custom";
        sel.prepend(opt);
      }
      opt.textContent = `📍 ${STATE.customOrigin.nome}`;
      sel.value = "custom";
      refreshAll();
    }

    function setTransport(t) {
      STATE.transport = t;
      STATE.visibleLimit = 20;
      document.querySelectorAll(".transport-btn").forEach(b => {
        b.classList.toggle("pill-active", b.dataset.transport === t);
      });
      refreshAll();
    }

    function setMood(m) {
      STATE.mood = m;
      STATE.visibleLimit = 20;
      if (m === "sera" && STATE.timeSlot !== "sera") {
        setTimeSlot("sera");
        return;
      }
      document.querySelectorAll(".mood-btn").forEach(b => {
        b.classList.toggle("pill-active", b.dataset.mood === m);
      });
      refreshAll();
    }

    function setZone(z) {
      STATE.zone = z;
      STATE.comuneFilter = null;
      document.getElementById("comune-filter-pill").classList.add("hidden");
      STATE.visibleLimit = 20;
      if (z === "centro") setMapCamera("genova");
      else if (z === "tigullio_occ" || z === "tigullio_or" || z === "golfo_paradiso") setMapCamera("tigullio");
      else if (z === "polcevera_scrivia" || z === "ponente_stura") setMapCamera("valli");
      else setMapCamera("provincia");
      refreshAll();
    }

    function setComuneFilter(comuneNome) {
      STATE.comuneFilter = comuneNome;
      const pill = document.getElementById("comune-filter-pill");
      pill.textContent = `📍 Comune: ${comuneNome} ✕`;
      pill.classList.remove("hidden");
      const c = DATA.comuni.find(x => x.nome === comuneNome);
      if (c) {
        STATE.cam = { lat: c.lat, lon: c.lon, spanLon: comuneNome === "Genova" ? 0.14 : 0.12 };
      }
      refreshAll();
    }

    function clearComuneFilter() {
      STATE.comuneFilter = null;
      document.getElementById("comune-filter-pill").classList.add("hidden");
      setMapCamera("provincia");
      refreshAll();
    }

    function onSearchInput(val) {
      STATE.search = val;
      STATE.visibleLimit = 20;
      document.getElementById("clear-search-btn").classList.toggle("hidden", !val);
      refreshAll();
    }

    function setSelectedDate(dStr) {
      if (!dStr) return;
      STATE.selectedDate = dStr;
      const dt = parseDateStr(dStr);
      STATE.weekMondayStr = getMondayStr(dt);
      STATE.calYear = dt.getFullYear();
      STATE.calMonth = dt.getMonth() + 1;
      refreshAll();
    }

    function setTimeSlot(s) {
      STATE.timeSlot = s;
      document.querySelectorAll(".slot-btn").forEach(b => {
        b.classList.toggle("pill-active", b.dataset.slot === s);
      });
      refreshAll();
    }

    function toggleOnlyOpen(checked) {
      STATE.onlyOpen = checked;
      refreshAll();
    }

    function setSort(val) {
      STATE.sort = val;
      refreshAll();
    }

    function loadMorePlaces() {
      STATE.visibleLimit += 24;
      refreshAll();
    }

    function selectPlace(id, panMap) {
      STATE.selectedPlaceId = id;
      const p = PLACES_BY_ID[id];
      if (panMap && p) {
        STATE.cam.lat = p.lat;
        STATE.cam.lon = p.lon;
        if (STATE.cam.spanLon > 0.25) STATE.cam.spanLon = p.comune === "Genova" ? 0.06 : 0.14;
      }
      renderPlaceInspector();
      renderPlacesList(LAST_FILTERED);
      drawMap(LAST_FILTERED);
    }

    function toggleItinerariesCollapse() {
      STATE.itinerariesCollapsed = !STATE.itinerariesCollapsed;
      document.getElementById("toggle-itin-btn").textContent = STATE.itinerariesCollapsed ? "Mostra proposte pronte" : "Nascondi proposte pronte";
      renderItinerariesStrip();
    }

    function toggleDrawer(open) {
      document.getElementById("trip-drawer").classList.toggle("hidden", !open);
      document.getElementById("trip-drawer-backdrop").classList.toggle("hidden", !open);
    }

    function setTripStartHour(h) {
      STATE.tripStartHour = h;
      renderTripDrawer();
    }

    function moveTripStop(idx, dir) {
      const arr = getActiveTripIds();
      const target = idx + dir;
      if (target < 0 || target >= arr.length) return;
      const tmp = arr[idx];
      arr[idx] = arr[target];
      arr[target] = tmp;
      refreshAll();
    }

    function optimizeTripOrder() {
      const arr = getActiveTripIds();
      if (arr.length < 2) return;
      const remaining = [...arr];
      const ordered = [];
      let cur = getOrigin();
      while (remaining.length) {
        remaining.sort((a, b) => haversineKm(cur.lat, cur.lon, PLACES_BY_ID[a].lat, PLACES_BY_ID[a].lon) - haversineKm(cur.lat, cur.lon, PLACES_BY_ID[b].lat, PLACES_BY_ID[b].lon));
        const nextId = remaining.shift();
        ordered.push(nextId);
        cur = PLACES_BY_ID[nextId];
      }
      STATE.tripsByDate[STATE.selectedDate] = ordered;
      refreshAll();
    }

    function clearTripForActiveDate() {
      STATE.tripsByDate[STATE.selectedDate] = [];
      refreshAll();
    }

    function copyTripText() {
      const arr = getActiveTripIds();
      if (!arr.length) return;
      const origin = getOrigin();
      let h = STATE.tripStartHour;
      let prev = origin;
      const lines = [`🧭 PROGRAMMA TEMPO LIBERO — ${fmtHumanDate(STATE.selectedDate)}`, `Partenza da: ${origin.nome}`, ""];
      arr.forEach((id, i) => {
        const p = PLACES_BY_ID[id];
        const leg = calcTravel(prev, p);
        h += leg.min / 60;
        const s = fmtHour(h);
        h += p.durata_min / 60;
        const e = fmtHour(h);
        prev = p;
        lines.push(`${i+1}. ${s}–${e} | ${p.nome} (${p.comune}) — [${leg.badge}]`);
        if (p.personaggio) lines.push(`   👤 Personaggio: ${p.personaggio}`);
      });
      navigator.clipboard?.writeText(lines.join("\n"));
      const btn = document.getElementById("copy-trip-btn");
      btn.textContent = "✅ Programma Copiato!";
      setTimeout(() => { btn.textContent = "📋 Copia Tabella di Marcia"; }, 2000);
    }

    function surpriseMe() {
      const candidates = getFilteredPlaces(STATE.selectedDate, STATE.timeSlot, false).filter(x => x.place.tier === 1);
      const pool = candidates.length >= 2 ? candidates : getFilteredPlaces(STATE.selectedDate, STATE.timeSlot, false);
      if (!pool.length) return;
      const seed = pool[Math.floor(Math.random() * Math.min(12, pool.length))].place;
      const combo = [seed.id];
      const near = pool
        .filter(x => x.place.id !== seed.id && haversineKm(seed.lat, seed.lon, x.place.lat, x.place.lon) <= 6.5)
        .slice(0, 2);
      near.forEach(n => combo.push(n.place.id));
      STATE.tripsByDate[STATE.selectedDate] = combo;
      STATE.selectedPlaceId = seed.id;
      focusCameraOnStops(combo);
      if (STATE.view !== "day") switchView("day");
      else refreshAll();
      toggleDrawer(true);
    }

    function resetFilters() {
      STATE.transport = "all";
      STATE.mood = "all";
      STATE.zone = "all";
      STATE.comuneFilter = null;
      STATE.search = "";
      STATE.onlyOpen = false;
      document.getElementById("only-open-toggle").checked = false;
      document.getElementById("zone-select").value = "all";
      document.getElementById("search-input").value = "";
      document.getElementById("comune-filter-pill").classList.add("hidden");
      setTransport("all");
      setMood("all");
    }

    function shiftWeek(days) {
      const d = parseDateStr(STATE.weekMondayStr);
      d.setDate(d.getDate() + days);
      STATE.weekMondayStr = fmtDateStr(d);
      renderWeekView();
    }

    function jumpToDateInDayView(dStr) {
      setSelectedDate(dStr);
      switchView("day");
    }

    function shiftMonth(delta) {
      let m = STATE.calMonth + delta;
      let y = STATE.calYear;
      if (m < 1) { m = 12; y--; }
      if (m > 12) { m = 1; y++; }
      setCalendarMonth(y, m);
    }

    function setCalendarMonth(y, m) {
      STATE.calYear = y;
      STATE.calMonth = m;
      STATE.selectedDate = `${y}-${String(m).padStart(2,"0")}-01`;
      renderMonthView();
    }

    function selectCalendarDate(dStr) {
      STATE.selectedDate = dStr;
      renderMonthView();
    }

    let LAST_FILTERED = [];

    function refreshAll() {
      renderQuickDates();
      LAST_FILTERED = getFilteredPlaces(STATE.selectedDate, STATE.timeSlot, false);
      if (!LAST_FILTERED.some(x => x.place.id === STATE.selectedPlaceId) && LAST_FILTERED.length > 0) {
        STATE.selectedPlaceId = LAST_FILTERED[0].place.id;
      }
      if (STATE.view === "day") {
        renderDayAdviceBanner();
        renderItinerariesStrip();
        renderPlacesList(LAST_FILTERED);
        renderPlaceInspector();
        drawMap(LAST_FILTERED);
      } else if (STATE.view === "week") {
        renderWeekView();
      } else if (STATE.view === "month") {
        renderMonthView();
      }
      renderTripDrawer();
    }

    // Boot
    populateHubs();
    setupMapInteractions();
    refreshAll();
  </script>
</body>
</html>
"""

final_html = HTML_TEMPLATE.replace("__PAYLOAD_JSON__", payload_json)

with open("/Users/dany/genova/bussola_tempo_libero_genova.html", "w", encoding="utf-8") as f:
    f.write(final_html)

import os, re
size_kb = round(os.path.getsize("/Users/dany/genova/bussola_tempo_libero_genova.html") / 1024, 1)
print(f"Generated /Users/dany/genova/bussola_tempo_libero_genova.html ({size_kb} KB)")

# Audit generative_ui rules: check no sub-12px classes or :root
sub12 = re.findall(r"text-\[(?:[0-9]|10|11)px\]|font-size:\s*(?:[0-9]|10|11)px", final_html)
has_root = ":root" in final_html
print("Sub-12px matches:", sub12)
print("Has :root override:", has_root)
