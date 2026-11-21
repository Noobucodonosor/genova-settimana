# Analisi delle Fonti di Verifica Live e Specifiche Tecniche — Genova e Provincia

Data indagine: 2026-11-04  
Ambito: Uscite informali, tempo libero culturale e percorsi verificabili per la settimana corrente a Genova e provincia.

---

## 1. Executive Summary

La presente specifica analizza e definisce l'ecosistema di **fonti ufficiali, verificabili e live** per alimentare lo strumento delle uscite settimanali informali a Genova e provincia.

A differenza di strumenti generici basati su memorie statiche (soggette ad allucinazioni, eventi scaduti o luoghi chiusi per restauro), il sistema implementa un'architettura di verifica a 4 livelli (Dataset Locale Curato -> Reachability HTTP/TLS -> Parsing Temporale Settimanale -> Regole di Sicurezza Meteo/Accessibilità).

L'indagine ha identificato con successo gli endpoint primari per le 5 categorie d'interesse e ha individuato casi limite critici (come la chiusura per lavori PNRR del Museo di Arte Contemporanea di Villa Croce e la correzione di domini obsoleti per i cineclub e le biblioteche).

---

## 2. Features Discovered

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | Cinema d'Essai | Circuito Cinema Genova (Sivori, Ariston, Corallo, City, Odeon, America) | Programmazione cinematografica d'autore, rassegne VOS (versione originale sottotitolata), orari spettacoli per ogni sala del circuito. | Slug sala (`sivori`, `ariston`, `corallo`, `city`, `odeon`, `america`) | Lista film, sale, orari giornalieri, URL acquisto/scheda film | Pagina di cortesia o fallback su `/programmazione/` generale | Live probe `circuitocinemagenova.com` & REST API `wp-json/` |
| 2 | Cinema d'Essai | Cineclub Nickelodeon | Cinema d'essai storico e cineforum genovese in Via della Consolazione 5r. Programmazione giornaliera aggiornata e rassegne. | Data corrente / settimana | Titolo film, registi, orari spettacoli (`16:00`, `18:30`, `21:00`), rassegne | Timeout su HTTP chiaro; richiede `https://www.cineclubnickelodeon.it/` | Live probe & web search |
| 3 | Cinema d'Essai | Club Amici del Cinema (Sampierdarena) | Cineclub storico FICC e sala d'essai a Sampierdarena (Via Rolando 15). Rassegne d'autore, documentari e cineforum. | Data corrente / settimana | Titolo film in programmazione, orari feriali (21:00) e weekend (15:30, 18:30, 21:00), feed RSS | Dominio corretto `clubamicidelcinema.it` (vecchio `amicidelcinema.it` non risolve DNS) | Live probe & DNS check |
| 4 | Mostre & Arte | Palazzo Ducale — Mostre Temporanee | Grandi mostre d'arte contemporanea, fotografia e collezioni internazionali negli spazi del Ducale (Sottoporticato, Loggia degli Abati, Scalone). | Query `/mostre/` | Elenco mostre attive, date inizio/fine, sede interna, orari apertura (Mar-Dom 10-19, Ven fino 21) | Se scaduta o terminata: esclusione automatica dal filtro temporale | Live probe `palazzoducale.genova.it/mostre/` |
| 5 | Mostre & Arte | Palazzo Ducale — Eventi Culturali e Incontri | Incontri a ingresso libero, conferenze serali, presentazioni editoriali e dibattiti nelle sale del Maggior/Minor Consiglio. | Query `/eventi/` | Titolo conferenza, orario esatto (es. 20:30), relatore, sala, gratuità | Se vuoto o posticipato: nessun evento proposto per il giorno | Live probe `palazzoducale.genova.it/eventi/` |
| 6 | Mostre & Arte | Polo Museale di Nervi (GAM, Raccolte Frugone, Wolfsoniana) | Arte moderna, bronzi Belle Époque e collezioni di arti decorative e design Novecento (Wolfsoniana) nelle ville storiche dei Parchi di Nervi. | URL musei di Nervi | Orari feriali/festivi (Mar-Dom 11:00-17:00 inverno), tariffe, percorsi nel parco | Chiuso il lunedì; escluso automaticamente il lunedì | Live probe `museidigenova.it` e `wolfsoniana.it` |
| 7 | Mostre & Arte | Musei di Strada Nuova (Palazzo Rosso, Palazzo Bianco, Palazzo Tursi) | Complesso museale UNESCO di Via Garibaldi con pinacoteca, arredi storici e terrazza panoramica Mirador. | Data / giorno della settimana | Orari feriali e festivi (Mar-Ven 9-19, Sab-Dom 10-19, Lun chiuso), ingresso residenti domenicale | Chiusura settimanale Lunedì; redirect 301 gestito | Live probe `museidigenova.it/it/musei-di-strada-nuova` |
| 8 | Mostre & Arte | Castello D'Albertis — Museo delle Culture del Mondo | Castello neogotico con collezioni etnografiche, erboristiche e parco dei bastioni; accesso con ascensore panoramico Montegalletto. | Data / giorno della settimana | Orari apertura (Mar-Ven 10-17/18, Sab-Dom 10-18/19), info ascensore AMT | Chiuso Lunedì | Live probe `museidigenova.it` |
| 9 | Mostre & Arte (Negative Filter) | Museo d'Arte Contemporanea di Villa Croce | Verifica stato di accessibilità e orari per il museo di Carignano. | URL Villa Croce su museidigenova.it | Status: CHIUSO AL PUBBLICO per lavori PNRR a decorrere da gennaio 2025 fino a nuova comunicazione | Segnalazione automatica di inaccessibilità; esclusione dal set mostre | Live extraction del banner ufficiale "Chiuso al pubblico" |
| 10 | Biblioteche & Spazi Studio | Biblioteca Civica Berio | Biblioteca monumentale centrale in Via del Seminario 16: sale studio, chiostro affrescato, caffetteria e mostre bibliografiche. | Giorno / orario | Orari Lun-Ven 8:00-19:00, Sab 8:00-13:00; Domenica chiuso | Vecchia route `/content/...` restituisce 404; route ufficiale verificata `/berio` | Live probe `bibliotechedigenova.it/berio` |
| 11 | Biblioteche & Spazi Studio | Biblioteca De Amicis al Porto Antico | Biblioteca affacciata sulla darsena nei Maggioni del Cotone; spazio lettura, laboratori per ragazzi e fumetto. | Giorno / orario | Orari Lun-Sab 9:00-19:00, Domenica chiuso | Route corretta `/de-amicis` | Live probe `bibliotechedigenova.it/de-amicis` |
| 12 | Biblioteche & Spazi Studio | Biblioteca Universitaria di Genova | Saloni monumentali Art Déco nell'ex Grand Hotel Colombia in Piazza Acquaverde / Via Balbi. | Giorno feriale | Orari Lun-Ven 8:30-18:30; weekend chiuso | Chiuso Sab-Dom | Live probe `bibliotecauniversitaria.ge.it` |
| 13 | Passeggiate & Percorsi | Spianata Castelletto (Belvedere Montaldo) | Belvedere panoramico sui tetti del centro antico e sul porto; risalita con ascensore Liberty Portello-Castelletto. | Sempre aperto (outdoor) | Accesso 24/7; orari ascensore AMT 06:40-24:00; bar storici attivi | In caso di vento forte/allerta: fruibile a piedi via Salita della Spianata | Live probe `visitgenoa.it/it/spianata-castelletto_` |
| 14 | Passeggiate & Percorsi | Passeggiata Anita Garibaldi (Nervi) & Parchi | Percorso pedonale litoraneo di 2 km a picco sulla scogliera tra il porticciolo di Nervi e Capolungo, collegato ai Parchi e Roseto. | Sempre aperto (outdoor) | Accessibile dall'alba al tramonto; parchi 08:00-19:00/21:00 | Chiusura straordinaria in caso di mareggiate intense o allerta meteo | Live probe `visitgenoa.it/it/parchi-di-nervi-1` |
| 15 | Passeggiate & Percorsi | Borgo Marinaro di Boccadasse & Belvedere Capo Santa Chiara | Antico borgo marinaro alla fine di Corso Italia: ciottoli, barche da pesca, gelato e creuza panoramica verso Vernazzola. | Sempre aperto (outdoor) | Accesso libero h24; locali e creuza aperti | In caso di mareggiata l'accesso alla spiaggetta è sconsigliato | Live probe `visitgenoa.it/en/node/21375` |
| 16 | Passeggiate & Percorsi | Parco Urbano delle Mura, Righi & Forte Diamante | Sentieri panoramici dell'anello dei Forti lungo le mura seicentesche più lunghe d'Europa; risalita da Piazza della Zecca con funicolare storica. | Giorno della settimana | Funicolare Zecca-Righi (attiva 06:40-24:00); sentieri sempre aperti alla luce diurna | Sconsigliato con nebbia fitta, piogge o dopo il tramonto | Live probe `visitgenoa.it/it/parco-urbano-delle-mura-e-forti` |
| 17 | Passeggiate & Percorsi | Acquedotto Storico di Genova | Percorso pedonale lungo l'antico acquedotto medievale/ottocentesco in Val Bisagno (Ponte Sifone, Cavassolo, Staglieno). | Luce diurna | Sentiero pedonale pianeggiante libero h24; fermate bus AMT di supporto | Dominio terzi `acquedottostorico.it` non attivo; fonte autorevole Visit Genoa `/it/la-dellacqua-acquedotto-storico-di-genova` | Live probe & search web |
| 18 | Musica, Circoli & Club | Giardini Luzzati Spazio Comune | Circolo sociale e culturale nel centro storico: concerti dal vivo nel weekend, dj set, laboratori, cinema e area ristoro all'aperto. | Giorno e fascia oraria | Programmazione live settimanale (es. ven/sab), orari bar/spazio (10:00-24:00) | In caso di pioggia gli eventi all'aperto si spostano nell'Area Archeologica sotterranea | Live probe `giardiniluzzati.it` & feed social/stampa |
| 19 | Musica, Circoli & Club | Count Basie Jazz Club | Storico jazz club di Genova in Vico Tana 20r: musica dal vivo (jazz, blues, cantautorato, jam session) il fine settimana. | Data del weekend | Concerti Ven/Sab (apertura 20:45, live 21:15) e Dom (apertura 18:00, evento 18:30); prenotazione obbligatoria online | Accesso con tessera ARCI e prenotazione web; senza prenotazione ingresso non garantito | Live probe `countbasie.it` |
| 20 | Musica, Circoli & Club | La Claque in Agorà / Fondazione Luzzati Teatro della Tosse | Club live e sala per concerti, stand-up comedy e rassegne in Vico San Donato / Piazza Renato Negri. | Giorno infrasettimanale / weekend | Calendario spettacoli e concerti settimanali (inizio ore 21:00/21:30) | La route standard usa estensione `.htm` (`calendario.htm`), URL `.php` o cartelle nude reindirizzano a 404 | Live probe `teatrodellatosse.it/la-claque/` |

---

## 3. Edge Cases & Anomalie Verificate sul Campo

| # | Feature / Ente | Input Testato | Comportamento Rilevato | Causa e Azione di Validazione nel Tool |
|---|----------------|---------------|------------------------|----------------------------------------|
| E1 | Museo di Villa Croce | URL `.../it/museo-darte-contemporanea-di-villa-croce` | HTTP 200, ma la pagina espone il testo: *"Il Museo di Arte Contemporanea di Villa Croce rimane chiuso al pubblico... per lavori PNRR"* | **Regola Anti-Chiusura**: I parser devono scansionare le keyword di indisponibilità (`chiuso al pubblico`, `lavori in corso`, `fino a data da destinarsi`). L'ente deve essere escluso dalle proposte museali attive. |
| E2 | Cineclub Nickelodeon | `http://www.cineclubnickelodeon.it/` | Connection timeout su porta 80 | **Regola TLS**: Forzare protocollo `https://` con timeout di 5s. La versione HTTPS risponde regolarmente HTTP 200. |
| E3 | Club Amici del Cinema | `https://amicidelcinema.it/` | Errore DNS: `nodename nor servname provided` | **Regola Dominio Ufficiale**: Il dominio corretto registrato dall'associazione è `http://www.clubamicidelcinema.it/`. Il tool deve utilizzare l'host verificato. |
| E4 | Biblioteche di Genova (Berio / De Amicis) | `https://www.bibliotechedigenova.it/content/biblioteca-civica-berio` | HTTP 404 Not Found | **Regola Migrazione CMS**: Il portale ha migrato a route pulite: `/berio` e `/de-amicis`. Entrambi restituiscono HTTP 200. |
| E5 | Acquedotto Storico | `https://www.acquedottostorico.it/` | DNS non risolvibile | **Regola Istituzionale**: I siti amatoriali o di vecchi progetti possono scadere. La fonte autorevole persistente è il portale istituzionale Visit Genoa (`/it/la-dellacqua-acquedotto-storico-di-genova`). |
| E6 | Spianata Castelletto / Nervi | `https://www.visitgenoa.it/it/spianata-castelletto` | HTTP 301 / redirect a `.../spianata-castelletto_` | **Regola Segui-Redirect**: I client HTTP devono seguire fino a 3 redirect (HTTP 301/302) per raggiungere la risorsa canonical. |
| E7 | Allerta Idrogeologica Regionale | Giornate con bollettino di allerta arancione o rossa emesso da ARPAL / Protezione Civile Liguria | La Lanterna chiude le terrazze esterne; i Parchi di Nervi chiudono i cancelli; la Biblioteca Berio chiude in allerta rossa | **Filtro Sicurezza Ambientale**: Il generatore deve includere una nota prudenziale o escludere parchi e passeggiate a mare in caso di maltempo severo. |
| E8 | Orari Museali del Lunedì | Query per il giorno `Lunedì` | Quasi tutti i musei civici (Strada Nuova, Nervi, D'Albertis) sono chiusi il lunedì | **Regola Filtro Giornaliero**: Non proporre mai musei chiusi il lunedì. Fanno eccezione: Palazzo Ducale (mostre spesso aperte il lunedì pomeriggio), Acquario di Genova (aperto 7/7) e Museo Diocesano (aperto il lunedì). |

---

## 4. Protocollo di Verifica Live e Validazione Web

Per garantire il rispetto dei requisiti di veridicità (**R1**, **R5**) e prevenire allucinazioni o proposte obsolete:

### 4.1. Architettura di Validazione a 4 Livelli

```
[Layer 1: Catalogo Locale Autorizzato]
         │ (ID, Nome, Tipologia, Indirizzo, Coordinate, URL Ufficiale)
         ▼
[Layer 2: Sonda di Raggiungibilità Web & TLS]
         │ Verifica HTTP 200 su URL ufficiale dell'ente (timeout 5s, follow redirects)
         ▼
[Layer 3: Filtro Temporale Settimanale & Parsing Contenuti]
         │ 1. Verifica che la data dell'evento ricada nella settimana corrente (Lun-Dom)
         │ 2. Verifica che il giorno dell'uscita coincida con i giorni di apertura ordinaria
         │ 3. Scansione blacklist semantica ("chiuso per restauro", "annullato", "sold out")
         ▼
[Layer 4: Normalizzazione Dati & Data Contract]
         │ Generazione record validato conforme a JSON Schema
         ▼
[Output per Selezione Interattiva & Plain Writing WhatsApp]
```

### 4.2. Regole di Validazione Temporale
1. **Ancoraggio Settimanale**: La settimana corrente è definita dall'intervallo ISO: da lunedì ore `00:00` a domenica ore `23:59` della settimana di esecuzione.
2. **Eventi a Data Fissa (Mostre temporanee, concerti, conferenze)**:
   - Se l'evento ha una data singola, essa deve cadere esattamente nell'intervallo settimanale.
   - Se l'evento è un intervallo (es. mostre del Ducale `15 ott 2026 — 02 mag 2027`), il tool verifica che l'intervallo copra la settimana corrente.
3. **Attività Ricorrenti / Spazi Permanenti (Biblioteche, botteghe, passeggiate)**:
   - Viene verificato il campo `days_open` rispetto al giorno specificato nell'alternativa (es. Berio aperta solo Lun-Sab, domenica esclusa).
   - Viene verificata la compatibilità della fascia oraria (`mattina`, `pomeriggio`, `sera`).

### 4.3. Prevenzione Dati Fittizi e Allucinazioni
- **Nessuna proposta inventata**: Il generatore può produrre proposte solo se supportate da:
  1. Un URL ufficiale HTTP 200 raggiungibile appartenente alla whitelist degli enti verificati;
  2. Un riscontro effettivo nel dataset di riferimento del territorio metropolitano (`tempo_libero_dataset.json`, `guida_aperti_al_pubblico_provincia_genova.json`).
- **Nessun placeholder**: Campi obbligatori come `indirizzo`, `giorno`, `orario` e `url` devono essere completi; è vietato usare stringhe come `TBD`, `N/D` o orari fittizi `00:00`.

---

## 5. Data Contract per Voci Validate

Tutte le alternative passate al modulo di selezione interattiva e formattazione devono rispettare rigorosamente il seguente schema dati:

### 5.1. Schema JSON (Draft-07)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "VerifiedOutingEntry",
  "type": "object",
  "required": [
    "id",
    "title",
    "category",
    "municipality_zone",
    "venue_address",
    "day_of_week",
    "time_slot",
    "verified_hours",
    "verified_url",
    "description",
    "source_type",
    "verification_timestamp",
    "status"
  ],
  "properties": {
    "id": {
      "type": "string",
      "pattern": "^[a-z0-9_]+$",
      "description": "Identificativo univoco normalizzato snake_case"
    },
    "title": {
      "type": "string",
      "minLength": 3,
      "maxLength": 120,
      "description": "Nome dell'attività, evento o luogo"
    },
    "category": {
      "type": "string",
      "enum": [
        "cinema_dessai",
        "mostra_arte",
        "spazio_studio_lettura",
        "passeggiata_panoramica",
        "musica_live_circolo",
        "laboratorio_culturale",
        "bottega_storica"
      ]
    },
    "municipality_zone": {
      "type": "string",
      "description": "Comune o quartiere di Genova (es. Genova Centro Storico, Genova Nervi, Camogli, Chiavari)"
    },
    "venue_address": {
      "type": "string",
      "description": "Indirizzo civico completo e verificabile"
    },
    "day_of_week": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]
      },
      "minItems": 1
    },
    "time_slot": {
      "type": "string",
      "enum": ["mattina", "pomeriggio", "sera", "giornata_intera"]
    },
    "verified_hours": {
      "type": "string",
      "description": "Orario effettivo verificato (es. '10:00-19:00', 'Ore 21:15')"
    },
    "verified_url": {
      "type": "string",
      "format": "uri",
      "description": "URL ufficiale o istituzionale raggiungibile (HTTP 200)"
    },
    "description": {
      "type": "string",
      "description": "Descrizione concisa e naturale dell'attività (plain writing, senza trattini lunghi o enfasi da marketing)"
    },
    "source_type": {
      "type": "string",
      "enum": ["web_live", "local_verified"]
    },
    "verification_timestamp": {
      "type": "string",
      "format": "date-time"
    },
    "status": {
      "type": "string",
      "enum": ["verified_active", "temporarily_closed", "weather_dependent"]
    }
  }
}
```

### 5.2. Esempi di Record Convalidati per la Settimana Corrente (Novembre 2026)

#### Record 1: Mostra Temporanea (Web Live)
```json
{
  "id": "palazzo_ducale_renoir_monet",
  "title": "Mostra Renoir, Monet, Toulouse-Lautrec, Cézanne (Collezione Scharf)",
  "category": "mostra_arte",
  "municipality_zone": "Genova Centro Storico",
  "venue_address": "Piazza Giacomo Matteotti 9, 16123 Genova",
  "day_of_week": ["martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"],
  "time_slot": "pomeriggio",
  "verified_hours": "Mar-Dom 10:00-19:00 (Ven fino alle 21:00, Lun chiuso)",
  "verified_url": "https://palazzoducale.genova.it/mostra/renoir-monet-toulouse-lautrec-cezanne/",
  "description": "Capolavori dell'impressionismo e post-impressionismo nel sottoporticato dei Dogi.",
  "source_type": "web_live",
  "verification_timestamp": "2026-11-04T10:08:00Z",
  "status": "verified_active"
}
```

#### Record 2: Musica Live / Circolo Culturale (Web Live)
```json
{
  "id": "count_basie_gatto_nero",
  "title": "Concerto Gatto Nero Gatto Bianco (Folk balcanico e klezmer)",
  "category": "musica_live_circolo",
  "municipality_zone": "Genova Centro",
  "venue_address": "Vico Tana 20r, 16126 Genova",
  "day_of_week": ["venerdì"],
  "time_slot": "sera",
  "verified_hours": "Apertura ore 20:45, inizio concerto ore 21:15",
  "verified_url": "https://www.countbasie.it/",
  "description": "Serata di ritmi tarantolati e klezmer in vico Tana. Necessaria prenotazione online e tessera Arci.",
  "source_type": "web_live",
  "verification_timestamp": "2026-11-04T10:10:00Z",
  "status": "verified_active"
}
```

#### Record 3: Spazio Lettura / Biblioteca Monumentale (Local Verified)
```json
{
  "id": "biblio_civica_berio",
  "title": "Biblioteca Civica Berio e Caffetteria del Seminario",
  "category": "spazio_studio_lettura",
  "municipality_zone": "Genova Centro",
  "venue_address": "Via del Seminario 16, 16121 Genova",
  "day_of_week": ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato"],
  "time_slot": "pomeriggio",
  "verified_hours": "Lun-Ven 08:00-19:00, Sab 08:00-13:00",
  "verified_url": "https://www.bibliotechedigenova.it/berio",
  "description": "La biblioteca centrale nel seicentesco Seminario dei Chierici, con cortile interno silenzioso e caffetteria.",
  "source_type": "local_verified",
  "verification_timestamp": "2026-11-04T10:05:00Z",
  "status": "verified_active"
}
```

#### Record 4: Passeggiata Panoramica (Local Verified / Weather Dependent)
```json
{
  "id": "passeggiata_nervi_anita_garibaldi",
  "title": "Passeggiata Anita Garibaldi e Parchi di Nervi",
  "category": "passeggiata_panoramica",
  "municipality_zone": "Genova Nervi",
  "venue_address": "Passeggiata Anita Garibaldi, 16167 Genova Nervi",
  "day_of_week": ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"],
  "time_slot": "pomeriggio",
  "verified_hours": "Sempre accessibile alla luce diurna",
  "verified_url": "https://www.visitgenoa.it/it/parchi-di-nervi-1",
  "description": "Due chilometri di camminata a pelo d'acqua sugli scogli fino a Capolungo, tra pini marittimi e roseto.",
  "source_type": "local_verified",
  "verification_timestamp": "2026-11-04T10:10:00Z",
  "status": "weather_dependent"
}
```

---

## 6. Politiche di Fallback e Resilienza

1. **Web Source Unreachable (Network timeout / 5xx error)**:
   - Se il sito web di un ente non risponde entro 5 secondi (3 tentativi), il sistema non fallisce l'intera esecuzione.
   - Per gli spazi a orario stabile (biblioteche civiche, parchi storici, belvedere, musei permanenti), il record viene marcato con `source_type: "local_verified"` attingendo ai dati convalidati di `tempo_libero_dataset.json`.
   - Per gli eventi estemporanei (concerti, spettacoli a data singola), se la fonte live non è raggiungibile o non conferma la data esatta, l'evento **non viene emesso** per evitare allucinazioni su orari o artisti non presenti.
2. **Rate Limiting & Politeness**:
   - Tutte le chiamate web devono impostare un `User-Agent` descrittivo e un intervallo minimo di 200ms tra richieste consecutive verso lo stesso host.
3. **Caching Dinamico**:
   - I risultati delle interrogazioni live possono essere memorizzati in una cache locale su disco (con TTL di 6 ore) per garantire esecuzioni istantanee nelle sessioni interattive dell'utente.
