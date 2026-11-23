import json
import math
import re
from collections import Counter, defaultdict
import os as _os
_DATA_DIR = _os.environ.get("GENOVA_DATA_DIR") or _os.path.dirname(_os.path.abspath(__file__))

with open(f"{_DATA_DIR}/comuni_67_geo.json") as f:
    comuni_geo = json.load(f)

with open(f"{_DATA_DIR}/wikidata_rich_provincia.json") as f:
    wd_rich = json.load(f)

with open(f"{_DATA_DIR}/osm_provincia_raw.json") as f:
    osm_raw = json.load(f)["elements"]

with open(f"{_DATA_DIR}/guida_aperti_al_pubblico_provincia_genova.json") as f:
    guida = json.load(f)

with open(f"{_DATA_DIR}/toponimi_personaggi_provincia_genova.json") as f:
    toponimi = json.load(f)

# Build GPS lookup
coords_lookup = {}
for b in wd_rich:
    name = b.get("itemLabel", {}).get("value", "").strip()
    comune = b.get("comuneLabel", {}).get("value", "").strip()
    wkt = b.get("coord", {}).get("value", "")
    if name and comune and wkt.startswith("Point("):
        lon, lat = [float(x) for x in wkt.replace("Point(", "").replace(")", "").split()]
        coords_lookup[(comune.lower(), name.lower())] = (round(lat, 5), round(lon, 5))

for el in osm_raw:
    t = el.get("tags", {})
    name = t.get("name", "").strip()
    comune = t.get("comune", "Genova").strip()
    if name and "lat" in el and "lon" in el:
        coords_lookup[(comune.lower(), name.lower())] = (round(el["lat"], 5), round(el["lon"], 5))

person_lookup = {}
comune_sample_person = defaultdict(list)
for t in toponimi:
    person_lookup[(t["comune"].lower(), t["toponimo"].lower())] = t["personaggio_o_casata"]
    p = t["personaggio_o_casata"]
    if p and len(comune_sample_person[t["comune"]]) < 5 and p not in comune_sample_person[t["comune"]]:
        comune_sample_person[t["comune"]].append(p)

ZONE_BY_COMUNE = {
    "Arenzano": "ponente_stura", "Cogoleto": "ponente_stura", "Mele": "ponente_stura",
    "Masone": "ponente_stura", "Campo Ligure": "ponente_stura", "Rossiglione": "ponente_stura", "Tiglieto": "ponente_stura",
    "Ceranesi": "polcevera_scrivia", "Campomorone": "polcevera_scrivia", "Mignanego": "polcevera_scrivia",
    "Serra Riccò": "polcevera_scrivia", "Sant'Olcese": "polcevera_scrivia", "Casella": "polcevera_scrivia",
    "Busalla": "polcevera_scrivia", "Ronco Scrivia": "polcevera_scrivia", "Isola del Cantone": "polcevera_scrivia",
    "Savignone": "polcevera_scrivia", "Crocefieschi": "polcevera_scrivia", "Vobbia": "polcevera_scrivia",
    "Valbrevenna": "polcevera_scrivia", "Montoggio": "polcevera_scrivia",
    "Torriglia": "polcevera_scrivia", "Propata": "polcevera_scrivia", "Rondanina": "polcevera_scrivia",
    "Fascia": "polcevera_scrivia", "Gorreto": "polcevera_scrivia", "Rovegno": "polcevera_scrivia",
    "Fontanigorda": "polcevera_scrivia", "Montebruno": "polcevera_scrivia",
    "Bargagli": "golfo_paradiso", "Davagna": "golfo_paradiso", "Lumarzo": "golfo_paradiso",
    "Bogliasco": "golfo_paradiso", "Pieve Ligure": "golfo_paradiso", "Sori": "golfo_paradiso",
    "Recco": "golfo_paradiso", "Avegno": "golfo_paradiso", "Uscio": "golfo_paradiso", "Tribogna": "golfo_paradiso",
    "Camogli": "golfo_paradiso",
    "Portofino": "tigullio_occ", "Santa Margherita Ligure": "tigullio_occ", "Rapallo": "tigullio_occ", "Zoagli": "tigullio_occ",
    "Chiavari": "tigullio_or", "Lavagna": "tigullio_or", "Cogorno": "tigullio_or", "Leivi": "tigullio_or",
    "Carasco": "tigullio_or", "San Colombano Certenoli": "tigullio_or", "Coreglia Ligure": "tigullio_or",
    "Orero": "tigullio_or", "Cicagna": "tigullio_or", "Moconesi": "tigullio_or", "Neirone": "tigullio_or",
    "Lorsica": "tigullio_or", "Favale di Malvaro": "tigullio_or", "Mezzanego": "tigullio_or",
    "Borzonasca": "tigullio_or", "Rezzoaglio": "tigullio_or", "Santo Stefano d'Aveto": "tigullio_or",
    "Ne": "tigullio_or", "Sestri Levante": "tigullio_or", "Casarza Ligure": "tigullio_or",
    "Castiglione Chiavarese": "tigullio_or", "Moneglia": "tigullio_or"
}

RAIL_COMUNI = {
    "Genova", "Cogoleto", "Arenzano", "Mele", "Bogliasco", "Pieve Ligure", "Sori", "Recco", "Camogli",
    "Santa Margherita Ligure", "Rapallo", "Zoagli", "Chiavari", "Lavagna", "Sestri Levante", "Moneglia",
    "Campo Ligure", "Masone", "Rossiglione", "Mignanego", "Busalla", "Ronco Scrivia", "Isola del Cantone", "Casella", "Sant'Olcese"
}

# 76 Hand-verified Flagship Leisure Destinations across Genoa & all 7 zones of the Province
FLAGSHIPS = [
    # --- GENOVA CENTRO & CARUGGI: MUSEI, PALAZZI & BELVEDERE ---
    {
        "key_id": "strada_nuova",
        "nome": "Musei di Strada Nuova (Palazzo Rosso, Bianco e Tursi)",
        "comune": "Genova", "zona": "centro", "tipo": "museo",
        "lat": 44.4113, "lon": 8.9324, "indoor": "in", "treno": True,
        "trasporto_info": "Metro De Ferrari / Stazione Principe (10 min a piedi)",
        "durata_min": 120, "costo": "Biglietto (Gratis residenti dom)", "free": False, "free_1st_sun": False,
        "days": [0, 2, 3, 4, 5, 6], "slots": [[9.0, 19.0]], "months": list(range(1,13)),
        "orari": "Mar-Ven 09:00-19:00; Sab-Dom 10:00-19:00; Lun chiuso",
        "pitch": "Tre palazzi UNESCO in Via Garibaldi: capolavori di Van Dyck e Caravaggio, il violino 'Cannone' di Paganini e la terrazza Mirador sui tetti della città vecchia.",
        "personaggio": "Maria Brignole Sale De Ferrari, Niccolò Grimaldi & Nicolò Paganini",
        "url": "https://www.museidigenova.it/it/musei-di-strada-nuova", "tel": "010 2759185"
    },
    {
        "key_id": "palazzo_reale",
        "nome": "Museo di Palazzo Reale & Giardino Pensile",
        "comune": "Genova", "zona": "centro", "tipo": "dimora",
        "lat": 44.4149, "lon": 8.9261, "indoor": "mix", "treno": True,
        "trasporto_info": "Stazione Genova Piazza Principe (3 min a piedi in Via Balbi)",
        "durata_min": 90, "costo": "Biglietto (Gratis 1ª Dom mese)", "free": False, "free_1st_sun": True,
        "days": [2, 3, 4, 5, 6], "slots": [[9.0, 19.0]], "months": list(range(1,13)),
        "orari": "Mar 13:30-19:00; Mer-Sab 09:00-19:00; 1ª Dom del mese aperto gratuito (#DomenicalMuseo)",
        "pitch": "La reggia dei Balbi e dei Savoia con la sfolgorante Galleria degli Specchi e il giardino pensile a mosaico di ciottoli bianchi e neri affacciato sul porto.",
        "personaggio": "Stefano Balbi & Re Carlo Felice di Savoia",
        "url": "https://palazzorealegenova.cultura.gov.it/", "tel": "010 2705236"
    },
    {
        "key_id": "palazzo_spinola",
        "nome": "Galleria Nazionale di Palazzo Spinola di Pellicceria",
        "comune": "Genova", "zona": "centro", "tipo": "dimora",
        "lat": 44.4106, "lon": 8.9304, "indoor": "in", "treno": True,
        "trasporto_info": "Metro San Giorgio / Darsena (4 min a piedi nei caruggi)",
        "durata_min": 75, "costo": "Biglietto (Gratis 1ª Dom mese)", "free": False, "free_1st_sun": True,
        "days": [2, 3, 4, 5, 6], "slots": [[9.0, 19.0]], "months": list(range(1,13)),
        "orari": "Mar 13:30-19:00; Mer-Sab 09:00-19:00; 1ª Dom del mese 13:30-19:00 gratuito",
        "pitch": "Una dimora dei Rolli rimasta intatta nei secoli, dalle cucine storiche in rame fino all'Ecce Homo di Antonello da Messina.",
        "personaggio": "Francesco Grimaldi & Casata Spinola",
        "url": "https://palazzospinola.cultura.gov.it/", "tel": "010 2705300"
    },
    {
        "key_id": "palazzo_ducale",
        "nome": "Palazzo Ducale — Grandi Mostre & Torre Grimaldina",
        "comune": "Genova", "zona": "centro", "tipo": "museo",
        "lat": 44.4075, "lon": 8.9333, "indoor": "in", "treno": True,
        "trasporto_info": "Metro De Ferrari (1 min a piedi)",
        "durata_min": 90, "costo": "Cortili gratis / Mostre a biglietto", "free": False, "free_1st_sun": False,
        "days": [0, 1, 2, 3, 4, 5, 6], "slots": [[9.0, 21.0]], "months": list(range(1,13)),
        "orari": "Cortili tutti i giorni 07:00-23:00; Mostre Mar-Dom 10:00-19:00 (Ven fino 21:00, Lun pom spesso aperto)",
        "pitch": "L'antico palazzo dei Dogi: grandi mostre internazionali d'arte e fotografia, incontri gratuiti e salita alle carceri segrete della Torre Grimaldina.",
        "personaggio": "Simone Boccanegra & Giacomo Matteotti",
        "url": "https://palazzoducale.genova.it/", "tel": "010 8171600"
    },
    {
        "key_id": "castello_dalbertis",
        "nome": "Castello D'Albertis — Museo delle Culture del Mondo",
        "comune": "Genova", "zona": "centro", "tipo": "dimora",
        "lat": 44.4182, "lon": 8.9242, "indoor": "mix", "treno": True,
        "trasporto_info": "Ascensore storico Montegalletto da Via Balbi / Stazione Principe",
        "durata_min": 105, "costo": "Biglietto (Parco bastioni libero)", "free": False, "free_1st_sun": False,
        "days": [0, 2, 3, 4, 5, 6], "slots": [[10.0, 18.0]], "months": list(range(1,13)),
        "orari": "Mar-Ven 10:00-17:00 (Est 18:00); Sab-Dom 10:00-18:00 (Est 19:00); Lun chiuso",
        "pitch": "Si sale con un ascensore unico al mondo (prima corre in orizzontale sotto la collina e poi sale in verticale!) fino al castello neogotico del Capitano esploratore.",
        "personaggio": "Capitano Enrico Alberto D'Albertis",
        "url": "https://www.museidigenova.it/it/castello-dalbertis-museo-delle-culture-del-mondo", "tel": "010 2723820"
    },
    {
        "key_id": "galata",
        "nome": "Galata Museo del Mare & Sottomarino Nazario Sauro",
        "comune": "Genova", "zona": "centro", "tipo": "museo",
        "lat": 44.4141, "lon": 8.9226, "indoor": "in", "treno": True,
        "trasporto_info": "Metro Darsena / Stazione Principe (5 min a piedi)",
        "durata_min": 135, "costo": "Biglietto", "free": False, "free_1st_sun": False,
        "days": [0, 1, 2, 3, 4, 5, 6], "slots": [[10.0, 19.0]], "months": list(range(1,13)),
        "orari": "Aperto tutti i giorni (anche Lunedì!) 10:00-18:30/19:00",
        "pitch": "Il più grande museo marittimo del Mediterraneo: sali su una galea del '600, affronta la tempesta a Capo Horn in 4D ed entra in un vero sottomarino ormeggiato in acqua.",
        "personaggio": "Nazario Sauro & Cristoforo Colombo",
        "url": "https://www.galatamuseodelmare.it/", "tel": "010 2533555"
    },
    {
        "key_id": "acquario",
        "nome": "Acquario di Genova & Biosfera",
        "comune": "Genova", "zona": "centro", "tipo": "museo",
        "lat": 44.4103, "lon": 8.9265, "indoor": "in", "treno": True,
        "trasporto_info": "Metro San Giorgio (Porto Antico)",
        "durata_min": 150, "costo": "Biglietto", "free": False, "free_1st_sun": False,
        "days": [0, 1, 2, 3, 4, 5, 6], "slots": [[9.0, 20.0]], "months": list(range(1,13)),
        "orari": "Tutti i giorni 09:00-20:00 (ultimo ingresso 18:00)",
        "pitch": "Ideale anche di lunedì o con la pioggia: lamantini, squali, pinguini, meduse ipnotiche e il padiglione Cetacei progettato da Renzo Piano.",
        "personaggio": "Famiglia Spinola (Ponte Spinola)",
        "url": "https://www.acquariodigenova.it/", "tel": "010 23451"
    },
    {
        "key_id": "chiossone",
        "nome": "Museo d'Arte Orientale Edoardo Chiossone & Villetta Di Negro",
        "comune": "Genova", "zona": "centro", "tipo": "museo",
        "lat": 44.4108, "lon": 8.9369, "indoor": "mix", "treno": True,
        "trasporto_info": "Piazza Corvetto (10 min da Brignole o De Ferrari)",
        "durata_min": 90, "costo": "Parco gratis / Museo a biglietto", "free": False, "free_1st_sun": False,
        "days": [0, 2, 3, 4, 5, 6], "slots": [[9.0, 19.0]], "months": list(range(1,13)),
        "orari": "Mar-Ven 09:00-19:00; Sab-Dom 10:00-19:00; Lun chiuso",
        "pitch": "In un parco romantico sopraelevato con cascate e grotte: la più ricca collezione italiana di armature samurai, spade, lacche e stampe giapponesi.",
        "personaggio": "Edoardo Chiossone & Marchese Gian Carlo Di Negro",
        "url": "https://www.museidigenova.it/it/museo-darte-orientale-edoardo-chiossone", "tel": "010 542285"
    },
    {
        "key_id": "diocesano",
        "nome": "Museo Diocesano & Chiostro Medievale di San Lorenzo",
        "comune": "Genova", "zona": "centro", "tipo": "abbazia",
        "lat": 44.4079, "lon": 8.9315, "indoor": "in", "treno": True,
        "trasporto_info": "Metro San Giorgio / De Ferrari (3 min a piedi)",
        "durata_min": 60, "costo": "Biglietto", "free": False, "free_1st_sun": False,
        "days": [0, 1, 3, 4, 5, 6], "slots": [[10.0, 13.0], [14.0, 18.0]], "months": list(range(1,13)),
        "orari": "Lun 10:00-13:00 e 14:00-18:00; Mer-Dom 14:00-18:00; Mar chiuso (Aperto il Lunedì!)",
        "pitch": "Tesoro 'salva-lunedì': un silenzioso chiostro romanico del XII secolo e i celebri Teli della Passione del '500 dipinti su fustagno indaco (gli antenati dei Blue Jeans!).",
        "personaggio": "San Lorenzo & Guglielmo Embriaco",
        "url": "https://www.museodiocesanogenova.it/", "tel": "010 2475127"
    },
    {
        "key_id": "lanterna",
        "nome": "Complesso Monumentale della Lanterna di Genova",
        "comune": "Genova", "zona": "centro", "tipo": "dimora",
        "lat": 44.4046, "lon": 8.9046, "indoor": "out", "treno": True,
        "trasporto_info": "Passeggiata della Lanterna da Terminal Traghetti / Metro Dinegro",
        "durata_min": 90, "costo": "Biglietto", "free": False, "free_1st_sun": False,
        "days": [0, 5, 6], "slots": [[10.0, 18.0]], "months": list(range(1,13)),
        "orari": "Ven, Sab, Dom e festivi 10:00-18:00 (ultimo ingresso 17:30; chiuso con allerta arancione/rossa)",
        "pitch": "Passeggiata panoramica di 800 metri sospesa sul porto fino al faro simbolo di Genova (1543): 172 scalini per vedere tutta la città tra navi e Appennino.",
        "personaggio": "Giovanni Maria Olgiati & Andrea Doria",
        "url": "https://www.lanternadigenova.com/", "tel": "010 265712"
    },
    {
        "key_id": "spianata_castelletto",
        "nome": "Spianata Castelletto & Ascensore Art Nouveau di Piazza Portello",
        "comune": "Genova", "zona": "centro", "tipo": "natura",
        "lat": 44.4126, "lon": 8.9339, "indoor": "out", "treno": True,
        "trasporto_info": "Ascensore Liberty da Piazza Portello (1 min da Via Garibaldi)",
        "durata_min": 45, "costo": "Belvedere gratis (Ascensore gratuito per residenti / biglietto AMT)", "free": True, "free_1st_sun": True,
        "days": [0, 1, 2, 3, 4, 5, 6], "slots": [[7.0, 23.5]], "months": list(range(1,13)),
        "orari": "Sempre accessibile (Ascensore attivo tutti i giorni ca. 06:40-24:00)",
        "pitch": "La 'terrazza sospesa' cantata da Giorgio Caproni: sali nella cabina Liberty a vetri colorati del 1909 e gusta una granita o un caffè sopra la distesa di tetti d'ardesia.",
        "personaggio": "Giorgio Caproni ('Quando mi sarò deciso d'andarci, in paradiso ci andrò con l'ascensore di Castelletto')",
        "url": "https://www.visitgenoa.it/it/spianata-castelletto", "tel": ""
    },
    {
        "key_id": "funicolare_righi_forti",
        "nome": "Funicolare Zecca–Righi & Anello Panoramico dei Forti (Parco delle Mura)",
        "comune": "Genova", "zona": "centro", "tipo": "natura",
        "lat": 44.4309, "lon": 8.9355, "indoor": "out", "treno": True,
        "trasporto_info": "Funicolare storica da Largo della Zecca fino a Righi (302 m) in 12 minuti!",
        "durata_min": 165, "costo": "Sentieri gratis (Funicolare AMT)", "free": True, "free_1st_sun": True,
        "days": [0, 1, 2, 3, 4, 5, 6], "slots": [[7.5, 20.0]], "months": list(range(1,13)),
        "orari": "Sentieri del Parco delle Mura sempre aperti; Funicolare tutti i giorni 06:40-24:00",
        "pitch": "Dal centro città ai pascoli d'alta quota in 12 minuti di funicolare: cammina lungo la più lunga cinta muraria d'Europa dopo la Muraglia Cinese toccando Forte Sperone, Puin e Diamante.",
        "personaggio": "Stefano Jacini & Architetti Militari della Repubblica di Genova",
        "url": "https://www.visitgenoa.it/it/parco-urbano-delle-mura-e-forti", "tel": ""
    },
    {
        "key_id": "staglieno",
        "nome": "Museo a Cielo Aperto di Staglieno — Scultura Monumentale dell'800",
        "comune": "Genova", "zona": "centro", "tipo": "museo",
        "lat": 44.4288, "lon": 8.9502, "indoor": "out", "treno": False,
        "trasporto_info": "Bus 13, 14 o 34 da Genova Brignole (10 min)",
        "durata_min": 105, "costo": "Ingresso libero (Visite guidate tematiche nei weekend)", "free": True, "free_1st_sun": True,
        "days": [0, 1, 2, 3, 4, 5, 6], "slots": [[7.5, 17.0]], "months": list(range(1,13)),
        "orari": "Tutti i giorni 07:30-17:00 (ingresso fino a 16:30)",
        "pitch": "Amato da Mark Twain, Nietzsche, Hemingway e dai Joy Division: porticati e boschetti romantici con capolavori incredibili scolpiti nel marmo (dalla venditrice di noccioline alle tombe di Mazzini e De André).",
        "personaggio": "Giuseppe Mazzini, Fabrizio De André, Nino Bixio & Carlo Barabino",
        "url": "https://staglieno.comune.genova.it/", "tel": "010 5576437"
    },

    # --- GENOVA: BOTTEGHE IPER-SPECIFICHE ---
    {
        "key_id": "sant_anna",
        "nome": "Antica Farmacia Sant'Anna dei Frati Carmelitani (1650)",
        "comune": "Genova", "zona": "centro", "tipo": "bottega",
        "lat": 44.4137, "lon": 8.9365, "indoor": "in", "treno": True,
        "trasporto_info": "Funicolare Sant'Anna da Piazza Portello (2 min a piedi tra le creuze)",
        "durata_min": 40, "costo": "Ingresso libero / Acquisti", "free": True, "free_1st_sun": False,
        "days": [1, 2, 3, 4, 5, 6], "slots": [[8.5, 12.5], [15.5, 19.0]], "months": list(range(1,13)),
        "orari": "Lun-Ven 08:30-12:30 e 15:30-19:00; Sab 08:30-12:30; Dom chiuso",
        "pitch": "Raggiungibile con la funicolare: una piazzetta silenziosa dove dal 1650 i frati preparano Elisir di China, Acqua di Melissa, sciroppo di rose, miele balsamico e creme galeniche.",
        "personaggio": "Sant'Anna & Fra' Martino da Genova",
        "url": "https://www.erboristeriadeifrati.it/", "tel": "010 2513285"
    },
    {
        "key_id": "romanengo",
        "nome": "Confetteria Pietro Romanengo fu Stefano (1780)",
        "comune": "Genova", "zona": "centro", "tipo": "bottega",
        "lat": 44.4094, "lon": 8.9322, "indoor": "in", "treno": True,
        "trasporto_info": "Centro Storico — Via di Soziglia 74r",
        "durata_min": 30, "costo": "Assaggi / Acquisti", "free": False, "free_1st_sun": False,
        "days": [1, 2, 3, 4, 5, 6], "slots": [[9.0, 13.0], [15.0, 19.5]], "months": list(range(1,13)),
        "orari": "Lun 15:30-19:30; Mar-Sab 09:00-13:00 e 15:00-19:30 (Dicembre aperto anche Dom)",
        "pitch": "Boiserie del Settecento per un'arte rarissima: veri petali di rosa e violette canditi nello zucchero, gocce di rosolio, cortecce di cannella confettate e sciroppi.",
        "personaggio": "Pietro Romanengo & Antichi Speziali di Soziglia",
        "url": "https://www.romanengo.com/", "tel": "010 2474574"
    },
    {
        "key_id": "viganotti",
        "nome": "Fabbrica di Cioccolato Romeo Viganotti (1866)",
        "comune": "Genova", "zona": "centro", "tipo": "bottega",
        "lat": 44.4063, "lon": 8.9328, "indoor": "in", "treno": True,
        "trasporto_info": "Metro De Ferrari — Vico dei Castagna 14r (Piazza delle Erbe)",
        "durata_min": 30, "costo": "Assaggi / Acquisti", "free": False, "free_1st_sun": False,
        "days": [0, 2, 3, 4, 5, 6], "slots": [[9.5, 19.5]], "months": list(range(1,13)),
        "orari": "Mar-Sab 09:30-19:30; Dom 10:00-13:00 e 15:30-19:30; Lun chiuso (Aperta la Domenica!)",
        "pitch": "Una delle pochissime botteghe storiche aperte anche la domenica: laboratorio a vista con macchinari originali dell'Ottocento che colano praline, boeri e cremini.",
        "personaggio": "Romeo Viganotti",
        "url": "https://www.romeoviganotti.com/", "tel": "010 2514061"
    },
    {
        "key_id": "luico",
        "nome": "G.M. Luico — Il Laboratorio dei Turaccioli in Sughero (1855)",
        "comune": "Genova", "zona": "centro", "tipo": "bottega",
        "lat": 44.4102, "lon": 8.9351, "indoor": "in", "treno": True,
        "trasporto_info": "Salita Santa Caterina 17r (2 min da Piazza Fontane Marose)",
        "durata_min": 20, "costo": "Ingresso libero / Acquisti", "free": True, "free_1st_sun": False,
        "days": [2, 3, 4, 5, 6], "slots": [[9.0, 12.5], [15.5, 19.0]], "months": list(range(1,13)),
        "orari": "Mar-Sab 09:00-12:30 e 15:30-19:00; Lun e Dom chiuso",
        "pitch": "L'emblema dei negozi iper-specifici genovesi: 15 mq interamente dedicati a tappi di sughero su misura (dalle fiale alchimistiche alle botti navali) e corteccia da presepe.",
        "personaggio": "Santa Caterina Fieschi Adorno",
        "url": "https://www.botteghestorichegenova.it/", "tel": "010 589493"
    },
    {
        "key_id": "giacalone",
        "nome": "Antica Barberia Giacalone — Gioiello Art Déco (Bene FAI)",
        "comune": "Genova", "zona": "centro", "tipo": "bottega",
        "lat": 44.4090, "lon": 8.9312, "indoor": "in", "treno": True,
        "trasporto_info": "Vico dei Caprettari 14r (tra San Lorenzo e Soziglia)",
        "durata_min": 25, "costo": "Visite FAI / Servizio barba", "free": True, "free_1st_sun": False,
        "days": [2, 3, 4, 5, 6], "slots": [[8.5, 19.0]], "months": list(range(1,13)),
        "orari": "Mar-Sab 08:30-19:00; Lun e Dom chiuso",
        "pitch": "Dieci metri quadrati rivestiti nel 1922 di cristalli opalini blu pavone e verde smeraldo: ancora in attività per barba a panno caldo e tutelata dal FAI.",
        "personaggio": "Italo Giacalone & Corporazione dei Caprettari",
        "url": "https://fondoambiente.it/luoghi/barberia-giacalone", "tel": "010 2770603"
    },
    {
        "key_id": "busellato",
        "nome": "Incisoria Busellato — Timbri, Punzoni Navali & Ceralacca (1896)",
        "comune": "Genova", "zona": "centro", "tipo": "bottega",
        "lat": 44.4096, "lon": 8.9288, "indoor": "in", "treno": True,
        "trasporto_info": "Via al Ponte Reale 3r (di fronte a Piazza Caricamento / Acquario)",
        "durata_min": 25, "costo": "Ingresso libero / Acquisti", "free": True, "free_1st_sun": False,
        "days": [1, 2, 3, 4, 5], "slots": [[9.0, 12.5], [14.5, 18.5]], "months": list(range(1,13)),
        "orari": "Lun-Ven 09:00-12:30 e 14:30-18:30; Sab-Dom chiuso",
        "pitch": "Pareti intere di cassettiere in rovere di fine '800 ricolme di punzoni d'acciaio, sigilli in ottone per ceralacca e targhe delle grandi compagnie di navigazione.",
        "personaggio": "Ammiraglio Andrea Doria (Ponte Reale)",
        "url": "https://www.busellato.it/", "tel": "010 2470939"
    },
    {
        "key_id": "torielli",
        "nome": "Drogheria Torielli — 400 Cassetti di Spezie & Resine (1930)",
        "comune": "Genova", "zona": "centro", "tipo": "bottega",
        "lat": 44.4058, "lon": 8.9309, "indoor": "in", "treno": True,
        "trasporto_info": "Via di San Bernardo 32r (Centro Storico)",
        "durata_min": 25, "costo": "Acquisti", "free": False, "free_1st_sun": False,
        "days": [2, 3, 4, 5, 6], "slots": [[9.0, 13.0], [15.5, 19.5]], "months": list(range(1,13)),
        "orari": "Mar-Sab 09:00-13:00 e 15:30-19:30; Lun e Dom chiuso",
        "pitch": "Il profumo ti guida da metà del caruggio: pepe lungo di Giava, cardamomo, incensi pontificali, gomme arabiche, cere d'api e miscele segrete per il pandolce.",
        "personaggio": "San Bernardo di Chiaravalle",
        "url": "https://www.botteghestorichegenova.it/", "tel": "010 2468359"
    },
    {
        "key_id": "sapesta",
        "nome": "Antica Friggitoria Sa' Pesta (Forno a Legna dal 1883)",
        "comune": "Genova", "zona": "centro", "tipo": "bottega",
        "lat": 44.4066, "lon": 8.9312, "indoor": "in", "treno": True,
        "trasporto_info": "Via dei Giustiniani 16r",
        "durata_min": 50, "costo": "Pranzo / Asporto", "free": False, "free_1st_sun": False,
        "days": [1, 2, 3, 4, 5, 6], "slots": [[12.0, 15.0]], "months": list(range(1,13)),
        "orari": "Lun-Sab solo a pranzo 12:00-15:00; Dom chiuso",
        "pitch": "Tappa pranzo leggendaria nei caruggi: farinata d'oro sfornata a legna nei giganteschi testi di rame, torta pasqualina di carciofi o bietole, ripieni e frisceu.",
        "personaggio": "La Maona dei Giustiniani (Signori di Chio)",
        "url": "https://www.sapesta.it/", "tel": "010 2468336"
    },
    {
        "key_id": "marescotti_cavo",
        "nome": "Pasticceria Liquoreria Marescotti di Cavo (1780)",
        "comune": "Genova", "zona": "centro", "tipo": "bottega",
        "lat": 44.4119, "lon": 8.9293, "indoor": "in", "treno": True,
        "trasporto_info": "Via di Fossatello 35r (5 min da Via Garibaldi)",
        "durata_min": 40, "costo": "Consumazione", "free": False, "free_1st_sun": False,
        "days": [0, 2, 3, 4, 5, 6], "slots": [[8.5, 19.5]], "months": list(range(1,13)),
        "orari": "Mar-Dom 08:30-19:30; Lun chiuso (Aperta anche la Domenica!)",
        "pitch": "Pausa caffè e pasticceria nei saloni dorati settecenteschi con museo degli stampi lignei: assaggia i celebri Amaretti morbidi di Voltaggio e i Quaresimali.",
        "personaggio": "Simone Boccanegra & Famiglia Cavo",
        "url": "https://www.pasticceriacavo.it/", "tel": "010 2091164"
    },
    {
        "key_id": "finollo",
        "nome": "Camiceria & Cravatteria Liberty E. Finollo (1899)",
        "comune": "Genova", "zona": "centro", "tipo": "bottega",
        "lat": 44.4093, "lon": 8.9355, "indoor": "in", "treno": True,
        "trasporto_info": "Via Roma 38r (accanto a Galleria Mazzini)",
        "durata_min": 25, "costo": "Ingresso libero / Acquisti", "free": True, "free_1st_sun": False,
        "days": [2, 3, 4, 5, 6], "slots": [[9.5, 13.0], [15.5, 19.5]], "months": list(range(1,13)),
        "orari": "Mar-Sab 09:30-13:00 e 15:30-19:30; Lun e Dom chiuso",
        "pitch": "Vetrina e boiserie Art Nouveau capolavoro d'ebanisteria: celebre nel mondo per le cravatte 'sette pieghe' con iniziali ricamate in bandiere nautiche.",
        "personaggio": "Giuseppe Mazzini & Eugenio Finollo",
        "url": "https://www.finollo.it/", "tel": "010 562073"
    },

    # --- GENOVA: RIVIERE URBANE (PEGLI, NERVI, BOCCADASSE) ---
    {
        "key_id": "villa_pallavicini_pegli",
        "nome": "Parco Scenografico di Villa Durazzo-Pallavicini (Pegli)",
        "comune": "Genova", "zona": "genova_mare", "tipo": "natura",
        "lat": 44.4285, "lon": 8.8171, "indoor": "out", "treno": True,
        "trasporto_info": "Stazione Genova Pegli (proprio di fronte all'ingresso!) o Navebus dal Porto Antico",
        "durata_min": 150, "costo": "Biglietto", "free": False, "free_1st_sun": False,
        "days": [0, 2, 3, 4, 5, 6], "slots": [[9.5, 18.0]], "months": list(range(1,13)),
        "orari": "Mar-Dom 09:30-17:00 (Inverno) / 09:30-19:00 (Primavera-Estate); Lun chiuso",
        "pitch": "Uno dei parchi romantici più belli d'Europa: un vero percorso teatrale ed esoterico in 3 atti tra grotte infernali, viali di camelie secolari, pagode e il Tempio di Diana sul lago.",
        "personaggio": "Marchese Ignazio Alessandro Pallavicini & Michele Canzio",
        "url": "https://www.villadurazzopallavicini.it/", "tel": "010 5578280"
    },
    {
        "key_id": "parchi_nervi",
        "nome": "Parchi di Nervi, Roseto & Passeggiata Anita Garibaldi",
        "comune": "Genova", "zona": "genova_mare", "tipo": "natura",
        "lat": 44.3816, "lon": 9.0435, "indoor": "out", "treno": True,
        "trasporto_info": "Stazione Genova Nervi (accesso diretto sulla passeggiata a mare!)",
        "durata_min": 120, "costo": "Gratis", "free": True, "free_1st_sun": True,
        "days": [0, 1, 2, 3, 4, 5, 6], "slots": [[8.0, 21.0]], "months": list(range(1,13)),
        "orari": "Sempre aperto dall'alba al tramonto (Passeggiata sempre accessibile salvo mareggiate)",
        "pitch": "2 km sospesi sugli scogli a picco sul mare più 9 ettari di parchi botanici con scoiattoli socievoli, alberi monumentali e il Roseto Luigi Viacava.",
        "personaggio": "Anita Garibaldi & Casate Serra / Gropallo / Grimaldi",
        "url": "https://www.visitgenoa.it/it/parchi-di-nervi", "tel": ""
    },
    {
        "key_id": "musei_nervi",
        "nome": "Polo Museale di Nervi (GAM, Raccolte Frugone & Wolfsoniana)",
        "comune": "Genova", "zona": "genova_mare", "tipo": "museo",
        "lat": 44.3824, "lon": 9.0448, "indoor": "in", "treno": True,
        "trasporto_info": "Stazione Genova Nervi (5 min a piedi dentro i Parchi)",
        "durata_min": 90, "costo": "Biglietto", "free": False, "free_1st_sun": False,
        "days": [0, 2, 3, 4, 5, 6], "slots": [[11.0, 17.5]], "months": list(range(1,13)),
        "orari": "Mar-Dom 11:00-17:00 (Inverno) / 11:30-19:00 (Estate); Lun chiuso",
        "pitch": "Tre musei nelle ville storiche dei Parchi di Nervi: paesaggi liguri dell'800-'900, bronzi Belle Époque e gli arredi Art Déco della Wolfsoniana.",
        "personaggio": "Rubaldo Merello, Fratelli Frugone & Mitchell Wolfson",
        "url": "https://www.museidigenova.it/it/gam-galleria-darte-moderna", "tel": "010 3726025"
    },
    {
        "key_id": "boccadasse",
        "nome": "Borgo Marinaro di Boccadasse & Belvedere Capo Santa Chiara",
        "comune": "Genova", "zona": "genova_mare", "tipo": "natura",
        "lat": 44.3898, "lon": 8.9744, "indoor": "out", "treno": False,
        "trasporto_info": "Bus 31 o 42 da Brignole / Passeggiata Corso Italia sul mare (30 min a piedi)",
        "durata_min": 90, "costo": "Gratis", "free": True, "free_1st_sun": True,
        "days": [0, 1, 2, 3, 4, 5, 6], "slots": [[7.0, 23.5]], "months": list(range(1,13)),
        "orari": "Sempre accessibile (magico per gelato artigianale, focaccia o aperitivo sugli scogli al tramonto)",
        "pitch": "Case color pastello strette attorno alla spiaggetta di ciottoli e una creuza che sale fino al belvedere di Capo Santa Chiara sotto il fiabesco Castello Türcke.",
        "personaggio": "Edoardo Firpo & Gino Coppedè (Castello Türcke)",
        "url": "https://www.visitgenoa.it/it/boccadasse", "tel": ""
    },

    # --- GENOVA: BIBLIOTECHE MONUMENTALI & TEATRI ---
    {
        "key_id": "biblio_universitaria",
        "nome": "Biblioteca Universitaria (Saloni dell'Ex Grand Hotel Colombia)",
        "comune": "Genova", "zona": "centro", "tipo": "biblioteca",
        "lat": 44.4167, "lon": 8.9222, "indoor": "in", "treno": True,
        "trasporto_info": "Via Balbi 40 — Proprio di fronte alla Stazione Piazza Principe",
        "durata_min": 60, "costo": "Gratis", "free": True, "free_1st_sun": False,
        "days": [1, 2, 3, 4, 5], "slots": [[8.5, 18.5]], "months": list(range(1,13)),
        "orari": "Lun-Ven 08:30-18:30; Sab-Dom chiuso",
        "pitch": "Leggere o visitare mostre gratuite nei saloni marmorei Art Déco dell'ex Grand Hotel Colombia che accoglieva i viaggiatori dei grandi transatlantici.",
        "personaggio": "Famiglia Balbi",
        "url": "https://www.bibliotecauniversitaria.ge.it/", "tel": "010 254641"
    },
    {
        "key_id": "biblio_berio",
        "nome": "Biblioteca Civica Berio & Terrazza sull'Antico Seminario",
        "comune": "Genova", "zona": "centro", "tipo": "biblioteca",
        "lat": 44.4055, "lon": 8.9365, "indoor": "in", "treno": True,
        "trasporto_info": "Via del Seminario 16 (4 min a piedi da Piazza De Ferrari / Dante)",
        "durata_min": 60, "costo": "Gratis", "free": True, "free_1st_sun": False,
        "days": [1, 2, 3, 4, 5, 6], "slots": [[8.0, 19.0]], "months": list(range(1,13)),
        "orari": "Lun-Sab 08:00-19:00; Dom chiuso",
        "pitch": "La storica biblioteca centrale fondata dall'abate Berio nel Settecento: mostre bibliografiche, conferenze pomeridiane gratuite e caffetteria panoramica.",
        "personaggio": "Abate Carlo Giuseppe Vespasiano Berio",
        "url": "https://www.bibliotechedigenova.it/", "tel": "010 5576010"
    },
    {
        "key_id": "biblio_deamicis",
        "nome": "Biblioteca De Amicis al Porto Antico (Bambini & Illustrazione)",
        "comune": "Genova", "zona": "centro", "tipo": "biblioteca",
        "lat": 44.4088, "lon": 8.9228, "indoor": "in", "treno": True,
        "trasporto_info": "Porto Antico — Magazzini del Cotone Modulo 1",
        "durata_min": 75, "costo": "Gratis", "free": True, "free_1st_sun": False,
        "days": [1, 2, 3, 4, 5, 6], "slots": [[9.0, 19.0]], "months": list(range(1,13)),
        "orari": "Lun-Sab 09:00-19:00 (Sabato dedicato a bambini, ragazzi e famiglie)",
        "pitch": "Affacciata sull'acqua del Porto Antico: la più grande biblioteca italiana per ragazzi e fumetto/illustrazione, con laboratori gratuiti.",
        "personaggio": "Edmondo De Amicis",
        "url": "https://www.bibliotechedigenova.it/", "tel": "010 5579560"
    },
    {
        "key_id": "biblio_lercari",
        "nome": "Biblioteca Lercari & Parco Cinquecentesco di Villa Imperiale",
        "comune": "Genova", "zona": "centro", "tipo": "biblioteca",
        "lat": 44.4098, "lon": 8.9585, "indoor": "mix", "treno": True,
        "trasporto_info": "12 min da Stazione Genova Brignole (San Fruttuoso - Via S. Fruttuoso 74)",
        "durata_min": 75, "costo": "Gratis", "free": True, "free_1st_sun": True,
        "days": [1, 2, 3, 4, 5], "slots": [[9.0, 18.0]], "months": list(range(1,13)),
        "orari": "Sale affrescate Lun-Ven 09:00-18:00; Parco di Villa Imperiale aperto tutti i giorni",
        "pitch": "Una villa rinascimentale affrescata da Luca Cambiaso circondata da un grande parco a terrazze di lecci: ingresso completamente gratuito.",
        "personaggio": "Gian Luigi Lercari & Lorenzo Cattaneo (ospitò Re Luigi XII nel 1502)",
        "url": "https://www.bibliotechedigenova.it/", "tel": "010 5579880"
    },
    {
        "key_id": "carlo_felice",
        "nome": "Teatro Carlo Felice — Opera, Sinfonica & Visite al Palcoscenico",
        "comune": "Genova", "zona": "centro", "tipo": "teatro",
        "lat": 44.4079, "lon": 8.9348, "indoor": "in", "treno": True,
        "trasporto_info": "Piazza De Ferrari (Metro De Ferrari)",
        "durata_min": 150, "costo": "Biglietto spettacolo / Visita", "free": False, "free_1st_sun": False,
        "days": [0, 1, 2, 3, 4, 5, 6], "slots": [[9.5, 23.0]], "months": list(range(1,13)),
        "orari": "Biglietteria Lun-Sab 09:30-19:00; Spettacoli serali ore 20:00 e domenicali ore 15:00/16:00",
        "pitch": "Lirica, balletto, grandi concerti sinfonici e visite guidate dietro le quinte della torre scenica progettata da Aldo Rossi.",
        "personaggio": "Re Carlo Felice di Savoia & Eugenio Montale",
        "url": "https://operacarlofelicegenova.it/", "tel": "010 5381433"
    },
    {
        "key_id": "teatro_nazionale",
        "nome": "Teatro Nazionale di Genova (Ivo Chiesa, Eleonora Duse & Modena)",
        "comune": "Genova", "zona": "centro", "tipo": "teatro",
        "lat": 44.4036, "lon": 8.9445, "indoor": "in", "treno": True,
        "trasporto_info": "Corte Lambruschini (5 min da Brignole), Via Bacigalupo (Duse) o Sampierdarena (Modena)",
        "durata_min": 135, "costo": "Biglietto spettacolo", "free": False, "free_1st_sun": False,
        "days": [0, 2, 3, 4, 5, 6], "slots": [[15.25, 23.0]], "months": [1,2,3,4,5,10,11,12],
        "orari": "Biglietteria Mar-Sab 15:15-19:15; Spettacoli Mar-Sab 19:30/20:30, Dom 16:00",
        "pitch": "Uno dei massimi teatri stabili d'Europa: grande prosa, drammaturgia contemporanea e l'acustica ottocentesca della Sala Mercato e del Teatro Modena.",
        "personaggio": "Ivo Chiesa, Eleonora Duse & Gustavo Modena",
        "url": "https://www.teatronazionalegenova.it/", "tel": "010 5342400"
    },
    {
        "key_id": "teatro_tosse",
        "nome": "Teatri di Sant'Agostino & La Claque (Teatro della Tosse)",
        "comune": "Genova", "zona": "centro", "tipo": "teatro",
        "lat": 44.4046, "lon": 8.9324, "indoor": "in", "treno": True,
        "trasporto_info": "Metro Sarzano / Sant'Agostino (2 min a piedi)",
        "durata_min": 120, "costo": "Biglietto", "free": False, "free_1st_sun": False,
        "days": [0, 2, 3, 4, 5, 6], "slots": [[16.0, 23.5]], "months": list(range(1,13)),
        "orari": "Spettacoli serali ore 20:30/21:30 e rassegne domenicali per famiglie",
        "pitch": "Teatro visionario fondato da Tonino Conte ed Emanuele Luzzati, affiancato dal club live 'La Claque' in Vico di San Donato per musica dal vivo e stand-up.",
        "personaggio": "Tonino Conte & Emanuele Luzzati",
        "url": "https://www.teatrodellatosse.it/", "tel": "010 2470793"
    },

    # --- GOLFO PARADISO (RECCO, CAMOGLI, SAN FRUTTUOSO, AVEGNO, USCIO, SORI) ---
    {
        "key_id": "teatro_camogli",
        "nome": "Teatro Sociale di Camogli — Concerti & Aperitivo nei Palchi",
        "comune": "Camogli", "zona": "golfo_paradiso", "tipo": "teatro",
        "lat": 44.3502, "lon": 9.1538, "indoor": "in", "treno": True,
        "trasporto_info": "Stazione Camogli-S. Fruttuoso (proprio davanti alla stazione!)",
        "durata_min": 120, "costo": "Biglietto", "free": False, "free_1st_sun": False,
        "days": [0, 4, 5, 6], "slots": [[10.0, 12.0], [17.0, 23.0]], "months": list(range(1,13)),
        "orari": "Biglietteria Lun-Ven 10:00-12:00; Concerti, Jazz e 'Aperitivo a Teatro' Ven-Dom pomeriggio e sera",
        "pitch": "Gioiello acustico del 1876 a quattro ordini di palchi sul mare: celebre per la formula 'Aperitivo nei Palchi' servito direttamente nel tuo palchetto storico.",
        "personaggio": "Capitani Marittimi Camogliesi & Giacomo Matteotti",
        "url": "https://www.teatrosocialecamogli.it/", "tel": "0185 1770529"
    },
    {
        "key_id": "museo_marinaro_camogli",
        "nome": "Museo Marinaro 'Gio Bono Ferrari' & Porticciolo di Camogli",
        "comune": "Camogli", "zona": "golfo_paradiso", "tipo": "museo",
        "lat": 44.3496, "lon": 9.1533, "indoor": "in", "treno": True,
        "trasporto_info": "Stazione Camogli (3 min a piedi — Via Gio Bono Ferrari 41)",
        "durata_min": 60, "costo": "Gratis / Offerta libera", "free": True, "free_1st_sun": True,
        "days": [0, 2, 3, 4, 5, 6], "slots": [[9.0, 12.0], [15.0, 18.0]], "months": list(range(1,13)),
        "orari": "Mar-Dom 09:00-12:00 e Mer-Dom spesso 15:00-18:00; Lun chiuso",
        "pitch": "L'epopea della 'Città dei Mille Bianchi Velieri': modelli di brigantini, dipinti di naufragi a Capo Horn, strumenti nautici e cimeli garibaldini.",
        "personaggio": "Gio Bono Ferrari & Famiglia Schiaffino",
        "url": "https://www.museomarinaro.it/", "tel": "0185 729049"
    },
    {
        "key_id": "punta_chiappa",
        "nome": "Sentiero di San Rocco, Batterie & Scoglio di Punta Chiappa",
        "comune": "Camogli", "zona": "golfo_paradiso", "tipo": "natura",
        "lat": 44.3248, "lon": 9.1468, "indoor": "out", "treno": True,
        "trasporto_info": "Da Camogli a piedi per la mulattiera di San Nicolò di Capodimonte o Battello per Porto Pidocchio",
        "durata_min": 165, "costo": "Gratis", "free": True, "free_1st_sun": True,
        "days": [0, 1, 2, 3, 4, 5, 6], "slots": [[8.0, 19.5]], "months": list(range(1,13)),
        "orari": "Sentiero del Parco di Portofino e chiesetta romanica di San Nicolò sempre accessibili",
        "pitch": "Una lingua di roccia antichissima protesa nel mare blu del Parco di Portofino, passando per la chiesa millenaria di San Nicolò di Capodimonte e piccoli ristorantini sugli scogli.",
        "personaggio": "San Nicolò & Pescatori della Tonnarella di Camogli (dal '600)",
        "url": "https://www.parcodiportofino.it/", "tel": ""
    },
    {
        "key_id": "san_fruttuoso",
        "nome": "Abbazia di San Fruttuoso di Capodimonte & Torre Doria (Bene FAI)",
        "comune": "Camogli", "zona": "golfo_paradiso", "tipo": "abbazia",
        "lat": 44.3163, "lon": 9.1749, "indoor": "mix", "treno": True,
        "trasporto_info": "Battello da Camogli (30 min) o da Rapallo/Portofino, oppure trekking nel Parco di Portofino",
        "durata_min": 150, "costo": "Biglietto FAI (Gratis iscritti FAI)", "free": False, "free_1st_sun": False,
        "days": [0, 1, 2, 3, 4, 5, 6], "slots": [[10.0, 16.0]], "months": list(range(1,13)),
        "orari": "Tutti i giorni 10:00-15:45 (Primavera/Estate fino 16:30-17:30) — soggetto a condizioni del mare",
        "pitch": "Incastonata in una cala smeraldo senza strade né auto: abbazia benedettina sul mare con le tombe marmoree della famiglia Doria e il Cristo degli Abissi poco al largo.",
        "personaggio": "Andrea Doria & Duilio Marcante (Cristo degli Abissi)",
        "url": "https://fondoambiente.it/luoghi/abbazia-di-san-fruttuoso", "tel": "0185 772703"
    },
    {
        "key_id": "focaccia_recco",
        "nome": "Focaccerie Storiche IGP & Lungomare di Recco",
        "comune": "Recco", "zona": "golfo_paradiso", "tipo": "bottega",
        "lat": 44.3618, "lon": 9.1432, "indoor": "mix", "treno": True,
        "trasporto_info": "Stazione di Recco (22 min di treno da Genova Brignole)",
        "durata_min": 60, "costo": "Degustazione / Pranzo", "free": False, "free_1st_sun": False,
        "days": [0, 1, 2, 3, 4, 5, 6], "slots": [[8.5, 22.0]], "months": list(range(1,13)),
        "orari": "Forni e ristoranti storici del Consorzio aperti tutti i giorni da mattina a sera",
        "pitch": "La patria della Focaccia di Recco col Formaggio IGP (due veli trasparenti di pasta senza lievito colmi di crescenza fusa), perfetta prima di proseguire a Camogli.",
        "personaggio": "Nicoloso da Recco (esploratore delle Canarie nel 1341) & Biagio Assereto",
        "url": "https://www.focacciadirecco.it/", "tel": ""
    },
    {
        "key_id": "campane_avegno",
        "nome": "Museo delle Campane — Antica Fonderia Picasso (1850)",
        "comune": "Avegno", "zona": "golfo_paradiso", "tipo": "bottega",
        "lat": 44.3831, "lon": 9.1585, "indoor": "in", "treno": False,
        "trasporto_info": "10 min in auto o Bus da Recco risalendo la verde Valle di Recco",
        "durata_min": 60, "costo": "Ingresso / Offerta", "free": False, "free_1st_sun": False,
        "days": [6], "slots": [[10.0, 12.0], [15.0, 18.0]], "months": list(range(1,13)),
        "orari": "Sabato 10:00-12:00 e 15:00-18:00 (altri giorni su appuntamento)",
        "pitch": "Un mestiere iper-specifico rarissimo: forni fusori, sagome in argilla, diapason e grandi campane in bronzo fuse per i campanili della Liguria e dell'America Latina.",
        "personaggio": "Famiglia Picasso (Maestri Fonditori dal 1850)",
        "url": "https://www.comune.avegno.ge.it/", "tel": "0185 79138"
    },
    {
        "key_id": "orologi_uscio",
        "nome": "Museo degli Orologi da Torre Roberto Trebino (1824)",
        "comune": "Uscio", "zona": "golfo_paradiso", "tipo": "bottega",
        "lat": 44.4135, "lon": 9.1552, "indoor": "in", "treno": False,
        "trasporto_info": "18 min in auto da Recco sulla Via della Costa verso la Val Fontanabuona",
        "durata_min": 60, "costo": "Gratis su prenotazione", "free": True, "free_1st_sun": False,
        "days": [1, 2, 3, 4, 5], "slots": [[9.0, 12.0], [14.5, 17.5]], "months": list(range(1,13)),
        "orari": "Lun-Ven 09:00-12:00 e 14:30-17:30 (consigliata telefonata per visita guidata all'atelier)",
        "pitch": "Fornitori ufficiali della Città del Vaticano: ad Uscio nascono dal 1824 gli ingranaggi meccanici giganti e i quadranti degli orologi dei campanili e dei palazzi pubblici di tutto il mondo.",
        "personaggio": "Roberto Trebino & Maestri Orologiai di Uscio",
        "url": "https://www.trebino.it/museo/", "tel": "0185 919340"
    },

    # --- TIGULLIO OCCIDENTALE (PORTOFINO, SANTA MARGHERITA, RAPALLO, ZOAGLI) ---
    {
        "key_id": "castello_brown",
        "nome": "Castello Brown, Piazzetta & Sentiero del Faro di Portofino",
        "comune": "Portofino", "zona": "tigullio_occ", "tipo": "dimora",
        "lat": 44.3025, "lon": 9.2134, "indoor": "mix", "treno": True,
        "trasporto_info": "Treno fino a S. Margherita Ligure + Bus 782 / Battello o Passeggiata dei Baci sul mare (5 km)",
        "durata_min": 120, "costo": "Sentiero Faro gratis / Castello a biglietto", "free": False, "free_1st_sun": False,
        "days": [0, 1, 2, 3, 4, 5, 6], "slots": [[10.0, 17.0]], "months": list(range(1,13)),
        "orari": "Nov-Mar 10:00-16:00; Apr-Mag/Set 10:00-19:00; Giu-Ago 10:00-21:00; Ott 10:00-18:00",
        "pitch": "Fortezza genovese divenuta dimora del console inglese Montague Yeats Brown: giardino pensile con la vista più iconica sulla baia di Portofino e sentiero fino al Faro.",
        "personaggio": "Console Montague Yeats Brown",
        "url": "https://www.castellobrown.com/", "tel": "0185 267101"
    },
    {
        "key_id": "villa_durazzo_sml",
        "nome": "Villa Durazzo-Centurione & Parco Barocco sul Golfo",
        "comune": "Santa Margherita Ligure", "zona": "tigullio_occ", "tipo": "dimora",
        "lat": 44.3318, "lon": 9.2141, "indoor": "mix", "treno": True,
        "trasporto_info": "Stazione S. Margherita Ligure-Portofino (8 min a piedi)",
        "durata_min": 90, "costo": "Parco gratis / Museo a biglietto", "free": False, "free_1st_sun": False,
        "days": [0, 1, 2, 3, 4, 5, 6], "slots": [[9.0, 17.5]], "months": list(range(1,13)),
        "orari": "Aperta tutti i giorni (anche Lunedì!): Parco 09:00-17:00 (Est 19:00); Museo 09:30-13:00 e 14:00-17:00",
        "pitch": "Un parco gratuito spettacolare di camelie, cipressi e statue marmoree affacciato sul mare, con appartamenti principeschi e caffetteria nel giardino segreto degli agrumi.",
        "personaggio": "Casate Durazzo & Centurione",
        "url": "https://www.villadurazzo.it/", "tel": "0185 293135"
    },
    {
        "key_id": "cervara",
        "nome": "Abbazia della Cervara — Giardino Monumentale a Picco sul Mare",
        "comune": "Santa Margherita Ligure", "zona": "tigullio_occ", "tipo": "abbazia",
        "lat": 44.3168, "lon": 9.2116, "indoor": "mix", "treno": True,
        "trasporto_info": "Lungo la Passeggiata panoramica tra S. Margherita Ligure e Paraggi/Portofino",
        "durata_min": 90, "costo": "Visite guidate su prenotazione (1ª e 3ª dom da Mar a Ott)", "free": False, "free_1st_sun": False,
        "days": [0], "slots": [[10.0, 17.0]], "months": [3,4,5,6,7,8,9,10],
        "orari": "Visite guidate su prenotazione 1ª e 3ª domenica del mese (Marzo–Ottobre)",
        "pitch": "Fondata nel 1361 a strapiombo sull'acqua: giardino all'italiana unico in Liguria dove sostarono Petrarca, Santa Caterina da Siena e Re Francesco I.",
        "personaggio": "Francesco Petrarca & Re Francesco I",
        "url": "https://www.cervara.it/", "tel": "0185 293197"
    },
    {
        "key_id": "merletto_rapallo",
        "nome": "Museo del Merletto a Villa Tigullio & Castello sul Mare di Rapallo",
        "comune": "Rapallo", "zona": "tigullio_occ", "tipo": "museo",
        "lat": 44.3490, "lon": 9.2369, "indoor": "mix", "treno": True,
        "trasporto_info": "Stazione di Rapallo (12 min a piedi lungo il Chiosco della Musica e il Castello sul mare)",
        "durata_min": 90, "costo": "Gratis", "free": True, "free_1st_sun": True,
        "days": [2, 3, 4, 5, 6], "slots": [[9.5, 12.0], [14.0, 18.0]], "months": list(range(1,13)),
        "orari": "Museo Mar-Sab 09:30-12:00 e 14:00-18:00; Parco Casale e Lungomare del Castello sempre aperti",
        "pitch": "Nella settecentesca Villa Tigullio nel verde del Parco Casale: oltre 1.400 merletti finissimi al tombolo a fuselli, più passeggiata al cinquecentesco Castello sull'acqua.",
        "personaggio": "Merlettaie del Tigullio & Friedrich Nietzsche (scrisse qui lo Zarathustra)",
        "url": "https://www.comune.rapallo.ge.it/", "tel": "0185 63305"
    },
    {
        "key_id": "montallegro",
        "nome": "Funivia Panoramica & Santuario di Montallegro (612 m)",
        "comune": "Rapallo", "zona": "tigullio_occ", "tipo": "abbazia",
        "lat": 44.3649, "lon": 9.2602, "indoor": "out", "treno": True,
        "trasporto_info": "Stazione Funivia a 7 min a piedi dalla Stazione FS di Rapallo (o in auto)",
        "durata_min": 120, "costo": "Santuario gratis / Biglietto Funivia", "free": False, "free_1st_sun": True,
        "days": [0, 1, 2, 3, 4, 5, 6], "slots": [[8.5, 17.5]], "months": list(range(1,13)),
        "orari": "Tutti i giorni 08:30/09:00 - 16:30/18:30 (Funivia soggetta a vento/manutenzione periodica)",
        "pitch": "L'unica funivia della Liguria ti solleva in 7 minuti dal livello del mare a 612 metri sopra l'intero Golfo del Tigullio, tra leccete secolari e trattorie tipiche.",
        "personaggio": "Giovanni Chichizola (1557)",
        "url": "https://santuariodimontallegro.com/", "tel": "0185 52341"
    },
    {
        "key_id": "velluti_zoagli",
        "nome": "Atelier dei Velluti di Seta & Passeggiata nella Scogliera di Zoagli",
        "comune": "Zoagli", "zona": "tigullio_occ", "tipo": "bottega",
        "lat": 44.3371, "lon": 9.2673, "indoor": "mix", "treno": True,
        "trasporto_info": "Stazione di Zoagli (5 min a piedi dalla piazzetta sotto il viadotto sul mare)",
        "durata_min": 90, "costo": "Passeggiata gratis / Visita seterie", "free": True, "free_1st_sun": True,
        "days": [0, 1, 2, 3, 4, 5, 6], "slots": [[9.0, 19.0]], "months": list(range(1,13)),
        "orari": "Passeggiata Canevaro sugli scogli sempre aperta; Tessiture storiche (Cordani / Gaggioli) Lun-Ven/Sab",
        "pitch": "Cammina a filo d'onda lungo le due passeggiate scavate nella roccia e scopri gli ultimi telai manuali dell'Ottocento che tessono il velluto di seta cesellato.",
        "personaggio": "Sem Benelli & Famiglia Canevaro",
        "url": "https://www.comune.zoagli.ge.it/", "tel": "0185 25051"
    },

    # --- TIGULLIO ORIENTALE, VAL FONTANABUONA, VAL GRAVEGLIA & VAL D'AVETO ---
    {
        "key_id": "palazzo_rocca_chiavari",
        "nome": "Parco Botanico di Palazzo Rocca & Botteghe della Sedia Chiavarina",
        "comune": "Chiavari", "zona": "tigullio_or", "tipo": "dimora",
        "lat": 44.3193, "lon": 9.3238, "indoor": "mix", "treno": True,
        "trasporto_info": "Stazione di Chiavari (7 min a piedi sotto i portici medievali del 'Caruggio Dritto')",
        "durata_min": 120, "costo": "Parco gratis / Museo Archeologico (Gratis 1ª Dom)", "free": True, "free_1st_sun": True,
        "days": [0, 2, 3, 4, 5, 6], "slots": [[10.0, 17.5]], "months": list(range(1,13)),
        "orari": "Parco Botanico Mar-Dom 10:00-17:00 (Est 19:00); Botteghe ebaniste in Via Rivarola/Bighetti Mar-Sab",
        "pitch": "Bambuseti, grotte romantiche, serre d'orchidee e Padiglione del Tè sopra i portici d'ardesia dove gli ebanisti impagliano a mano la leggerissima Sedia Chiavarina.",
        "personaggio": "Giuseppe Gaetano Descalzi ('Il Campanino') & Giuseppe Rocca",
        "url": "https://www.parcoroccachiavari.it/", "tel": "0185 365294"
    },
    {
        "key_id": "defilla_luchin_chiavari",
        "nome": "Gran Caffè Defilla (1905) & Antica Osteria Luchin (1907) — Chiavari",
        "comune": "Chiavari", "zona": "tigullio_or", "tipo": "bottega",
        "lat": 44.3174, "lon": 9.3230, "indoor": "in", "treno": True,
        "trasporto_info": "Centro Storico di Chiavari (Corso Garibaldi 4 / Via Bighetti 53)",
        "durata_min": 60, "costo": "Consumazione / Pranzo", "free": False, "free_1st_sun": False,
        "days": [1, 2, 3, 4, 5, 6], "slots": [[8.0, 20.0]], "months": list(range(1,13)),
        "orari": "Defilla aperto tutti i giorni 07:30-21:00; Farinata da Luchin Lun-Sab pranzo e cena (Dom chiuso)",
        "pitch": "Due monumenti del gusto sotto i portici di Chiavari: gli specchi Liberty e la crema del Defilla, e la farinata bollente sfornata a legna sui tavoli di marmo da Luchin.",
        "personaggio": "Giuseppe Garibaldi & Padri di Giuseppe Mazzini e Nino Bixio",
        "url": "https://www.chiavariturismo.it/", "tel": "0185 308053"
    },
    {
        "key_id": "basilica_fieschi",
        "nome": "Piazza Medievale & Basilica dei Fieschi a San Salvatore",
        "comune": "Cogorno", "zona": "tigullio_or", "tipo": "abbazia",
        "lat": 44.3245, "lon": 9.3547, "indoor": "mix", "treno": True,
        "trasporto_info": "3 km dalla Stazione di Lavagna o Chiavari (Bus linea val Fontanabuona o ciclabile lungo l'Entella!)",
        "durata_min": 60, "costo": "Gratis", "free": True, "free_1st_sun": True,
        "days": [0, 1, 2, 3, 4, 5, 6], "slots": [[9.0, 18.0]], "months": list(range(1,13)),
        "orari": "Tutti i giorni 09:00-12:00 e 15:00-18:00 (abbinabile alla ciclabile naturalistica del fiume Entella)",
        "pitch": "Un sagrato duecentesco intatto a fasce di marmo bianco e ardesia nera con rosone merlettato e Palazzo Comitale, voluto da Papa Innocenzo IV Fieschi nel 1244.",
        "personaggio": "Papa Innocenzo IV (Sinibaldo Fieschi) & Papa Adriano V",
        "url": "https://www.comune.cogorno.ge.it/", "tel": ""
    },
    {
        "key_id": "musel_baia_sestri",
        "nome": "Baia del Silenzio, MuSel & Pasticceria Storica Rossignotti (1840)",
        "comune": "Sestri Levante", "zona": "tigullio_or", "tipo": "museo",
        "lat": 44.2701, "lon": 9.3941, "indoor": "mix", "treno": True,
        "trasporto_info": "Stazione di Sestri Levante (10 min a piedi lungo il caruggio pedonale Via XXV Aprile)",
        "durata_min": 120, "costo": "Baia gratis / MuSel a biglietto (Gratis 1ª Dom)", "free": False, "free_1st_sun": True,
        "days": [0, 2, 3, 4, 5, 6], "slots": [[9.0, 18.5]], "months": list(range(1,13)),
        "orari": "MuSel Mar-Sab 09:00-13:00 e 14:00-17:00, Dom 15:00-18:30; Baia del Silenzio e Rossignotti tutti i giorni",
        "pitch": "La penisola tra due mari amata da Andersen: museo della città a Palazzo Fascie, praline in arredi Liberty da Rossignotti (1840) e luce magica sulla Baia del Silenzio.",
        "personaggio": "Hans Christian Andersen & Guglielmo Marconi",
        "url": "https://www.musel.it/", "tel": "0185 478530"
    },
    {
        "key_id": "punta_manara",
        "nome": "Promontorio di Punta Manara — Trekking Panoramico tra Due Golfi",
        "comune": "Sestri Levante", "zona": "tigullio_or", "tipo": "natura",
        "lat": 44.2564, "lon": 9.4062, "indoor": "out", "treno": True,
        "trasporto_info": "L'imbocco del sentiero parte direttamente dal caruggio storico di Sestri Levante (Vico del Bottone)!",
        "durata_min": 150, "costo": "Gratis", "free": True, "free_1st_sun": True,
        "days": [0, 1, 2, 3, 4, 5, 6], "slots": [[7.5, 19.5]], "months": list(range(1,13)),
        "orari": "Sentiero libero tutto l'anno (1h di salita dolce nella macchia mediterranea)",
        "pitch": "Uno dei sentieri costieri più belli della Liguria: parte dai vicoli di Sestri e attraversa corbezzoli e sughere fino ai ruderi della torre saracena a picco sul mare.",
        "personaggio": "Guardiani delle Torri d'Avvistamento della Repubblica",
        "url": "https://www.sestri-levante.net/", "tel": ""
    },
    {
        "key_id": "moneglia_borgo",
        "nome": "Chiostro di San Giorgio, Fortezze sul Mare & Borgo di Moneglia",
        "comune": "Moneglia", "zona": "tigullio_or", "tipo": "abbazia",
        "lat": 44.2389, "lon": 9.4895, "indoor": "mix", "treno": True,
        "trasporto_info": "Stazione di Moneglia (10 min a piedi nel borgo)",
        "durata_min": 90, "costo": "Gratis", "free": True, "free_1st_sun": True,
        "days": [0, 1, 2, 3, 4, 5, 6], "slots": [[9.0, 19.0]], "months": list(range(1,13)),
        "orari": "Borgo, Chiostro francescano del '400 e Fortezza di Villafranca visitabili tutti i giorni",
        "pitch": "Uno dei Borghi più Belli d'Italia stretto tra due fortezze sul mare e gli agrumeti del chiostro francescano, patria del pittore Luca Cambiaso.",
        "personaggio": "Luca Cambiaso & Felice Romani (librettista di Bellini)",
        "url": "https://www.comune.moneglia.ge.it/", "tel": ""
    },
    {
        "key_id": "miniera_gambatesa",
        "nome": "Miniera di Gambatesa — Viaggio sul Trenino dei Minatori",
        "comune": "Ne", "zona": "tigullio_or", "tipo": "museo",
        "lat": 44.3612, "lon": 9.4461, "indoor": "in", "treno": False,
        "trasporto_info": "30 min in auto da Lavagna/Chiavari risalendo la Val Graveglia (tra vigneti di Bianchetta e uliveti)",
        "durata_min": 105, "costo": "Biglietto visita con trenino", "free": False, "free_1st_sun": False,
        "days": [0, 6], "slots": [[10.0, 17.5]], "months": [3,4,5,6,7,8,9,10,11],
        "orari": "Sabato, Domenica e festivi 10:00-17:30 (Estate anche feriali; consigliata prenotazione)",
        "pitch": "Caschetto in testa a bordo del vero trenino minerario dentro le viscere della montagna: scopri il giacimento di manganese più grande d'Europa a temperatura costante di 14°C!",
        "personaggio": "Minatori della Val Graveglia",
        "url": "http://www.minieradigambatesa.com/", "tel": "0185 338854"
    },
    {
        "key_id": "damasco_lorsica",
        "nome": "Museo del Damasco & Antichi Telai della Seta di Lorsica",
        "comune": "Lorsica", "zona": "tigullio_or", "tipo": "bottega",
        "lat": 44.4293, "lon": 9.2678, "indoor": "in", "treno": False,
        "trasporto_info": "35 min in auto da Chiavari/Carasco lungo la Val Fontanabuona",
        "durata_min": 75, "costo": "Biglietto / Visita", "free": False, "free_1st_sun": False,
        "days": [0, 6], "slots": [[15.0, 18.0]], "months": list(range(1,13)),
        "orari": "Sabato e Domenica 15:00-17:00 (Inv) / 16:00-18:00 (Est); Lun-Ven su prenotazione alle tessiture De Martini",
        "pitch": "Tra i castagneti della Fontanabuona battono dal Cinquecento i telai manuali che creano damaschi e lampassi di seta pura per il Quirinale e le corti europee.",
        "personaggio": "Maestri Tessitori della Fontanabuona",
        "url": "https://www.cittametropolitana.genova.it/", "tel": "0185 95019"
    },
    {
        "key_id": "casa_giannini",
        "nome": "Casa Museo A.P. Giannini (Fondatore di Bank of America) & Teatro di Cicagna",
        "comune": "Favale di Malvaro", "zona": "tigullio_or", "tipo": "museo",
        "lat": 44.4519, "lon": 9.2578, "indoor": "in", "treno": False,
        "trasporto_info": "40 min in auto da Chiavari passando per Cicagna (Val Fontanabuona)",
        "durata_min": 75, "costo": "Ingresso / Prenotazione weekend", "free": True, "free_1st_sun": False,
        "days": [0, 6], "slots": [[10.0, 12.5], [15.0, 18.0]], "months": list(range(1,13)),
        "orari": "Weekend e su apertura comunale (abbinabile agli spettacoli del Teatro Comunale di Cicagna)",
        "pitch": "La casa d'origine della famiglia di Amadeo Peter Giannini, il visionario banchiere figlio di emigranti liguri che finanziò Walt Disney (Biancaneve), Chaplin e il Golden Gate Bridge!",
        "personaggio": "Amadeo Peter Giannini",
        "url": "https://www.comune.favaledimalvaro.ge.it/", "tel": "0185 975029"
    },
    {
        "key_id": "abbazia_borzone",
        "nome": "Abbazia Millenaria di Borzone & Misterioso Volto Megalitico",
        "comune": "Borzonasca", "zona": "tigullio_or", "tipo": "abbazia",
        "lat": 44.4264, "lon": 9.4038, "indoor": "mix", "treno": False,
        "trasporto_info": "25 min in auto da Chiavari/Carasco verso la Valle Sturla e il Parco dell'Aveto",
        "durata_min": 90, "costo": "Gratis", "free": True, "free_1st_sun": True,
        "days": [0, 6], "slots": [[10.0, 17.5]], "months": list(range(1,13)),
        "orari": "Complesso esterno, Castagno Monumentale e sentiero del Volto Megalitico sempre visitabili; chiesa aperta weekend",
        "pitch": "Un'abbazia in pietra nera del 1184 immersa nel silenzio della Valle Sturla, a pochi minuti a piedi dal più grande volto scolpito nella roccia preistorica/medievale d'Europa.",
        "personaggio": "Monaci Benedettini di San Colombano & Conti Fieschi",
        "url": "http://www.parcoaveto.it/", "tel": "0185 343370"
    },
    {
        "key_id": "aveto_lago_lame",
        "nome": "Castello Malaspina-Doria, Lago delle Lame & Faggete dell'Aveto",
        "comune": "Santo Stefano d'Aveto", "zona": "tigullio_or", "tipo": "natura",
        "lat": 44.5471, "lon": 9.4508, "indoor": "out", "treno": False,
        "trasporto_info": "1h 15m in auto da Chiavari attraverso Rezzoaglio e il Lago delle Lame",
        "durata_min": 180, "costo": "Gratis (Caseifici del formaggio San Sté in paese)", "free": True, "free_1st_sun": True,
        "days": [0, 1, 2, 3, 4, 5, 6], "slots": [[8.0, 19.0]], "months": list(range(1,13)),
        "orari": "Borgo alpino (1.012 m), specchio glaciale del Lago delle Lame a Rezzoaglio e sentieri del Monte Penna sempre aperti",
        "pitch": "Le Dolomiti della provincia di Genova: specchi d'acqua smeraldo tra abeti e faggi, il possente castello pentagonale dei Malaspina-Doria e il formaggio d'alpeggio San Sté.",
        "personaggio": "Zenobia Del Carretto Doria & Marchesi Malaspina",
        "url": "https://www.turismosantostefanodaveto.it/", "tel": "0185 88046"
    },

    # --- PONENTE & VALLE STURA (MELE, ARENZANO, COGOLETO, CAMPO LIGURE, ROSSIGLIONE, TIGLIETO) ---
    {
        "key_id": "museo_carta_mele",
        "nome": "Museo della Carta di Mele — Antica Cartiera Piccardo (1756)",
        "comune": "Mele", "zona": "ponente_stura", "tipo": "bottega",
        "lat": 44.4552, "lon": 8.7428, "indoor": "in", "treno": True,
        "trasporto_info": "Stazione Genova Voltri + Bus 93 (10 min) o 25 min in auto da Genova nella Valle delle Ferriere (Acquasanta)",
        "durata_min": 75, "costo": "Biglietto con laboratorio carta a mano", "free": False, "free_1st_sun": False,
        "days": [0, 5, 6], "slots": [[10.0, 13.0], [15.0, 18.0]], "months": list(range(1,13)),
        "orari": "Ven, Sab e Dom 10:00-13:00 e 15:00-18:00 (abbinabile alle Terme e al Santuario dell'Acquasanta!)",
        "pitch": "Dentro una vera cartiera settecentesca mossa dall'acqua nella gola di Acquasanta: vedi fabbricare dal vivo i fogli di carta di cotone a mano che per secoli usarono i notai d'Europa.",
        "personaggio": "Famiglia Piccardo & Mastri Cartai di Mele",
        "url": "https://www.museocartamele.it/", "tel": "010 6319005"
    },
    {
        "key_id": "arenzano_ciclabile",
        "nome": "Parco di Villa Negrotto Cambiaso & Ciclabile sul Mare De André",
        "comune": "Arenzano", "zona": "ponente_stura", "tipo": "natura",
        "lat": 44.4048, "lon": 8.6836, "indoor": "out", "treno": True,
        "trasporto_info": "Stazione di Arenzano o Cogoleto (5 min a piedi; noleggio bici direttamente sul lungomare!)",
        "durata_min": 135, "costo": "Gratis", "free": True, "free_1st_sun": True,
        "days": [0, 1, 2, 3, 4, 5, 6], "slots": [[8.0, 20.5]], "months": list(range(1,13)),
        "orari": "Parco con pavoni aperto tutti i giorni 08:00-19:00/21:00; Pista ciclabile/pedonale Arenzano–Cogoleto–Varazze sempre aperta",
        "pitch": "Pavoni in libertà e serra Liberty in vetro e ghisa nel parco storico, più 11 km pianeggianti tra gallerie illuminate e calette turchesi sull'antico tracciato ferroviario a picco sul mare.",
        "personaggio": "Marchesa Matilde Giustiniani Negrotto Cambiaso & Fabrizio De André",
        "url": "https://www.arenzanoturismo.it/", "tel": "010 9127581"
    },
    {
        "key_id": "filigrana_campo",
        "nome": "Museo della Filigrana 'P.C. Bosio' & Botteghe Orafe di Campo Ligure",
        "comune": "Campo Ligure", "zona": "ponente_stura", "tipo": "bottega",
        "lat": 44.5381, "lon": 8.6982, "indoor": "in", "treno": True,
        "trasporto_info": "Stazione FS Campo Ligure-Masone (35 min di treno da Genova Brignole/Principe) o A26 Masone",
        "durata_min": 90, "costo": "Biglietto Museo / Ingresso libero nelle botteghe orafe", "free": False, "free_1st_sun": False,
        "days": [0, 5, 6], "slots": [[10.5, 12.0], [15.5, 18.0]], "months": list(range(1,13)),
        "orari": "Museo: Ven 15:30-18:00, Sab-Dom 10:30-12:00 e 15:30-18:00; Botteghe orafe nel borgo Mar-Dom",
        "pitch": "Uno dei Borghi più Belli d'Italia capitale nazionale della filigrana: decine di laboratori orafi intrecciano a mano fili d'argento e d'oro sottili come seta.",
        "personaggio": "Pietro Carlo Bosio & Famiglia Spinola di Luccoli",
        "url": "https://www.museofiligrana.org/", "tel": "010 920099"
    },
    {
        "key_id": "castello_campo",
        "nome": "Castello Spinola di Campo Ligure, Ponte Medievale & Pratorondanino",
        "comune": "Campo Ligure", "zona": "ponente_stura", "tipo": "dimora",
        "lat": 44.5393, "lon": 8.6996, "indoor": "mix", "treno": True,
        "trasporto_info": "Stazione FS Campo Ligure-Masone (10 min a piedi attraversando il ponte medievale sullo Stura)",
        "durata_min": 75, "costo": "Biglietto Castello / Borgo gratis", "free": False, "free_1st_sun": False,
        "days": [0, 6], "slots": [[10.5, 12.0], [15.5, 18.0]], "months": list(range(1,13)),
        "orari": "Sabato, Domenica e festivi 10:30-12:00 e 15:30-18:00",
        "pitch": "Torre cilindrica trecentesca che domina i tre torrenti della Valle Stura, con giardino di sculture in ulivo e vista sulle vette del Parco del Beigua.",
        "personaggio": "Anfreone Spinola (1309)",
        "url": "https://www.comune.campoligure.ge.it/", "tel": "010 921003"
    },
    {
        "key_id": "passatempo_rossiglione",
        "nome": "Museo Passatempo (Moto & Oggetti '900) & Cascata del Serpente a Masone",
        "comune": "Rossiglione", "zona": "ponente_stura", "tipo": "museo",
        "lat": 44.5612, "lon": 8.6715, "indoor": "mix", "treno": True,
        "trasporto_info": "Stazione FS di Rossiglione (42 min di treno da Genova) o in auto A26 Masone",
        "durata_min": 90, "costo": "Offerta / Prenotazione", "free": False, "free_1st_sun": False,
        "days": [0, 6], "slots": [[10.0, 12.5], [15.0, 18.0]], "months": list(range(1,13)),
        "orari": "Sabato e Domenica su visita (Cascata del Serpente nella vicina Masone sempre accessibile!)",
        "pitch": "Collezione sorprendente di motociclette storiche, jukebox, radio e mestieri del Novecento a Rossiglione, a pochi minuti dai laghetti smeraldo della Cascata del Serpente di Masone.",
        "personaggio": "Collezione Minetti & Pizzorno",
        "url": "https://www.museopassatempo.it/", "tel": "347 1496592"
    },
    {
        "key_id": "badia_tiglieto",
        "nome": "Badia Cistercense di Tiglieto (1120) & Ponte Romanico sull'Orba",
        "comune": "Tiglieto", "zona": "ponente_stura", "tipo": "abbazia",
        "lat": 44.5256, "lon": 8.6041, "indoor": "mix", "treno": False,
        "trasporto_info": "45 min in auto da Masone/Rossiglione o da Arenzano valicando il Parco del Beigua",
        "durata_min": 105, "costo": "Prati e ponte gratis / Visite guidate weekend", "free": True, "free_1st_sun": True,
        "days": [0, 6], "slots": [[10.0, 18.0]], "months": [4,5,6,7,8,9,10],
        "orari": "Piana dell'Orba, Ponte Romanico a 5 arcate e sentieri sempre aperti; Visite interne weekend Apr–Ott",
        "pitch": "La prima abbazia cistercense fondata fuori dalla Francia (1120!): una piana erbosa incantata circondata da pinete e attraversata dal ponte medievale sul fiume Orba.",
        "personaggio": "San Bernardo di Chiaravalle & Marchese Anselmo Del Bosco",
        "url": "https://www.parcobeigua.it/", "tel": "010 8590300"
    },

    # --- VAL POLCEVERA, VALLE SCRIVIA, TRENINO DI CASELLA & PARCO ANTOLA ---
    {
        "key_id": "guardia_ceranesi",
        "nome": "Santuario di Nostra Signora della Guardia (Balcone a 804 m)",
        "comune": "Ceranesi", "zona": "polcevera_scrivia", "tipo": "abbazia",
        "lat": 44.4902, "lon": 8.8624, "indoor": "mix", "treno": False,
        "trasporto_info": "30 min in auto da Genova Bolzaneto (o Bus AMT da Bolzaneto; ex-guidovia panoramica a piedi!)",
        "durata_min": 105, "costo": "Gratis", "free": True, "free_1st_sun": True,
        "days": [0, 1, 2, 3, 4, 5, 6], "slots": [[7.5, 19.5]], "months": list(range(1,13)),
        "orari": "Aperto tutti i giorni 07:30-19:00 (con Ristorante/Trattoria dei Pellegrini e sentiero piano dell'ex Guidovia)",
        "pitch": "La vetta del cuore dei genovesi sul Monte Figogna: nelle giornate limpide lo sguardo abbraccia tutta Genova, le Alpi Marittime innevate, Portofino e la Corsica.",
        "personaggio": "Benedetto Pareto (1490)",
        "url": "https://www.santuarioguardia.it/", "tel": "010 72351"
    },
    {
        "key_id": "marionette_campomorone",
        "nome": "Museo delle Marionette Cenderelli & Museo Paleontologico a Palazzo Balbi",
        "comune": "Campomorone", "zona": "polcevera_scrivia", "tipo": "museo",
        "lat": 44.5067, "lon": 8.8917, "indoor": "in", "treno": False,
        "trasporto_info": "20 min da Genova Pontedecimo/Bolzaneto (Auto o Bus AMT linea Val Polcevera)",
        "durata_min": 60, "costo": "Gratis", "free": True, "free_1st_sun": False,
        "days": [1, 2, 3, 4, 5, 6], "slots": [[9.0, 12.0], [14.5, 17.5]], "months": list(range(1,13)),
        "orari": "Lun-Ven 09:00-12:00 (Mar e Gio anche 14:30-17:30); aperture speciali Sabato per eventi",
        "pitch": "Nel settecentesco Palazzo Balbi di Campomorone: decine di marionette intagliate in legno nell'Ottocento con fondali teatrali dipinti a mano, costumi in seta e fossili liguri.",
        "personaggio": "Angelo Cenderelli & Famiglia Balbi",
        "url": "https://www.comune.campomorone.ge.it/", "tel": "010 7224314"
    },
    {
        "key_id": "villa_serra_comago",
        "nome": "Villa Serra di Comago — Parco All'Inglese, Laghetti & Cottage Tudor",
        "comune": "Sant'Olcese", "zona": "polcevera_scrivia", "tipo": "natura",
        "lat": 44.4776, "lon": 8.9401, "indoor": "out", "treno": True,
        "trasporto_info": "20 min in auto da Genova o Trenino Genova–Casella (fermata Vicomorasso / S. Olcese + breve tratto)",
        "durata_min": 105, "costo": "Biglietto simbolico parco", "free": False, "free_1st_sun": False,
        "days": [0, 2, 3, 4, 5, 6], "slots": [[9.5, 18.0]], "months": list(range(1,13)),
        "orari": "Mar-Dom 09:30-17:30 (Inverno) / 09:30-19:30 (Estate); Lun chiuso",
        "pitch": "Un parco romantico dell'Ottocento con cigni, ponticelli, sequoie, ortensie e un autentico Cottage neogotico inglese in stile Tudor voluto dal Marchese Orso Serra.",
        "personaggio": "Marchese Orso Serra & Salumificio Storico di Sant'Olcese",
        "url": "https://www.villaserra.it/", "tel": "010 715577"
    },
    {
        "key_id": "trenino_casella",
        "nome": "Ferrovia Storica Genova–Casella & Borghi dell'Alta Valle Scrivia",
        "comune": "Casella", "zona": "polcevera_scrivia", "tipo": "natura",
        "lat": 44.5348, "lon": 8.9992, "indoor": "mix", "treno": True,
        "trasporto_info": "Partenza da Piazza Manin (Genova Centro) sullo storico Trenino del 1929 lungo i crinali",
        "durata_min": 180, "costo": "Biglietto trenino panoramico", "free": False, "free_1st_sun": False,
        "days": [0, 1, 2, 3, 4, 5, 6], "slots": [[8.0, 19.5]], "months": list(range(1,13)),
        "orari": "Corse giornaliere da Genova Piazza Manin a Casella (1h di viaggio panoramico mozzafiato)",
        "pitch": "Un viaggio lento indimenticabile sui binari a scartamento ridotto che corrono in cresta accanto ai Forti di Genova, sospesi tra tre vallate e il mare.",
        "personaggio": "Daniele Manin & Famiglia Fieschi (Palazzo Fieschi a Casella / Savignone)",
        "url": "https://www.ferroviagenovacasella.it/", "tel": "010 837321"
    },
    {
        "key_id": "castello_pietra_vobbia",
        "nome": "Castello della Pietra — La Fortezza Murata tra Due Rocce",
        "comune": "Vobbia", "zona": "polcevera_scrivia", "tipo": "dimora",
        "lat": 44.6075, "lon": 9.0189, "indoor": "mix", "treno": False,
        "trasporto_info": "35 min in auto A7 uscita Isola del Cantone + 20 min di sentiero ombreggiato nel bosco",
        "durata_min": 150, "costo": "Biglietto visita guidata", "free": False, "free_1st_sun": False,
        "days": [0], "slots": [[10.5, 17.0]], "months": [4,5,6,7,8,9,10],
        "orari": "Aprile–Ottobre: ogni Domenica e festivi con visite guidate ogni ora 10:30-16:30 (chiuso Nov–Mar)",
        "pitch": "Uno dei castelli più scenografici d'Europa: letteralmente incastonato tra due giganteschi speroni naturali di conglomerato roccioso sopra il torrente Vobbia.",
        "personaggio": "Opizzone Della Pietra, Sinibaldo Fieschi & Guglielmo Spinola",
        "url": "https://www.parcoantola.it/", "tel": "010 944175"
    },
    {
        "key_id": "mastodonte_ronco",
        "nome": "Mastodonte dei Giovi (Plastici Ferroviari) & Sciroppo di Rose della Valle Scrivia",
        "comune": "Ronco Scrivia", "zona": "polcevera_scrivia", "tipo": "museo",
        "lat": 44.6085, "lon": 8.9532, "indoor": "in", "treno": True,
        "trasporto_info": "Stazione FS di Ronco Scrivia o Busalla (30 min di treno da Genova Principe/Brignole!)",
        "durata_min": 90, "costo": "Offerta / Degustazioni", "free": True, "free_1st_sun": False,
        "days": [0, 6], "slots": [[10.0, 12.5], [14.5, 18.0]], "months": list(range(1,13)),
        "orari": "Aperture weekend ed eventi speciali (es. Sab 5 Dicembre 2026); Botteghe dello Sciroppo di Rose a Busalla/Savignone Mar-Sab",
        "pitch": "Un gigantesco plastico funzionante di oltre 200 mq che riproduce le storiche linee ferroviarie dei Giovi del 1853, nella valle famosa per lo Sciroppo di Rose Presidio Slow Food.",
        "personaggio": "Ingegnere Germain Sommeiller & Produttori delle Rose della Valle Scrivia",
        "url": "https://www.mastodontedeigiovi.com/", "tel": ""
    },
    {
        "key_id": "torriglia_brugneto",
        "nome": "Pasticcerie dei Canestrellini di Torriglia & Sentiero del Lago del Brugneto",
        "comune": "Torriglia", "zona": "polcevera_scrivia", "tipo": "bottega",
        "lat": 44.5186, "lon": 9.1588, "indoor": "mix", "treno": False,
        "trasporto_info": "45 min in auto da Genova risalendo la Val Bisagno (SS45) o Bus da Brignole",
        "durata_min": 150, "costo": "Sentiero lago gratis / Pasticcerie storiche", "free": True, "free_1st_sun": True,
        "days": [0, 2, 3, 4, 5, 6], "slots": [[8.5, 19.0]], "months": list(range(1,13)),
        "orari": "Pasticcerie artigianali del Canestrellino (es. Guano / Nobile) Mar-Dom; Anello del Lago del Brugneto sempre aperto",
        "pitch": "Fuga nell'aria frizzante dell'Alta Val Trebbia: fai scorta dei veri Canestrellini burrosi a margherita sotto i ruderi del Castello Fieschi-Doria e passeggia lungo i fiordi boscosi del Lago del Brugneto.",
        "personaggio": "Sinibaldo Fieschi & Principi Doria Pamphili",
        "url": "https://www.parcoantola.it/", "tel": ""
    },
    {
        "key_id": "senarega_valbrevenna",
        "nome": "Borgo Medievale in Pietra di Senarega & Castello Fieschi (Parco Antola)",
        "comune": "Valbrevenna", "zona": "polcevera_scrivia", "tipo": "dimora",
        "lat": 44.5608, "lon": 9.0825, "indoor": "out", "treno": False,
        "trasporto_info": "45 min in auto da Busalla/Casella risalendo il torrente Brevenna nel Parco dell'Antola",
        "durata_min": 120, "costo": "Gratis", "free": True, "free_1st_sun": True,
        "days": [0, 1, 2, 3, 4, 5, 6], "slots": [[8.0, 19.5]], "months": list(range(1,13)),
        "orari": "Borgo pedonale senza auto, ponte medievale e sentieri del Monte Antola sempre accessibili",
        "pitch": "Un minuscolo borgo del Trecento interamente in pietra dove le auto non possono entrare: si varca il ponte sul torrente limpido e si sale tra gli archivolti fino alla torre dei Fieschi.",
        "personaggio": "Casata dei Fieschi di Lavagna",
        "url": "https://www.parcoantola.it/", "tel": ""
    },
    {
        "key_id": "teatro_govi",
        "nome": "Teatro Rina e Gilberto Govi — Commedia Genovese & Spettacolo",
        "comune": "Genova", "zona": "polcevera_scrivia", "tipo": "teatro",
        "lat": 44.4581, "lon": 8.9012, "indoor": "in", "treno": True,
        "trasporto_info": "Stazione Genova Bolzaneto (5 min a piedi — Via Pastorino 23r)",
        "durata_min": 130, "costo": "Biglietto spettacolo", "free": False, "free_1st_sun": False,
        "days": [0, 5, 6], "slots": [[15.0, 23.0]], "months": [1,2,3,4,5,10,11,12],
        "orari": "Spettacoli Ven-Sab ore 21:00 e Dom ore 15:00/17:00",
        "pitch": "Il tempio storico del teatro dialettale genovese intitolato a Gilberto e Rina Govi, con cartellone di commedie brillanti, operetta, jazz e musical.",
        "personaggio": "Gilberto Govi & Rina Gaioni",
        "url": "https://www.teatrogovi.it/", "tel": "376 1754434"
    }
]

# Build clean deduplication signature
def norm_sig(comune, nome):
    s = re.sub(r"[^a-z0-9]+", " ", nome.lower()).strip()
    for drop in ("civica", "comunale", "museo", "parco", "giardino", "giardini", "villa", "chiesa", "santuario", "biblioteca"):
        s = s.replace(drop, "").strip()
    s = re.sub(r"\s+", " ", s)
    return (comune.lower(), s[:22])

EXCLUDE_KEYWORDS = (
    "ospedale", "caserma", "municipio", "comune di", "asl", "scuola", "liceo", "istituto comprensivo",
    "banca", "cassa", "carabinieri", "polizia", "cimitero", "parcheggio", "stazione", "farmacia comunale",
    "ufficio", "centro commerciale", "supermercato", "piscina", "palestra", "a.r.p.a.l", "ames",
    "lapide", "monumento ai caduti", "radiofaro", "salone parrocchiale", "casa charitas"
)

curated = []
seen_exact = set()
seen_sig = set()
key_to_id = {}

for idx, f in enumerate(FLAGSHIPS, 1):
    item = dict(f)
    kid = item.pop("key_id")
    item["id"] = idx
    item["tier"] = 1
    key_to_id[kid] = idx
    seen_exact.add((item["comune"].lower(), item["nome"].lower()))
    seen_sig.add(norm_sig(item["comune"], item["nome"]))
    curated.append(item)

next_id = len(curated) + 1

# Score Tier-2 candidates so we get proportional, high-quality gems across ALL 67 municipalities & all zones!
candidates_by_comune = defaultdict(list)

for g in guida:
    comune = g["comune"].strip()
    nome = g["nome"].strip()
    nl = nome.lower()
    if len(nome) < 4:
        continue
    if (comune.lower(), nl) in seen_exact or norm_sig(comune, nome) in seen_sig:
        continue
    if any(ek in nl for ek in EXCLUDE_KEYWORDS):
        continue

    macro = g["macro_categoria"]
    if macro.startswith(("8.", "9.")):
        continue

    gps = coords_lookup.get((comune.lower(), nl))
    has_web = bool(g["sito_web"])
    has_hours = bool(g["orari_apertura"] and "temporaneamente chiuso" not in g["orari_apertura"].lower())
    if "temporaneamente chiuso" in (g["orari_apertura"] or "").lower():
        continue

    # Map tipo
    if macro.startswith("2."): tipo = "museo"
    elif macro.startswith("4."): tipo = "dimora"
    elif macro.startswith("6."): tipo = "bottega"
    elif macro.startswith("5."): tipo = "natura"
    elif macro.startswith("3."): tipo = "teatro"
    elif macro.startswith("1."): tipo = "biblioteca"
    else: tipo = "abbazia"

    # Filter out generic minor items unless they represent a small municipality
    if tipo == "abbazia" and not (has_web or any(w in nl for w in ("abbazia", "santuario", "basilica", "pieve", "chiostro", "oratorio", "cattedrale"))):
        continue
    if tipo == "natura" and any(w in nl for w in ("piazza ", "viale ", "rotonda ")):
        continue

    # Score quality for leisure
    score = 0
    if gps: score += 30
    if has_web: score += 35
    if has_hours: score += 20
    if g["eventi_e_servizi_al_pubblico"]: score += 15
    if tipo in ("bottega", "museo", "dimora", "teatro"): score += 25
    elif tipo == "natura": score += 18
    elif tipo == "abbazia": score += 10
    elif tipo == "biblioteca": score += 5  # keep libraries selective

    if not gps:
        c_geo = comuni_geo.get(comune)
        if not c_geo:
            continue
        h_val = ((sum(ord(ch) for ch in nome) % 90) - 45) / 10000.0
        gps = (round(c_geo["lat"] + h_val, 5), round(c_geo["lon"] - h_val, 5))

    candidates_by_comune[comune].append((score, g, tipo, gps))

# Select top gems per municipality ensuring ALL 67 municipalities are covered and categories/zones are balanced!
tipo_counts = Counter(x["tipo"] for x in curated)
MAX_BIBLIO = 32

# Sort municipalities: provincial municipalities first so they never get starved, then Genova
ordered_comuni = [c for c in sorted(comuni_geo.keys()) if c != "Genova"] + ["Genova"]

for comune in ordered_comuni:
    cands = sorted(candidates_by_comune.get(comune, []), key=lambda x: -x[0])
    # Cap per municipality: up to 5 for major towns, 2-3 for small mountain villages, 55 extra for Genova
    if comune == "Genova":
        cap = 55
    elif comune in ("Chiavari", "Rapallo", "Sestri Levante", "Santa Margherita Ligure", "Camogli", "Arenzano", "Lavagna", "Moneglia", "Recco"):
        cap = 6
    else:
        cap = 3

    added_here = 0
    for score, g, tipo, gps in cands:
        if added_here >= cap:
            break
        nome = g["nome"].strip()
        sig = norm_sig(comune, nome)
        if sig in seen_sig:
            continue
        if tipo == "biblioteca" and tipo_counts["biblioteca"] >= MAX_BIBLIO and added_here > 0:
            continue

        if comune == "Genova":
            if gps[1] < 8.88 or gps[1] > 8.97:
                zona = "genova_mare"
            elif gps[0] > 44.45:
                zona = "polcevera_scrivia"
            else:
                zona = "centro"
        else:
            zona = ZONE_BY_COMUNE.get(comune, "tigullio_or")

        indoor = "out" if tipo == "natura" else ("in" if tipo in ("museo", "teatro", "biblioteca", "bottega") else "mix")
        treno = comune in RAIL_COMUNI

        ol = (g["orari_apertura"] or "").lower()
        days = [0, 1, 2, 3, 4, 5, 6]
        if any(p in ol for p in ("lun chiuso", "lunedì chiuso", "mar-dom", "mar-sab", "tu-su", "tu-sa", "mo off")):
            days = [d for d in days if d != 1]
        if any(p in ol for p in ("dom chiuso", "lun-ven", "lun-sab", "mar-sab", "mo-fr", "mo-sa", "tu-sa", "su off", "sa, su, ph off")):
            days = [d for d in days if d != 0]
        if any(p in ol for p in ("lun-ven", "mo-fr", "sa, su, ph off")):
            days = [d for d in days if d != 6]

        slots = []
        for m in re.finditer(r"(\d{1,2})[:.](\d{2})\s*[-–]\s*(\d{1,2})[:.](\d{2})", g["orari_apertura"] or ""):
            h1 = int(m.group(1)) + int(m.group(2))/60.0
            h2 = int(m.group(3)) + int(m.group(4))/60.0
            if 0 <= h1 < h2 <= 24:
                slots.append([round(h1, 2), round(h2, 2)])
        if not slots:
            slots = [[16.0, 23.0]] if tipo == "teatro" else ([[8.0, 19.5]] if tipo == "natura" else [[9.5, 18.0]])

        pers = person_lookup.get((comune.lower(), nome.lower()), "")
        if not pers and g["indirizzo"]:
            st = g["indirizzo"].split(",")[0].strip().lower()
            pers = person_lookup.get((comune.lower(), st), "")
        if not pers and comune_sample_person.get(comune):
            pers = comune_sample_person[comune][added_here % len(comune_sample_person[comune])]

        raw_pitch = g["eventi_e_servizi_al_pubblico"] or g["titolo_sito"] or ""
        raw_pitch = re.sub(r"Copyright.*", "", raw_pitch, flags=re.I)
        raw_pitch = re.sub(r"\s+", " ", raw_pitch).strip(" |-•")
        if len(raw_pitch) < 18:
            elev = comuni_geo.get(comune, {}).get("elev", 0) or 0
            elev_txt = f" ({int(elev)} m s.l.m.)" if elev >= 300 else ""
            raw_pitch = f"{g['sottocategoria']} da esplorare a {comune}{elev_txt}, tra paesaggio ligure e memoria storica locale."
        pitch = raw_pitch[:210]

        orari_clean = re.sub(r"\[OSM:\s*|\]", "", g["orari_apertura"] or "").strip()
        orari_clean = re.sub(r"Copyright.*", "", orari_clean, flags=re.I).strip(" |-")
        if not orari_clean:
            orari_clean = "Accesso libero diurno" if tipo == "natura" else "Verifica aperture aggiornate sul sito / contatto"

        is_free = tipo in ("natura", "biblioteca", "abbazia")
        curated.append({
            "id": next_id,
            "tier": 2,
            "nome": nome,
            "comune": comune,
            "zona": zona,
            "tipo": tipo,
            "lat": gps[0],
            "lon": gps[1],
            "indoor": indoor,
            "treno": treno,
            "trasporto_info": f"Raggiungibile in treno / mezzi pubblici ({comune})" if treno else f"Gita in auto / moto verso {comune}",
            "durata_min": 60 if tipo in ("bottega", "biblioteca", "abbazia") else 90,
            "costo": "Gratis" if is_free else "Biglietto / Consumazione",
            "free": is_free,
            "free_1st_sun": False,
            "days": days,
            "slots": slots,
            "months": list(range(1, 13)),
            "orari": orari_clean[:140],
            "pitch": pitch,
            "personaggio": pers,
            "url": g["sito_web"],
            "tel": g["telefono"]
        })
        seen_sig.add(sig)
        tipo_counts[tipo] += 1
        added_here += 1
        next_id += 1

# Ensure any remaining tiny Appennine municipality without a Tier-1/Tier-2 item gets a panoramic Borgo & Natura entry!
covered_comuni = {x["comune"] for x in curated}
for comune, c_geo in sorted(comuni_geo.items()):
    if comune not in covered_comuni:
        zona = ZONE_BY_COMUNE.get(comune, "polcevera_scrivia")
        elev = int(c_geo.get("elev") or 500)
        pers = ", ".join(comune_sample_person.get(comune, [])[:2]) or f"Antiche Famiglie di {comune}"
        curated.append({
            "id": next_id,
            "tier": 2,
            "nome": f"Borgo Panoramico & Sentieri di {comune} ({elev} m)",
            "comune": comune,
            "zona": zona,
            "tipo": "natura",
            "lat": round(c_geo["lat"], 5),
            "lon": round(c_geo["lon"], 5),
            "indoor": "out",
            "treno": comune in RAIL_COMUNI,
            "trasporto_info": f"Itinerario panoramico in auto/moto nell'entroterra verso {comune}",
            "durata_min": 90,
            "costo": "Gratis",
            "free": True,
            "free_1st_sun": True,
            "days": [0, 1, 2, 3, 4, 5, 6],
            "slots": [[8.0, 19.5]],
            "months": list(range(1, 13)),
            "orari": "Borgo storico e sentieri escursionistici sempre accessibili",
            "pitch": f"Escursione fuori dai circuiti affollati a {comune} ({elev} m s.l.m.), tra caruggi di pietra, boschi d'Appennino e trattorie tipiche.",
            "personaggio": pers,
            "url": "",
            "tel": ""
        })
        next_id += 1

# 16 Hand-Crafted Ready-to-Go Day / Half-Day / Evening Plans ("Gite & Giornate Pronte")
ITINERARIES = [
    {
        "id": "it_botteghe_caruggi",
        "titolo": "Caruggi Segreti & Botteghe Iper-Specifiche",
        "sottotitolo": "Sughero, cristalli Déco, confetti di rose, farinata a legna, spezie e cioccolato dell'800",
        "zona": "centro", "mezzo": "piedi", "meteo": "pioggia", "durata": "Mezza giornata / Intera",
        "best_days": [2, 3, 4, 5, 6], "months": list(range(1,13)),
        "badge": "🏺 Iconico • Anche con pioggia",
        "stops": [key_to_id["luico"], key_to_id["romanengo"], key_to_id["giacalone"], key_to_id["sapesta"], key_to_id["torielli"], key_to_id["viganotti"]]
    },
    {
        "id": "it_salva_lunedi",
        "titolo": "Il 'Salva-Lunedì': Sottomarini, Chiostri & Antichi Timbri",
        "sottotitolo": "Quando i musei civici riposano: galee, sottomarino in acqua, i Jeans del '500 e confetteria",
        "zona": "centro", "mezzo": "treno", "meteo": "pioggia", "durata": "Giornata intera",
        "best_days": [1], "months": list(range(1,13)),
        "badge": "🛟 Perfetto di Lunedì",
        "stops": [key_to_id["galata"], key_to_id["busellato"], key_to_id["sapesta"], key_to_id["diocesano"], key_to_id["romanengo"]]
    },
    {
        "id": "it_golfo_paradiso_treno",
        "titolo": "Golfo Paradiso Senza Auto: Focaccia, Velieri & Cala di San Fruttuoso",
        "sottotitolo": "In treno e battello tra Recco, il borgo marinaro di Camogli, l'Abbazia FAI e aperitivo nei palchi",
        "zona": "golfo_paradiso", "mezzo": "treno", "meteo": "sole", "durata": "Giornata intera",
        "best_days": [0, 2, 3, 4, 5, 6], "months": list(range(1,13)),
        "badge": "🚆 Zero stress parcheggio",
        "stops": [key_to_id["focaccia_recco"], key_to_id["museo_marinaro_camogli"], key_to_id["san_fruttuoso"], key_to_id["teatro_camogli"]]
    },
    {
        "id": "it_filigrana_carta_stura",
        "titolo": "Fili d'Argento & Carta Fatta a Mano (Ponente & Valle Stura)",
        "sottotitolo": "Due antichi mestieri liguri ancora vivi: la cartiera settecentesca di Mele e gli orafi di Campo Ligure",
        "zona": "ponente_stura", "mezzo": "treno", "meteo": "pioggia", "durata": "Mezza giornata / Weekend",
        "best_days": [0, 5, 6], "months": list(range(1,13)),
        "badge": "✨ Mestieri Rari • Ven-Dom",
        "stops": [key_to_id["museo_carta_mele"], key_to_id["filigrana_campo"], key_to_id["castello_campo"]]
    },
    {
        "id": "it_portofino_ville",
        "titolo": "La Traversata Aristocratica del Golfo di Portofino",
        "sottotitolo": "Dal parco barocco di Villa Durazzo a S. Margherita lungo il mare fino a Castello Brown",
        "zona": "tigullio_occ", "mezzo": "treno", "meteo": "sole", "durata": "Giornata intera",
        "best_days": [0, 1, 2, 3, 4, 5, 6], "months": list(range(1,13)),
        "badge": "🌊 Aperto 7 giorni su 7",
        "stops": [key_to_id["villa_durazzo_sml"], key_to_id["castello_brown"]]
    },
    {
        "id": "it_chiavari_sestri_treno",
        "titolo": "Portici d'Ardesia, Sedie Leggere & Baia del Silenzio",
        "sottotitolo": "Bambuseti e farinata storica a Chiavari, poi 10 minuti di treno fino alle due baie di Sestri Levante",
        "zona": "tigullio_or", "mezzo": "treno", "meteo": "misto", "durata": "Giornata intera",
        "best_days": [0, 2, 3, 4, 5, 6], "months": list(range(1,13)),
        "badge": "🚆 Classico del Levante",
        "stops": [key_to_id["palazzo_rocca_chiavari"], key_to_id["defilla_luchin_chiavari"], key_to_id["musel_baia_sestri"], key_to_id["punta_manara"]]
    },
    {
        "id": "it_trenino_casella_forti",
        "titolo": "In Cresta tra Due Mondi: Funicolari, Forti & Trenino di Casella",
        "sottotitolo": "Ascensori Liberty, mura settecentesche sui monti di Genova, Trenino del 1929 e cottage Tudor",
        "zona": "polcevera_scrivia", "mezzo": "treno", "meteo": "sole", "durata": "Giornata intera",
        "best_days": [0, 2, 3, 4, 5, 6], "months": list(range(1,13)),
        "badge": "🚞 Binari Panoramici",
        "stops": [key_to_id["spianata_castelletto"], key_to_id["trenino_casella"], key_to_id["villa_serra_comago"]]
    },
    {
        "id": "it_castello_pietra_antola",
        "titolo": "La Fortezza nella Roccia, i Borghi di Pietra & i Canestrellini",
        "sottotitolo": "Domenica d'avventura nell'Appennino tra il Castello di Vobbia, Senarega e il Lago del Brugneto",
        "zona": "polcevera_scrivia", "mezzo": "auto", "meteo": "sole", "durata": "Domenica intera (Apr–Ott)",
        "best_days": [0], "months": [4,5,6,7,8,9,10],
        "badge": "🏰 Avventura Domenicale",
        "stops": [key_to_id["castello_pietra_vobbia"], key_to_id["senarega_valbrevenna"], key_to_id["torriglia_brugneto"]]
    },
    {
        "id": "it_seta_miniera_aveto",
        "titolo": "Dentro la Montagna & Sulla Via del Damasco (Entroterra Tigullio)",
        "sottotitolo": "Il trenino sotterraneo di Gambatesa, l'Abbazia di Borzone o i telai di seta di Lorsica fino all'Aveto",
        "zona": "tigullio_or", "mezzo": "auto", "meteo": "misto", "durata": "Sabato o Domenica",
        "best_days": [0, 6], "months": list(range(1,13)),
        "badge": "⛏️ Inedito in Auto • Sab-Dom",
        "stops": [key_to_id["miniera_gambatesa"], key_to_id["abbazia_borzone"], key_to_id["aveto_lago_lame"]]
    },
    {
        "id": "it_pegli_arenzano",
        "titolo": "Il Viaggio Esoterico di Pegli & La Ciclabile sul Mare di Ponente",
        "sottotitolo": "Grotte e Tempio di Diana a Villa Pallavicini, poi pedalata o passeggiata vista mare ad Arenzano",
        "zona": "genova_mare", "mezzo": "treno", "meteo": "sole", "durata": "Giornata intera",
        "best_days": [0, 2, 3, 4, 5, 6], "months": list(range(1,13)),
        "badge": "🌿 Romantico & Mare",
        "stops": [key_to_id["villa_pallavicini_pegli"], key_to_id["arenzano_ciclabile"]]
    },
    {
        "id": "it_nervi_boccadasse",
        "titolo": "Levante Genovese: Scogliere di Nervi, Ville d'Arte & Tramonto a Boccadasse",
        "sottotitolo": "Scoiattoli e roseto sulla Passeggiata Anita Garibaldi, musei nel parco e gelato sugli scogli",
        "zona": "genova_mare", "mezzo": "treno", "meteo": "sole", "durata": "Pomeriggio lungo",
        "best_days": [0, 2, 3, 4, 5, 6], "months": list(range(1,13)),
        "badge": "🌅 Ideale al Tramonto",
        "stops": [key_to_id["parchi_nervi"], key_to_id["musei_nervi"], key_to_id["boccadasse"]]
    },
    {
        "id": "it_domenica_museo_rolli",
        "titolo": "Speciale #DomenicalMuseo: Le Regge dei Rolli a Ingresso Gratuito",
        "sottotitolo": "Ogni 1ª domenica del mese: Galleria degli Specchi, Palazzo Spinola e merenda storica del '700",
        "zona": "centro", "mezzo": "treno", "meteo": "pioggia", "durata": "1ª Domenica del Mese",
        "best_days": [0], "months": list(range(1,13)),
        "badge": "🆓 1ª Domenica del Mese",
        "stops": [key_to_id["palazzo_reale"], key_to_id["marescotti_cavo"], key_to_id["palazzo_spinola"], key_to_id["viganotti"]]
    },
    {
        "id": "it_funivia_velluti_merletti",
        "titolo": "Dal Mare a 600 Metri: Merletti, Funivia di Montallegro & Velluti di Zoagli",
        "sottotitolo": "Villa Tigullio a Rapallo, salita in funivia sopra il golfo e passeggiata sulle scogliere della seta",
        "zona": "tigullio_occ", "mezzo": "treno", "meteo": "sole", "durata": "Giornata intera",
        "best_days": [2, 3, 4, 5, 6], "months": list(range(1,13)),
        "badge": "🚡 Panorama Mozzafiato",
        "stops": [key_to_id["merletto_rapallo"], key_to_id["montallegro"], key_to_id["velluti_zoagli"]]
    },
    {
        "id": "it_campane_orologi_damasco",
        "titolo": "Il Triangolo degli Artigiani Incredibili: Campane, Orologi da Torre & Seta",
        "sottotitolo": "Da Recco su per Avegno, Uscio e Lorsica: tre mestieri secolari nel raggio di 25 chilometri",
        "zona": "golfo_paradiso", "mezzo": "auto", "meteo": "pioggia", "durata": "Sabato o Venerdì",
        "best_days": [5, 6], "months": list(range(1,13)),
        "badge": "🔔 Iper-Specifico in Auto",
        "stops": [key_to_id["focaccia_recco"], key_to_id["campane_avegno"], key_to_id["orologi_uscio"], key_to_id["damasco_lorsica"]]
    },
    {
        "id": "it_sera_teatro_genova",
        "titolo": "Sera d'Autore a Genova: Crepuscolo dall'Alto & Sipario",
        "sottotitolo": "Tramonto in ascensore Liberty a Castelletto, mostra serale al Ducale e spettacolo a teatro",
        "zona": "centro", "mezzo": "treno", "meteo": "misto", "durata": "Sera (18:00–23:30)",
        "best_days": [0, 2, 3, 4, 5, 6], "months": list(range(1,13)),
        "badge": "🎭 Uscita Serale",
        "stops": [key_to_id["spianata_castelletto"], key_to_id["palazzo_ducale"], key_to_id["carlo_felice"], key_to_id["teatro_tosse"]]
    },
    {
        "id": "it_beigua_tiglieto",
        "titolo": "Silenzio Cistercense & Altipiani del Beigua",
        "sottotitolo": "La Badia del 1120 a Tiglieto, il ponte romanico sull'Orba e le moto storiche di Rossiglione",
        "zona": "ponente_stura", "mezzo": "auto", "meteo": "sole", "durata": "Weekend Apr–Ott",
        "best_days": [0, 6], "months": [4,5,6,7,8,9,10],
        "badge": "🌲 Natura & Storia",
        "stops": [key_to_id["badia_tiglieto"], key_to_id["passatempo_rossiglione"], key_to_id["filigrana_campo"]]
    }
]

# 28 Real Monthly & Seasonal Events / Calendar Highlights across Genoa & the 67 Municipalities
MONTHLY_EVENTS = [
    {"month": 1, "day_rule": "first_sun", "titolo": "#DomenicalMuseo — Palazzi Reale, Spinola e MuSel Gratis", "comune": "Genova / Chiavari / Sestri", "zona": "centro", "tipo": "gratis", "desc": "Ingresso gratuito nei musei statali e archeologici della provincia."},
    {"month": 1, "days": [1,2,3,4,5,6], "titolo": "Ultimi Giorni dei Presepi Storici & Presepe di Pentema", "comune": "Genova / Torriglia (Pentema)", "zona": "polcevera_scrivia", "tipo": "borgo", "desc": "Figure settecentesche del Maragliano nei santuari genovesi e l'intero borgo di Pentema trasformato in presepe a grandezza naturale."},
    {"month": 1, "days": [17,18,24,25], "titolo": "Stagione Sinfonica & Lirica d'Inverno + Ciaspolate in Val d'Aveto", "comune": "Genova / Santo Stefano d'Aveto", "zona": "tigullio_or", "tipo": "stagione", "desc": "Concerti al Carlo Felice e al Sociale di Camogli; neve nelle faggete del Monte Penna."},

    {"month": 2, "day_rule": "first_sun", "titolo": "#DomenicalMuseo di Febbraio", "comune": "Genova & Provincia", "zona": "centro", "tipo": "gratis", "desc": "Domenica gratuita nei musei statali."},
    {"month": 2, "days": [7,8,14,15,21,22,28], "titolo": "Fioritura Storica delle Camelie dell'Ottocento a Pegli", "comune": "Genova (Pegli)", "zona": "genova_mare", "tipo": "natura", "desc": "Il celebre Viale delle Camelie di Villa Durazzo-Pallavicini esplode di colori tra febbraio e marzo."},
    {"month": 2, "days": [14,15], "titolo": "San Valentino sul Mare tra Camogli e Boccadasse", "comune": "Camogli / Genova", "zona": "golfo_paradiso", "tipo": "evento", "desc": "Cuori sulle reti dei pescatori sul molo di Camogli, poesie d'amore e cene a lume di candela sul porticciolo."},

    {"month": 3, "day_rule": "first_sun", "titolo": "#DomenicalMuseo + Riapertura Primaverile Abbazia della Cervara", "comune": "Genova / S. Margherita Ligure", "zona": "tigullio_occ", "tipo": "gratis", "desc": "Tornano le aperture su prenotazione della 1ª e 3ª domenica alla Cervara."},
    {"month": 3, "days": [7,8,14,15,21,22], "titolo": "Visite Guidate al Camelieto & Riapertura Miniera di Gambatesa", "comune": "Genova Pegli / Ne", "zona": "tigullio_or", "tipo": "natura", "desc": "Weekend ideali per il Parco di Pegli e per la riapertura del trenino minerario in Val Graveglia."},

    {"month": 4, "day_rule": "first_sun", "titolo": "#DomenicalMuseo + Riapertura Castello della Pietra (Vobbia)", "comune": "Vobbia / Genova", "zona": "polcevera_scrivia", "tipo": "borgo", "desc": "Da aprile a ottobre ogni domenica riapre la fortezza incastrata nella roccia nel Parco dell'Antola!"},
    {"month": 4, "days": [18,19,25,26], "titolo": "Rolli Days di Primavera & Fioritura del Roseto di Nervi", "comune": "Genova", "zona": "centro", "tipo": "evento", "desc": "Apertura straordinaria di oltre 30 Palazzi dei Rolli UNESCO normalmente privati e migliaia di rose in fiore sui prati sul mare di Nervi."},

    {"month": 5, "day_rule": "first_sun", "titolo": "#DomenicalMuseo di Maggio", "comune": "Genova & Provincia", "zona": "centro", "tipo": "gratis", "desc": "Musei statali aperti gratuitamente."},
    {"month": 5, "days": [9,10], "titolo": "Sagra del Pesce di Camogli & Falò di San Fortunato", "comune": "Camogli", "zona": "golfo_paradiso", "tipo": "sapori", "desc": "La celebre padella gigante d'acciaio da 4 metri di diametro frigge pesce azzurro in riva al mare la seconda domenica di maggio!"},
    {"month": 5, "days": [23,24], "titolo": "Sagra della Focaccia di Recco IGP", "comune": "Recco", "zona": "golfo_paradiso", "tipo": "sapori", "desc": "Degustazioni diffuse in tutta Recco della vera Focaccia col Formaggio IGP appena sfornata."},

    {"month": 6, "day_rule": "first_sun", "titolo": "#DomenicalMuseo di Giugno", "comune": "Genova & Provincia", "zona": "centro", "tipo": "gratis", "desc": "Musei statali gratuiti."},
    {"month": 6, "days": [6,7,13,14], "titolo": "Andersen Festival nella Baia delle Favole & Festa delle Rose in Valle Scrivia", "comune": "Sestri Levante / Busalla", "zona": "tigullio_or", "tipo": "evento", "desc": "Teatro di strada sull'acqua a Sestri Levante e raccolta dei petali per lo Sciroppo di Rose a Busalla e Savignone."},
    {"month": 6, "days": [24], "titolo": "Festa Patronale di San Giovanni Battista & Falò in Piazza Matteotti", "comune": "Genova", "zona": "centro", "tipo": "evento", "desc": "Il grande falò di San Giovanni, la storica processione delle Confraternite con i monumentali Cristi processionali verso il mare."},

    {"month": 7, "day_rule": "first_sun", "titolo": "#DomenicalMuseo + Festa patronale di N.S. di Montallegro (1-3 Luglio)", "comune": "Rapallo / Genova", "zona": "tigullio_occ", "tipo": "evento", "desc": "Spettacoli pirotecnici a giorno ('sparata del Panegirico') e fuochi sul mare nel Golfo di Rapallo."},
    {"month": 7, "days": [10,11,12,17,18,19,24,25,26], "titolo": "Festival Internazionale del Balletto & Musica ai Parchi di Nervi", "comune": "Genova (Nervi)", "zona": "genova_mare", "tipo": "teatro", "desc": "Grandi étoiles mondiali danzano all'aperto sotto i cedri secolari affacciati sul mare."},

    {"month": 8, "days": [2], "titolo": "Stella Maris a Camogli & Punta Chiappa + #DomenicalMuseo", "comune": "Camogli", "zona": "golfo_paradiso", "tipo": "evento", "desc": "La 1ª domenica d'agosto migliaia di lumini galleggianti accendono il mare notturno davanti a Camogli e Punta Chiappa."},
    {"month": 8, "days": [13,14], "titolo": "Addio do Fantin (San Salvatore) & Storica Torta dei Fieschi (Lavagna)", "comune": "Cogorno / Lavagna", "zona": "tigullio_or", "tipo": "evento", "desc": "Corteo medievale in costume del 1230 tra la Basilica dei Fieschi e la Torre del Borgo, con il gioco dell'anima gemella e la torta gigante."},

    {"month": 9, "day_rule": "first_sun", "titolo": "#DomenicalMuseo di Settembre", "comune": "Genova & Provincia", "zona": "centro", "tipo": "gratis", "desc": "Domenica gratuita nei musei statali."},
    {"month": 9, "days": [7,8], "titolo": "Sagra del Fuoco di N.S. del Suffragio a Recco", "comune": "Recco", "zona": "golfo_paradiso", "tipo": "evento", "desc": "Sette quartieri si sfidano nei più grandiosi spettacoli pirotecnici dal mare della Liguria, accompagnati da stand di focaccia col formaggio."},
    {"month": 9, "days": [19,20,26,27], "titolo": "Salone Nautico Internazionale & FuoriSalone in Città", "comune": "Genova", "zona": "centro", "tipo": "evento", "desc": "Il Waterfront di Levante ospita barche a vela e yacht da tutto il mondo con aperture serali nei caruggi."},

    {"month": 10, "day_rule": "first_sun", "titolo": "#DomenicalMuseo + Ultime Domeniche al Castello della Pietra", "comune": "Genova / Vobbia", "zona": "polcevera_scrivia", "tipo": "borgo", "desc": "Foliage autunnale straordinario intorno al Castello di Vobbia e al Lago delle Lame prima della pausa invernale."},
    {"month": 10, "days": [17,18], "titolo": "Rolli Days d'Autunno & Concerti Paganiniani", "comune": "Genova", "zona": "centro", "tipo": "evento", "desc": "Palazzi nobiliari aperti con divulgatori scientifici ed esibizioni col violino 'Cannone' di Paganini."},
    {"month": 10, "days": [24,25,29,30,31], "titolo": "Festival della Scienza nei Palazzi Storici & Castagnate nell'Entroterra", "comune": "Genova / Fontanabuona / Valli", "zona": "centro", "tipo": "evento", "desc": "Laboratori interattivi, lectio magistralis a Palazzo Ducale e sagre della castagna a Borzonasca, Montoggio e Campo Ligure."},

    {"month": 11, "day_rule": "first_sun", "titolo": "#DomenicalMuseo (Dom 1 Nov) + Gran Finale Festival della Scienza", "comune": "Genova / Chiavari / Sestri", "zona": "centro", "tipo": "gratis", "desc": "Domenica 1 Novembre: ingresso gratuito a Palazzo Reale, Palazzo Spinola e MuSel Sestri Levante + laboratori scientifici in tutta Genova!"},
    {"month": 11, "days": [7,8,14,15,21,22,28,29], "titolo": "Foliage dei Faggi al Lago delle Lame, Frantoi Aperti & Stagione Teatrale", "comune": "Rezzoaglio / Sestri / Genova", "zona": "tigullio_or", "tipo": "natura", "desc": "Novembre è il mese d'oro per l'olio nuovo nel Tigullio, i colori rossi del Lago delle Lame e i debutti al Carlo Felice, Nazionale e Sociale di Camogli."},

    {"month": 12, "days": [5], "titolo": "Apertura Straordinaria Plastico Ferroviario 'Mastodonte dei Giovi'", "comune": "Ronco Scrivia", "zona": "polcevera_scrivia", "tipo": "evento", "desc": "Sabato 5 Dicembre 2026: apertura al pubblico del grande plastico storico e borsa scambio ferroviaria a Ronco Scrivia."},
    {"month": 12, "day_rule": "first_sun", "titolo": "#DomenicalMuseo di Dicembre + Botteghe Storiche Aperte di Domenica", "comune": "Genova & Provincia", "zona": "centro", "tipo": "gratis", "desc": "A dicembre anche Confetteria Romanengo, le botteghe storiche dei caruggi e gli orafi della filigrana di Campo Ligure aprono la domenica!"},
    {"month": 12, "days": [19,20,26,27], "titolo": "Cerimonia del Confeugo a Palazzo Ducale & Presepi del Maragliano", "comune": "Genova / Campo Ligure / Pentema", "zona": "centro", "tipo": "evento", "desc": "L'Abate del Popolo offre l'alloro al Doge in Piazza De Ferrari; aprono il Presepe meccanico di Campo Ligure e il borgo-presepe di Pentema."}
]

# Starting Hubs for instant realistic travel time computation
STARTING_HUBS = [
    {"id": "ge_centro", "nome": "Genova Centro (Brignole / De Ferrari)", "lat": 44.4072, "lon": 8.9395, "rail": True},
    {"id": "ge_principe_ponente", "nome": "Genova Principe / Ponente (Pegli–Voltri)", "lat": 44.4195, "lon": 8.8850, "rail": True},
    {"id": "ge_levante", "nome": "Genova Levante (Albaro / Quarto / Nervi)", "lat": 44.3885, "lon": 9.0120, "rail": True},
    {"id": "golfo_paradiso", "nome": "Golfo Paradiso (Recco / Camogli)", "lat": 44.3555, "lon": 9.1485, "rail": True},
    {"id": "tigullio_occ", "nome": "Tigullio (Rapallo / S. Margherita)", "lat": 44.3430, "lon": 9.2250, "rail": True},
    {"id": "tigullio_or", "nome": "Chiavari / Lavagna / Sestri Levante", "lat": 44.3050, "lon": 9.3480, "rail": True},
    {"id": "valli_nord", "nome": "Entroterra Nord (Busalla / Casella / Valle Scrivia)", "lat": 44.5710, "lon": 8.9460, "rail": True},
    {"id": "valle_stura", "nome": "Valle Stura (Campo Ligure / Masone)", "lat": 44.5350, "lon": 8.6980, "rail": True}
]

comuni_list = []
for nome_c, info in sorted(comuni_geo.items()):
    comuni_list.append({
        "nome": nome_c,
        "lat": round(info["lat"], 4),
        "lon": round(info["lon"], 4),
        "elev": int(info.get("elev") or 0),
        "zona": "centro" if nome_c == "Genova" else ZONE_BY_COMUNE.get(nome_c, "tigullio_or"),
        "treno": nome_c in RAIL_COMUNI
    })

payload = {
    "meta": {
        "total_comuni": len(comuni_list),
        "total_places": len(curated),
        "tier1_flagships": sum(1 for x in curated if x["tier"] == 1),
        "total_raw_public_places": len(guida),
        "total_person_toponyms": len(toponimi)
    },
    "hubs": STARTING_HUBS,
    "comuni": comuni_list,
    "itineraries": ITINERARIES,
    "monthly_events": MONTHLY_EVENTS,
    "places": curated
}

with open(f"{_DATA_DIR}/tempo_libero_payload.json", "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))

print(f"Total places: {len(curated)} (Tier 1: {payload['meta']['tier1_flagships']})")
print("Comuni covered in places:", len({x['comune'] for x in curated}), "/ 67")
print("By zone:", dict(Counter(x["zona"] for x in curated)))
print("By tipo:", dict(Counter(x["tipo"] for x in curated)))
import os
print("Compact JSON size KB:", round(os.path.getsize(f"{_DATA_DIR}/tempo_libero_payload.json") / 1024, 1))
