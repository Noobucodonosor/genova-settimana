# ADR-0001: Unificazione Monorepo, Architettura Core e Pipeline Dati

- **Stato:** Accettato (Baseline)
- **Priorità:** P0 — Critica
- **Data:** 2026-11-21
- **Autori:** `@Noobucodonosor`, Antigravity
- **Fonti:** Analisi multifocale del repository `/Users/dany/genova`, `.agents/teamwork/PROJECT.md`, GitHub Issues `#1`, `#2`

---

## 1. Contesto e Problema

1. **Scissione Git:** attualmente solo `site/` è un repository Git (`Noobucodonosor/genova-settimana`), mentre tutto il codice sorgente Python (`genova_outings/`, `build_*.py`, `generate_*.py`, `tests/`) e i dataset JSON/CSV in `/Users/dany/genova` non sono versionati. Inoltre `site/odonomastica/` contiene copie duplicate di script Python (`build_complete_dataset.py`, `classify_toponimi.py`).
2. **Dati inline e duplicazione:** le app statiche in `site/` (`bussola.html`, `dashboard.html`, `esercenti.html`) incorporano fino a 1.75 MB di JSON inline e usano generatori separati rispetto a `genova_outings/`.
3. **Disallineamento Milestone M3:** `PROJECT.md` prevede `genova_outings/cli.py` e il launcher `genova_outings.py`, attualmente assenti (causando 12 test skippati in `run_tests.py`).

---

## 2. Decisione Architetturale

1. **Monorepo unico su `Noobucodonosor/genova-settimana`:**
   - Spostare il repository Git alla root `/Users/dany/genova`, versionando sorgenti Python, `tests/`, `docs/adr/`, `AGENTS.md`, configurazioni `.github/` e `site/` (target di pubblicazione GitHub Pages).
   - Eliminare le copie duplicate degli script Python dentro `site/odonomastica/` mantenendo in `site/` solo artefatti pubblicabili.
2. **Separazione ETL Dati / Frontend Editoriale (Issues `#1`, `#2`):**
   - Evolvere la pipeline ETL verso dataset JSON normalizzati in `data/` (`events.json`, `esercenti.json`, `odonomastica.json`) caricati asincronamente dalle viste HTML con validazione anti-scraping sporco (`TASK-GS-BE-01`).
   - Unificare le 4 app sotto un design system editoriale coerente (`TASK-GS-FE-01`).
3. **Completamento CLI Milestone M3:**
   - Esporre `genova_outings/cli.py` e `genova_outings.py` allineati a `__main__.py` e ai test E2E.

---

## 3. Conseguenze

- **Positive:** storico Git completo per codice e output, review su PR, eliminazione del rischio di perdita locale, ridotto peso iniziale delle pagine HTML.
- **Trade-off / Vincoli:** richiede `.gitignore` rigoroso (nessun file >50 MB o cache temporanea non voluta) e configurazione GitHub Pages dalla cartella `site/`.

---

## 4. Task Operativi Collegati (con Definition of Done)

- [ ] **TASK-GS-BE-01** (`#1`): **Pipeline Python ETL: separazione dati JSON e normalizzazione testi eventi**
  - *File coinvolti*: `scripts/build_data.py`, `data/*.json`
  - *Acceptance Criteria*: `events.json`, `esercenti.json`, `odonomastica.json` generati deterministicamente e validati.
  - *Verification Step*: Esecuzione script ETL + validator con 0 errori.
- [ ] **TASK-GS-FE-01** (`#2`): **Restyling editoriale unificato anti-slop (Genova Civica)**
  - *File coinvolti*: `site/*.html`, generatori frontend
  - *Acceptance Criteria*: Layout verificato a `1440×900` e `390×844` senza overflow né console error; caricamento JSON asincrono.
  - *Verification Step*: Ispezione browser reale desktop/mobile.
- [ ] **TASK-REPO-01**: **Unificazione monorepo Git in `/Users/dany/genova` su `Noobucodonosor/genova-settimana`**
  - *File coinvolti*: `.gitignore`, `site/odonomastica/`, `.github/workflows/`
  - *Acceptance Criteria*: Root `/Users/dany/genova` è repo Git con remote `Noobucodonosor/genova-settimana`; `site/odonomastica/*.py` rimossi senza perdere i sorgenti in root; `site/` servito correttamente su GitHub Pages.
  - *Verification Step*: `git status`, `git log -n 3`, `pre_release_check.py`.
- [ ] **TASK-CLI-01**: **Completamento Milestone M3 (`genova_outings/cli.py` + `genova_outings.py`)**
  - *File coinvolti*: `genova_outings/cli.py`, `genova_outings.py`, `genova_outings/__main__.py`
  - *Acceptance Criteria*: I 12 test E2E precedentemente skippati vengono eseguiti e passano.
  - *Verification Step*: `python3 run_tests.py` (84/84 passed, 0 skipped).
