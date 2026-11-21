## 2026-11-04T10:00:07Z
You are a Teamwork Explorer investigating user interaction, selection mechanics, and WhatsApp plain-writing generation for the Genova informal outings tool.

Your working directory is:
/Users/dany/genova/.agents/teamwork/explorer_interaction_plainwriting/

MANDATORY FIRST STEP:
Read the user request document at:
/Users/dany/genova/.agents/teamwork/ORIGINAL_REQUEST.md

OBJECTIVE:
Investigate requirements R2, R3, R4 and design the interaction and generation pipeline:
1. Selection Mechanism (R2):
   - Design options for user interaction to review the complete list of weekly alternatives and check/toggle options:
     - Terminal interactive CLI with curses / prompt_toolkit / questionary / inquirer / simple numbered interactive selection.
     - Optional lightweight local web UI (HTML/Python HTTP server) or terminal interactive mode.
     - Ensure the user sees all key information (category, title, venue/zone, day/time, source link) and can easily pick 1 or more options.
2. WhatsApp Message Generation (R3 & R4):
   - WhatsApp formatting rules: proper bolding (*text*), clean spacing, natural layout, subtle emoji (e.g. 🎬, 🏛️, 🌿, ☕).
   - Strict adherence to Plain Writing (/plain-writing):
     - Natural, direct, informal Italian.
     - NO long dashes (neither em-dash "—" nor en-dash "–"). Only standard commas, colons, or parentheses.
     - NO marketing buzzwords, puffery, or hype (avoid "imperdibile", "splendido", "magico", "esperienza unica").
     - ABSOLUTELY NO references to "date", "appuntamento romantico", "uscita a due", or romantic framing. It must read like an easy-going suggestion between modern friends or acquaintances ("Ecco qualche idea carina per questa settimana se ti va di fare un salto...").
     - Ready for direct copy-paste into WhatsApp.
3. Architecture & testability:
   - What interface contract should exist between the extraction/verification catalog and this selection/formatting component?
   - How can we write automated tests for plain-writing compliance (regex for dashes, ban-list for forbidden romantic/marketing terms, formatting checks)?

DELIVERABLES:
1. Write `/Users/dany/genova/.agents/teamwork/explorer_interaction_plainwriting/analysis.md`.
2. Write `/Users/dany/genova/.agents/teamwork/explorer_interaction_plainwriting/handoff.md` with:
   - CLI / UI interaction design
   - WhatsApp plain-writing templates and formatting engine design
   - Automated plain-writing validation rules & test specs.
3. Update `/Users/dany/genova/.agents/teamwork/explorer_interaction_plainwriting/progress.md`.
4. Send a message to orchestrator with summary and path to handoff.

RULES:
- Read-only exploration. Do NOT modify source files.
- Communicate via files and send_message.
