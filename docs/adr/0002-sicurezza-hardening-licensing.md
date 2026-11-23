# ADR-0002: Sicurezza, Hardening Web/TLS, Zero Dipendenze Esterne e Licensing Open Data

- **Stato:** Accettato
- **Priorità:** P0 — Critica
- **Data:** 2026-11-21
- **Autori:** `@Noobucodonosor`, Antigravity
- **Fonti:** Audit sicurezza e compliance su `genova_outings/`, `build_bussola_html.py`, `generate_dashboard_html.py`, `generate_navigatore_esercenti.py`, `site/`

---

## 1. Contesto e Problema

1. **DOM XSS e Script Injection:** `web_ui.py`, `generate_dashboard_html.py`, `generate_navigatore_esercenti.py` e punti di `build_bussola_html.py` interpolano dati provenienti da fonti esterne (incluso OpenStreetMap/Wikidata) in `innerHTML` e `href="..."` senza escaping completo né validazione dello schema `^https?://`. Inoltre `export_static.py` e gli altri generatori iniettano `json.dumps(..., ensure_ascii=False)` dentro `<script>` senza escapare `<` (`\u003c`).
2. **TLS disabilitato e server locale esposto:** `verifier.py:322-324` imposta `ssl.CERT_NONE` e `check_hostname = False`; `web_ui.py` espone `Access-Control-Allow-Origin: *` e legge `Content-Length` senza cap massimo né gestione `ValueError`.
3. **Dipendenza runtime esterna non pinnata:** `build_bussola_html.py`, `generate_dashboard_html.py` e `generate_navigatore_esercenti.py` caricano `https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js` senza SRI, contraddicendo il requisito offline-friendly.
4. **Compliance Open Data:** le pagine in `site/` usano dati OpenStreetMap e Wikidata senza esporre l'attribuzione obbligatoria `© OpenStreetMap contributors (ODbL 1.0)`.

---

## 2. Decisione Architetturale

1. **Hardening XSS & JSON inline:**
   - Introdurre escaping HTML sistematico (o costruzione DOM tramite `textContent` / `createElement`) su tutti i punti `innerHTML` in `web_ui.py` e nei generatori `build_*.py` / `generate_*.py`.
   - Validare `^https?://` prima di popolare qualsiasi `href`.
   - Sostituire `<` con `\u003c` in tutti i payload JSON serializzati dentro tag `<script>`.
2. **Hardening TLS e Server Locale:**
   - Ripristinare la verifica TLS di default in `verifier.py` (con eventuale allowlist esplicita e loggata solo se strettamente necessaria).
   - Limitare `Access-Control-Allow-Origin` a `http://127.0.0.1` / `localhost` in `web_ui.py` e imporre un limite massimo (es. 1 MB) + validazione su `Content-Length`.
3. **CSS Vanilla Modulare/Inline (Zero Dipendenze Node/CDN):**
   - Rimuovere `https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js` dalle 3 app provinciali sostituendolo con CSS vanilla modulare/inline, senza introdurre build step Node/npm.
4. **Attribuzione Open Data:**
   - Aggiungere il footer legale `© OpenStreetMap contributors (ODbL 1.0) · Wikidata (CC0)` in tutte le app che consumano dati OSM/Wikidata e in `site/README.md`.

---

## 3. Conseguenze

- **Positive:** eliminazione vulnerabilità XSS/script injection/MitM, funzionamento 100% offline reale, conformità legale ODbL.
- **Trade-off / Vincoli:** richiede refactoring mirato degli stili CSS nelle 3 app provinciali; eventuali piccoli siti culturali con certificati TLS scaduti verranno segnalati come non verificati anziché accettati silenziosamente.

---

## 4. Task Operativi Collegati (con Definition of Done)

- [x] **TASK-SEC-01**: **Hardening XSS, Script Injection, TLS e server locale**
  - *File coinvolti*: `genova_outings/web_ui.py`, `genova_outings/export_static.py`, `genova_outings/verifier.py`, `build_bussola_html.py`, `generate_dashboard_html.py`, `generate_navigatore_esercenti.py`
  - *Acceptance Criteria*: Nessuna interpolazione non escapata in `innerHTML`; `<` escapato in `\u003c` nei JSON inline; `href` validati `^https?://`; TLS verificato di default in `verifier.py`; CORS ristretto e `Content-Length` limitato in `web_ui.py`.
  - *Verification Step*: Test unitari di sicurezza (payload `<script>`, `javascript:alert(1)`, `CERT_NONE` rimosso) + `python3 -m unittest discover -s tests`.
- [x] **TASK-CSS-01**: **Rimozione `tailwindcss.min.js` con CSS vanilla e attribuzione ODbL 1.0**
  - *File coinvolti*: `build_bussola_html.py`, `generate_dashboard_html.py`, `generate_navigatore_esercenti.py`, `site/README.md`
  - *Acceptance Criteria*: Zero riferimenti a `gstatic.com` nei sorgenti e negli HTML generati; footer con `© OpenStreetMap contributors (ODbL 1.0)` presente su tutte le viste OSM.
  - *Verification Step*: `grep -rn "tailwindcss\|gstatic" site/ *.py` (0 match) e verifica visiva/browser offline.
