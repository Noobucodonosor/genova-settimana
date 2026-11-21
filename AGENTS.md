# AGENTS.md — Contesto & Linee Guida per Agenti AI e Sviluppatori

> **REGOLA AUREA (MANDATORY):**
> Prima di modificare l'architettura, toccare il modello dati, aggiungere endpoint o sviluppare nuove feature, **DEVI leggere [`docs/adr/README.md`](./docs/adr/README.md)** e gli ADR specifici nella cartella [`docs/adr/`](./docs/adr/).

---

## 1. Panoramica del Progetto

- **Nome Progetto:** Genova Civica / `genova_outings`
- **Repository:** `Noobucodonosor/genova-settimana` (monorepo in `/Users/dany/genova` con deploy statico di `site/` su GitHub Pages)
- **Descrizione Sintetica:** Suite civica e culturale per Genova e i 67 comuni della Città Metropolitana: agenda settimanale verificata con export WhatsApp, navigatore esercenti, bussola del territorio, dashboard provinciale e odonomastica.
- **Stack Tecnologico:**
  - **Backend / ETL:** Python 3 (`genova_outings/`, script `build_*.py` / `generate_*.py`, stdlib-first)
  - **Frontend:** HTML5 + CSS vanilla modulare/inline + JavaScript vanilla (zero dipendenze runtime esterne, offline-friendly)
  - **Dati / Fonti:** JSON/CSV locali, OpenStreetMap (`ODbL 1.0`), Wikidata (`CC0`), scraping/probe HTTP controllati verso siti culturali ufficiali
  - **Hosting / CI:** GitHub Pages (`site/`) + GitHub Actions

---

## 2. Mappa dei File Principali

| File / Cartella | Ruolo |
| :--- | :--- |
| [`docs/adr/README.md`](./docs/adr/README.md) | **Indice degli ADR**, diagramma architetturale Mermaid e **Master Task Backlog**. |
| [`docs/adr/NNNN-*.md`](./docs/adr/) | Singoli Architecture Decision Records con contesto, decisioni e task collegati. |
| [`.github/ISSUE_TEMPLATE/`](./.github/ISSUE_TEMPLATE/) | Template standard per l'apertura di GitHub Issues (`adr_task.yml`, `bug_report.yml`). |
| [`.github/PULL_REQUEST_TEMPLATE.md`](./.github/PULL_REQUEST_TEMPLATE.md) | Checklist di PR allineata a ADR, Verification Step e modalità `Show` / `Ask`. |
| [`genova_outings/`](./genova_outings/) | Pacchetto Python core: catalogo settimanale (`catalog.py`), verifica URL (`verifier.py`), estrattori (`programme.py`), formatter WhatsApp (`formatter.py`), validatore (`validator.py`), web UI (`web_ui.py`) ed export statico (`export_static.py`). |
| [`build_bussola_html.py`](./build_bussola_html.py), [`generate_dashboard_html.py`](./generate_dashboard_html.py), [`generate_navigatore_esercenti.py`](./generate_navigatore_esercenti.py) | Generatori HTML statici per le viste provinciali (`bussola.html`, `dashboard.html`, `esercenti.html`). |
| [`site/`](./site/) | Output HTML/asset pubblicati su GitHub Pages (`index.html`, `bussola.html`, `dashboard.html`, `esercenti.html`, `odonomastica/`). |
| [`tests/`](./tests/) e [`run_tests.py`](./run_tests.py) | Suite unit & E2E (`unittest`). |

---

## 3. Metodologia di Lavoro (ADR + GitHub Issues)

1. **Ogni decisione architetturale o di sicurezza** è documentata in `docs/adr/NNNN-titolo.md`.
2. **Ogni task operativo** ha un codice univoco (`TASK-<MODULO>-XX`) censito nell'ADR di origine, in `docs/adr/README.md` e su **GitHub Issues**.
3. **Priorità Standard:**
   - `P0-critical`: Sicurezza (XSS, TLS, CORS), compliance licenze open data, integrità monorepo, test E2E bloccanti.
   - `P1-high`: CI/CD settimanale, portabilità path, test offline scraper/export, parità formatter WhatsApp.
   - `P2-medium`: Esternalizzazione dati editoriali, consolidamento ecosistemi, accessibilità e telemetria.
4. **Sviluppo & Flusso GitHub:**
   - **Bivio `Issue` vs `Branch`:** per task esplorativi/architetturali salva prima il piano in una Issue (*Plan-to-Issue*); apri un branch (`feat/TASK-XXX-01`, `fix/TASK-XXX-01`) solo su task perimetrati. Scoperte fuori scope → nuova Issue separata, mai *scope drift*.
   - **Draft PR & Rollback sicuro:** apri presto una Draft PR (`gh pr create --draft`); usa micro-PR e **Squash Merge** su `main`. **Mai `git rebase -i`** (usa `git reset --soft` per salvare parti valide; `--force-with-lease` solo prima di review umane, altrimenti `git revert`).
   - **Flusso graduato (`Show` vs `Ask`):** modifiche `P0-critical`, sicurezza o cambi a `docs/adr/`, `AGENTS.md` e `.github/**` richiedono sempre review umana (**Ask**).
   - **Verification Step reale:** esegui sempre il test previsto nella Issue verificando il comportamento sul diff, ispeziona `gh pr diff` e usa commit atomici:
     ```bash
     git commit -m "feat(TASK-XXX-01): descrizione sintetica della modifica (closes #N)"
     ```

---

## 4. Sicurezza & Regole Critiche

- **Zero XSS / Script Injection:** ogni interpolazione in `innerHTML` deve essere escapata; i JSON inline in `<script>` devono escapare `<` (`\u003c`); tutti gli `href` devono validare `^https?://`.
- **Verifica TLS attiva:** mai disabilitare globalmente `ssl.CERT_NONE` / `check_hostname = False`.
- **Zero dipendenze runtime esterne:** le pagine in `site/` non devono caricare script esterni non pinnati (es. `tailwindcss.min.js`), ma usare CSS vanilla locale/inline.
- **Attribuzione Open Data:** ogni pagina che usa dati OpenStreetMap o Wikidata deve esporre `© OpenStreetMap contributors (ODbL 1.0)` e nota `Wikidata (CC0)`.
- **Mai committare segreti o file >50 MB:** `.env`, token e database locali restano in `.gitignore`. Prima di ogni rilascio esegui:
  ```bash
  python3 ~/.gemini/config/skills/adr-github-methodology/scripts/pre_release_check.py
  ```

---

## 5. Comandi Rapidi di Sviluppo e Test

```bash
# Suite E2E a 4 tier
python3 run_tests.py

# Suite completa unit + E2E
python3 -m unittest discover -s tests

# Rigenerazione pagina statica settimanale (site/index.html)
python3 -m genova_outings.export_static site

# Lista GitHub Issues attive
gh issue list -R Noobucodonosor/genova-settimana --limit 30
```
