# BRIEFING — 2026-11-04T10:12:00Z

## Mission
Investigate interaction mechanics (CLI/TUI/Web), WhatsApp plain-writing generation, and automated validation rules for informal outings in Genova.

## 🔒 My Identity
- Archetype: explorer
- Roles: investigator, synthesizer
- Working directory: /workspace/genova/.agents/teamwork/explorer_interaction_plainwriting/
- Original parent: ea549bc9-720f-4415-ada7-07a80ee3c531
- Milestone: Interaction, Selection Mechanics & WhatsApp Plain-Writing Generation

## 🔒 Key Constraints
- Read-only investigation — do NOT implement code in src/
- Natural, direct, informal Italian for WhatsApp copy
- NO long dashes (neither em-dash "—" nor en-dash "–")
- NO marketing buzzwords/puffery ("imperdibile", "splendido", "magico", etc.)
- ABSOLUTELY NO romantic framing ("date", "appuntamento romantico", "uscita a due")
- Clean WhatsApp formatting (*bold*, natural spacing, subtle emoji)
- Standard 5-component handoff report

## Current Parent
- Conversation ID: ea549bc9-720f-4415-ada7-07a80ee3c531
- Updated: 2026-11-04T10:12:00Z

## Investigation State
- **Explored paths**:
  - `/workspace/genova/.agents/teamwork/ORIGINAL_REQUEST.md` (Requirements R2, R3, R4 and ACs 29-42)
  - `/workspace/.gemini/config/plugins/mobbin/skills/plain-writing/SKILL.md` (Core plain writing rules)
  - `/workspace/genova/tempo_libero_payload.json` (Discovered existing em-dash contamination)
  - Python runtime environment (Identified available vs missing packages)
- **Key findings**:
  - Python 3.14.3 lacks prompt_toolkit/questionary/rich; selection interface must use standard library (numbered interactive REPL or curses, plus optional local web UI via `http.server`).
  - Existing datasets contain em-dashes `—`; an automated dash sanitizer is required before WhatsApp rendering.
  - Italian "date" (plural of data) triggers romance regexes if unhandled; templates systematically use "i giorni" or "il calendario" to strictly satisfy AC 40 with zero ambiguity.
  - WhatsApp formatting rules specified (*bold*, raw URLs, subtle emoji, clean whitespace).
  - Complete `PlainWritingValidator` and test suites specified and verified.
- **Unexplored areas**: None within assigned scope (R2, R3, R4).

## Key Decisions Made
- Multi-mode selection architecture: Numbered Terminal REPL (default zero-dep) + Lightweight Local Web UI (optional visual cards with live preview & clipboard copy) + CLI argument flags (headless automation).
- 3-stage formatter pipeline: Dash/Puffery Sanitizer -> Plain Italian Friend Templating -> Automated `PlainWritingValidator`.
- Complete data contract formalized via `OutingOption` and `WeeklyCatalog`.

## Artifact Index
- `DISPATCH.md` — Initial dispatch instructions
- `BRIEFING.md` — Persistent working memory and state
- `progress.md` — Liveness heartbeat and completed tasks
- `analysis.md` — Comprehensive technical investigation report
- `handoff.md` — 5-component handoff report for downstream implementation and testing
