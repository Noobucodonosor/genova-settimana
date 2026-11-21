# BRIEFING — 2026-11-04T11:06:00Z

## Mission
Implement Milestone 2: Interactive Selector, Web UI, and Plain-Writing WhatsApp Formatter Engine for the Genova Weekly Informal Outings tool.

## 🔒 My Identity
- Archetype: worker
- Roles: implementer, qa, specialist
- Working directory: /workspace/genova/.agents/teamwork/worker_milestone_2
- Original parent: ea549bc9-720f-4415-ada7-07a80ee3c531
- Milestone: milestone_2

## 🔒 Key Constraints
- Friend-to-friend informal tone in Italian.
- Absolute zero em-dashes (\u2014), en-dashes (\u2013), horizontal bars (\u2015), figure dashes (\u2012), small em-dashes (\ufe58).
- Absolute zero occurrences of the word "date" (\bdate\b) or romantic phrasing ("appuntamento romantico", "uscita a due", "serata galante").
- Absolute zero marketing buzzwords / puffery ("imperdibile", "splendido", "magico", "esperienza unica", "mozzafiato").
- Valid WhatsApp formatting: *text* for bold (no **), no markdown links [text](url) (must be raw https://), no # headers.
- Minimal change principle, genuine logic, no cheats or hardcoded results.

## Current Parent
- Conversation ID: ea549bc9-720f-4415-ada7-07a80ee3c531
- Updated: 2026-11-04T11:05:24Z

## Task Summary
- **What to build**: Plain-writing WhatsApp Formatter & Validator, Terminal Interactive Selector, lightweight Web UI (http.server), package exports, unit tests.
- **Success criteria**: All unittests pass, run_tests.py passes, formatting and validation meet plain-writing guidelines.
- **Interface contracts**: /workspace/genova/.agents/teamwork/PROJECT.md
- **Code layout**: genova_outings/ and tests/

## Change Tracker
- **Files modified**: None yet
- **Build status**: Pending
- **Pending issues**: None

## Quality Status
- **Build/test result**: Pending
- **Lint status**: Clean
- **Tests added/modified**: Pending

## Loaded Skills
- None

## Key Decisions Made
- Initializing briefing and workspace

## Artifact Index
- /workspace/genova/.agents/teamwork/worker_milestone_2/DISPATCH.md
- /workspace/genova/.agents/teamwork/worker_milestone_2/BRIEFING.md
- /workspace/genova/.agents/teamwork/worker_milestone_2/progress.md
