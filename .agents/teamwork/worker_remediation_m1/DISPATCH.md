## 2026-11-04T10:48:45Z
You are a Teamwork Worker implementing targeted remediation for Milestone 1 based on adversarial challenge and review findings.

Your working directory is:
/Users/dany/genova/.agents/teamwork/worker_remediation_m1/

MANDATORY FIRST STEP:
Read the user request document at:
/Users/dany/genova/.agents/teamwork/ORIGINAL_REQUEST.md

BACKGROUND & AUDIT EVIDENCE:
Carefully read the handoff reports containing the exact reproduced findings:
- /Users/dany/genova/.agents/teamwork/challenger_1_m1/handoff.md
- /Users/dany/genova/.agents/teamwork/challenger_2_m1/handoff.md
- /Users/dany/genova/.agents/teamwork/auditor_m1/handoff.md
- /Users/dany/genova/.agents/teamwork/reviewer_1_m1/handoff.md
- /Users/dany/genova/.agents/teamwork/reviewer_2_m1/handoff.md

FILES TO REMEDIATE:
- `genova_outings/verifier.py`
- `genova_outings/catalog.py`
- `genova_outings/models.py`
- `tests/test_verifier.py`, `tests/test_catalog.py`

SPECIFIC DEFECTS TO FIX:
1. Harden `is_blacklisted_venue()` in `verifier.py`:
   - Match regex `villa[\s_\-]*croce` against venue name, URL, and description (catching `villa_croce`, `villa-croce`, `villa  croce`, `villa%20croce`, and URL path slugs).
   - Add permanently closed venues: Teatro Cantero in Chiavari (`teatro cantero`, `cantero chiavari`).
   - Add inactive summer seasonal arenas in November: `circuito sul mare`, `arena sturla`.
2. Fix `is_civic_museum_closed_on_day()` in `verifier.py`:
   - Correctly check `day_of_week`. Civic museums in Genoa are ONLY closed on Mondays (`"lun"`, `"lunedi"`, `"monday"`, `0`). They are OPEN Tuesday through Sunday. Do NOT report them closed on other days.
3. Refine deduplication key in `catalog.py`:
   - Deduplicate using `(norm_venue, category, title_slug)` instead of coarse `(norm_venue, category)`.
   - Ensure distinct exhibitions at the same venue (specifically Palazzo Ducale: World Press Photo 2026, Renoir/Monet, Casa Luzzati) are ALL retained in the catalog.
4. Support Category Synonyms in `get_weekly_catalog(category=...)`:
   - Use `OutingCategory.from_str(category)` so inputs like `"film"` or `"cinema d'essai"` correctly filter to `OutingCategory.CINEMA`.
5. Sanitize `address` field in `catalog.py`:
   - Ensure `sanitize_text(address)` is called on raw addresses before creating `OutingOption`, so zero em-dashes `\u2014` or en-dashes `\u2013` appear in any field.
6. Harden `sanitize_text` in `verifier.py`:
   - Collapse multiple colons (`re.sub(r':\s*:+', ':', ...)`) so `: :` or `::` is never produced.
   - Clean quotes and handle non-string arguments safely in `clean_url`.
7. Also ensure `conftest.py` compatibility:
   - Check if `conftest.py` has alias `Verifier = verifier` or `get_weekly_catalog` export matching tests.

VERIFICATION REQUIRED:
Execute:
- `python3 -m unittest discover tests`
- `python3 run_tests.py -v`
Verify all unit, E2E, and adversarial challenge tests pass with 0 errors and 0 failures.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

DELIVERABLES:
1. Implemented fixes in `genova_outings/` and tests.
2. Write `/Users/dany/genova/.agents/teamwork/worker_remediation_m1/handoff.md`.
3. Update `/Users/dany/genova/.agents/teamwork/worker_remediation_m1/progress.md`.
4. Send completion message to orchestrator with summary and handoff path.
