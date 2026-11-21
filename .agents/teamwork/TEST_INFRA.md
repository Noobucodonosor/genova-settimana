# E2E Test Infra: Genova Weekly Informal Outings Tool

## Test Philosophy
- **Requirement-Driven & Opaque-Box**: Tests are derived strictly from `ORIGINAL_REQUEST.md` (R1-R5, Acceptance Criteria), treating the tool from the perspective of an end user and external caller.
- **Strict Plain-Writing & Integrity Assurance**: Binary automated assertions against long dashes (`\u2014`, `\u2013`), banned romantic words (`date`, `appuntamento`, `romantico`), and promotional buzzwords.
- **Zero Hallucination & Authentic Source Verification**: Verification that all returned venues exist, have valid URLs, and active current-week schedules.

## Feature Inventory
| # | Feature | Source (Requirement) | Tier 1 (Min 5) | Tier 2 (Min 5) | Tier 3 (Pairwise) | Tier 4 (Scenario) |
|---|---------|----------------------|:--------------:|:--------------:|:-----------------:|:-----------------:|
| F1 | Local Dataset Aggregation | R1, AC-1 | 5 | 5 | ✓ | ✓ |
| F2 | Live Verification & Closure Filter | R1, R5, AC-2 | 5 | 5 | ✓ | ✓ |
| F3 | Unified Outing Catalog & Schema | R1, R5, AC-1, AC-2 | 5 | 5 | ✓ | ✓ |
| F4 | Interactive Selector (REPL/Web/CLI) | R2, AC-1 | 5 | 5 | ✓ | ✓ |
| F5 | WhatsApp Plain-Writing Formatter | R3, R4, AC-3, AC-4 | 5 | 5 | ✓ | ✓ |
| F6 | Automated Plain-Writing Validator | R4, AC-4 | 5 | 5 | ✓ | ✓ |
| F7 | Main CLI & Output Integration | R1, R2, R3, AC-1, AC-3 | 5 | 5 | ✓ | ✓ |

## Test Architecture
- **Test Runner**: Invoked via standard `python3 run_tests.py` or `python3 -m unittest discover tests`.
- **Directory**: `tests/`
  - `test_e2e_tier1_features.py`: >= 35 unit/feature tests (isolated happy-path per feature).
  - `test_e2e_tier2_boundaries.py`: >= 35 boundary, corner-case, and negative input tests.
  - `test_e2e_tier3_pairwise.py`: >= 7 pairwise combination tests across feature modules.
  - `test_e2e_tier4_scenarios.py`: >= 5 full end-to-end user journey scenarios.
- **Pass/Fail Semantics**: All test suites must exit with return code 0. Any failure, warning assertion, or detected dash causes non-zero exit.

## Real-World Application Scenarios (Tier 4)
| # | Scenario | Features Exercised | Expected Outcome |
|---|----------|--------------------|------------------|
| S1 | Cinema d'essai evening with friends | F1, F2, F3, F4, F5, F6, F7 | Extracts active Sivori/Nickelodeon movies, user selects 1 cinema, outputs ready WhatsApp text with film name, venue, time, link. |
| S2 | Weekend afternoon art exhibition + walk | F1, F2, F3, F4, F5, F6, F7 | Selects Palazzo Ducale exhibition and Spianata Castelletto walk; checks closure filter on Villa Croce; formats combined message. |
| S3 | Study session & informal quiet reading | F1, F3, F4, F5, F6, F7 | Selects Berio or De Amicis library, generates friendly suggestion message with opening hours and addresses. |
| S4 | Live music / cultural club night out | F1, F2, F3, F4, F5, F6, F7 | Filters Count Basie or La Claque weekend concerts, selects Friday show, formats WhatsApp text with Arci entry note and link. |
| S5 | Quick multi-category selection via CLI flags | F1, F2, F3, F4, F5, F6, F7 | Headless command `--select 1,3,5 --output msg.txt`, outputs validated message and writes to disk with zero user prompts. |

## Coverage Thresholds
- **Tier 1**: ≥ 35 test cases (5 per feature × 7 features)
- **Tier 2**: ≥ 35 boundary/corner test cases (5 per feature × 7 features)
- **Tier 3**: ≥ 7 pairwise interaction tests
- **Tier 4**: ≥ 5 realistic end-to-end application scenarios
- **Total Minimum Test Count**: ≥ 82 automated test cases
