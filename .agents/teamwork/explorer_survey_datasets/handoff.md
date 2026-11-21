# Handoff Report — Survey of Datasets and Codebase for Informal Outings in Genova

**Agent**: explorer_survey_datasets  
**Recipient**: Orchestrator (ea549bc9-720f-4415-ada7-07a80ee3c531)  
**Date**: 2026-11-04T10:13:00Z  
**Working Directory**: `/workspace/genova/.agents/teamwork/explorer_survey_datasets/`  

---

## 1. Observation

Direct observations performed on local assets in `/workspace/genova`:

1. **Dataset Inventory and Sizes**:
   - `tempo_libero_payload.json` (264,774 bytes): contains dictionary with keys `['meta', 'hubs', 'comuni', 'itineraries', 'monthly_events', 'places']`.
     - `places`: 326 items (73 tier 1 flagships + 253 tier 2 destinations).
     - Breakdown by `tipo`: `abbazia`: 75, `museo`: 68, `dimora`: 56, `bottega`: 49, `biblioteca`: 32, `natura`: 31, `teatro`: 15.
     - Coverage: exactly 67 municipalities represented.
     - `itineraries`: 16 multi-stage routes (e.g., `it_botteghe_caruggi`, `it_salva_lunedi`, `it_nervi_boccadasse`, `it_portofino_ville`).
     - `monthly_events`: 31 events with `day_rule` and descriptions.
   - `tempo_libero_dataset.json` (339,800 bytes): 340 items with fields `['nome', 'comune', 'zona', 'tipo', 'lat', 'lon', 'indoor', 'treno', 'trasporto_info', 'durata_min', 'costo', 'free_1st_sun', 'days', 'slots', 'months', 'orari', 'pitch', 'personaggio', 'url', 'tel', 'id', 'tier']`.
   - `dashboard_items.json` (1,934,618 bytes): 1,987 items with 100% population of `days_open`, `hours_range`, `orari_apertura`, `eventi_e_servizi_al_pubblico`.
   - `guida_aperti_al_pubblico_provincia_genova.json` (2,197,896 bytes): 4,251 records across 9 macro-categories.
     - Macro 1 (Biblioteche): 326 items.
     - Macro 2 (Musei): 163 items.
     - Macro 3 (Teatri, Cinema): 115 items (37 cinemas, 50 theatres).
     - Macro 4 (Palazzi, Castelli): 628 items.
     - Macro 5 (Parchi, Giardini): 278 items.
     - Macro 6 (Botteghe Storiche): 174 items.
     - Macro 9 (Istituzioni/Scuole): 2,006 items (to be excluded).
   - `esercenti_genova_provincia_db.json` (2,753,108 bytes): 4,966 records. Contains 61 independent bookstores, 8 record/music shops, 43 art/stationery shops, 36 historic confectioneries, 52 traditional sciamadde/bakeries.
   - `crawled_urls_cache.json` (393,058 bytes): 834 crawled URLs, 581 returning HTTP 200 `OK`, 118 with parsed hours, 398 with parsed events.

2. **Current Programming & Real Events Observed**:
   - `guida_aperti_al_pubblico_provincia_genova.json` contains live programming:
     - Cinema America (`https://circuitocinemagenova.com/america/`): shows at 16:00, 18:45, 21:00.
     - Cinema Sivori (`https://circuitocinemagenova.com/sivori/`): shows at 16:00, 21:15.
     - Cinema Odeon (`https://circuitocinemagenova.com/odeon/`): shows at 16:00, 18:30, 21:15.
     - Cineclub Nickelodeon (`http://www.cineclubnickelodeon.it/`): Fri 16:00/18:00, Sat 18:30/21:00, Sun 16:00/18:00.
     - Sala Mercato / Teatro Nazionale: show "Mio padre è Sylvester Stallone" running 03–08 November 2026.
     - Teatro Sociale di Camogli (`https://www.teatrosocialecamogli.it`): aperitivi in musica and concerts.
     - Museo della Filigrana a Campo Ligure (`http://www.museofiligrana.org/`): autumn schedule Fri 16:30–18:00, Sat–Sun 10:30–12:00 and 15:30–18:00.

3. **Existing Script Mechanisms**:
   - `build_tempo_libero_engine.py`: lines 46–69 define `ZONE_BY_COMUNE` (7 geographic zones), lines 71–75 define `RAIL_COMUNI` (25 rail-accessible towns), lines 78–300 define hand-curated `FLAGSHIPS`.
   - `build_dashboard_data.py`: lines 199–250 define `parse_schedule()` mapping textual opening hours into `days_open` integers (`0=Dom, 1=Lun, ..., 6=Sab`) and float hour intervals.
   - `crawl_all_websites.py`: multithreaded crawler with rate limiting and URL caching.

4. **Data Hygiene Findings**:
   - 0 dummy, lorem-ipsum, or placeholder texts in `tempo_libero_payload.json` or `dashboard_items.json`.
   - Substring inspection confirmed "mastodonte" in `Mastodonte dei Giovi` caused a literal string match on "todo", but no actual placeholder tasks exist.
   - 47 URLs out of 326 in `tempo_libero_payload.json` are unreachable or flagged `OFFLINE_OR_PROTECTED` (e.g. `turismoinliguria.com` is parked). Fallback to official portals (`visitgenoa.it`, `museidigenova.it`, `teatrodellatosse.it`) is needed.

---

## 2. Logic Chain

1. *From User Requirements (R1–R5 in `ORIGINAL_REQUEST.md`)*:
   - The user needs an extraction tool for real, active, verified informal outings in Genova and its province for the current week (Wednesday 4 Nov – Sunday 8 Nov 2026), with interactive checkbox selection and plain-writing WhatsApp export without the word "date" or long dashes (`—`, `–`).
2. *From Observations 1 and 2*:
   - Local datasets already possess over 400 verified, non-cliché activities perfectly tailored to an "uscita informale moderna":
     - Cinema d'essai (Sivori, America, Nickelodeon, Odeon) with active showtimes.
     - Art exhibitions & quirky museums (Palazzo Ducale, Castello D'Albertis, Wolfsoniana, Museo Filigrana).
     - Craft workshops & historical botteghe (Luico sughero, Romanengo confetteria, Viganotti cioccolato, Farinata Sa' Pesta).
     - Open libraries with courtyards and terraces (Berio, De Amicis al Porto Antico).
     - Scenic walks & urban trails (Spianata Castelletto, Passeggiata di Nervi, Boccadasse, Parco delle Mura / Righi).
     - Independent theatres & live music clubs (La Claque / Teatro della Tosse, Sala Mercato, Sociale Camogli).
3. *From Observations 3 and 4*:
   - By reusing `parse_schedule` logic from `build_dashboard_data.py` and the `FLAGSHIPS` / `places` from `tempo_libero_payload.json` combined with the cinema/theatre records in `guida_aperti_al_pubblico_provincia_genova.json`, the extraction engine can deterministically filter candidates open on the target days of the current week (`days_open` intersecting `{0, 2, 3, 4, 5, 6}`).
   - By applying a domain fallback rule, dead links (such as squatted domains) can be safely sanitized to official cultural portals (`https://www.museidigenova.it/`, `https://www.visitgenoa.it/`, `https://circuitocinemagenova.com/`).
4. *Therefore*:
   - No external live scraping pipeline is required from scratch: the local datasets provide an authoritative baseline of candidates that can be filtered and presented in under a second.

---

## 3. Caveats

1. **Live Weather Constraints**: Weather conditions for upcoming days (Thu–Sun) determine outdoor walk suitability. Outdoor scenic walks (e.g. Spianata, Nervi, Boccadasse) should be tagged with `indoor: "out" | "in" | "mix"` so users can pick according to the forecast.
2. **Cinema Weekly Changeover**: Italian cinemas typically refresh weekly schedules on Thursdays. Crawled schedules for America, Sivori, and Odeon reflect the current week's active releases; the extraction tool should link directly to the official cinema page for real-time ticket booking.
3. **Parked URLs**: Approximately 10–15% of older tourist board links in OpenStreetMap are stale or parked. The fallback mechanism to official municipality portals (`visitgenoa.it`) is essential to prevent dead links in WhatsApp messages.

---

## 4. Conclusion

1. **Available Data Assets**: `tempo_libero_payload.json`, `guida_aperti_al_pubblico_provincia_genova.json`, `dashboard_items.json`, and `esercenti_genova_provincia_db.json` contain all necessary verified entities, addresses, hours, and descriptions.
2. **Recommended Pipeline**:
   - Create an extraction module (`extract_settimana_informale.py`) that reads `tempo_libero_payload.json` and selected records from `guida_aperti_al_pubblico_provincia_genova.json`.
   - Filter down to ~25–35 prime candidates representing 6 core categories:
     1. `cinema_essai`: Cinema d'essai & cineforum
     2. `mostre_musei`: Mostre temporanee & musei d'atmosfera
     3. `botteghe_laboratori`: Botteghe storiche, degustazioni & artigianato
     4. `passeggiate_panorami`: Passeggiate panoramiche & borghi marinari
     5. `teatri_musica`: Teatri indipendenti & musica acustica
     6. `biblioteche_chiostri`: Biblioteche aperte con chiostro o giardino
   - Save the catalog to `catalogo_uscite_settimana.json`.
3. **Interactive Selection & Output**:
   - Provide a terminal CLI with multi-select checkboxes (or numbered multi-choice) allowing the user to pick 1 to 5 options.
   - Generate WhatsApp text formatted in plain writing:
     - No long dashes (`—` or `–`).
     - No mentions of "date" or romantic pressure.
     - Clean bullet points with bold titles (`*Nome Posto*`), time, 1-line reason, and official verified link.

---

## 5. Verification Method

To independently verify the facts and conclusions in this report:

1. **Inspect Category Counts and Field Completeness**:
   ```bash
   python3 -c "
   import json
   with open('/workspace/genova/tempo_libero_payload.json') as f:
       d = json.load(f)
   print('Places count:', len(d['places']), 'Flagships:', sum(1 for p in d['places'] if p.get('tier')==1))
   with open('/workspace/genova/dashboard_items.json') as f:
       dash = json.load(f)
   print('Dashboard items with days_open:', sum(1 for x in dash if x.get('days_open')))
   "
   ```
2. **Verify Cinema & Theatre Schedules in Guida**:
   ```bash
   python3 -c "
   import json
   with open('/workspace/genova/guida_aperti_al_pubblico_provincia_genova.json') as f:
       g = json.load(f)
   cinemas = [x for x in g if x.get('sottocategoria') == 'cinema' and x.get('orari_apertura')]
   for c in cinemas[:4]:
       print(c['nome'], '|', c['sito_web'])
   "
   ```
3. **Verify Analysis Report**:
   Inspect `/workspace/genova/.agents/teamwork/explorer_survey_datasets/analysis.md` for complete data tables and architecture designs.
