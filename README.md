# Genova Civica & Cultura — Hub Interattivo (67 Comuni)

Raccolta di web app statiche, open data e script Python dedicati al territorio della **Città Metropolitana di Genova (67 comuni)**: eventi culturali, botteghe ed esercenti locali, luoghi aperti al pubblico e storia della città ricostruita attraverso l'odonomastica (OpenStreetMap + Wikidata `P138`).

## Demo Live (GitHub Pages)
- **[Cosa facciamo Genova](https://noobucodonosor.github.io/genova-settimana/)** (`index.html`) — Guida conversazionale settimanale: cinema, mostre, musica, biblioteche, botteghe e passeggiate.
- **[Navigatore Esercenti & Artigiani (4.966 Attività)](https://noobucodonosor.github.io/genova-settimana/esercenti.html)** (`esercenti.html`) — Motore di ricerca locale su negozi di quartiere, botteghe storiche e artigiani nei 67 comuni.
- **[Bussola del Tempo Libero](https://noobucodonosor.github.io/genova-settimana/bussola.html)** (`bussola.html`) — Esplorazione interattiva per interessi e aree della provincia di Genova.
- **[Dashboard Cosa è Aperto (Giorno / Settimana / Mese)](https://noobucodonosor.github.io/genova-settimana/dashboard.html)** (`dashboard.html`) — Panoramica dei luoghi culturali, civici e ricreativi aperti al pubblico.

## Storia di Genova Ricostruita dalle Strade (`odonomastica/`)
Pipeline Python che incrocia i toponimi di **OpenStreetMap** con le relazioni **Wikidata (`P138` — *named after*)** per ricostruire la mappa dei personaggi storici intitolati alle vie e piazze di Genova:
- [`odonomastica/elenco_integrale_personaggi_genova.md`](./odonomastica/elenco_integrale_personaggi_genova.md) — Elenco storico ragionato
- [`odonomastica/toponimi_personaggi_genova_integrale.csv`](./odonomastica/toponimi_personaggi_genova_integrale.csv) — Dataset strutturato CSV
- [`odonomastica/classify_toponimi.py`](./odonomastica/classify_toponimi.py) & [`odonomastica/build_complete_dataset.py`](./odonomastica/build_complete_dataset.py) — Script di classificazione e costruzione dataset

## Stack Tecnologico
- **Frontend:** HTML5, CSS3, Vanilla JavaScript (zero dipendenze runtime, funzionamento instant-load offline-friendly)
- **Data Pipeline:** Python 3, OpenStreetMap Overpass API, Wikidata SPARQL/JSON, CSV/Markdown
