# BRIEFING — 2026-11-04T10:01:00Z

## Mission
Investigate and specify authoritative, live-verifiable sources for Genova and provincia to ensure all proposed informal outing activities for the current week are authentic, currently open/active, and backed by verifiable URLs or official endpoints.

## 🔒 My Identity
- Archetype: spec_miner
- Roles: Specification Miner (Live Verification Sources)
- Working directory: /workspace/genova/.agents/teamwork/spec_miner_live_sources
- Original parent: ea549bc9-720f-4415-ada7-07a80ee3c531
- Milestone: M1_spec_mining

## 🔒 Key Constraints
- Read-only exploration and specification mining. Do NOT write application code.
- Communicate via files and send_message.
- Must verify authoritative domains and entities in Genova and provincia.
- Must formulate robust verification and web validation protocols.
- Must formulate data contract for verified entries.

## Current Parent
- Conversation ID: ea549bc9-720f-4415-ada7-07a80ee3c531
- Updated: 2026-11-04T09:59:57Z

## Task Summary
- **What to build**: Specification analysis, curated authoritative sources, verification protocols, and data contracts for live verification sources in Genova & provincia.
- **Success criteria**: Comprehensive catalog of authoritative domains and venues, live query and validation rules, schema specification for verified entries, and fallback strategies.
- **Interface contracts**: /workspace/genova/.agents/teamwork/ORIGINAL_REQUEST.md
- **Code layout**: .agents/teamwork/spec_miner_live_sources/

## Key Decisions Made
- Spec mining will probe both local datasets (crawled_urls_cache.json, tempo_libero_dataset.json, guide_aperti, etc.) and live authoritative web endpoints in Genova to verify active status and actual schedules.
- Identified negative closure constraint on Villa Croce (closed for PNRR work until further notice); added to negative filter rule.
- Identified exact canonical paths for civic libraries (/berio, /de-amicis) and cineclubs (clubamicidelcinema.it, https://www.cineclubnickelodeon.it/).
- Live probing confirmed active exhibitions at Palazzo Ducale (Renoir/Monet, World Press Photo, Casa Luzzati), Count Basie concerts (Gatto Nero, La Pausa del Duca), La Claque shows (010 Li Evito Male, omaggio De Gregori), and Giardini Luzzati (Mellow Mood).
- Finalized 4-tier validation pipeline and 13-field JSON Schema data contract.

## Artifact Index
- DISPATCH.md — Task dispatch assignment
- BRIEFING.md — Working memory and identity
- progress.md — Liveness heartbeat
- spec_analysis.md — Comprehensive analysis of live verification sources
- handoff.md — Final 5-component handoff report
