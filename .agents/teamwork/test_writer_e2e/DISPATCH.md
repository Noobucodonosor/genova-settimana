## 2026-11-04T10:17:42Z
You are a Teamwork Test Writer responsible for the E2E Testing Track of the Genova Weekly Informal Outings tool.

Your working directory is:
/workspace/genova/.agents/teamwork/test_writer_e2e/

MANDATORY FIRST STEP:
Read the user request document at:
/workspace/genova/.agents/teamwork/ORIGINAL_REQUEST.md

BACKGROUND CONTEXT:
Read:
- /workspace/genova/.agents/teamwork/PROJECT.md
- /workspace/genova/.agents/teamwork/TEST_INFRA.md
- /workspace/genova/.agents/teamwork/explorer_interaction_plainwriting/handoff.md
- /workspace/genova/.agents/teamwork/spec_miner_live_sources/handoff.md
- /workspace/genova/.agents/teamwork/explorer_survey_datasets/handoff.md

OBJECTIVE:
Design and implement the complete, opaque-box, requirement-driven E2E test suite across Tiers 1-4 per `TEST_INFRA.md`.
You EXCLUSIVELY own:
- `tests/conftest.py` (if using pytest) or standard unittest helpers
- `tests/test_e2e_tier1_features.py` (Tier 1: Feature Coverage, >= 5 tests per feature for 7 features = >= 35 tests)
- `tests/test_e2e_tier2_boundaries.py` (Tier 2: Boundary & Corner Cases, >= 5 tests per feature for 7 features = >= 35 tests)
- `tests/test_e2e_tier3_pairwise.py` (Tier 3: Pairwise interactions across features, >= 7 tests)
- `tests/test_e2e_tier4_scenarios.py` (Tier 4: Realistic end-to-end user journeys, >= 5 scenarios)
- `run_tests.py` (Zero-dependency test runner using Python standard library `unittest` that executes all tiers and reports exit code 0 on full pass)
Total test cases must be >= 82 tests.

KEY VALIDATION CHECKS TO EMBED IN TESTS:
1. Plain-writing assertions: Fail if any em-dash `\u2014` or en-dash `\u2013` appears in WhatsApp output.
2. Anti-romance / date check: Fail if the word "date" (case-insensitive boundary) or romantic phrasing ("appuntamento romantico", "uscita galante") appears in the output.
3. Anti-buzzword check: Fail if hype words ("imperdibile", "splendido", "magico", "esperienza unica", "mozzafiato") appear.
4. Genuine data check: Assert that returned venues correspond to real Genova places, valid HTTP/HTTPS URLs, active schedules, and exclude closed venues (e.g. assert Villa Croce is NOT returned).
5. Interactive selector & CLI headless execution: Test flag `--select 1,2`, `--category`, `--output`, `--web` mode initialization.

PUBLISH TEST_READY.md:
Once the test suite and `run_tests.py` are created and verified to run, create `/workspace/genova/.agents/teamwork/TEST_READY.md` containing:
- Command to run full suite (`python3 run_tests.py`)
- Tier breakdown counts
- Verification checklist.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

DELIVERABLES:
1. Write tests in `tests/` and `run_tests.py`.
2. Write `/workspace/genova/.agents/teamwork/TEST_READY.md`.
3. Write `/workspace/genova/.agents/teamwork/test_writer_e2e/handoff.md`.
4. Update `/workspace/genova/.agents/teamwork/test_writer_e2e/progress.md`.
5. Send a message to orchestrator with summary and path to handoff.
