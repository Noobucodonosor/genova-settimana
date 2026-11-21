## 2026-11-04T10:17:58Z
You are a Teamwork Worker implementing Milestone 1: Core Catalog & Live Verification Engine for the Genova Weekly Informal Outings tool.

Your working directory is:
/Users/dany/genova/.agents/teamwork/worker_milestone_1/

MANDATORY FIRST STEP:
Read the user request document at:
/Users/dany/genova/.agents/teamwork/ORIGINAL_REQUEST.md

BACKGROUND CONTEXT:
Read:
- /Users/dany/genova/.agents/teamwork/PROJECT.md
- /Users/dany/genova/.agents/teamwork/explorer_survey_datasets/handoff.md
- /Users/dany/genova/.agents/teamwork/spec_miner_live_sources/handoff.md
- /Users/dany/genova/.agents/teamwork/explorer_interaction_plainwriting/handoff.md

EXCLUSIVELY OWNED FILES:
You own and will implement:
- `genova_outings/__init__.py`
- `genova_outings/models.py`: Data models (`OutingCategory`, `OutingOption`, etc.) per the interface contract in `PROJECT.md`.
- `genova_outings/verifier.py`: Verification prober (HTTP reachability checks, active schedule verification, and negative filters — explicitly blacklisting closed venues such as Villa Croce which is closed for PNRR works).
- `genova_outings/catalog.py`: Aggregates records from local datasets (`tempo_libero_payload.json`, `guida_aperti_al_pubblico`, `dashboard_items.json`, `esercenti_genova_provincia_db`) and live verified endpoints (Circuito Cinema, Nickelodeon, Palazzo Ducale, Berio, De Amicis, Count Basie, La Claque, Giardini Luzzati, etc.). Filters for informal leisure/cultural outings. Sanitizes em/en-dashes from titles and descriptions. Returns `List[OutingOption]`.
- `tests/test_models.py`, `tests/test_catalog.py`, `tests/test_verifier.py`: Unit tests for Milestone 1.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

VERIFICATION REQUIREMENT:
You must run Python build/test commands to verify your code (e.g. `python3 -m unittest tests/test_models.py tests/test_catalog.py tests/test_verifier.py`). Document commands and results in your handoff report.

DELIVERABLES:
1. Implemented code in `genova_outings/` and unit tests in `tests/`.
2. Write `/Users/dany/genova/.agents/teamwork/worker_milestone_1/handoff.md` with:
   - Implemented modules and signatures
   - Build & test commands executed and results
   - Verified data hygiene and negative checks (Villa Croce excluded).
3. Update `/Users/dany/genova/.agents/teamwork/worker_milestone_1/progress.md`.
4. Send a message to orchestrator with summary and path to handoff.

## 2026-11-04T10:30:46Z
**Context**: Milestone 1 status check
**Content**: Checking in on your progress regarding Milestone 1 (Catalog & Live Verification Engine). Code and unit tests appear in genova_outings/ and tests/. Please provide an update on your test execution and the delivery of your handoff report.
**Action**: Run your unit tests, draft your handoff report, and send your completion message.
