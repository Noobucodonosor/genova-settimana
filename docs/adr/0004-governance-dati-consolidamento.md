# ADR-0004: Governance Dati Editoriali, Consolidamento Ecosistemi e Accessibilità

- **Stato:** Proposto
- **Priorità:** P2 — Media
- **Data:** 2026-11-21
- **Autori:** `@Noobucodonosor`, Antigravity
- **Fonti:** Analisi Product/Domain, Architettura e UX/UI

---

## 1. Contesto e Problema

1. **Dati editoriali hardcoded:** `AUTHORITATIVE_LIVE_OUTINGS` in `catalog.py` (mostre stagionali, locali) e blacklist in `verifier.py` sono cablati nel codice Python, rendendo macchinoso l'aggiornamento stagionale.
2. **Due ecosistemi paralleli:** `genova_outings/` e gli script provinciali (`build_bussola_html.py`, `generate_dashboard_html.py`, `generate_navigatore_esercenti.py`) non condividono ancora un layer dati/template comune.
3. **Accessibilità e osservabilità scraper:** le card cliccabili usano `<div class="card">` senza `<label>`/gestione tastiera completa; `programme.py` restituisce `[]` silenziosamente quando un sito cambia HTML.

---

## 2. Decisione Architetturale

1. **Esternalizzazione Configurazione Editoriale:**
   - Spostare `AUTHORITATIVE_LIVE_OUTINGS`, mostre con date di validità (`valid_from` / `valid_to`) e blacklist domini in file JSON/YAML versionati sotto `data/config/`.
2. **Consolidamento Layer Dati e Template:**
   - Definire un modulo condiviso per caricamento dataset, normalizzazione comuni (67 comuni Città Metropolitana) e componenti UI/footer comuni tra `genova_outings` e le viste provinciali.
3. **Accessibilità & Telemetria Scraper:**
   - Migrare le card a `<label>` semantiche o widget accessibili da tastiera (`Enter`/`Space`, focus visibile).
   - Emettere un report sintetico a fine `attach_programmes()` che segnali gli estrattori con 0 risultati.

---

## 3. Conseguenze

- **Positive:** manutenzione editoriale senza toccare codice Python, riduzione duplicazioni tra script, migliore accessibilità WCAG e diagnosi rapida di parser rotti.
- **Trade-off / Vincoli:** richiede migrazione ordinata dopo la stabilizzazione P0/P1.

---

## 4. Task Operativi Collegati (con Definition of Done)

- [x] **TASK-DATA-01**: **Esternalizzazione `AUTHORITATIVE_LIVE_OUTINGS` e blacklist in file dati versionati**
  - *File coinvolti*: `genova_outings/catalog.py`, `genova_outings/verifier.py`, `data/config/*.json`
  - *Acceptance Criteria*: Nessun evento stagionale hardcoded in `catalog.py`; supporto campi di scadenza `valid_to`.
  - *Verification Step*: Test catalogo con fixture temporali + `python3 run_tests.py`.
- [x] **TASK-ARCH-02**: **Consolidamento layer dati/template tra `genova_outings` e generatori provinciali**
  - *File coinvolti*: `genova_outings/`, `build_*.py`, `generate_*.py`
  - *Acceptance Criteria*: Helper condivisi per I/O dati, escape HTML e footer licenze senza duplicazione.
  - *Verification Step*: Rigenerazione completa di `site/` con diff verificato.
- [x] **TASK-A11Y-01**: **Accessibilità card da tastiera e telemetria estrattori `programme.py`**
  - *File coinvolti*: `genova_outings/web_ui.py`, `genova_outings/export_static.py`, `genova_outings/programme.py`
  - *Acceptance Criteria*: Selezione card completa via tastiera (`Tab`, `Space`/`Enter`); report fine esecuzione per estrattori a 0 eventi.
  - *Verification Step*: Verifica navigazione tastiera in browser + test log telemetria.
