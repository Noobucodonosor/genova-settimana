## 2026-11-04T11:05:24Z
[Message] timestamp=2026-11-04T11:05:24Z sender=ea549bc9-720f-4415-ada7-07a80ee3c531 priority=MESSAGE_PRIORITY_HIGH content=You are a Teamwork Worker implementing Milestone 2: Interactive Selector, Web UI, and Plain-Writing WhatsApp Formatter Engine for the Genova Weekly Informal Outings tool.

Your working directory is:
/workspace/genova/.agents/teamwork/worker_milestone_2/

MANDATORY FIRST STEP:
Read the user request document at:
/workspace/genova/.agents/teamwork/ORIGINAL_REQUEST.md

BACKGROUND CONTEXT:
Read:
- /workspace/genova/.agents/teamwork/PROJECT.md
- /workspace/genova/.agents/teamwork/explorer_interaction_plainwriting/handoff.md
- /workspace/genova/.agents/teamwork/worker_remediation_m1/handoff.md

EXCLUSIVELY OWNED FILES:
You own and will implement:
1. `genova_outings/validator.py`:
   - `validate_plain_writing(text: str) -> Tuple[bool, List[str]]`: Automated validation checking for:
     - Absolute zero em-dashes (`\u2014`), en-dashes (`\u2013`), horizontal bars (`\u2015`), figure dashes (`\u2012`), small em-dashes (`\ufe58`).
     - Absolute zero occurrences of the word "date" (case-insensitive word boundary `\bdate\b`) or romantic phrasing ("appuntamento romantico", "uscita a due", "serata galante").
     - Absolute zero marketing buzzwords / puffery ("imperdibile", "splendido", "magico", "esperienza unica", "mozzafiato").
     - Valid WhatsApp formatting: single asterisk bolding `*text*` (no `**`), no markdown links `[text](url)` (must be raw `https://`), no `#` headers.
   - `sanitize_for_whatsapp(text: str) -> str`: Helper stripping forbidden characters, dashes, and buzzwords.
2. `genova_outings/formatter.py`:
   - `format_whatsapp_message(selected_options: List[OutingOption], tone: str = "amichevole") -> str`:
     - Friend-to-friend informal tone in Italian ("Ciao! Ho visto queste cose carine per questa settimana a Genova se ti va di fare un salto...").
     - Discrete category emoji (🎬, 🏛️, 🌿, 📚, 🎭, 🎶, ☕).
     - Bolded titles (`*Titolo*`), venue and zone, day/time slot, and clean raw URL without trailing punctuation.
     - Automatically runs `validate_plain_writing()` on the result before returning.
3. `genova_outings/selector.py`:
   - Terminal interactive selector with checkbox toggling `[x] / [ ]`:
     - Allows viewing the complete catalog of options.
     - Multi-selection support: toggle numbers (e.g. `1,3`, `+2`, `-1`, `all`, `none`, `cat cinema`, `done`, `preview`).
     - Headless / programmatic selection helpers for CLI flags (`--select 1,2`, `--all`, `--category cinema`).
4. `genova_outings/web_ui.py`:
   - Optional lightweight local web UI running via Python standard library `http.server` on localhost:8765:
     - HTML/CSS/JS frontend showing cards with checkboxes, category filter pills, clickable official links, real-time WhatsApp message preview, and 1-click clipboard copy (`navigator.clipboard`).
     - Includes API endpoints `/api/catalog` and `/api/format` to generate WhatsApp messages dynamically.
5. `genova_outings/__init__.py`:
   - Export public functions: `format_whatsapp_message`, `validate_plain_writing`, `interactive_select`, `start_web_ui`.
6. Unit tests:
   - `tests/test_validator.py`, `tests/test_formatter.py`, `tests/test_selector.py`.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

VERIFICATION REQUIRED:
Execute:
- `python3 -m unittest discover tests`
- `python3 run_tests.py -v`
Verify that all Milestone 2 unit tests and all E2E Tier 1-4 tests pass.

DELIVERABLES:
1. Implemented code in `genova_outings/` and tests.
2. Write `/workspace/genova/.agents/teamwork/worker_milestone_2/handoff.md`.
3. Update `/workspace/genova/.agents/teamwork/worker_milestone_2/progress.md`.
4. Send completion message to orchestrator with summary and handoff path.
