# Genova Civica & Cultura (`genova-settimana`)

Piattaforma open-data e agenda civica statica per **Genova e tutti i 67 comuni della Città Metropolitana**: eventi settimanali verificati, navigatore su **4.966 esercenti locali**, bussola tempo libero, dashboard provinciale e storia delle vie (odonomastica OSM + Wikidata).

**Live su GitHub Pages:** [https://noobucodonosor.github.io/genova-settimana/](https://noobucodonosor.github.io/genova-settimana/)

![Anteprima desktop Genova Civica & Cultura](./docs/preview/desktop.png)

## Viste Live
- **Agenda Settimana:** [index.html](https://noobucodonosor.github.io/genova-settimana/)
- **Bussola Tempo Libero:** [bussola.html](https://noobucodonosor.github.io/genova-settimana/bussola.html)
- **Navigatore Esercenti (4.966 attività):** [esercenti.html](https://noobucodonosor.github.io/genova-settimana/esercenti.html)
- **Storie & Vie (Odonomastica OSM + Wikidata):** [storie.html](https://noobucodonosor.github.io/genova-settimana/storie.html)
- **Dashboard 67 Comuni:** [dashboard.html](https://noobucodonosor.github.io/genova-settimana/dashboard.html)

## Struttura del Repository
```text
genova-settimana/
├── genova_outings/    # Package Python core (catalog, verifier, export_static, web_ui)
├── scripts/           # Pipeline di build (`build_data.py`) e script ETL (`scripts/etl/`)
├── data/              # Dataset normalizzati (`data/`) e sorgenti grezze (`data/raw/`)
├── site/              # Sito statico PWA pubblicato automaticamente su GitHub Pages
├── tests/             # Suite di test unitari, sicurezza XSS/TLS e portabilità
├── docs/              # ADR, anteprime visive ed esportazioni Markdown (`docs/exports/`)
├── pyproject.toml     # Configurazione pacchetto Python
└── LICENSE            # Licenza MIT
```

## Avvio Locale e Test
```bash
# Esegui la suite di test offline
python3 -m unittest discover -s tests -v
python3 run_tests.py

# Rigenera i dataset normalizzati e il sito statico
python3 scripts/build_data.py
python3 -m genova_outings.export_static site
```

## Automazione CI/CD
- **Aggiornamento settimanale (`update-events.yml`):** esegue test, rigenera `data/events.json` e `site/index.html` ogni lunedì.
- **Deploy continuo (`deploy-pages.yml`):** pubblica `site/` su GitHub Pages ad ogni aggiornamento.
- **Fonti Open Data:** © OpenStreetMap contributors (ODbL 1.0) · Wikidata (CC0).

## Licenza
Rilasciato sotto licenza [MIT](./LICENSE).
