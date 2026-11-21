# Handoff Report — Adversarial Stress-Testing: Milestone 1

**Agent**: challenger_1_m1 (critic, specialist)  
**Recipient**: Orchestrator (`ea549bc9-720f-4415-ada7-07a80ee3c531`)  
**Date**: 2026-11-04T10:45:00Z  
**Verdict**: **REQUEST_CHANGES**  
**Working Directory**: `/workspace/genova/.agents/teamwork/challenger_1_m1/`  
**Test Suite Created**: `/workspace/genova/tests/test_adversarial_m1.py`

---

## 1. Observation

Adversarial stress-testing of Milestone 1 (`genova_outings/models.py`, `genova_outings/verifier.py`, `genova_outings/catalog.py`) was executed across 5 target objective dimensions plus logic invariant checking.

### Observation 1.1: Negative Closure Blacklist Bypass (`genova_outings/verifier.py:32-60, 138-158`)
- Code:
  ```python
  def is_blacklisted_venue(name: str, description: str = "", url: str = "") -> bool:
      combined = f"{name} {description} {url}".lower()
      for banned in BLACKLISTED_SUBSTRINGS:
          if banned in combined:
              return True
  ```
  `BLACKLISTED_SUBSTRINGS` only contains exact strings `"villa croce"` and `"villa-croce"`.
- Execution:
  Tested 22 variations via `python3 -c "from genova_outings.verifier import is_blacklisted_venue..."`.
- Output:
  ```text
  [BLOCKED] name='Villa Croce' url=''
  [BLOCKED] name="Museo d'Arte Contemporanea Villa Croce" url=''
  [BLOCKED] name='biblioteca villa croce' url=''
  [BLOCKED] name='via villa croce' url=''
  [BLOCKED] name='Museo di Villa Croce' url=''
  [BYPASSED] name='Villa   Croce' url=''
  [BYPASSED] name='Villa\tCroce' url=''
  [BYPASSED] name='Villa\nCroce' url=''
  [BYPASSED] name='Villa - Croce' url=''
  [BYPASSED] name='Villa- Croce' url=''
  [BYPASSED] name='Villa -Croce' url=''
  [BYPASSED] name='Villa_Croce' url=''
  [BYPASSED] name='villacroce' url=''
  [BYPASSED] name='Villa.Croce' url=''
  [BYPASSED] name='Villa/Croce' url=''
  [BYPASSED] name='Mostra' url='https://genova.it/evento-villa_croce'
  [BYPASSED] name='Mostra' url='https://genova.it/evento/villa%20croce'
  [BYPASSED] name='Mostra' url='https://genova.it/evento?loc=villa+croce'
  ```
- Impact on `verify_outing`:
  Testing an `OutingOption` with `venue="Villa - Croce"` or `description="Mostra a Villa_Croce"` produces:
  ```text
  is_valid: True
  reason: Verified valid active outing
  ```
  The closed venue Villa Croce is validated as an active weekly outing!

### Observation 1.2: `is_civic_museum_closed_on_day` Ignores `day_of_week` (`genova_outings/verifier.py:169-181`)
- Code:
  ```python
  def is_civic_museum_closed_on_day(venue_name: str, day_of_week: int) -> bool:
      """Check if a civic museum is closed on the target day.
      In standard Python datetime weekday, Monday is 0.
      In 0-indexed Sunday systems (0=Dom, 1=Lun), Monday is 1.
      We accept both conventions: if day_of_week is in (0, 1) and matches Monday.
      """
      v_lower = venue_name.lower()
      for cm in MONDAY_CLOSED_MUSEUMS:
          if cm in v_lower:
              return True
      return False
  ```
- Tool Command:
  ```bash
  python3 -c "
  from genova_outings.verifier import is_civic_museum_closed_on_day
  for day in range(7):
      print(f'Day {day}: closed={is_civic_museum_closed_on_day(\"Musei di Strada Nuova\", day)}')
  "
  ```
- Output:
  ```text
  Day 0: closed=True
  Day 1: closed=True
  Day 2: closed=True
  Day 3: closed=True
  Day 4: closed=True
  Day 5: closed=True
  Day 6: closed=True
  ```
  The function completely omits the `day_of_week` condition and marks civic museums as closed every single day of the week, including Saturday and Sunday.

### Observation 1.3: Deduplication Key Collision Silently Drops Real Exhibitions (`genova_outings/catalog.py:721-726`)
- Code:
  ```python
  norm_venue = "".join(ch for ch in opt.venue.lower() if ch.isalnum())
  key = (norm_venue, opt.category.value)
  if key in seen_keys:
      continue
  seen_keys.add(key)
  deduped.append(opt)
  ```
- Execution:
  Audited `load_authoritative_live_options()` and `load_catalog_items()`.
- Output:
  ```text
  Authoritative live: ['ducale_mostra_impressionisti', 'ducale_world_press_photo', 'ducale_incontri_culturali']
  Deduplicated catalog: ['ducale_mostra_impressionisti', 'ducale_incontri_culturali']
  ```
  `ducale_world_press_photo` (Palazzo Ducale: World Press Photo 2026, Category: MOSTRA) is SILENTLY DROPPED from the catalog because it shares the key `("palazzoducale", "mostra")` with Impressionisti.
  Across all aggregated sources, 19 distinct events are dropped due to this overly coarse key.

### Observation 1.4: Category Filter Fails on Supported Synonyms (`genova_outings/catalog.py:750-752`, `genova_outings/models.py:186`)
- Code:
  ```python
  target_cat = category.value if isinstance(category, OutingCategory) else str(category).lower().strip()
  ```
- Output:
  ```text
  category='cinema' -> items returned: 20
  category='film'   -> items returned: 0 (despite OutingCategory.from_str('film') == OutingCategory.CINEMA)
  category='mostre' -> items returned: 0 (despite OutingCategory.from_str('mostre') == OutingCategory.MOSTRA)
  category='walk'   -> items returned: 0
  category='libri'  -> items returned: 0
  ```
  Users passing natural category synonyms supported by `models.py` receive empty catalogs.
  In `WeeklyCatalog.filter_by_category(None)`, passing `None` returns `[]` instead of all items.

### Observation 1.5: Character Sanitization & URL Cleaner Edge Cases (`genova_outings/verifier.py:114-124, 127-136`)
- Code & Outputs:
  1. Multiple dashes:
     `sanitize_text("Palazzo Ducale ——— Mostra")` produces `'Palazzo Ducale:: Mostra'` (leaves `::` because non-overlapping regex pass `re.sub(r":\s*:", ":", ...)` only handles 2 colons).
  2. Edge dashes:
     `sanitize_text("— Mostra —")` produces `': Mostra:'` (leaves dangling colons).
  3. Other unicode dashes:
     Figure dash `\u2012` and small em-dash `\ufe58` are untouched and slip through into output.
  4. Quoted URLs:
     `clean_url('"https://circuitocinemagenova.com/sivori/"')` does not strip quotation marks, causing `verify_outing` to reject the URL as invalid.
  5. URL input type:
     `clean_url(123)` raises `AttributeError: 'int' object has no attribute 'strip'`.
  6. Italian verb:
     `sanitize_text("Date una mano ai volontari")` produces `'giorni una mano ai volontari'`.

### Observation 1.6: Network Resilience & Concurrency Probing
- Tool Command:
  Stress test with 200 batch calls across 20 threads against mock & real endpoints.
- Output:
  ```text
  Stress completed in 2.20s with 0 errors across 200 batch calls.
  ```
  `probe_url_reachability` and `probe_urls_batch` degrade gracefully under 404, 500, NXDOMAIN, and connection timeout without throwing unhandled exceptions.

---

## 2. Logic Chain

1. *Requirement R5 & Acceptance Criteria (`ORIGINAL_REQUEST.md:24-25, 35-37`)*:
   - "Tutte le alternative proposte corrispondono a luoghi reali di Genova o provincia effettivamente aperti e con programmazione o orari attivi nella settimana corrente... Nel testo e nei dati generati non sono presenti dati fittizi, placeholder o allucinazioni."
2. *From Observation 1.1*:
   - Villa Croce is closed for PNRR works. Because `is_blacklisted_venue` checks unnormalized substrings, trivial real-world formatting (spaces, hyphens, underscores, URL query parameters) bypasses the filter, causing `verify_outing` to declare closed Villa Croce as `is_valid: True`.
3. *From Observation 1.2*:
   - `is_civic_museum_closed_on_day` claims major museums (Strada Nuova, D'Albertis, GAM) are closed on Saturday and Sunday because it omitted `day_of_week in (0, 1)`. Downstream selector/formatter logic relying on this helper will improperly reject weekend museum visits.
4. *From Observation 1.3*:
   - `catalog.py` deduplication uses `(venue, category)`. Major cultural institutions host multiple distinct exhibitions or screenings concurrently. Deduplication by `(venue, category)` silently discards genuine weekly highlights such as *World Press Photo 2026* at Palazzo Ducale.
5. *From Observation 1.4*:
   - `get_weekly_catalog(category="film")` ignores `OutingCategory.from_str`, returning 0 items to users requesting films.
6. *From Observation 1.5*:
   - Multiple em-dashes leave double colons `::` and leading/trailing colons, degrading plain-writing output.
7. *Therefore*:
   - Milestone 1 contains multiple logic and data-integrity defects that directly compromise catalog completeness, closure filtering, and downstream consumption.

---

## 3. Caveats

1. The core HTTP prober (`probe_url_reachability`) and concurrency handling (`probe_urls_batch`) demonstrated solid network resilience and thread safety during testing.
2. The authoritative seed list contains high-quality real venues in Genova.
3. Fixes for these defects are straightforward, localized, and do not require architectural redesign.

---

## 4. Conclusion

**Verdict: REQUEST_CHANGES**

Milestone 1 cannot be approved in its current state. The following fixes must be implemented by the worker:

1. **Fix `is_blacklisted_venue` normalization (`verifier.py`)**:
   - Normalize string before substring matching: replace all non-alphanumeric characters with spaces (`re.sub(r"[\W_]+", " ", unquote(combined))`), and check regex `re.search(r"\bvilla[\W_]*croce\b", combined)`.
2. **Fix `is_civic_museum_closed_on_day` (`verifier.py`)**:
   - Insert `if day_of_week not in (0, 1): return False` before the museum name loop.
3. **Fix deduplication key (`catalog.py`)**:
   - Change deduplication key to `(norm_venue, norm_title, opt.category.value)` so distinct events at the same venue (e.g. World Press Photo 2026 at Palazzo Ducale) are not dropped.
4. **Fix category synonym parsing (`catalog.py`, `models.py`)**:
   - In `get_weekly_catalog`, parse `category` via `OutingCategory.from_str(category).value`.
   - In `WeeklyCatalog.filter_by_category`, parse `category` via `OutingCategory.from_str(category).value` and handle `None`.
5. **Fix dash sanitization and URL cleaner (`verifier.py`)**:
   - Loop `re.sub(r":+", ":", cleaned)` or use regex `re.sub(r":(?:\s*:)+", ":", cleaned)` until collapsed, and strip leading/trailing colons.
   - Expand prohibited dashes to include `\u2012`, `\ufe58`, `\uff0d`.
   - Strip leading/trailing quotes and brackets in `clean_url(url: str)` and ensure safe type conversion (`str(url or "").strip()`).

---

## 5. Verification Method

The complete regression and adversarial test suite has been committed to:
`/workspace/genova/tests/test_adversarial_m1.py`

To independently verify all findings and test fixes:

1. **Run Adversarial Suite**:
   ```bash
   python3 -m unittest tests/test_adversarial_m1.py
   ```
   *Current status*: 20 tests pass demonstrating and confirming each observed behavior.

2. **Run Full Test Suite**:
   ```bash
   python3 -m unittest discover tests
   ```
   *Current status*: 139 tests run in ~4.7s.

3. **Post-Fix Verification Invalidation Condition**:
   - When the worker applies the requested fixes, updating the tests to assert strict blocking of all Villa Croce bypasses, retention of `ducale_world_press_photo`, and correct museum opening on day 5 (Saturday) must all pass.
