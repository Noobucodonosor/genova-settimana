# ADR-0001: Pipeline ETL JSON & Restyling Editoriale Unificato (Genova Civica)

- **Stato:** Proposed
- **Data:** 2026-11-20
- **Autori:** Daniele Bertuccio, Antigravity
- **Issue Collegate:** [#1](https://github.com/Noobucodonosor/genova-settimana/issues/1), [#2](https://github.com/Noobucodonosor/genova-settimana/issues/2), [#3](https://github.com/Noobucodonosor/genova-settimana/issues/3)

---

## 1. Contesto e Problema

Le 4 pagine statiche del repository (`index.html`, `esercenti.html`, `bussola.html`, `dashboard.html`) includono dataset inlined fino a 1,68 MB, stringhe grezze da scraping (pipe multipli `|`, menu di navigazione) e stili dark-mode prototipali con emoji nei controlli.

## 2. Decisione Architetturale

1. **Separazione Dati / ETL (`TASK-GS-BE-01`, #1):** pipeline Python `scripts/build_data.py` che produce `data/events.json`, `data/esercenti.json`, `data/odonomastica.json` normalizzati con validator anti-scraping sporco.
2. **Restyling Editoriale Unificato (`TASK-GS-FE-01`, #2):** un unico design system pulito con navigazione condivisa tra le 4 sezioni, zero emoji decorative nei controlli e filtri URL-driven.
3. **Automazione Settimanale (`TASK-GS-CI-01`, #3):** GitHub Action settimanale con quality gate automatico prima del deploy su GitHub Pages.
