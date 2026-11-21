"""Catalog aggregator and normalizer for Genova Weekly Informal Outings.

Aggregates verified leisure and cultural options for the current week from:
1. Local verified datasets (`tempo_libero_payload.json`, `guida_aperti_al_pubblico`,
   `dashboard_items.json`, `esercenti_genova_provincia_db`).
2. Authoritative live verified endpoints (Circuito Cinema, Cineclub Nickelodeon,
   Palazzo Ducale, Berio, De Amicis, Count Basie, La Claque, Giardini Luzzati, etc.).

Enforces:
- Negative filters (explicitly blacklists closed venues like Villa Croce).
- Plain-writing data hygiene (sanitizes em/en dashes, hype words, and romance terms).
- Category normalization to OutingCategory enum.
- Live reachability verification when requested.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set

from genova_outings.models import OutingCategory, OutingOption
from genova_outings.verifier import (
    clean_url,
    is_blacklisted_venue,
    is_weather_dependent_venue,
    probe_url_reachability,
    probe_urls_batch,
    sanitize_text,
    verify_outing,
)

logger = logging.getLogger(__name__)

# Base directory for local datasets
DEFAULT_DATA_DIR = Path("/Users/dany/genova")

# Authoritative live verified entities for current-week informal outings in Genova
AUTHORITATIVE_LIVE_OUTINGS: List[Dict[str, object]] = [
    {
        "id": "circuito_cinema_sivori",
        "title": "Cinema Sivori: Rassegna d'Essai e Prime Visioni",
        "category": OutingCategory.CINEMA,
        "venue": "Cinema Sivori",
        "zone": "Centro",
        "address": "Salita Santa Caterina 12",
        "day_time": "Da martedì a domenica ore 16:00 / 18:30 / 21:15",
        "verified_url": "https://circuitocinemagenova.com/sivori/",
        "description": "Lo storico cinema d'essai nel cuore della città, con film d'autore in lingua originale sottotitolata e rassegne tematiche.",
        "source_type": "live_web",
        "is_weather_dependent": False,
        "time_slot": "sera",
        "cost_info": "Biglietto 7-9€ (ridotto cineclub)",
        "is_free": False,
        "tags": ["indoor", "lingua_originale", "essai"],
    },
    {
        "id": "circuito_cinema_america",
        "title": "Cinema America: Proiezioni d'Autore",
        "category": OutingCategory.CINEMA,
        "venue": "Cinema America",
        "zone": "Centro / Foce",
        "address": "Via Colombo 11",
        "day_time": "Tutti i giorni ore 16:00 / 18:45 / 21:00",
        "verified_url": "https://circuitocinemagenova.com/america/",
        "description": "Sala d'autore a pochi passi da Piazza Brignole, con proiezioni pomeridiane e serali del circuito indipendente.",
        "source_type": "live_web",
        "is_weather_dependent": False,
        "time_slot": "sera",
        "cost_info": "Biglietto 7-9€",
        "is_free": False,
        "tags": ["indoor", "essai"],
    },
    {
        "id": "circuito_cinema_odeon",
        "title": "Cinema Odeon: Cinema e Cultura",
        "category": OutingCategory.CINEMA,
        "venue": "Cinema Odeon",
        "zone": "Foce / Albaro",
        "address": "Corso Buenos Aires 83",
        "day_time": "Tutti i giorni ore 16:00 / 18:30 / 21:15",
        "verified_url": "https://circuitocinemagenova.com/odeon/",
        "description": "Polo cinematografico della Foce con programmazione settimanale di cinema italiano e internazionale contemporaneo.",
        "source_type": "live_web",
        "is_weather_dependent": False,
        "time_slot": "sera",
        "cost_info": "Biglietto 7-9€",
        "is_free": False,
        "tags": ["indoor"],
    },
    {
        "id": "cineclub_nickelodeon",
        "title": "Cineclub Nickelodeon: Rassegna Cineforum e Cinema di Ricerca",
        "category": OutingCategory.CINEMA,
        "venue": "Cineclub Nickelodeon",
        "zone": "Centro",
        "address": "Via della Consolazione 5r",
        "day_time": "Martedì-Domenica ore 16:00 / 18:30 / 21:00",
        "verified_url": "https://www.cineclubnickelodeon.it/",
        "description": "Cineclub storico genovese dedicato al cinema d'autore, retrospettive cinematografiche e festival indipendenti.",
        "source_type": "live_web",
        "is_weather_dependent": False,
        "time_slot": "sera",
        "cost_info": "Ingresso con tessera cineclub",
        "is_free": False,
        "tags": ["indoor", "cineforum", "indipendente"],
    },
    {
        "id": "club_amici_del_cinema",
        "title": "Club Amici del Cinema: Rassegna d'Essai di Quartiere",
        "category": OutingCategory.CINEMA,
        "venue": "Club Amici del Cinema",
        "zone": "Sampierdarena",
        "address": "Via Carlo Rolando 15",
        "day_time": "Lunedì-Venerdì ore 21:00; Sabato-Domenica ore 15:30 / 18:30 / 21:00",
        "verified_url": "http://www.clubamicidelcinema.it/",
        "description": "Presidio culturale attivo dal 1976 con rassegne a tema, incontri con registi e proiezioni di documentari.",
        "source_type": "live_web",
        "is_weather_dependent": False,
        "time_slot": "sera",
        "cost_info": "Biglietto 6€",
        "is_free": False,
        "tags": ["indoor", "cineclub"],
    },
    {
        "id": "ducale_mostra_impressionisti",
        "title": "Palazzo Ducale: Mostra Impressionisti e Avanguardie Collezione Scharf",
        "category": OutingCategory.MOSTRA,
        "venue": "Palazzo Ducale",
        "zone": "Centro",
        "address": "Piazza Giacomo Matteotti 9",
        "day_time": "Da martedì a domenica ore 10:00-19:00 (venerdì apertura serale fino alle 21:00)",
        "verified_url": "https://palazzoducale.genova.it/mostre/",
        "description": "Esposizione dedicata ai capolavori di Renoir, Monet, Cézanne e Toulouse-Lautrec allestita negli spazi del Sottoporticato.",
        "source_type": "live_web",
        "is_weather_dependent": False,
        "time_slot": "pomeriggio",
        "cost_info": "Biglietto mostra",
        "is_free": False,
        "tags": ["indoor", "mostra", "arte"],
    },
    {
        "id": "ducale_world_press_photo",
        "title": "Palazzo Ducale: World Press Photo 2026",
        "category": OutingCategory.MOSTRA,
        "venue": "Palazzo Ducale",
        "zone": "Centro",
        "address": "Piazza Giacomo Matteotti 9",
        "day_time": "Da martedì a domenica ore 10:00-19:00",
        "verified_url": "https://palazzoducale.genova.it/mostre/",
        "description": "La mostra internazionale di fotogiornalismo ospitata nella Loggia degli Abati, con gli scatti premiati dell'anno.",
        "source_type": "live_web",
        "is_weather_dependent": False,
        "time_slot": "pomeriggio",
        "cost_info": "Biglietto mostra",
        "is_free": False,
        "tags": ["indoor", "fotografia"],
    },
    {
        "id": "ducale_incontri_culturali",
        "title": "Palazzo Ducale: Incontri e Conferenze al Maggior Consiglio",
        "category": OutingCategory.LABORATORIO,
        "venue": "Palazzo Ducale",
        "zone": "Centro",
        "address": "Piazza Giacomo Matteotti 9",
        "day_time": "Mercoledì e giovedì ore 18:00 / 20:30",
        "verified_url": "https://palazzoducale.genova.it/eventi/",
        "description": "Rassegna di incontri aperti al pubblico su storia, letteratura e trasformazioni urbane nella Sala del Maggior Consiglio.",
        "source_type": "live_web",
        "is_weather_dependent": False,
        "time_slot": "sera",
        "cost_info": "Ingresso libero fino a esaurimento posti",
        "is_free": True,
        "tags": ["indoor", "conferenze", "cultura"],
    },
    {
        "id": "polo_museale_nervi_gam",
        "title": "Polo Museale di Nervi: Galleria d'Arte Moderna e Parchi",
        "category": OutingCategory.MOSTRA,
        "venue": "GAM Galleria d'Arte Moderna",
        "zone": "Nervi",
        "address": "Via Serra Gropallo 4",
        "day_time": "Da martedì a domenica ore 11:00-17:00 (lunedì chiuso)",
        "verified_url": "https://www.museidigenova.it/it/gam-galleria-darte-moderna",
        "description": "Collezioni dell'Ottocento e Novecento ligure all'interno di Villa Saluzzo Serra, immersa nel verde dei Parchi di Nervi.",
        "source_type": "live_web",
        "is_weather_dependent": False,
        "time_slot": "pomeriggio",
        "cost_info": "Biglietto museo (gratis la passeggiata nei parchi)",
        "is_free": False,
        "tags": ["indoor", "museo", "parco"],
    },
    {
        "id": "musei_strada_nuova",
        "title": "Musei di Strada Nuova: Palazzi Rosso, Bianco e Tursi",
        "category": OutingCategory.MOSTRA,
        "venue": "Musei di Strada Nuova",
        "zone": "Centro",
        "address": "Via Garibaldi 11",
        "day_time": "Martedì-Venerdì ore 09:00-19:00; Sabato-Domenica ore 10:00-19:00 (Lunedì chiuso)",
        "verified_url": "https://www.museidigenova.it/it/musei-di-strada-nuova",
        "description": "I palazzi dei Rolli con le quadrerie genovesi, il cannone di Paganini e la terrazza panoramica Mirador sulla città antica.",
        "source_type": "live_web",
        "is_weather_dependent": False,
        "time_slot": "pomeriggio",
        "cost_info": "Biglietto unico 3 musei",
        "is_free": False,
        "tags": ["indoor", "unesco", "arte"],
    },
    {
        "id": "castello_dalbertis",
        "title": "Castello D'Albertis: Museo delle Culture del Mondo e Parco",
        "category": OutingCategory.MOSTRA,
        "venue": "Castello D'Albertis",
        "zone": "Castelletto",
        "address": "Corso Dogali 18 (Ascensore Montegalletto)",
        "day_time": "Martedì-Venerdì ore 10:00-17:00; Sabato-Domenica ore 10:00-18:00 (Lunedì chiuso)",
        "verified_url": "https://www.museidigenova.it/it/castello-dalbertis-museo-delle-culture-del-mondo",
        "description": "Dimora neogotica del Capitano D'Albertis affacciata sul porto, con collezioni etno-antropologiche e parco panoramico.",
        "source_type": "live_web",
        "is_weather_dependent": False,
        "time_slot": "pomeriggio",
        "cost_info": "Biglietto museo",
        "is_free": False,
        "tags": ["indoor", "panoramico", "culture"],
    },
    {
        "id": "biblioteca_civica_berio",
        "title": "Biblioteca Civica Berio: Chiostro del Seicento e Spazio Lettura",
        "category": OutingCategory.BIBLIOTECA,
        "venue": "Biblioteca Civica Berio",
        "zone": "Centro",
        "address": "Via del Seminario 16",
        "day_time": "Lunedì-Venerdì ore 08:00-19:00; Sabato ore 08:00-13:00",
        "verified_url": "https://www.bibliotechedigenova.it/berio",
        "description": "La principale biblioteca civica cittadina nell'ex Seminario dei Chierici, con chiostro centrale alberato, emeroteca e caffetteria.",
        "source_type": "live_web",
        "is_weather_dependent": False,
        "time_slot": "pomeriggio",
        "cost_info": "Accesso libero",
        "is_free": True,
        "tags": ["indoor", "studio", "chiostro"],
    },
    {
        "id": "biblioteca_de_amicis",
        "title": "Biblioteca De Amicis: Spazio Lettura sul Mare al Porto Antico",
        "category": OutingCategory.BIBLIOTECA,
        "venue": "Biblioteca De Amicis",
        "zone": "Porto Antico",
        "address": "Magazzini del Cotone, 2° Modulo",
        "day_time": "Da lunedì a sabato ore 09:00-19:00",
        "verified_url": "https://www.bibliotechedigenova.it/de-amicis",
        "description": "Spazio di lettura e consultazione situato sul molo dei Magazzini del Cotone con ampie vetrate affacciate sul porto.",
        "source_type": "live_web",
        "is_weather_dependent": False,
        "time_slot": "pomeriggio",
        "cost_info": "Accesso libero",
        "is_free": True,
        "tags": ["indoor", "porto_antico", "libri"],
    },
    {
        "id": "biblioteca_universitaria",
        "title": "Biblioteca Universitaria di Genova: Salone Storico di Via Balbi",
        "category": OutingCategory.BIBLIOTECA,
        "venue": "Biblioteca Universitaria",
        "zone": "Principe",
        "address": "Via Balbi 40",
        "day_time": "Da lunedì a venerdì ore 08:30-18:30",
        "verified_url": "https://www.bibliotecauniversitaria.ge.it/",
        "description": "Spazio studio e ricerca nell'ex Hotel Colombia di fronte alla stazione Principe, con sale di consultazione aperte a tutti.",
        "source_type": "live_web",
        "is_weather_dependent": False,
        "time_slot": "pomeriggio",
        "cost_info": "Accesso libero",
        "is_free": True,
        "tags": ["indoor", "storico", "studio"],
    },
    {
        "id": "spianata_castelletto_belvedere",
        "title": "Spianata Castelletto: Belvedere Montaldo e Tetti di Genova",
        "category": OutingCategory.PASSEGGIATA,
        "venue": "Spianata Castelletto",
        "zone": "Castelletto",
        "address": "Belvedere Luigi Montaldo (raggiungibile con ascensore Liberty da Piazza Portello)",
        "day_time": "Sempre accessibile h24 (ascensore in servizio ore 06:40-24:00)",
        "verified_url": "https://www.visitgenoa.it/it/spianata-castelletto_",
        "description": "La terrazza panoramica che domina il centro storico, il porto e la sopraelevata. Ideale al tramonto o nelle sere limpide.",
        "source_type": "live_web",
        "is_weather_dependent": True,
        "time_slot": "flessibile",
        "cost_info": "Gratuito (ascensore AMT gratuito per residenti e turisti)",
        "is_free": True,
        "tags": ["outdoor", "panoramico", "tramonto"],
    },
    {
        "id": "passeggiata_nervi_anita_garibaldi",
        "title": "Passeggiata Anita Garibaldi: Scogliera e Parchi di Nervi",
        "category": OutingCategory.PASSEGGIATA,
        "venue": "Passeggiata di Nervi",
        "zone": "Nervi",
        "address": "Dal porticciolo di Nervi a Capolungo",
        "day_time": "Sempre accessibile h24 (parchi aperti ore 08:00-19:00)",
        "verified_url": "https://www.visitgenoa.it/it/parchi-di-nervi-1",
        "description": "Percorso pedonale lungo la scogliera a picco sul mare collegato ai parchi storici e al roseto.",
        "source_type": "live_web",
        "is_weather_dependent": True,
        "time_slot": "flessibile",
        "cost_info": "Accesso libero",
        "is_free": True,
        "tags": ["outdoor", "scogliera", "mare"],
    },
    {
        "id": "borgo_boccadasse_capo_chiara",
        "title": "Borgo di Boccadasse: Il Porticciolo dei Pescatori e Capo Santa Chiara",
        "category": OutingCategory.PASSEGGIATA,
        "venue": "Boccadasse",
        "zone": "Albaro / Boccadasse",
        "address": "Fine Corso Italia, Piazza Nettuno",
        "day_time": "Sempre accessibile h24",
        "verified_url": "https://www.visitgenoa.it/en/node/21375",
        "description": "L'antico borgo marinaro con case pastello sulla spiaggia di ciottoli, la creusa verso Capo Santa Chiara e vista sul monte di Portofino.",
        "source_type": "live_web",
        "is_weather_dependent": True,
        "time_slot": "flessibile",
        "cost_info": "Accesso libero",
        "is_free": True,
        "tags": ["outdoor", "borgo", "mare"],
    },
    {
        "id": "parco_mura_funicolare_righi",
        "title": "Parco Urbano delle Mura: Funicolare Zecca-Righi e Forti",
        "category": OutingCategory.PASSEGGIATA,
        "venue": "Parco delle Mura e Funicolare Righi",
        "zone": "Righi",
        "address": "Partenza Funicolare Largo Zecca, arrivo Righi Belvedere",
        "day_time": "Funicolare attiva ore 06:40-24:00, sentieri percorribili con luce diurna",
        "verified_url": "https://www.visitgenoa.it/it/parco-urbano-delle-mura-e-forti",
        "description": "Sentiero panoramico lungo la cinta muraria secentesca che collega Forte Castellaccio, Sperone e Diamante con vista sulle vallate.",
        "source_type": "live_web",
        "is_weather_dependent": True,
        "time_slot": "flessibile",
        "cost_info": "Sentieri gratuiti; funicolare integrata rete urbana AMT",
        "is_free": True,
        "tags": ["outdoor", "trekking_urbano", "panoramico"],
    },
    {
        "id": "acquedotto_storico_genova",
        "title": "Acquedotto Storico di Genova: Percorso Pedonale nel Verde",
        "category": OutingCategory.PASSEGGIATA,
        "venue": "Acquedotto Storico",
        "zone": "Val Bisagno / Staglieno",
        "address": "Accesso da Cavassolo, Molassana o Ponte Sifone Geirato",
        "day_time": "Percorribile liberamente nelle ore di luce",
        "verified_url": "https://www.visitgenoa.it/it/la-dellacqua-acquedotto-storico-di-genova",
        "description": "Antico condotto medievale e ottocentesco trasformato in itinerario pianeggiante tra ponti sifone, boschi e orti collinari.",
        "source_type": "live_web",
        "is_weather_dependent": True,
        "time_slot": "pomeriggio",
        "cost_info": "Accesso libero",
        "is_free": True,
        "tags": ["outdoor", "natura", "storia"],
    },
    {
        "id": "giardini_luzzati_spazio_comune",
        "title": "Giardini Luzzati: Spazio Comune, Serate, Dj Set e Musica",
        "category": OutingCategory.RITROVO,
        "venue": "Giardini Luzzati",
        "zone": "Centro Storico",
        "address": "Piazza Giardini Luzzati",
        "day_time": "Tutti i giorni ore 10:00-24:00 (venerdì e sabato fino alle 02:00 con dj set e live)",
        "verified_url": "https://giardiniluzzati.it/",
        "description": "Piazza aperta e circolo nel cuore dei caruggi con area archeologica, bar all'aperto, dj set, concerti acustici e serate per bere qualcosa e ballare.",
        "source_type": "live_web",
        "is_weather_dependent": False,
        "time_slot": "sera",
        "cost_info": "Ingresso libero",
        "is_free": True,
        "tags": ["ritrovo", "musica", "caruggi", "ballare", "dj", "serata", "bere", "aperitivo"],
    },
    {
        "id": "count_basie_jazz_club",
        "title": "Count Basie Jazz Club: Concerti dal Vivo, Blues Dance e Milonga",
        "category": OutingCategory.MUSICA,
        "venue": "Count Basie Jazz Club",
        "zone": "Centro Storico / Carmine",
        "address": "Vico Tana 20r",
        "day_time": "Giovedì, venerdì, sabato e domenica ore 20:30-00:30",
        "verified_url": "https://www.countbasie.it/",
        "description": "Circolo Arci in un locale con volte in pietra nel Carmine: concerti jazz, serate per ballare Blues Dance e swing, milonga di tango La Cueva e jam session.",
        "source_type": "live_web",
        "is_weather_dependent": False,
        "time_slot": "sera",
        "cost_info": "Ingresso con tessera Arci e contributo spettacolo",
        "is_free": False,
        "tags": ["indoor", "jazz", "live_music", "ballare", "ballo", "swing", "blues", "milonga", "tango", "serata"],
    },
    {
        "id": "la_claque_teatro_della_tosse",
        "title": "La Claque in Agorà: Live Club, Concerti, Dj Set e Serate",
        "category": OutingCategory.MUSICA,
        "venue": "La Claque / Teatro della Tosse",
        "zone": "Centro Storico",
        "address": "Vico San Donato 9",
        "day_time": "Da mercoledì a domenica ore 21:00 / 21:30",
        "verified_url": "https://www.teatrodellatosse.it/eventi/",
        "description": "Il club e spazio live del Teatro della Tosse in Vico San Donato per concerti funk, ska, swing, dj set per ballare, stand-up comedy e teatro musicale.",
        "source_type": "live_web",
        "is_weather_dependent": False,
        "time_slot": "sera",
        "cost_info": "Biglietto serata 10-15€",
        "is_free": False,
        "tags": ["indoor", "live_music", "comedy", "ballare", "ballo", "club", "dj", "serata", "concerto"],
    },
    {
        "id": "zena_swingers_social_dance",
        "title": "ZenaSwingers: Serate Social Dance, Swing, Lindy Hop e Dj Set",
        "category": OutingCategory.MUSICA,
        "venue": "ZenaSwingers Genova",
        "zone": "Centro / Porto Antico",
        "address": "Via San Giorgio 2 / Piazze del Centro Storico",
        "day_time": "Da lunedì a sabato ore 20:00-23:30 (serate social dance e ballo nel fine settimana)",
        "verified_url": "https://www.zenaswingers.it/",
        "description": "La community genovese di ballo swing e Lindy Hop: organizza serate social dance con musica dal vivo, dj set vintage, lezioni aperte e balli clandestini nelle piazze.",
        "source_type": "live_web",
        "is_weather_dependent": False,
        "time_slot": "sera",
        "cost_info": "Serate a ingresso libero o contributo associativo",
        "is_free": False,
        "tags": ["ballare", "ballo", "swing", "lindy_hop", "dj", "serata", "musica", "social_dance"],
    },
    {
        "id": "mog_mercato_orientale_serate",
        "title": "MOG Mercato Orientale: Cocktail Bar, Aperitivo e Serate con Musica",
        "category": OutingCategory.RITROVO,
        "venue": "MOG Mercato Orientale Genova",
        "zone": "Centro / Via XX Settembre",
        "address": "Via XX Settembre 75r (Piazza della Corte)",
        "day_time": "Lunedì-Giovedì ore 10:00-23:00; Venerdì-Sabato ore 10:00-24:00; Domenica ore 11:00-22:30",
        "verified_url": "https://www.moggenova.it/eventi/",
        "description": "La corte coperta dentro il Mercato Orientale storico con vineria, birreria, cocktail bar, cucine dal mondo, aperitivi in musica e serate a tema.",
        "source_type": "live_web",
        "is_weather_dependent": False,
        "time_slot": "sera",
        "cost_info": "Ingresso libero, consumazione ai banchi",
        "is_free": True,
        "tags": ["indoor", "ritrovo", "bere", "aperitivo", "cena", "serata", "musica", "cocktail", "vino"],
    },
    {
        "id": "circolo_vega_musica_ballo",
        "title": "Circolo Vega e Spazi Sociali di Ponente: Serate, Ballo e Musica",
        "category": OutingCategory.MUSICA,
        "venue": "Circolo Vega",
        "zone": "Sampierdarena / Ponente",
        "address": "Via Pisoni 3",
        "day_time": "Venerdì, sabato e domenica ore 21:00-01:00",
        "verified_url": "https://www.circolovega.it/",
        "description": "Circolo ricreativo e musicale con pista da ballo, serate danzanti, musica dal vivo e incontri serali nel fine settimana.",
        "source_type": "live_web",
        "is_weather_dependent": False,
        "time_slot": "sera",
        "cost_info": "Ingresso soci",
        "is_free": False,
        "tags": ["indoor", "ballare", "ballo", "serata", "musica", "pista"],
    },
]


def _build_option_from_raw(
    id_val: str,
    title: str,
    category: OutingCategory,
    venue: str,
    zone: str,
    day_time: str,
    url: str,
    description: str,
    source_type: str = "verified_local",
    address: str = "",
    time_slot: str = "flessibile",
    cost_info: Optional[str] = None,
    is_free: bool = False,
    tags: Optional[List[str]] = None,
    raw_metadata: Optional[Dict[str, object]] = None,
) -> Optional[OutingOption]:
    """Factory helper that validates, sanitizes, and builds an OutingOption."""
    # Negative filtering check (Villa Croce, closed venues, non-informal institutions)
    if is_blacklisted_venue(venue, description, url):
        return None

    # Sanitize strings to remove long dashes and forbidden phrasing
    clean_t = sanitize_text(title)
    clean_d = sanitize_text(description)
    clean_dt = sanitize_text(day_time)
    clean_v = sanitize_text(venue)
    clean_addr = sanitize_text(address) if address else ""
    clean_u = clean_url(url)

    if not clean_u:
        return None

    weather_dep = is_weather_dependent_venue(clean_v, category, zone)

    return OutingOption(
        id=id_val,
        title=clean_t,
        category=category,
        venue=clean_v,
        zone=zone,
        day_time=clean_dt,
        verified_url=clean_u,
        description=clean_d,
        source_type=source_type,
        is_weather_dependent=weather_dep,
        address=clean_addr,
        time_slot=time_slot,
        cost_info=cost_info,
        is_free=is_free,
        tags=tags or [],
        raw_metadata=raw_metadata or {},
    )


def load_authoritative_live_options() -> List[OutingOption]:
    """Generate OutingOption instances from curated authoritative live entries."""
    results: List[OutingOption] = []
    for raw in AUTHORITATIVE_LIVE_OUTINGS:
        opt = _build_option_from_raw(
            id_val=str(raw["id"]),
            title=str(raw["title"]),
            category=raw["category"],  # type: ignore
            venue=str(raw["venue"]),
            zone=str(raw["zone"]),
            day_time=str(raw["day_time"]),
            url=str(raw["verified_url"]),
            description=str(raw["description"]),
            source_type="live_web",
            address=str(raw.get("address", "")),
            time_slot=str(raw.get("time_slot", "flessibile")),
            cost_info=raw.get("cost_info"),  # type: ignore
            is_free=bool(raw.get("is_free", False)),
            tags=raw.get("tags"),  # type: ignore
            raw_metadata={"live_source": "spec_miner_verified"},
        )
        if opt:
            results.append(opt)
    return results


def load_local_tempo_libero(data_dir: Path) -> List[OutingOption]:
    """Extract informal options from tempo_libero_payload.json."""
    path = data_dir / "tempo_libero_payload.json"
    if not path.exists():
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except Exception as e:
        logger.warning("Could not read tempo_libero_payload.json: %s", e)
        return []

    results: List[OutingOption] = []
    places = payload.get("places", [])

    # Curate high-quality tier 1 flagships and selected informal venues
    for p in places:
        # We only accept Tier 1 flagships or specific informal botteghe / biblioteche
        tier = p.get("tier", 2)
        tipo = p.get("tipo", "")
        if tier != 1 and tipo not in ("bottega", "biblioteca", "teatro"):
            continue

        nome = p.get("nome", "")
        url = p.get("url", "")
        if not url:
            continue

        # Map tipo to OutingCategory
        if tipo == "bottega":
            cat = OutingCategory.RITROVO if "caff" in nome.lower() or "confetteria" in nome.lower() or "cioccolato" in nome.lower() or "friggitoria" in nome.lower() or "barberia" in nome.lower() else OutingCategory.LABORATORIO
        elif tipo == "biblioteca":
            cat = OutingCategory.BIBLIOTECA
        elif tipo in ("museo", "dimora"):
            cat = OutingCategory.MOSTRA
        elif tipo == "teatro":
            cat = OutingCategory.MUSICA
        elif tipo == "natura":
            cat = OutingCategory.PASSEGGIATA
        else:
            cat = OutingCategory.ALTRO

        desc = p.get("pitch", "") or p.get("personaggio", "")
        orari = p.get("orari", "") or "Orari standard da verificare sul sito ufficiale"
        zona = p.get("zona", "Genova")

        slug_id = f"tl_{p.get('id', '')}_{cat.value}"

        opt = _build_option_from_raw(
            id_val=slug_id,
            title=nome,
            category=cat,
            venue=nome.split("—")[0].split("(")[0].strip(),
            zone=zona.capitalize(),
            day_time=orari,
            url=url,
            description=desc,
            source_type="verified_local",
            address=p.get("trasporto_info", ""),
            time_slot="pomeriggio",
            cost_info=p.get("costo"),
            is_free=bool(p.get("free", False)),
            tags=[tipo, zona],
            raw_metadata=p,
        )
        if opt:
            results.append(opt)

    return results


def load_local_guida_aperti(data_dir: Path) -> List[OutingOption]:
    """Extract verified informal cinemas, theatres, and open cultural sites from guida."""
    path = data_dir / "guida_aperti_al_pubblico_provincia_genova.json"
    if not path.exists():
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            guida = json.load(f)
    except Exception as e:
        logger.warning("Could not read guida_aperti_al_pubblico_provincia_genova.json: %s", e)
        return []

    results: List[OutingOption] = []
    seen_names: Set[str] = set()

    for item in guida:
        subcat = str(item.get("sottocategoria", "")).lower()
        macro = str(item.get("macro_categoria", ""))
        url = str(item.get("sito_web", "")).strip()
        nome = str(item.get("nome", "")).strip()

        if not url or url.lower() in ("no_url", "none", ""):
            continue
        if not (url.startswith("http://") or url.startswith("https://")):
            continue

        # Keep cinemas and theatres with active schedules
        if subcat in ("cinema", "theatre", "teatro") or "3." in macro:
            norm_name = nome.lower()
            if norm_name in seen_names:
                continue

            orari = item.get("orari_apertura", "")
            cat = OutingCategory.CINEMA if "cinema" in subcat or "cinema" in norm_name else OutingCategory.MUSICA
            desc = item.get("eventi_e_servizi_al_pubblico", "") or f"Programmazione spettacoli e proiezioni presso {nome}."
            comune = item.get("comune", "Genova")

            opt = _build_option_from_raw(
                id_val=f"guida_{len(results)}_{cat.value}",
                title=f"{nome}: Programmazione Spettacoli",
                category=cat,
                venue=nome,
                zone=comune,
                day_time=orari if orari else "Consultare la programmazione settimanale sul sito ufficiale",
                url=url,
                description=desc,
                source_type="verified_local",
                address=item.get("indirizzo", ""),
                time_slot="sera",
                tags=[subcat, comune],
                raw_metadata=item,
            )
            if opt:
                results.append(opt)
                seen_names.add(norm_name)

    return results


def load_local_esercenti_informali(data_dir: Path) -> List[OutingOption]:
    """Extract independent historic bookshops, vinyl shops, and traditional sciamadde."""
    path = data_dir / "esercenti_genova_provincia_db.json"
    if not path.exists():
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            esercenti = json.load(f)
    except Exception as e:
        logger.warning("Could not read esercenti_genova_provincia_db.json: %s", e)
        return []

    results: List[OutingOption] = []
    target_keywords = ["libreria", "dischi in vinile", "confetteria", "cioccolato", "farinata"]

    for item in esercenti:
        spec = str(item.get("categoria_specifica", "")).lower()
        desc_raw = str(item.get("cosa_trovi_qui", "")).lower()
        url = str(item.get("sito_o_social", "")).strip()

        if not url or not (url.startswith("http://") or url.startswith("https://")):
            continue

        is_target = any(kw in spec or kw in desc_raw for kw in target_keywords)
        if not is_target:
            continue

        nome = item.get("nome", "")
        comune = item.get("comune", "Genova")

        if "libreria" in spec or "libri" in desc_raw:
            cat = OutingCategory.BIBLIOTECA
        elif "dischi" in spec or "vinile" in desc_raw:
            cat = OutingCategory.MUSICA
        else:
            cat = OutingCategory.RITROVO

        orari = item.get("orari", "") or "Orari di apertura del locale"
        desc = item.get("cosa_trovi_qui", "") or f"Locale storico indipendente a {comune}."

        opt = _build_option_from_raw(
            id_val=f"es_{len(results)}_{cat.value}",
            title=f"{nome}: {spec.title()}",
            category=cat,
            venue=nome,
            zone=comune,
            day_time=orari,
            url=url,
            description=desc,
            source_type="verified_local",
            address=item.get("indirizzo", ""),
            time_slot="pomeriggio",
            tags=[spec],
            raw_metadata=item,
        )
        if opt:
            results.append(opt)

    return results


def load_catalog_items(data_dir: Optional[Path] = None) -> List[OutingOption]:
    """Aggregate all options from authoritative live sources and local datasets.

    Deduplicates candidates and strictly applies negative blacklist filters.
    """
    directory = data_dir or DEFAULT_DATA_DIR

    # 1. Start with high-priority authoritative live verified endpoints
    all_options: List[OutingOption] = load_authoritative_live_options()

    # 2. Append curated items from local datasets
    tl_options = load_local_tempo_libero(directory)
    all_options.extend(tl_options)

    guida_options = load_local_guida_aperti(directory)
    all_options.extend(guida_options)

    es_options = load_local_esercenti_informali(directory)
    all_options.extend(es_options)

    # 3. Deduplicate by (normalized venue, category)
    deduped: List[OutingOption] = []
    seen_keys: Set[Tuple[str, str]] = set()

    for opt in all_options:
        # Extra safety check against blacklisted closed venues (Villa Croce, Cantero, summer arenas, etc.)
        if is_blacklisted_venue(opt.venue, opt.description, opt.verified_url):
            continue

        norm_venue = "".join(ch for ch in opt.venue.lower() if ch.isalnum())
        title_slug = "".join(ch for ch in opt.title.lower() if ch.isalnum())
        key = (norm_venue, opt.category.value, title_slug)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        deduped.append(opt)

    return deduped


def get_weekly_catalog(
    live_verify: bool = True,
    category: Optional[str] = None,
    data_dir: Optional[Path] = None,
) -> List[OutingOption]:
    """Interface function: returns curated, verified list of active options for current week.

    Args:
        live_verify: If True, performs HTTP reachability probes and negative validation.
        category: Optional category filter (e.g. 'cinema', 'mostra', 'passeggiata', or synonyms like 'film').
        data_dir: Optional custom path to data directory.

    Returns:
        List of OutingOption objects meeting all plain-writing, accuracy, and reachability rules.
    """
    raw_catalog = load_catalog_items(data_dir=data_dir)

    # Filter by category if requested, supporting category synonyms
    target_cat: Optional[str] = None
    if category is not None:
        cat_str = str(category).strip()
        if cat_str:
            if isinstance(category, OutingCategory):
                target_cat = category.value
            else:
                target_cat = OutingCategory.from_str(cat_str).value

    # Pre-probe reachability in parallel if live_verify is requested
    if live_verify:
        candidate_urls = [
            opt.verified_url for opt in raw_catalog
            if not (target_cat and opt.category.value != target_cat)
        ]
        probe_urls_batch(candidate_urls, max_workers=16, timeout=3.0)

    verified_list: List[OutingOption] = []

    for option in raw_catalog:
        if target_cat and option.category.value != target_cat:
            continue

        if live_verify:
            # Run verifier with reachability prober
            vres = verify_outing(option, check_network=True)
            if not vres.is_valid:
                # Log rejection and omit
                logger.debug("Omitted invalid outing %s: %s", option.id, vres.reason)
                continue
            # Apply any sanitized title or description adjustments
            if vres.clean_title:
                option.title = vres.clean_title
            if vres.clean_description:
                option.description = vres.clean_description

        # Final sanity check: ensure no em/en dashes slip through in any text field
        option.title = sanitize_text(option.title)
        option.description = sanitize_text(option.description)
        option.day_time = sanitize_text(option.day_time)
        option.venue = sanitize_text(option.venue)
        option.address = sanitize_text(option.address)

        verified_list.append(option)

    return [o for o in verified_list if has_usable_schedule(o.day_time)]


_MONTH_NUM = {m: i for i, m in enumerate(
    ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio",
     "agosto", "settembre", "ottobre", "novembre", "dicembre"], 1)}
_OPEN_ACCESS = ("sempre", "tutti i giorni", "accesso libero", "alba", "tramonto")


def has_usable_schedule(day_time: str, today: Optional["date"] = None) -> bool:
    """True if day_time states real hours or open access and mentions no past date."""
    import re
    from datetime import date
    t = (day_time or "").lower()
    if not t or "verifica aperture" in t or "orari di apertura del locale" in t:
        return False
    today = today or date.today()
    for d, m in re.findall(r"\b(\d{1,2})\s+(" + "|".join(_MONTH_NUM) + r")\b", t):
        try:
            when = date(today.year, _MONTH_NUM[m], int(d))
        except ValueError:
            continue
        if when < today and (today - when).days < 200:
            return False
    return bool(re.search(r"\d{1,2}[:.]\d{2}|\bore\s+\d{1,2}\b", t)) or any(k in t for k in _OPEN_ACCESS)
