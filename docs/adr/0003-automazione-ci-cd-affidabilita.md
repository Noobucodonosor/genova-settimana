# ADR-0003: Automazione CI/CD Settimanale, Portabilità e Affidabilità QA

- **Stato:** Proposto
- **Priorità:** P1 — Alta
- **Data:** 2026-11-21
- **Autori:** `@Noobucodonosor`, Antigravity
- **Fonti:** Analisi DevOps/SRE, QA/Reliability e UX/Content; GitHub Issue `#3`

---

## 1. Contesto e Problema

1. **Staleness settimanale:** `site/index.html` si aggiorna solo con esecuzioni manuali locali (l'ultimo aggiornamento risale all'8 novembre 2026, mentre oggi è 21 novembre).
2. **Non portabilità:** `catalog.py:37`, `verifier.py:269` e gli script `build_*.py` / `generate_*.py` usano path assoluti `/Users/dany/genova`, impedendo l'esecuzione in CI. Manca `pyproject.toml`.
3. **Cache HTTP priva di TTL:** `crawled_urls_cache.json` non ha scadenza, mantenendo `Cached OK` anche per siti chiusi o spostati.
4. **Gap di test e parità WhatsApp:** `programme.py` (510 righe di regex scraping) ed `export_static.py` hanno 0 test dedicati; `export_static.py` genera messaggi WhatsApp senza URL ufficiali, divergendo da `formatter.py` e `validator.py`.

---

## 2. Decisione Architetturale

1. **Workflow CI/CD Settimanale (Issue `#3`):**
   - Configurare `.github/workflows/update-events.yml` con trigger `schedule` settimanale + `workflow_dispatch`, esecuzione test, rigenerazione di `site/index.html` (e `data/events.json` quando pronto) e commit automatico solo se valido.
2. **Portabilità e Packaging:**
   - Sostituire tutti i path `/Users/dany/genova` con risoluzione relativa alla root del repo o env var `GENOVA_DATA_DIR`.
   - Aggiungere `pyproject.toml` con versione Python supportata.
   - Introdurre TTL configurabile (es. 7 giorni) sulle entry di `crawled_urls_cache.json`.
3. **Test Suite Offline per Scraper ed Export:**
   - Salvare snapshot HTML rappresentativi in `tests/fixtures/` per testare in isolamento deterministico tutti gli estrattori di `programme.py` e il generatore `export_static.py`, risolvendo i `ResourceWarning` nei mock HTTP.
4. **Parità Formatter WhatsApp:**
   - Allineare la funzione JS `message()` in `export_static.py` alle regole di `formatter.py` e `validator.py`, includendo gli URL ufficiali verificati.

---

## 3. Conseguenze

- **Positive:** sito pubblico sempre aggiornato, eseguibilità su qualsiasi macchina/runner CI, rilevamento immediato di regressioni negli scraper.
- **Trade-off / Vincoli:** i test su fixture HTML verificano la logica dei parser ma non rilevano automaticamente cambi DOM sui siti reali finché non si aggiornano le fixture o si esegue un controllo live in CI.

---

## 4. Task Operativi Collegati (con Definition of Done)

- [x] **TASK-GS-CI-01** (`#3`): **GitHub Action settimanale per aggiornamento eventi e validazione dati**
  - *File coinvolti*: `.github/workflows/update-events.yml`
  - *Acceptance Criteria*: Workflow schedulato + manuale funzionante; fail-fast se il validator rileva errori.
  - *Verification Step*: Esecuzione manuale `workflow_dispatch` verde.
- [x] **TASK-PORT-01**: **Portabilità path (`GENOVA_DATA_DIR`), `pyproject.toml` e TTL cache HTTP**
  - *File coinvolti*: `genova_outings/catalog.py`, `genova_outings/verifier.py`, `build_*.py`, `generate_*.py`, `pyproject.toml`
  - *Acceptance Criteria*: Zero occorrenze di `/Users/dany/genova` nel codice; TTL attivo su `crawled_urls_cache.json`.
  - *Verification Step*: `grep -rn "/Users/dany" genova_outings/ *.py` (0 match) + test TTL cache.
- [x] **TASK-QA-01**: **Copertura test offline per `programme.py` ed `export_static.py` + fix `ResourceWarning`**
  - *File coinvolti*: `tests/fixtures/*`, `tests/test_programme.py`, `tests/test_export_static.py`, `tests/test_*.py`
  - *Acceptance Criteria*: Copertura di tutti gli estrattori di `programme.py` e dell'output di `export_static.py`; `unittest` senza `ResourceWarning`.
  - *Verification Step*: `python3 -W default -m unittest discover -s tests`.
- [x] **TASK-UX-01**: **Parità formatter WhatsApp tra `formatter.py` ed `export_static.py`**
  - *File coinvolti*: `genova_outings/export_static.py`, `genova_outings/formatter.py`, `genova_outings/validator.py`
  - *Acceptance Criteria*: Il messaggio generato da `site/index.html` include gli URL verificati e rispetta le regole di `validator.py`.
  - *Verification Step*: Test automatico sul testo generato da `export_static.py`.
