import json
import os as _os
_DATA_DIR = _os.environ.get("GENOVA_DATA_DIR") or _os.path.dirname(_os.path.abspath(__file__))

with open(f"{_DATA_DIR}/dashboard_items.json") as f:
    items = json.load(f)

# Sort items so those with verified rich schedules & websites come first
def sort_key(x):
    score = 0
    if x.get("sito_web"): score -= 4
    if x.get("telefono"): score -= 2
    if "Bottega Storica" in x.get("sottocategoria", ""): score -= 5
    if x.get("orari_apertura") and not x["orari_apertura"].startswith("Consultare") and not x["orari_apertura"].startswith("Aperto tutti i giorni per visite"):
        score -= 4
    if x.get("personaggio"): score -= 1
    return (score, x["comune"], x["nome"])

items_sorted = sorted(items, key=sort_key)

# Compact keys for embedding in HTML
compact_items = []
for idx, it in enumerate(items_sorted, 1):
    compact_items.append({
        "id": idx,
        "c": it["comune"],
        "n": it["nome"],
        "m": it["macro_categoria"],
        "s": it["sottocategoria"],
        "a": it["indirizzo"],
        "t": it["telefono"],
        "w": it["sito_web"],
        "o": it["orari_apertura"],
        "e": it["eventi_e_servizi_al_pubblico"][:260],
        "d": it["days_open"],
        "h": it["hours_range"],
        "sun": 1 if it["open_sunday"] else 0,
        "eve": 1 if it["open_evening"] else 0,
        "f1": 1 if it["free_first_sunday"] else 0,
        "mo": it["seasonal_months"],
        "p": it["personaggio"]
    })

json_payload = json.dumps(compact_items, ensure_ascii=False).replace("<", "\\u003c")

html_template = """<!DOCTYPE html>
<html lang="it">
<head>
  <meta charset="UTF-8">
  <title>Genova & Provincia (67 Comuni) — Dashboard Giorno / Settimana / Mese</title>
  <style>__VANILLA_CSS__</style>
  <style>
    .custom-scroll::-webkit-scrollbar { width: 6px; height: 6px; }
    .custom-scroll::-webkit-scrollbar-track { background: transparent; }
    .custom-scroll::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
  </style>
</head>
<body class="bg-[var(--background)] text-[var(--foreground)] antialiased min-h-screen flex flex-col">
  __SHARED_NAV__

  <!-- Top Header -->
  <header class="border-b border-[var(--border)] bg-[var(--card)] px-6 py-4 sticky top-0 z-30">
    <div class="flex flex-wrap items-center justify-between gap-4">
      <div>
        <div class="flex items-center gap-2">
          <span class="text-xs font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-[var(--primary)] text-[var(--primary-foreground)]">Planner Culturale & Urbano</span>
          <span class="text-xs text-[var(--muted-foreground)]">67 Comuni della Città Metropolitana di Genova • 1.987 Luoghi & Siti Web</span>
        </div>
        <h1 class="text-xl font-bold mt-1 text-[var(--foreground)]">Cosa è Aperto a Genova e Provincia: Giorno, Settimana, Mese</h1>
      </div>

      <!-- Horizon Switcher: OGGI / SETTIMANA / MESE / ITINERARIO -->
      <div class="inline-flex rounded-xl border border-[var(--border)] bg-[var(--background)] p-1 shadow-sm">
        <button id="tab-day" onclick="setHorizon('day')" class="px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-[var(--primary)] text-[var(--primary-foreground)] transition-all">
          1. Vista Giorno (Oggi / Ora)
        </button>
        <button id="tab-week" onclick="setHorizon('week')" class="px-3.5 py-1.5 text-xs font-semibold rounded-lg text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-all">
          2. Vista Settimana (Lun–Dom)
        </button>
        <button id="tab-month" onclick="setHorizon('month')" class="px-3.5 py-1.5 text-xs font-semibold rounded-lg text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-all">
          3. Vista Mese & Stagioni
        </button>
        <button id="tab-plan" onclick="setHorizon('plan')" class="px-3.5 py-1.5 text-xs font-semibold rounded-lg text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-all flex items-center gap-1.5">
          <span>Il Mio Programma</span>
          <span id="plan-count-badge" class="px-1.5 py-0.2 rounded-full text-xs bg-amber-500 text-white font-bold">0</span>
        </button>
      </div>
    </div>

    <!-- Global Search & Filter Bar -->
    <div class="mt-3 pt-3 border-t border-[var(--border)] grid grid-cols-1 md:grid-cols-12 gap-2.5 items-center">
      <div class="md:col-span-4 relative">
        <input id="search-input" type="text" oninput="applyFilters()" placeholder="Cerca biblioteca, museo, teatro, bottega, personaggio..."
          class="w-full px-3 py-1.5 text-xs rounded-lg border border-[var(--border)] bg-[var(--background)] text-[var(--foreground)] focus:outline-none focus:border-[var(--primary)]" />
      </div>
      <div class="md:col-span-3">
        <select id="comune-select" onchange="applyFilters()" class="w-full px-2.5 py-1.5 text-xs rounded-lg border border-[var(--border)] bg-[var(--background)] text-[var(--foreground)]">
          <option value="ALL">Tutti i 67 Comuni della Provincia</option>
        </select>
      </div>
      <div class="md:col-span-3">
        <select id="macro-select" onchange="applyFilters()" class="w-full px-2.5 py-1.5 text-xs rounded-lg border border-[var(--border)] bg-[var(--background)] text-[var(--foreground)]">
          <option value="ALL">Tutte le 9 Categorie (1.987 luoghi)</option>
          <option value="1.">1. Biblioteche & Archivi</option>
          <option value="2.">2. Musei, Gallerie & Acquario</option>
          <option value="3.">3. Teatri, Cinema, Arene & Spettacolo</option>
          <option value="4.">4. Palazzi dei Rolli, Ville, Castelli & Forti</option>
          <option value="5.">5. Parchi, Giardini Storici & Oasi</option>
          <option value="6.">6. Botteghe Storiche, Librerie & Ristorazione</option>
          <option value="7.">7. Cattedrali, Basiliche, Santuari & Abbazie</option>
          <option value="8.">8. Stadi, Porti Turistici & Impianti Sportivi</option>
          <option value="9.">9. Università, Ospedali & Istituzioni</option>
        </select>
      </div>
      <div class="md:col-span-2 flex items-center justify-end gap-2">
        <label class="flex items-center gap-1.5 text-xs cursor-pointer select-none">
          <input id="only-web" type="checkbox" onchange="applyFilters()" class="rounded border-[var(--border)]" />
          <span>Solo con Sito Web</span>
        </label>
      </div>
    </div>
  </header>

  <!-- Main Content Area -->
  <main class="flex-1 p-6 max-w-[1600px] w-full mx-auto space-y-5">

    <!-- ==================== VIEW 1: DAY SIMULATOR ==================== -->
    <section id="section-day" class="space-y-4">
      <div class="rounded-xl border border-[var(--border)] bg-[var(--card)] p-4 shadow-sm">
        <div class="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 class="text-sm font-bold text-[var(--foreground)]">Simulatore Giornaliero e Fascia Oraria</h2>
            <p class="text-xs text-[var(--muted-foreground)]">Scegli il giorno della settimana e l'orario (o attiva i filtri rapidi) per vedere cosa è aperto in quel preciso momento.</p>
          </div>
          <div class="flex flex-wrap items-center gap-2">
            <button onclick="setQuickToday()" class="px-3 py-1.5 rounded-lg text-xs font-semibold bg-amber-500 text-white hover:opacity-90">
              Imposta su Oggi (Domenica 1 Nov)
            </button>
            <button id="btn-filter-open-now" onclick="toggleOpenAtHour()" class="px-3 py-1.5 rounded-lg text-xs font-semibold border border-[var(--border)] bg-[var(--background)] text-[var(--foreground)]">
              Filtra: Solo Aperti all'orario scelto
            </button>
            <button id="btn-filter-1st-sun" onclick="toggleFirstSunday()" class="px-3 py-1.5 rounded-lg text-xs font-semibold border border-[var(--border)] bg-[var(--background)] text-[var(--foreground)]">
              Speciale 1ª Domenica del Mese (Musei Gratis)
            </button>
          </div>
        </div>

        <!-- Day Pills + Time Slider -->
        <div class="mt-4 pt-3 border-t border-[var(--border)] grid grid-cols-1 lg:grid-cols-12 gap-4 items-center">
          <div class="lg:col-span-7 flex flex-wrap gap-1.5" id="day-pills">
            <button onclick="selectDay(1)" data-day="1" class="day-pill px-3 py-1.5 rounded-lg text-xs font-semibold border border-[var(--border)] bg-[var(--background)]">Lunedì</button>
            <button onclick="selectDay(2)" data-day="2" class="day-pill px-3 py-1.5 rounded-lg text-xs font-semibold border border-[var(--border)] bg-[var(--background)]">Martedì</button>
            <button onclick="selectDay(3)" data-day="3" class="day-pill px-3 py-1.5 rounded-lg text-xs font-semibold border border-[var(--border)] bg-[var(--background)]">Mercoledì</button>
            <button onclick="selectDay(4)" data-day="4" class="day-pill px-3 py-1.5 rounded-lg text-xs font-semibold border border-[var(--border)] bg-[var(--background)]">Giovedì</button>
            <button onclick="selectDay(5)" data-day="5" class="day-pill px-3 py-1.5 rounded-lg text-xs font-semibold border border-[var(--border)] bg-[var(--background)]">Venerdì</button>
            <button onclick="selectDay(6)" data-day="6" class="day-pill px-3 py-1.5 rounded-lg text-xs font-semibold border border-[var(--border)] bg-[var(--background)]">Sabato</button>
            <button onclick="selectDay(0)" data-day="0" class="day-pill px-3 py-1.5 rounded-lg text-xs font-semibold bg-[var(--primary)] text-[var(--primary-foreground)]">Domenica</button>
          </div>

          <div class="lg:col-span-5 flex items-center gap-3">
            <span class="text-xs font-semibold text-[var(--muted-foreground)] shrink-0">Orario visita:</span>
            <input id="hour-slider" type="range" min="7" max="23" step="0.5" value="11" oninput="updateHourSlider(this.value)" class="w-full accent-amber-500 cursor-pointer" />
            <span id="hour-display" class="text-xs font-bold font-mono px-2.5 py-1 rounded bg-[var(--content)] border border-[var(--border)] min-w-[64px] text-center">11:00</span>
          </div>
        </div>
      </div>

      <!-- KPI Summary Cards for Selected Day -->
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div class="p-3.5 rounded-xl border border-[var(--border)] bg-[var(--card)]">
          <div class="text-xs text-[var(--muted-foreground)]">Luoghi Aperti nel Giorno Scelto</div>
          <div id="kpi-open-day" class="text-xl font-bold text-emerald-500 mt-0.5">0</div>
        </div>
        <div class="p-3.5 rounded-xl border border-[var(--border)] bg-[var(--card)]">
          <div class="text-xs text-[var(--muted-foreground)]">Aperti all'Orario Selezionato</div>
          <div id="kpi-open-hour" class="text-xl font-bold text-amber-500 mt-0.5">0</div>
        </div>
        <div class="p-3.5 rounded-xl border border-[var(--border)] bg-[var(--card)]">
          <div class="text-xs text-[var(--muted-foreground)]">Aperture Serali / Teatri (dopo le 19:30)</div>
          <div id="kpi-evening" class="text-xl font-bold text-blue-500 mt-0.5">0</div>
        </div>
        <div class="p-3.5 rounded-xl border border-[var(--border)] bg-[var(--card)]">
          <div class="text-xs text-[var(--muted-foreground)]">Con Sito Web Ufficiale Diretto</div>
          <div id="kpi-websites" class="text-xl font-bold text-[var(--foreground)] mt-0.5">0</div>
        </div>
      </div>
    </section>

    <!-- ==================== VIEW 2: WEEK MATRIX (LUN-DOM) ==================== -->
    <section id="section-week" class="hidden space-y-4">
      <div class="rounded-xl border border-[var(--border)] bg-[var(--card)] p-4 shadow-sm">
        <h2 class="text-sm font-bold text-[var(--foreground)]">Pianificatore Settimanale (Colpo d'occhio Lunedì – Domenica)</h2>
        <p class="text-xs text-[var(--muted-foreground)] mt-0.5">
          A Genova molti musei civici chiudono il lunedì (mentre il Museo Diocesano, l'Acquario, il Galata, la Biblioteca Berio e De Amicis sono aperti!), e molte biblioteche di quartiere chiudono la domenica. Clicca su una colonna per filtrare quel giorno.
        </p>
        <div id="week-summary-grid" class="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2.5 mt-4"></div>
      </div>
    </section>

    <!-- ==================== VIEW 3: MONTH & SEASONAL CALENDAR ==================== -->
    <section id="section-month" class="hidden space-y-4">
      <div class="rounded-xl border border-[var(--border)] bg-[var(--card)] p-4 shadow-sm">
        <div class="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h2 class="text-sm font-bold text-[var(--foreground)]">Calendario Mensile, Stagionalità e Grandi Appuntamenti (Gennaio – Dicembre)</h2>
            <p class="text-xs text-[var(--muted-foreground)]">Seleziona un mese per vedere gli eventi ricorrenti in città e provincia, gli orari estivi/invernali e le aperture stagionali (es. Castello della Pietra).</p>
          </div>
        </div>
        <div id="month-pills" class="grid grid-cols-3 sm:grid-cols-6 lg:grid-cols-12 gap-1.5 mt-3"></div>
        <div id="month-highlights" class="mt-4 p-4 rounded-xl bg-[var(--content)] border border-[var(--border)] space-y-2"></div>
      </div>
    </section>

    <!-- ==================== VIEW 4: SAVED ITINERARY ==================== -->
    <section id="section-plan" class="hidden space-y-4">
      <div class="rounded-xl border border-[var(--border)] bg-[var(--card)] p-4 shadow-sm flex items-center justify-between">
        <div>
          <h2 class="text-sm font-bold text-[var(--foreground)]">Il Tuo Programma Personalizzato (Tappe Salvate & Racconto dei Personaggi)</h2>
          <p class="text-xs text-[var(--muted-foreground)]">Le tappe che hai aggiunto con il pulsante "+ Aggiungi al programma", complete di orari, sito web e personaggio storico collegato.</p>
        </div>
        <button onclick="clearPlan()" class="px-3 py-1.5 rounded-lg text-xs font-semibold border border-[var(--border)] hover:bg-[var(--content)]">Svuota lista</button>
      </div>
      <div id="plan-list" class="grid grid-cols-1 md:grid-cols-2 gap-3"></div>
    </section>

    <!-- ==================== RESULTS LIST & PAGINATION ==================== -->
    <section id="results-section" class="space-y-3">
      <div class="flex flex-wrap items-center justify-between gap-2">
        <div id="results-counter" class="text-xs font-semibold text-[var(--muted-foreground)]">Mostrando risultati...</div>
        <div class="flex items-center gap-2">
          <button onclick="changePage(-1)" class="px-3 py-1 rounded border border-[var(--border)] bg-[var(--card)] text-xs font-medium hover:bg-[var(--content)]">← Precedenti</button>
          <span id="page-indicator" class="text-xs font-mono">Pag. 1</span>
          <button onclick="changePage(1)" class="px-3 py-1 rounded border border-[var(--border)] bg-[var(--card)] text-xs font-medium hover:bg-[var(--content)]">Successivi →</button>
        </div>
      </div>

      <div id="cards-grid" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3.5"></div>
    </section>

  </main>

  <script>
    const ITEMS = __JSON_PAYLOAD__;

    const DAY_NAMES = ["Domenica", "Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato"];
    const MONTH_DATA = [
      { m: 1, name: "Gennaio", season: "Orario Invernale", highlights: "• 1ª Domenica del Mese: ingresso gratuito a Palazzo Reale, Palazzo Spinola e Musei Civici.\\n• Presepi storici nelle chiese, a Palazzo Rosso e al Santuario della Madonnetta fino all'Epifania.\\n• Stagione Sinfonica e Lirica al Teatro Carlo Felice e prosa al Teatro Nazionale." },
      { m: 2, name: "Febbraio", season: "Orario Invernale", highlights: "• Fioritura storica delle Camelie antiche a Villa Durazzo-Pallavicini (Pegli).\\n• Carnevale e rassegne dialettali al Teatro Rina e Gilberto Govi (Bolzaneto).\\n• Confetteria Romanengo e Marescotti di Cavo: inizia la produzione dei 'Quaresimali' genovesi di marzapane." },
      { m: 3, name: "Marzo", season: "Transizione Primavera", highlights: "• Passaggio all'orario estivo per Galata Museo del Mare (10:00–19:00 tutti i giorni).\\n• Giornate FAI di Primavera: apertura straordinaria dell'Antica Barberia Giacalone, Castello Mackenzie e ville storiche in provincia." },
      { m: 4, name: "Aprile", season: "Orario Estivo", highlights: "• Riapertura stagionale del Castello della Pietra a Vobbia (visite guidate ogni domenica e festivi 10:30–16:30).\\n• Edizione Primaverile dei Rolli Days: apertura straordinaria dei Palazzi dei Rolli UNESCO." },
      { m: 5, name: "Maggio", season: "Orario Estivo", highlights: "• Raccolta dei petali di rosa per lo Sciroppo di Rose tradizionale (Antica Farmacia Sant'Anna, Romanengo e Valle Scrivia).\\n• Sagra del Pesce di Camogli (seconda domenica di maggio) e Festa Patronale a Sori.\\n• Premio Hans Christian Andersen – Baia delle Favole a Sestri Levante (MuSel e centro storico)." },
      { m: 6, name: "Giugno", season: "Orario Estivo Prolungato", highlights: "• Apertura serale prolungata di Castello Brown a Portofino (10:00–21:00) e Parco di Villa Durazzo a Santa Margherita.\\n• Suq Festival al Porto Antico e rassegne estive all'Arena del Mare." },
      { m: 7, name: "Luglio", season: "Estate & Festival", highlights: "• Festival Internazionale del Balletto e della Musica nei Parchi di Nervi (Villa Grimaldi Fassio / Villa Serra).\\n• Aperture notturne del Parco di Villa Durazzo a Santa Margherita Ligure (fino alle 23:00).\\n• Torta dei Fieschi e rievocazioni storiche tra Lavagna e Cogorno." },
      { m: 8, name: "Agosto", season: "Estate", highlights: "• Torta dei Fieschi a Lavagna (14 agosto) attorno alla Torre Fieschi e Basilica di Santo Stefano.\\n• Notte Bianca e cinema all'aperto nei cortili di Palazzo Ducale e Villa Rossi (Sestri Ponente)." },
      { m: 9, name: "Settembre", season: "Estate / Autunno", highlights: "• Salone Nautico Internazionale di Genova e regate storiche.\\n• Festa di Nostra Signora del Suffragio a Recco (8 settembre) con spettacoli pirotecnici e stand gastronomici." },
      { m: 10, name: "Ottobre", season: "Autunno Culturale", highlights: "• Festival della Scienza (Palazzo Ducale, Biblioteca De Amicis, Galata, Museo Doria).\\n• Edizione Autunnale dei Rolli Days e Premio Internazionale di Violino 'Nicolò Paganini' (Palazzo Tursi e Carlo Felice).\\n• Ultimo mese di apertura stagionale del Castello della Pietra a Vobbia." },
      { m: 11, name: "Novembre", season: "Orario Invernale", highlights: "• Domenica 1 Novembre: 1ª Domenica del Mese (#DomenicalMuseo) con ingresso gratuito nei musei statali (Palazzo Reale, Palazzo Spinola) e civici per residenti.\\n• Visite monumentali al Cimitero Monumentale di Staglieno (sculture del Realismo borghese).\\n• Pieno cartellone teatrale al Carlo Felice, Ivo Chiesa, Gustavo Modena, Politeama e Teatro Sociale di Camogli." },
      { m: 12, name: "Dicembre", season: "Festività & Tradizione", highlights: "• Apertura domenicale straordinaria delle Botteghe Storiche (Romanengo, Viganotti, Cavo, Torielli, Antica Farmacia Sant'Anna).\\n• Cerimonia del Confeugo a Palazzo Ducale e mostra del Pandolce Genovese." }
    ];

    let currentHorizon = "day";
    let selectedDay = 0; // Default Sunday (since current date is Sunday Nov 1, 2026)
    let selectedHour = 11.0;
    let selectedMonth = 11; // November
    let filterOnlyOpenAtHour = false;
    let filterFirstSunday = false;
    let currentPage = 1;
    const PAGE_SIZE = 24;
    let filteredList = [];
    let savedPlan = new Set();

    function initSelects() {
      const comuniCounts = {};
      ITEMS.forEach(it => { comuniCounts[it.c] = (comuniCounts[it.c] || 0) + 1; });
      const sel = document.getElementById("comune-select");
      Object.keys(comuniCounts).sort().forEach(c => {
        const opt = document.createElement("option");
        opt.value = c;
        opt.textContent = `${c} (${comuniCounts[c]})`;
        sel.appendChild(opt);
      });
      renderMonthPills();
      renderMonthHighlights();
      renderWeekSummary();
      applyFilters();
    }

    function isOpenOnDay(item, dayIndex) {
      if (!item.mo.includes(selectedMonth)) return false;
      if (filterFirstSunday && dayIndex === 0 && item.f1 === 1) return true;
      return item.d.includes(dayIndex);
    }

    function isOpenAtHour(item, dayIndex, hourVal) {
      if (!isOpenOnDay(item, dayIndex)) return false;
      if (!item.h || item.h.length === 0) return true;
      return item.h.some(r => hourVal >= r[0] && hourVal <= r[1]);
    }

    function setHorizon(h) {
      currentHorizon = h;
      ["day", "week", "month", "plan"].forEach(t => {
        const btn = document.getElementById("tab-" + t);
        const sec = document.getElementById("section-" + t);
        if (t === h) {
          btn.className = "px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-[var(--primary)] text-[var(--primary-foreground)] transition-all flex items-center gap-1.5";
          sec.classList.remove("hidden");
        } else {
          btn.className = "px-3.5 py-1.5 text-xs font-semibold rounded-lg text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-all flex items-center gap-1.5";
          sec.classList.add("hidden");
        }
      });
      document.getElementById("results-section").classList.toggle("hidden", h === "plan");
      if (h === "week") renderWeekSummary();
      if (h === "plan") renderPlanList();
      applyFilters();
    }

    function selectDay(d) {
      selectedDay = d;
      document.querySelectorAll(".day-pill").forEach(btn => {
        if (parseInt(btn.dataset.day) === d) {
          btn.className = "day-pill px-3 py-1.5 rounded-lg text-xs font-semibold bg-[var(--primary)] text-[var(--primary-foreground)]";
        } else {
          btn.className = "day-pill px-3 py-1.5 rounded-lg text-xs font-semibold border border-[var(--border)] bg-[var(--background)]";
        }
      });
      currentPage = 1;
      applyFilters();
    }

    function updateHourSlider(val) {
      selectedHour = parseFloat(val);
      const hrs = Math.floor(selectedHour);
      const mins = (selectedHour % 1) === 0.5 ? "30" : "00";
      document.getElementById("hour-display").textContent = `${String(hrs).padStart(2, '0')}:${mins}`;
      applyFilters();
    }

    function toggleOpenAtHour() {
      filterOnlyOpenAtHour = !filterOnlyOpenAtHour;
      const btn = document.getElementById("btn-filter-open-now");
      if (filterOnlyOpenAtHour) {
        btn.className = "px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-600 text-white";
      } else {
        btn.className = "px-3 py-1.5 rounded-lg text-xs font-semibold border border-[var(--border)] bg-[var(--background)] text-[var(--foreground)]";
      }
      currentPage = 1;
      applyFilters();
    }

    function toggleFirstSunday() {
      filterFirstSunday = !filterFirstSunday;
      const btn = document.getElementById("btn-filter-1st-sun");
      if (filterFirstSunday) {
        selectedDay = 0;
        selectDay(0);
        btn.className = "px-3 py-1.5 rounded-lg text-xs font-semibold bg-blue-600 text-white";
      } else {
        btn.className = "px-3 py-1.5 rounded-lg text-xs font-semibold border border-[var(--border)] bg-[var(--background)] text-[var(--foreground)]";
      }
      currentPage = 1;
      applyFilters();
    }

    function setQuickToday() {
      selectedMonth = 11;
      selectedDay = 0; // Sunday Nov 1, 2026
      filterFirstSunday = true;
      document.getElementById("btn-filter-1st-sun").className = "px-3 py-1.5 rounded-lg text-xs font-semibold bg-blue-600 text-white";
      selectDay(0);
      renderMonthPills();
      renderMonthHighlights();
    }

    function applyFilters() {
      const q = document.getElementById("search-input").value.trim().toLowerCase();
      const com = document.getElementById("comune-select").value;
      const mac = document.getElementById("macro-select").value;
      const onlyWeb = document.getElementById("only-web").checked;

      let baseMatches = ITEMS.filter(it => {
        if (com !== "ALL" && it.c !== com) return false;
        if (mac !== "ALL" && !it.m.startsWith(mac)) return false;
        if (onlyWeb && !it.w) return false;
        if (!it.mo.includes(selectedMonth)) return false;
        if (q) {
          const hay = `${it.n} ${it.c} ${it.s} ${it.a} ${it.e} ${it.p}`.toLowerCase();
          if (!hay.includes(q)) return false;
        }
        return true;
      });

      // Update KPIs for selectedDay
      const openDayCount = baseMatches.filter(it => isOpenOnDay(it, selectedDay)).length;
      const openHourCount = baseMatches.filter(it => isOpenAtHour(it, selectedDay, selectedHour)).length;
      const eveCount = baseMatches.filter(it => isOpenOnDay(it, selectedDay) && it.eve === 1).length;
      const webCount = baseMatches.filter(it => Boolean(it.w)).length;

      document.getElementById("kpi-open-day").textContent = openDayCount;
      document.getElementById("kpi-open-hour").textContent = openHourCount;
      document.getElementById("kpi-evening").textContent = eveCount;
      document.getElementById("kpi-websites").textContent = webCount;

      if (filterFirstSunday) {
        baseMatches = baseMatches.filter(it => it.f1 === 1 || (it.m.startsWith("2.") && isOpenOnDay(it, 0)));
      } else if (filterOnlyOpenAtHour) {
        baseMatches = baseMatches.filter(it => isOpenAtHour(it, selectedDay, selectedHour));
      }

      filteredList = baseMatches;
      renderCards();
    }

    function renderCards() {
      const grid = document.getElementById("cards-grid");
      grid.innerHTML = "";

      const totalPages = Math.max(1, Math.ceil(filteredList.length / PAGE_SIZE));
      if (currentPage > totalPages) currentPage = totalPages;

      const start = (currentPage - 1) * PAGE_SIZE;
      const pageItems = filteredList.slice(start, start + PAGE_SIZE);

      document.getElementById("results-counter").textContent =
        `Trovati ${filteredList.length} luoghi (${DAY_NAMES[selectedDay]}, ore ${document.getElementById("hour-display").textContent}) — Pagina ${currentPage} di ${totalPages}`;
      document.getElementById("page-indicator").textContent = `${currentPage} / ${totalPages}`;

      pageItems.forEach(it => {
        const openDay = isOpenOnDay(it, selectedDay);
        const openNow = isOpenAtHour(it, selectedDay, selectedHour);
        const inPlan = savedPlan.has(it.id);

        let statusBadge = "";
        if (openNow) {
          statusBadge = `<span class="px-2 py-0.5 rounded-full text-xs font-bold bg-emerald-500/15 text-emerald-500 border border-emerald-500/30">Aperto alle ${document.getElementById("hour-display").textContent}</span>`;
        } else if (openDay) {
          statusBadge = `<span class="px-2 py-0.5 rounded-full text-xs font-semibold bg-amber-500/15 text-amber-500 border border-amber-500/30">Aperto ${DAY_NAMES[selectedDay]} (altro orario)</span>`;
        } else {
          statusBadge = `<span class="px-2 py-0.5 rounded-full text-xs font-semibold bg-red-500/15 text-red-400 border border-red-500/30">Chiuso ${DAY_NAMES[selectedDay]}</span>`;
        }

        // Day badges L M M G V S D
        const dayOrder = [1, 2, 3, 4, 5, 6, 0];
        const dayLetters = ["L", "M", "M", "G", "V", "S", "D"];
        const dayDots = dayOrder.map((dIdx, i) => {
          const active = isOpenOnDay(it, dIdx);
          const isCurr = dIdx === selectedDay;
          return `<span class="w-5 h-5 rounded text-xs flex items-center justify-center font-bold ${
            active
              ? (isCurr ? 'bg-emerald-600 text-white ring-2 ring-amber-400' : 'bg-emerald-500/20 text-emerald-500')
              : 'bg-[var(--background)] text-[var(--muted-foreground)] opacity-40'
          }">${dayLetters[i]}</span>`;
        }).join("");

        const esc = s => String(s ?? "").replace(/[&<>"']/g, m => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[m]));
        const safeHref = /^https?:\/\//i.test(String(it.w ?? "").trim()) ? it.w.trim() : "";
        const card = document.createElement("div");
        card.className = "rounded-xl border border-[var(--border)] bg-[var(--card)] p-4 shadow-sm flex flex-col justify-between gap-3 hover:border-[var(--primary)] transition-all";
        card.innerHTML = `
          <div class="space-y-2">
            <div class="flex items-start justify-between gap-2">
              <span class="text-xs font-bold uppercase tracking-wider text-amber-500">${esc(it.c)} • ${esc((it.m || "").split('.')[1] || "")}</span>
              ${statusBadge}
            </div>
            <h3 class="text-base font-bold text-[var(--foreground)] leading-snug">${esc(it.n)}</h3>
            ${it.a ? `<div class="text-xs text-[var(--muted-foreground)]">📍 ${esc(it.a)}</div>` : ""}
            
            <div class="p-2.5 rounded-lg bg-[var(--content)] border border-[var(--border)] space-y-1">
              <div class="text-xs font-semibold text-[var(--foreground)]">🕒 ${esc(it.o)}</div>
              <div class="flex items-center gap-1 pt-1">${dayDots}</div>
            </div>

            ${it.e ? `<p class="text-xs text-[var(--muted-foreground)] leading-relaxed">✨ <strong class="text-[var(--foreground)]">Eventi & Servizi:</strong> ${esc(it.e)}</p>` : ""}
            ${it.p ? `<div class="text-xs px-2.5 py-1 rounded bg-blue-500/10 border border-blue-500/25 text-blue-400 font-medium">🏛️ Personaggio collegato: <strong>${esc(it.p)}</strong></div>` : ""}
          </div>

          <div class="pt-2 border-t border-[var(--border)] flex flex-wrap items-center justify-between gap-2">
            <div class="flex items-center gap-2">
              ${safeHref ? `<a href="${esc(safeHref)}" target="_blank" rel="noopener" class="px-2.5 py-1 rounded-md text-xs font-semibold bg-[var(--primary)] text-[var(--primary-foreground)] hover:opacity-90">Sito Web ↗</a>` : `<span class="text-xs text-[var(--muted-foreground)]">Sito non censito</span>`}
              ${it.t ? `<span class="text-xs text-[var(--muted-foreground)] font-mono">📞 ${esc(it.t)}</span>` : ""}
            </div>
            <button onclick="togglePlanItem(${Number(it.id)})" class="px-2.5 py-1 rounded-md text-xs font-semibold border ${
              inPlan ? 'border-amber-500 bg-amber-500 text-white' : 'border-[var(--border)] bg-[var(--background)] text-[var(--foreground)] hover:bg-[var(--content)]'
            }">
              ${inPlan ? '✓ Nel Programma' : '+ Programma'}
            </button>
          </div>
        `;
        grid.appendChild(card);
      });
    }

    function changePage(delta) {
      const totalPages = Math.max(1, Math.ceil(filteredList.length / PAGE_SIZE));
      currentPage = Math.min(totalPages, Math.max(1, currentPage + delta));
      renderCards();
      window.scrollTo({ top: 0, behavior: "smooth" });
    }

    function renderWeekSummary() {
      const container = document.getElementById("week-summary-grid");
      container.innerHTML = "";
      const order = [1, 2, 3, 4, 5, 6, 0];
      order.forEach(dIdx => {
        const openItems = ITEMS.filter(it => isOpenOnDay(it, dIdx));
        const libs = openItems.filter(it => it.m.startsWith("1.")).length;
        const mus = openItems.filter(it => it.m.startsWith("2.")).length;
        const thea = openItems.filter(it => it.m.startsWith("3.")).length;
        const shops = openItems.filter(it => it.m.startsWith("6.")).length;

        const box = document.createElement("div");
        box.onclick = () => { selectDay(dIdx); setHorizon("day"); };
        box.className = `p-3 rounded-xl border cursor-pointer transition-all ${
          selectedDay === dIdx ? 'border-amber-500 bg-[var(--content)]' : 'border-[var(--border)] bg-[var(--background)] hover:bg-[var(--content)]'
        }`;
        box.innerHTML = `
          <div class="text-xs font-bold text-[var(--foreground)]">${DAY_NAMES[dIdx]}</div>
          <div class="text-lg font-bold text-emerald-500 mt-0.5">${openItems.length} aperti</div>
          <div class="mt-2 space-y-0.5 text-xs text-[var(--muted-foreground)]">
            <div>📚 Biblioteche: <strong>${libs}</strong></div>
            <div>🖼️ Musei: <strong>${mus}</strong></div>
            <div>🎭 Teatri/Cinema: <strong>${thea}</strong></div>
            <div>🏺 Botteghe/Locali: <strong>${shops}</strong></div>
          </div>
        `;
        container.appendChild(box);
      });
    }

    function renderMonthPills() {
      const container = document.getElementById("month-pills");
      container.innerHTML = "";
      MONTH_DATA.forEach(mObj => {
        const btn = document.createElement("button");
        btn.onclick = () => {
          selectedMonth = mObj.m;
          renderMonthPills();
          renderMonthHighlights();
          applyFilters();
        };
        btn.className = `px-2.5 py-2 rounded-lg text-xs font-semibold border transition-all ${
          selectedMonth === mObj.m
            ? 'bg-[var(--primary)] text-[var(--primary-foreground)] border-[var(--primary)]'
            : 'bg-[var(--background)] text-[var(--foreground)] border-[var(--border)] hover:bg-[var(--content)]'
        }`;
        btn.textContent = mObj.name;
        container.appendChild(btn);
      });
    }

    function renderMonthHighlights() {
      const mObj = MONTH_DATA.find(x => x.m === selectedMonth);
      const box = document.getElementById("month-highlights");
      const lines = mObj.highlights.split("\\n").map(l => `<div class="text-xs text-[var(--foreground)]">${l}</div>`).join("");
      box.innerHTML = `
        <div class="flex items-center justify-between">
          <span class="text-sm font-bold text-amber-500">Calendario di ${mObj.name} — ${mObj.season}</span>
          <span class="text-xs text-[var(--muted-foreground)]">Clicca sui filtri in alto per esplorare i luoghi attivi a ${mObj.name}</span>
        </div>
        <div class="space-y-1 mt-1">${lines}</div>
      `;
    }

    function togglePlanItem(id) {
      if (savedPlan.has(id)) {
        savedPlan.delete(id);
      } else {
        savedPlan.add(id);
      }
      document.getElementById("plan-count-badge").textContent = savedPlan.size;
      renderCards();
      if (currentHorizon === "plan") renderPlanList();
    }

    function clearPlan() {
      savedPlan.clear();
      document.getElementById("plan-count-badge").textContent = "0";
      renderPlanList();
      renderCards();
    }

    function renderPlanList() {
      const container = document.getElementById("plan-list");
      container.innerHTML = "";
      if (savedPlan.size === 0) {
        container.innerHTML = `<div class="col-span-2 p-6 rounded-xl border border-[var(--border)] bg-[var(--card)] text-center text-xs text-[var(--muted-foreground)]">Nessuna tappa ancora salvata. Clicca su "+ Programma" su qualsiasi scheda per costruire il tuo itinerario giornaliero o settimanale!</div>`;
        return;
      }
      const planItems = ITEMS.filter(it => savedPlan.has(it.id));
      planItems.forEach((it, idx) => {
        const esc = s => String(s ?? "").replace(/[&<>"']/g, m => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[m]));
        const safeHref = /^https?:\/\//i.test(String(it.w ?? "").trim()) ? it.w.trim() : "";
        const div = document.createElement("div");
        div.className = "p-4 rounded-xl border border-amber-500/40 bg-[var(--card)] flex flex-col justify-between gap-2";
        div.innerHTML = `
          <div>
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-amber-500">Tappa ${idx + 1} • ${esc(it.c)}</span>
              <button onclick="togglePlanItem(${Number(it.id)})" class="text-xs text-red-400 hover:underline">Rimuovi</button>
            </div>
            <h4 class="text-base font-bold text-[var(--foreground)] mt-0.5">${esc(it.n)}</h4>
            <div class="text-xs text-[var(--muted-foreground)] mt-0.5">📍 ${esc(it.a || it.c)}</div>
            <div class="text-xs font-semibold text-[var(--foreground)] mt-1.5">🕒 ${esc(it.o)}</div>
            <p class="text-xs text-[var(--muted-foreground)] mt-1">${esc(it.e)}</p>
            ${it.p ? `<div class="mt-2 text-xs text-blue-400 font-medium">🏛️ Personaggio per la tua Storia: <strong>${esc(it.p)}</strong></div>` : ""}
          </div>
          <div class="pt-2 border-t border-[var(--border)] flex items-center justify-between">
            ${safeHref ? `<a href="${esc(safeHref)}" target="_blank" rel="noopener" class="text-xs font-semibold text-[var(--primary)] underline">Apri Sito Ufficiale ↗</a>` : `<span></span>`}
            <span class="text-xs font-mono text-[var(--muted-foreground)]">${esc(it.t || "")}</span>
          </div>
        `;
        container.appendChild(div);
      });
    }

    initSelects();
  </script>
  <footer class="px-6 py-4 border-t border-[var(--border)] text-center text-xs text-[var(--muted-foreground)]">
    Dati geografici e toponimi: © OpenStreetMap contributors (ODbL 1.0) · Wikidata (CC0).
  </footer>
</body>
</html>
"""

from genova_outings.vanilla_css import VANILLA_CSS
from genova_outings.html_utils import render_shared_nav
final_html = html_template.replace("__VANILLA_CSS__", VANILLA_CSS).replace("__SHARED_NAV__", render_shared_nav("dashboard")).replace("__JSON_PAYLOAD__", json_payload)

with open(f"{_DATA_DIR}/dashboard_genova_provincia.html", "w", encoding="utf-8") as f:
    f.write(final_html)

print("Generated /Users/dany/genova/dashboard_genova_provincia.html successfully! Size:", len(final_html) // 1024, "KB")
