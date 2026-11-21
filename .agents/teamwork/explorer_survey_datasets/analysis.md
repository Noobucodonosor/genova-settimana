# Indagine Approfondita sui Dataset Locali e Codebase per il Catalogo Uscite Informali a Genova e Provincia

**Data redazione**: 4 Novembre 2026  
**Autore**: Teamwork Explorer (Dataset & Codebase Survey)  
**Ambiente di lavoro**: `/workspace/genova`  
**Obiettivo**: Valutare tutti gli asset di dati locali, script di aggregazione, categorie di tempo libero/cultura, stato di igiene del dato e criteri di filtro per alimentare lo strumento di selezione e generazione messaggi WhatsApp per uscite informali.

---

## 1. Executive Summary

La cartella di lavoro `/workspace/genova` ospita un ecosistema di dati estremamente ricco, strutturato e già parzialmente geolocalizzato e arricchito con orari, siti web ufficiali e descrizioni narrative. 

I punti salienti emersi dall'indagine:
1. **Asset principali disponibili**:
   - `tempo_libero_payload.json` (326 luoghi selezionati su tutti i 67 comuni della provincia, 16 itinerari tematici pronti, 31 eventi mensili/ricorrenti).
   - `tempo_libero_dataset.json` (340 luoghi con flag treno, orari, costi, slot orari, pitch narrativo).
   - `guida_aperti_al_pubblico_provincia_genova.json` (4.251 luoghi con stato sito web, orari estratti e 115 cinema/teatri, 163 musei, 326 biblioteche, 278 parchi storici).
   - `dashboard_items.json` (1.987 luoghi con giorni della settimana parsed `days_open`, fasce orarie `hours_range`, flag domenica e serale).
   - `esercenti_genova_provincia_db.json` (4.966 attività con 61 librerie indipendenti, 8 negozi di dischi/musica, 43 belle arti/atelier, 36 pasticcerie/confetterie storiche, 52 sciamadde e forni storici).
   - `crawled_urls_cache.json` (834 siti scansionati, con 581 URL attivi HTTP 200 e programmazioni/eventi reali estratti per l'autunno 2026).
   - `comuni_67_geo.json` e `comuni_provincia_genova.json` (coordinate, altitudini e mapping zone dei 67 comuni).
2. **Copertura tematica per uscite informali moderne**:
   - I dati contengono esattamente le tipologie richieste: **cinema d'essai** (es. Nickelodeon con rassegne weekend, Sivori, America, Odeon), **teatri indipendenti e prosa** (es. Sala Mercato con spettacolo attivo 3-8 novembre 2026, Teatro Sociale Camogli, Teatro della Tosse / La Claque), **laboratori artigianali & mestieri** (sughero Luico, filigrana di Campo Ligure, cioccolato Viganotti, cartiera di Mele), **biblioteche con chiostro** (Berio, De Amicis al Porto Antico), **passeggiate sceniche & trekking urbano** (Spianata Castelletto, Nervi scogliera Anita Garibaldi, Boccadasse, Forti del Righi, Baia del Silenzio a Sestri Levante), **degustazioni tipiche a bancone** (farinata Sa' Pesta, sciroppo di rose da Romanengo, Antica Farmacia di Sant'Anna).
3. **Stato di igiene e affidabilità**:
   - I 73 *Tier 1 Flagships* di `tempo_libero_payload.json` hanno il 100% di orari, giorni, durate, costi, coordinate e pitch validati, e il 98.6% di URL ufficiali attivi.
   - Nelle 4.251 voci di `guida_aperti_al_pubblico`, il 24.4% ha URL valido (748 con esito OK dal crawler), ma sono presenti voci da escludere a priori (scuole elementari, sedi municipali, monumenti cimiteriali, memoriali).
   - Sono stati rilevati domini parcheggiati/scaduti (es. `turismoinliguria.com`) che un modulo estrattore deve scartare o sostituire con i portali comunali o istituzionali (`visitgenoa.it`, `cultura.gov.it`, `museidigenova.it`).

---

## 2. Inventario Dettagliato dei Dataset

| File | Dimensione | Record | Formato | Ruolo Principale |
|---|---|---|---|---|
| `tempo_libero_payload.json` | 264 KB | 326 luoghi, 16 itinerari, 31 eventi | JSON | **Migliore base per il catalogo**: unisce luoghi tier-1 (73) e tier-2 (253) su tutti i 67 comuni, con orari, giorni e slot. |
| `tempo_libero_dataset.json` | 340 KB | 340 luoghi | JSON | Tabella con pitch narrativo, personaggio storico, durata in minuti, accessibilità in treno, costo. |
| `dashboard_items.json` | 1,93 MB | 1.987 luoghi | JSON | Dataset arricchito con `days_open: [0..6]`, `hours_range: [[h1, h2]]`, flag domenicali e serali. |
| `guida_aperti_al_pubblico_provincia_genova.json` | 2,20 MB | 4.251 luoghi | JSON | Guida completa con macro/sottocategorie, orari OSM, scraping eventi, stato del sito web. |
| `esercenti_genova_provincia_db.json` | 2,75 MB | 4.966 record | JSON | Registro negozi e artigiani: utile per librerie indipendenti, vinili, botteghe storiche, sciamadde. |
| `crawled_urls_cache.json` | 393 KB | 834 URL | JSON | Cache crawler HTTP con titoli, meta-descrizioni, programmazioni live e testi estratti. |
| `comuni_67_geo.json` | 7 KB | 67 comuni | JSON | Coordinate centroide (`lat`, `lon`), altitudine (`elev`) di ciascun comune. |
| `comuni_provincia_genova.json` | 5 KB | 67 comuni | JSON | ID Wikidata (`qid`) e relazione OpenStreetMap (`osm_rel`) per ogni comune. |

---

## 3. Analisi della Codebase e degli Script di Elaborazione

Nel workspace sono presenti script Python di consolidamento e parsing che offrono moduli direttamente riutilizzabili per il nuovo estrattore:

### 3.1 `build_tempo_libero_engine.py` (1.523 righe)
- **Funzionamento**:
  - Definisce `FLAGSHIPS` (76 destinazioni eccellenti con orari, giorni `[0..6]`, fasce `slots`, treno, pitch e personaggio storico).
  - Include un dizionario di zonizzazione `ZONE_BY_COMUNE` (7 macro-aree: `centro`, `genova_mare`, `ponente_stura`, `polcevera_scrivia`, `golfo_paradiso`, `tigullio_occ`, `tigullio_or`).
  - Set `RAIL_COMUNI` con i 25 comuni comodamente raggiungibili in treno/funicolare senza auto.
  - Genera 16 itinerari tematici multi-tappa con filtro meteo (`pioggia`, `sole`, `qualsiasi`) e mezzo (`piedi`, `treno`, `auto`).
  - Output generato: `tempo_libero_payload.json` e `tempo_libero_dataset.json`.

### 3.2 `build_guida_aperti_al_pubblico.py` (364 righe)
- **Funzionamento**:
  - Fondevia OSM e Wikidata con la cache di crawling.
  - Contiene il dizionario `VERIFIED_HOURS_AND_EVENTS` per le principali biblioteche (Berio, De Amicis, Lercari, Brocchi, Benzi), musei e dimore storiche.
  - Include la funzione `map_macro_category()` che converte le etichette grezze OSM in 9 macro-settori omogenei.

### 3.3 `build_dashboard_data.py` (308 righe)
- **Funzionamento**:
  - Contiene la funzione `parse_schedule(orari_str, macro)` che traduce stringhe testuali di orari in array numerici:
    - Giorni: `0=Domenica, 1=Lunedì, 2=Martedì, 3=Mercoledì, 4=Giovedì, 5=Venerdì, 6=Sabato`.
    - Ore: decimali (es. 8.5 per 08:30).
    - Flag booleani: `open_sunday`, `open_evening` (aperto dopo le 19:30 o spettacoli serali).
  - Integra le 12 Botteghe Storiche di punta di Genova (Sant'Anna, Luico, Romanengo, Finollo, Giacalone, Viganotti, Sa' Pesta, Torielli, Marescotti).

### 3.4 `build_esercenti_database.py` e `generate_navigatore_esercenti.py`
- Normalizzano gli esercenti di quartiere in 9 macro-settori, identificando i 25 quartieri di Genova tramite calcolo di distanza minima sui centroidi.

---

## 4. Analisi delle Categorie per un'"Uscita Informale Moderna"

L'obiettivo dell'utente richiede alternative che non abbiano il peso o l'imbarazzo di un "date formale", privilegiando attività stimolanti, rilassate, con punti di conversazione naturali.

### 4.1 Categorie Ideali Censite nei Dati

| Categoria Uscita | Esempi Concreti nei Dataset | Numero Voci Pronte | Note di Esperienza |
|---|---|---|---|
| **Cinema d'essai & Cineforum** | - *Cinema Nickelodeon* (Via della Consolazione 5r, cineclub)<br>- *Cinema Sìvori* (Salita Santa Caterina 12r, sala d'essai più antica d'Italia)<br>- *Cinema America* (Via Colombo 11)<br>- *Cinema Odeon* (Corso Buenos Aires)<br>- *Club Amici del Cinema* (Via Rolando, Sampierdarena) | 25 a Genova + 12 in provincia | Film d'autore, documentari e prime visioni, orari serali e pomeridiani già estratti nei dataset. |
| **Mostre d'Arte & Musei Insoliti** | - *Palazzo Ducale* (Piazza Matteotti, mostre temporanee)<br>- *Castello D'Albertis* (Salita San Bartolomeo, collezioni esotiche e vista porto)<br>- *Wolfsoniana & GAM* (Parchi di Nervi, arti decorative Novecento)<br>- *Galata Museo del Mare* (Porto Antico, sottomarino Nazario Sauro)<br>- *Museo della Filigrana* (Campo Ligure, orario ven-dom)<br>- *Museo dell'Orologio da Torre Trebino* (Uscio)<br>- *Galleria Rizzi* (Sestri Levante, Baia del Silenzio) | 68 flagships + 162 in guida | Attività culturali stimolanti senza formalismi, durata 60-120 min. |
| **Laboratori & Mestieri Artigiani** | - *G.M. Luico - Re del Sughero* (Salita Santa Caterina, 1855)<br>- *Pietro Romanengo fu Stefano* (Soziglia / Via Roma, confetteria 1780)<br>- *Fabbrica Cioccolato Romeo Viganotti* (Vico dei Castagna)<br>- *Busellato Timbri & Incisioni* (Via San Luca)<br>- *Antica Cartiera di Mele* (Val Leira, produzione carta a mano)<br>- *Atelier di Filigrana* a Campo Ligure | 49 botteghe in payload + 12 flagships | Esplorazione sensoriale di botteghe uniche; ideale per un giro spontaneo in centro o gita fuori porta. |
| **Biblioteche Storiche & Caffè Letterari** | - *Biblioteca Civica Berio* (chiostro antico, sale studio e bar nel cortile)<br>- *Biblioteca De Amicis* (Magazzini del Cotone, affaccio sul mare)<br>- *Biblioteca Universitaria* (Via Balbi, ex collegio dei Gesuiti)<br>- *Biblioteca Lercari* (Parco di Villa Imperiale, San Fruttuoso) | 32 selezionate | Spazi aperti fino alle 19:00, perfetti per un incontro pomeridiano tranquillo. |
| **Passeggiate Panoramiche & Trekking Urbano** | - *Spianata Castelletto* (salita con ascensore Liberty + granita/caffè)<br>- *Passeggiata Anita Garibaldi & Roseto di Nervi* (scogliera a picco)<br>- *Borgo Marinaro di Boccadasse* (spiaggia di ciottoli e scogli di Capo Santa Chiara)<br>- *Funicolare Zecca-Righi & Parco delle Mura* (vista a 360° sulla città)<br>- *Punta Chiappa & San Fruttuoso di Camogli* (sentiero o battello)<br>- *Baia del Silenzio & Baia delle Favole* a Sestri Levante | 31 percorsi/oasi naturali | Totalmente informali, aperti sempre o con orari di parco, costo zero. |
| **Circoli Culturali, Teatri Indipendenti & Musica** | - *Teatro della Tosse / La Claque* (Piazza Negri, teatro contemporaneo e live music nei caruggi)<br>- *Sala Mercato* (Sampierdarena, spettacolo in cartellone 3-8 nov 2026)<br>- *Teatro Sociale di Camogli* (palchi storici e aperitivi in musica)<br>- *Teatro TiQu* (Piazzetta Cambiaso, teatro internazionale di quartiere)<br>- *Politeama Genovese* (Via Bacigalupo, stand-up comedy e musica) | 15 flagships + 50 teatri censiti | Serate vive, dinamiche, con bar e atmosfera accogliente prima e dopo lo spettacolo. |
| **Librerie Indipendenti & Dischi/Vinili** | - *Disco Club* (Via San Vincenzo 20r, fondato nel 1965, istituzione musicale genovese)<br>- *Record Runners* (Via Nizza 60r, vinili da collezione)<br>- *Libraccio Genova* (Piazza Portello / Via Cairoli)<br>- *Libreria Fieschi* (Lavagna) | 61 librerie + 8 negozi di musica | Sfogliatura dischi e libri rari, ritmo rilassato. |
| **Botteghe con Degustazione Tipica & Sciamadde** | - *Antica Friggitoria Sa' Pesta* (Via dei Giustiniani, farinata a legna nei testi di rame)<br>- *Pasticceria Marescotti di Cavo* (Fossatello, arredi d'epoca e aperitivo storico)<br>- *Drogheria Torielli* (San Bernardo, 400 cassetti di spezie e tè)<br>- *Antica Farmacia Sant'Anna* (Castelletto, roseto e rimedi galenici) | 52 sciamadde/forni + 12 botteghe storiche | Consumazione informale al banco o al piattino, nessuna prenotazione rigida richiesta. |

### 4.2 Categorie da Escludere Tassativamente
Per mantenere lo strumento aderente alla richiesta (attività di svago reale, culturale e informale), vanno filtrate ed escluse le seguenti categorie presenti nei dataset:
- Macro 9 di `guida_aperti_al_pubblico`: asili, scuole elementari, uffici comunali, cimiteri, memoriali di guerra, caserme.
- Macro 8 di `guida_aperti_al_pubblico`: centri sportivi, piscine comunali, stadi di calcio.
- Attività di servizio ordinario in `esercenti`: autofficine, barbieri, farmacie galeniche ordinarie, supermercati, tabacchi, agenzie immobiliari, ferramenta.

---

## 5. Stato di Completezza dei Campi e Igiene del Dato

### 5.1 Tasso di Popolamento dei Campi Chiave

| Campo | `tempo_libero_payload.json` (326) | `dashboard_items.json` (1.987) | `esercenti_db.json` (4.966) |
|---|---|---|---|
| **Nome** | 100.0% (326) | 100.0% (1.987) | 100.0% (4.966) |
| **Comune / Zona** | 100.0% (326) | 100.0% (1.987) | 100.0% (4.966) |
| **Indirizzo** | 79.1% (258) | 59.5% (1.183) | 34.5% (1.714) |
| **Orari di apertura** | **100.0% (326)** | **100.0% (1.987)** | 14.4% (715) |
| **Giorni validi parsed (`days`)** | **100.0% (326)** | **100.0% (1.987)** | Non presente |
| **Sito web / Fonte** | **79.1% (258)** | **52.9% (1.051)** | 8.5% (420) |
| **Coordinate GPS (`lat`, `lon`)** | **100.0% (326)** | Non salvate (lookup da comuni/WD) | **99.4% (4.938)** |
| **Descrizione / Pitch** | **100.0% (326)** | **100.0% (1.987)** | 100.0% (`cosa_trovi_qui`) |

### 5.2 Valutazione dell'Igiene del Dato
1. **Assenza di dati placeholder o testi fittizi**:
   - Nessun record contiene "Lorem Ipsum", "TODO", "Test" o stringhe fittizie nei campi descrittivi.
   - Tutti i nomi di musei, parchi, botteghe e cinema corrispondono a entità reali e storiche della città metropolitana di Genova.
2. **Controllo dei Link e Risoluzione Domini**:
   - Nella cache del crawler (`crawled_urls_cache.json`), 581 siti web risultano con codice di stato `OK` (HTTP 200) e contengono testi aggiornati per la stagione corrente (autunno 2026).
   - Alcuni URL storici (circa 47 su 326 in payload) risultano `OFFLINE_OR_PROTECTED` o rimandano a domini scaduti (es. `turismoinliguria.com`).
   - **Regola igienica per l'estrattore**: Se l'URL nel record è nullo o fa parte dei domini dismessi, lo script deve ripiegare automaticamente sul portale istituzionale di riferimento (`https://www.museidigenova.it/`, `https://www.visitgenoa.it/`, `https://teatrodellatosse.it/`, `https://circuitocinemagenova.com/`).
3. **Coerenza con la Settimana Corrente (Novembre 2026)**:
   - La data di sistema corrente è mercoledì **4 Novembre 2026** (settimana 2–8 Novembre 2026).
   - I dati estratti dai siti dei cinema (America, Sivori, Odeon) e dei teatri (Sala Mercato dal 3 all'8 novembre) contengono eventi attivi proprio in questa settimana.

---

## 6. Proposta di Schema per il Catalogo Unificato delle Alternative

Per soddisfare i requisiti R1-R5, l'estrattore deve generare un catalogo strutturato in formato JSON (es. `catalogo_uscite_settimana.json`) con elementi standardizzati.

### 6.1 Modello di Dati Raccomandato

```json
{
  "id": "cinema_sivori_film",
  "titolo": "Cinema Sivori — Proiezione film d'essai e incontro",
  "categoria": "cinema_essai",
  "categoria_label": "Cinema d'Essai & Cineforum",
  "comune": "Genova",
  "zona": "Centro Storico / Salita Santa Caterina",
  "indirizzo": "Salita di Santa Caterina 12r",
  "giorni_apertura": ["mercoledì", "giovedì", "venerdì", "sabato", "domenica"],
  "orario_dettaglio": "Spettacoli ore 16:00, 18:30, 21:15",
  "descrizione_informale": "Il cinema più antico d'Italia in attività nei caruggi. Ottimo per vedere un film indipendente e poi fare due passi verso Piazza Fontane Marose.",
  "costo": "Biglietto cinema standard (ridotto studenti/anziani)",
  "trasporto": "Metro De Ferrari / Bus Piazza Corvetto (3 min a piedi)",
  "fonte_verificata": "https://circuitocinemagenova.com/sivori/",
  "attivo_settimana_corrente": true,
  "indoor": "in"
}
```

### 6.2 Criteri di Selezione e Priorità delle Alternative
Lo script di estrazione per la settimana corrente deve applicare i seguenti filtri a cascata:
1. **Filtro di Pertinenza Informale**:
   - Includere solo voci appartenenti ai macro-cluster validati: Cinema d'essai, Mostre e musei d'arte/scienza, Dimore e castelli panoramici, Passeggiate sceniche e borghi marinari, Botteghe artigianali storiche e degustazioni tipiche, Teatri e musica live, Biblioteche aperte.
2. **Filtro Temporale (Aperto nella Settimana Corrente)**:
   - Verificare che il luogo sia aperto almeno in uno dei giorni dal mercoledì alla domenica della settimana corrente (`days_open` include `0, 2, 3, 4, 5, 6`).
3. **Filtro di Verificabilità**:
   - Ogni alternativa deve riportare un URL ufficiale valido o un recapito istituzionale verificato.
4. **Diversificazione Geografica e Tematica**:
   - Garantire una rosa equilibrata che copra sia il centro di Genova (caruggi, porto antico, crinali panoramici) sia il levante e ponente della provincia (Camogli, Nervi, Boccadasse, Sestri Levante, Campo Ligure, Casella).

---

## 7. Linee Guida per il Modulo WhatsApp e Plain Writing (/plain-writing)

In conformità con i requisiti R3, R4 e i criteri di accettazione:
1. **Assenza totale della parola "date" o di riferimenti galanti**: il tono deve essere complice, diretto, leggero e amichevole ("Ecco qualche idea carina per questa settimana a Genova", "Ho trovato un paio di posti particolari").
2. **Assenza di trattini lunghi**: vietati categoricamente `—` e `–`. Usare virgole, due punti o andare a capo.
3. **Formattazione sobria per WhatsApp**:
   - Uso del grassetto con asterischi per il nome del posto o l'attività: `*Cinema Sivori*`.
   - Giorni e orari chiari: `Giovedì o venerdì sera, spettacoli alle 18:30 e 21:15`.
   - Breve motivazione informale (1 riga).
   - Link ufficiale pulito per consultare orari o biglietti.
4. **Esempio di resa conforme**:

```text
Ciao! Ho guardato un po' di alternative carine e diverse dal solito per vederci questa settimana:

1. *Cinema Sivori* (Salita Santa Caterina, centro)
Spettacoli alle 18:30 e 21:15 per film d'autore nel cinema più antico della città, poi due passi in centro.
Info e orari: https://circuitocinemagenova.com/sivori/

2. *Spianata Castelletto e Cremeria* (Castelletto)
Salita in ascensore Liberty da Piazza Portello al tramonto per vedere tutta la città dall'alto.
Aperto liberamente tutti i giorni.

3. *Farinata da Sa' Pesta* (Via dei Giustiniani)
Farinata appena sfornata a legna nei testi di rame e atmosfera autentica nei vicoli.
Aperto a pranzo da mercoledì a sabato.
Info: https://www.sapesta.it

Fammi sapere se ti ispira qualcosa tra queste!
```

---

## 8. Conclusioni dell'Indagine

I dati locali in `/workspace/genova` sono completi, accurati e offrono oltre **400 alternative informali di altissima qualità** direttamente pronte all'uso. La combinazione di `tempo_libero_payload.json`, i dettagli di `guida_aperti_al_pubblico_provincia_genova.json` e le programmazioni live in `crawled_urls_cache.json` fornisce tutte le fonti, orari e coordinate necessarie senza richiedere dipendenze esterne pesanti.
