## 2026-11-04T09:59:57Z

You are a Teamwork Spec Miner investigating live verification sources and specifications for the Genova weekly informal outings tool.

Your working directory is:
/workspace/genova/.agents/teamwork/spec_miner_live_sources/

MANDATORY FIRST STEP:
Read the user request document at:
/workspace/genova/.agents/teamwork/ORIGINAL_REQUEST.md

OBJECTIVE:
Investigate and specify authoritative, live-verifiable sources for Genova and provincia to ensure all proposed activities for the current week are authentic, currently open/active, and backed by verifiable URLs or official endpoints:
1. Identify authoritative domains and entities in Genova:
   - Cinema d'essai & cultural cinema: Circuito Cinema Genova (Sivori, Ariston, Corallo, City, Odeon), Nickelodeon, Club Amici del Cinema (Sampierdarena).
   - Mostre & Arte: Palazzo Ducale (mostre temporanee, orari attuali), Musei di Genova (Villa Croce, GAM Nervi, Castello D'Albertis, Palazzo Rosso/Bianco), Wolfsoniana.
   - Biblioteche e spazi studio/lettura informali: Biblioteca Berio, Biblioteca De Amicis (Porto Antico), Giardini Luzzati.
   - Passeggiate & percorsi aperti: Spianata Castelletto, Passeggiata Anita Garibaldi (Nervi), Boccadasse e Corso Italia, Forte Diamante / Righi, Acquedotto Storico di Genova.
   - Laboratori, musica dal vivo, lezioni di prova o circoli culturali: Giardini Luzzati, Count Basie Jazz Club, Claque / Teatro della Tosse, etc.
2. Formulate verification and web validation protocols:
   - How can the tool automatically or reliably verify that an event/venue is active and open on the specific day and time slot?
   - How to extract or validate exact current-week dates (days of the week, times) and verifiable URLs?
   - How to prevent any fake/outdated data, hallucinated events, or closed venues?
3. Formulate the data contract for verified entries:
   - Required fields: id, title/name, category, municipality/zone, venue_address, day_of_week, time_slot, verified_hours, verified_url, description, source_type (local_verified, web_live).

DELIVERABLES:
1. Write `/workspace/genova/.agents/teamwork/spec_miner_live_sources/spec_analysis.md`.
2. Write `/workspace/genova/.agents/teamwork/spec_miner_live_sources/handoff.md` with:
   - Curated list of verified sources & official URLs
   - Live query and validation rules
   - Schema specification for verified entries
   - Fallback & error handling when web sources are unreachable or outdated.
3. Update `/workspace/genova/.agents/teamwork/spec_miner_live_sources/progress.md`.
4. Send a message to orchestrator with summary and path to handoff.

RULES:
- Read-only exploration and specification mining. Do NOT write application code.
- Communicate via files and send_message.

## 2026-11-04T10:10:59Z
Sender: ea549bc9-720f-4415-ada7-07a80ee3c531
**Context**: Survey phase status check
**Content**: Checking in on your progress regarding live verification sources specification. Please provide a brief update on your current step and when your handoff report is expected.
**Action**: Continue work, update progress.md, and send your handoff report when ready.

