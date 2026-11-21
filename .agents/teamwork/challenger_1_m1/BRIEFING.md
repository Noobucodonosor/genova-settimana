# BRIEFING — 2026-11-04T10:45:00Z

## Mission
Adversarially stress-test Milestone 1 (Core Catalog & Live Verification Engine) of `genova_outings` across closure blacklisting, character sanitization, network resilience, edge-case category filtering, and concurrency.

## 🔒 My Identity
- Archetype: empirical-challenger
- Roles: critic, specialist
- Working directory: /Users/dany/genova/.agents/teamwork/challenger_1_m1
- Original parent: ea549bc9-720f-4415-ada7-07a80ee3c531
- Milestone: milestone_1
- Instance: 1 of 1

## 🔒 Key Constraints
- Review-only / challenger — empirical verification through test scripts
- Do NOT silently modify implementation code; report findings for worker/orchestrator
- Empirically execute all test cases; do not rely on assumptions

## Current Parent
- Conversation ID: ea549bc9-720f-4415-ada7-07a80ee3c531
- Updated: not yet

## Review Scope
- **Files reviewed**: `genova_outings/models.py`, `genova_outings/catalog.py`, `genova_outings/verifier.py`, `tests/`
- **Interface contracts**: `/Users/dany/genova/.agents/teamwork/PROJECT.md`, `/Users/dany/genova/.agents/teamwork/ORIGINAL_REQUEST.md`
- **Review criteria**: Negative closure robustness, dash/unicode sanitization, network/timeout handling, category filtering edge cases, concurrent probing resilience.

## Attack Surface
- **Hypotheses tested**:
  1. Negative closure bypass via whitespace, separators, underscores, and URL encodings.
  2. Character sanitization breaks on multi-dashes, edge dashes, and unlisted unicode dashes.
  3. URL cleaner crashes on non-string inputs and fails to strip quotes/parentheses.
  4. Network prober crashes on 404, 500, NXDOMAIN, and timeouts.
  5. Category filtering breaks on supported synonyms and whitespace.
  6. Civic museum closure helper logic correctness across weekdays.
  7. Deduplication collision across multiple events at the same venue.
  8. Concurrency contention and thread safety under rapid parallel requests.
- **Vulnerabilities found**:
  1. **Villa Croce Blacklist Bypass** (`verifier.py:148-158`): 13 whitespace, separator, and URL variations (`"Villa  Croce"`, `"Villa - Croce"`, `"Villa_Croce"`, `"villa%20croce"`, etc.) bypass blacklist and are validated by `verify_outing`.
  2. **Civic Museum Weekday Logic Bug** (`verifier.py:169-181`): `is_civic_museum_closed_on_day` ignores `day_of_week` and returns `True` for every day of the week (including weekends).
  3. **Coarse Deduplication Drops Real Events** (`catalog.py:721-726`): Deduplicating strictly by `(venue, category)` silently drops `ducale_world_press_photo` and 18 other valid options.
  4. **Synonym Filter Breakdown** (`catalog.py:750-752`, `models.py:186`): `get_weekly_catalog(category="film")` fails to use `OutingCategory.from_str`, returning 0 items.
  5. **Sanitization Defects** (`verifier.py:114-124`, `127-136`): 3+ dashes produce `::`, quotes are not stripped in `clean_url`, and non-string URL raises `AttributeError`.
- **Untested angles**:
  - Live scraping of dynamically rendered JavaScript pages (future milestone).

## Loaded Skills
- None requested in dispatch.

## Key Decisions Made
- Verdict: **REQUEST_CHANGES** due to confirmed high-severity vulnerabilities in negative blacklist bypass, museum closure logic, and deduplication event dropping.
- Added comprehensive adversarial suite `tests/test_adversarial_m1.py` with 20 regression tests documenting all findings.

## Artifact Index
- `/Users/dany/genova/.agents/teamwork/challenger_1_m1/DISPATCH.md` — Inbound message
- `/Users/dany/genova/.agents/teamwork/challenger_1_m1/progress.md` — Liveness & status tracking
- `/Users/dany/genova/.agents/teamwork/challenger_1_m1/handoff.md` — Final adversarial report with REQUEST_CHANGES verdict
- `/Users/dany/genova/tests/test_adversarial_m1.py` — Adversarial test suite
