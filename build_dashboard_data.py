import json
import re

with open("/Users/dany/genova/guida_aperti_al_pubblico_provincia_genova.json") as f:
    records = json.load(f)

with open("/Users/dany/genova/toponimi_personaggi_provincia_genova.json") as f:
    toponimi = json.load(f)

# Build lookup for historical character linked to the place or its street
person_by_place = {}
for t in toponimi:
    person_by_place[(t["comune"].lower(), t["toponimo"].lower())] = (t["personaggio_o_casata"], t["descrizione_categoria"])

# Also add Botteghe Storiche of Genova with exact opening schedules so the user has the hyper-specific shops right inside the planner!
BOTTEGHE_STORICHE = [
    {
        "comune": "Genova",
        "nome": "Antica Farmacia Sant'Anna dei Frati Carmelitani",
        "macro_categoria": "6. Botteghe Storiche, Librerie & Ristorazione Tipica",
        "sottocategoria": "Bottega Storica (1650) - Spezieria Conventuale",
        "indirizzo": "Piazza Sant'Anna, 8r (Castelletto)",
        "telefono": "010 2513285",
        "email": "info@erboristeriadeifrati.it",
        "sito_web": "https://www.erboristeriadeifrati.it",
        "orari_apertura": "Lun-Ven 08:30-12:30 e 15:30-19:00; Sab 08:30-12:30; Dom chiuso",
        "eventi_e_servizi_al_pubblico": "Visite guidate all'antica spezieria del 1650 e al roseto dei Frati; rimedi galenici, Elisir di China, Acqua di Melissa e cosmetici conventuali",
        "days_open": [1, 2, 3, 4, 5, 6],
        "hours_range": [[8.5, 12.5], [15.5, 19.0]],
        "personaggio": "Sant'Anna & Padre Martino da Genova (1650)"
    },
    {
        "comune": "Genova",
        "nome": "G.M. Luico — Il Re del Sughero (Turaccioli)",
        "macro_categoria": "6. Botteghe Storiche, Librerie & Ristorazione Tipica",
        "sottocategoria": "Bottega Storica (1855) - Artigianato del Sughero",
        "indirizzo": "Salita Santa Caterina, 17r",
        "telefono": "010 589493",
        "email": "",
        "sito_web": "https://www.botteghestorichegenova.it",
        "orari_apertura": "Mar-Sab 09:00-12:30 e 15:30-19:00; Lun e Dom chiuso",
        "eventi_e_servizi_al_pubblico": "Laboratorio iper-specifico dedicato esclusivamente a tappi su misura, cortecce di sughero sardo, galleggianti da pesca e presepi",
        "days_open": [2, 3, 4, 5, 6],
        "hours_range": [[9.0, 12.5], [15.5, 19.0]],
        "personaggio": "Caterina Fieschi Adorno (Santa Caterina da Genova)"
    },
    {
        "comune": "Genova",
        "nome": "Confetteria Pietro Romanengo fu Stefano",
        "macro_categoria": "6. Botteghe Storiche, Librerie & Ristorazione Tipica",
        "sottocategoria": "Bottega Storica (1780) - Confetteria e Drogheria Coloniale",
        "indirizzo": "Via di Soziglia, 74r / Via Roma, 51r",
        "telefono": "010 2474574",
        "email": "info@romanengo.com",
        "sito_web": "https://www.romanengo.com",
        "orari_apertura": "Lun 15:30-19:30; Mar-Sab 09:00-13:00 e 15:00-19:30; Dom chiuso (aperto a dicembre)",
        "eventi_e_servizi_al_pubblico": "Degustazioni stagionali: sciroppo di rose a maggio, violette candite, quaresimali in primavera, confetti e marron glacé in autunno/inverno",
        "days_open": [1, 2, 3, 4, 5, 6],
        "hours_range": [[9.0, 13.0], [15.0, 19.5]],
        "personaggio": "Corporazione degli Speziali di Soziglia (1780)"
    },
    {
        "comune": "Genova",
        "nome": "Camiceria & Cravatteria E. Finollo",
        "macro_categoria": "6. Botteghe Storiche, Librerie & Ristorazione Tipica",
        "sottocategoria": "Bottega Storica (1899) - Sartoria Liberty e Cravatte a 7 pieghe",
        "indirizzo": "Via Roma, 38r",
        "telefono": "010 562073",
        "email": "info@finollo.it",
        "sito_web": "https://www.finollo.it",
        "orari_apertura": "Mar-Sab 09:30-13:00 e 15:30-19:30; Lun e Dom chiuso",
        "eventi_e_servizi_al_pubblico": "Sartoria su misura in arredi Liberty del 1899; realizzazione cravatte a sette pieghe con bandiere del codice nautico ricamate a mano",
        "days_open": [2, 3, 4, 5, 6],
        "hours_range": [[9.5, 13.0], [15.5, 19.5]],
        "personaggio": "Giuseppe Mazzini & Eugenio Finollo"
    },
    {
        "comune": "Genova",
        "nome": "Tripperia La Casana",
        "macro_categoria": "6. Botteghe Storiche, Librerie & Ristorazione Tipica",
        "sottocategoria": "Bottega Storica (1890) - Antica Tripperia",
        "indirizzo": "Vico Casana, 3r",
        "telefono": "010 2474634",
        "email": "",
        "sito_web": "https://www.botteghestorichegenova.it",
        "orari_apertura": "Mar-Sab 08:30-13:30 e 16:00-19:30; Lun e Dom chiuso",
        "eventi_e_servizi_al_pubblico": "Calderoni di rame storici sul 'ronfò' in maiolica bianca; vendita e assaggio di trippa bollita e 'sbira' tradizionale",
        "days_open": [2, 3, 4, 5, 6],
        "hours_range": [[8.5, 13.5], [16.0, 19.5]],
        "personaggio": "Casata dei Banchieri Casana"
    },
    {
        "comune": "Genova",
        "nome": "Antica Barberia Giacalone (Bene FAI)",
        "macro_categoria": "6. Botteghe Storiche, Librerie & Ristorazione Tipica",
        "sottocategoria": "Bottega Storica (1882 / 1922) - Barberia Art Déco",
        "indirizzo": "Vico dei Caprettari, 14r",
        "telefono": "010 2770603",
        "email": "faigiacalone@fondoambiente.it",
        "sito_web": "https://fondoambiente.it/luoghi/barberia-giacalone",
        "orari_apertura": "Mar-Sab 08:30-19:00; Lun e Dom chiuso",
        "eventi_e_servizi_al_pubblico": "Rasatura tradizionale a panno caldo e visite culturali FAI nella cattedrale Art Déco di 10 mq in vetro opalino blu e verde",
        "days_open": [2, 3, 4, 5, 6],
        "hours_range": [[8.5, 19.0]],
        "personaggio": "Italo Giacalone & Corporazione dei Caprettari"
    },
    {
        "comune": "Genova",
        "nome": "Busellato Incisioni, Timbri e Targhe",
        "macro_categoria": "6. Botteghe Storiche, Librerie & Ristorazione Tipica",
        "sottocategoria": "Bottega Storica (1896) - Incisioni, Punzoni e Ceralacca",
        "indirizzo": "Via al Ponte Reale, 3r",
        "telefono": "010 2470939",
        "email": "info@busellato.it",
        "sito_web": "https://www.busellato.it",
        "orari_apertura": "Lun-Ven 09:00-12:30 e 14:30-18:30; Sab e Dom chiuso",
        "eventi_e_servizi_al_pubblico": "Cassettiere storiche in rovere del 1896 con punzoni navali, sigilli per ceralacca, targhe in ottone incise a bulino",
        "days_open": [1, 2, 3, 4, 5],
        "hours_range": [[9.0, 12.5], [14.5, 18.5]],
        "personaggio": "Ammiragli Doria & Capitani del Ponte Reale"
    },
    {
        "comune": "Genova",
        "nome": "Fabbrica di Cioccolato Romeo Viganotti",
        "macro_categoria": "6. Botteghe Storiche, Librerie & Ristorazione Tipica",
        "sottocategoria": "Bottega Storica (1866) - Cioccolateria Artigianale con Macchinari Ottocenteschi",
        "indirizzo": "Vico dei Castagna, 14r (Piazza delle Erbe)",
        "telefono": "010 2514061",
        "email": "info@romeoviganotti.com",
        "sito_web": "https://www.romeoviganotti.com",
        "orari_apertura": "Mar-Sab 09:30-19:30; Dom 10:00-13:00 e 15:30-19:30; Lun chiuso",
        "eventi_e_servizi_al_pubblico": "Produzione praline, boeri e gianduiotti con macchinari originali di fine '800 in funzione visibili dal laboratorio",
        "days_open": [0, 2, 3, 4, 5, 6],
        "hours_range": [[9.5, 19.5]],
        "personaggio": "Romeo Viganotti & Famiglia Castagna"
    },
    {
        "comune": "Genova",
        "nome": "Giovanni Rivara fu Luigi — Mezzari e Tele",
        "macro_categoria": "6. Botteghe Storiche, Librerie & Ristorazione Tipica",
        "sottocategoria": "Bottega Storica (1802) - Mezzari Liguri e Tessuti",
        "indirizzo": "Piazza San Lorenzo, 36r",
        "telefono": "010 2471115",
        "email": "",
        "sito_web": "https://www.botteghestorichegenova.it",
        "orari_apertura": "Mar-Sab 09:30-12:30 e 15:30-19:00; Lun mattina e Dom chiuso",
        "eventi_e_servizi_al_pubblico": "Esposizione e vendita dei tradizionali 'Mezzari' dell'Albero della Vita e della tela storica Blue Jeans di fronte alla Cattedrale",
        "days_open": [2, 3, 4, 5, 6],
        "hours_range": [[9.5, 12.5], [15.5, 19.0]],
        "personaggio": "San Lorenzo & Guglielmo Embriaco"
    },
    {
        "comune": "Genova",
        "nome": "Antica Friggitoria Sa' Pesta",
        "macro_categoria": "6. Botteghe Storiche, Librerie & Ristorazione Tipica",
        "sottocategoria": "Bottega Storica (1883) - Forno a Legna e Farinata nei Testi di Rame",
        "indirizzo": "Via dei Giustiniani, 16r",
        "telefono": "010 2468336",
        "email": "",
        "sito_web": "https://www.sapesta.it",
        "orari_apertura": "Lun-Sab 12:00-15:00; Dom chiuso",
        "eventi_e_servizi_al_pubblico": "Cottura continua nel forno a legna storico di farinata di ceci nei testi di rame, torta pasqualina, torta di riso e frisceu",
        "days_open": [1, 2, 3, 4, 5, 6],
        "hours_range": [[12.0, 15.0]],
        "personaggio": "La Maona dei Giustiniani (Signori di Chio)"
    },
    {
        "comune": "Genova",
        "nome": "Drogheria Torielli",
        "macro_categoria": "6. Botteghe Storiche, Librerie & Ristorazione Tipica",
        "sottocategoria": "Bottega Storica (1930) - 400 Cassetti di Spezie, Tè e Resine",
        "indirizzo": "Via di San Bernardo, 32r",
        "telefono": "010 2468359",
        "email": "",
        "sito_web": "https://www.botteghestorichegenova.it",
        "orari_apertura": "Mar-Sab 09:00-13:00 e 15:30-19:30; Lun e Dom chiuso",
        "eventi_e_servizi_al_pubblico": "Spezieria coloniale con 400 cassetti in legno di spezie sfuse da tutto il mondo, incensi, gomme arabiche, cere e tè pregiati",
        "days_open": [2, 3, 4, 5, 6],
        "hours_range": [[9.0, 13.0], [15.5, 19.5]],
        "personaggio": "San Bernardo di Chiaravalle"
    },
    {
        "comune": "Genova",
        "nome": "Pasticceria Marescotti di Cavo",
        "macro_categoria": "6. Botteghe Storiche, Librerie & Ristorazione Tipica",
        "sottocategoria": "Bottega Storica (1780) - Quaresimali Genovesi e Amaretti",
        "indirizzo": "Via di Fossatello, 35-37r",
        "telefono": "010 2091164",
        "email": "info@cavo.it",
        "sito_web": "https://www.pasticceriacavo.it",
        "orari_apertura": "Mar-Dom 08:30-19:30; Lun chiuso",
        "eventi_e_servizi_al_pubblico": "Saloni dorati settecenteschi, museo del dolce genovese (stampi antichi del Pandolce, Quaresimali di marzapane e Amaretti di Voltaggio)",
        "days_open": [0, 2, 3, 4, 5, 6],
        "hours_range": [[8.5, 19.5]],
        "personaggio": "Doge Simone Boccanegra & Famiglia Cavo"
    }
]

def parse_schedule(orari_str, macro):
    """
    Returns (days_open_list, hours_ranges_list, open_sunday, open_evening, free_first_sunday)
    Days: 0=Dom, 1=Lun, 2=Mar, 3=Mer, 4=Gio, 5=Ven, 6=Sab
    """
    ol = orari_str.lower()
    if "temporaneamente chiuso" in ol or "non è un museo a libero accesso" in ol:
        return [], [], False, False, False

    days = {0, 1, 2, 3, 4, 5, 6}
    if "lun chiuso" in ol or "lunedì chiuso" in ol or "lunedì: chiuso" in ol or "da martedì" in ol or "mar-dom" in ol or "mar-sab" in ol:
        days.discard(1)
    if "dom chiuso" in ol or "domenica chiuso" in ol or "sab-dom chiuso" in ol or "lun-ven" in ol or "lun-sab" in ol or "mar-sab" in ol:
        days.discard(0)
    if "sab-dom chiuso" in ol or "lun-ven" in ol:
        days.discard(6)
    if "mar chiuso" in ol or "martedì chiuso" in ol:
        days.discard(2)
    if "ven, sab, dom" in ol or "venerdì, sabato, domenica" in ol:
        days = {5, 6, 0}
    if "domenica e nei giorni festivi" in ol or "apr–ott (dom" in ol:
        days = {0}
    if "lun-mer" in ol:
        days = {1, 2, 3}

    # Extract hour numbers
    ranges = []
    for m in re.finditer(r"(\d{1,2})[:.](\d{2})\s*[-–]\s*(\d{1,2})[:.](\d{2})", orari_str):
        h1 = int(m.group(1)) + int(m.group(2))/60.0
        h2 = int(m.group(3)) + int(m.group(4))/60.0
        ranges.append([round(h1, 2), round(h2, 2)])

    if not ranges:
        if macro.startswith("5.") or macro.startswith("7."):
            ranges = [[8.0, 19.0]]
        elif macro.startswith("3."):
            ranges = [[15.0, 23.0]]
        else:
            ranges = [[9.0, 18.0]]

    open_sun = 0 in days
    open_eve = any(r[1] >= 19.5 for r in ranges) or macro.startswith("3.")
    free_first_sun = ("1ª domenica" in ol) or ("prima domenica" in ol) or ("musei di strada nuova" in ol) or ("palazzo reale" in ol) or ("palazzo spinola" in ol)
    if free_first_sun:
        open_sun = True

    return sorted(list(days)), ranges, open_sun, open_eve, free_first_sun

# Select the top ~360 richest items across all 9 categories and 67 municipalities (those with websites, explicit hours, or events) so the interactive HTML dashboard is lightning fast and super informative
curated_items = []
seen_names = set()

for b in BOTTEGHE_STORICHE:
    seen_names.add((b["comune"].lower(), b["nome"].lower()))
    b["open_sunday"] = 0 in b["days_open"]
    b["open_evening"] = any(r[1] >= 19.5 for r in b["hours_range"])
    b["free_first_sunday"] = False
    b["seasonal_months"] = [1,2,3,4,5,6,7,8,9,10,11,12]
    curated_items.append(b)

for r in records:
    key = (r["comune"].lower(), r["nome"].lower())
    if key in seen_names:
        continue
    # Prioritize records that have website OR explicit hours OR events OR are libraries/museums/theatres/castles/parks
    has_rich = bool(r["sito_web"] or r["eventi_e_servizi_al_pubblico"] or ("[" not in r["orari_apertura"] and r["orari_apertura"]))
    is_core_cat = r["macro_categoria"][0] in ("1", "2", "3")
    if not (has_rich or is_core_cat):
        continue

    days, ranges, open_sun, open_eve, free_1st = parse_schedule(r["orari_apertura"], r["macro_categoria"])
    
    # Determine seasonal months (e.g. Castello della Pietra Apr-Oct)
    months = [1,2,3,4,5,6,7,8,9,10,11,12]
    if "da aprile a fine ottobre" in r["orari_apertura"].lower() or "apr-ott" in r["orari_apertura"].lower():
        months = [4,5,6,7,8,9,10]

    # Match historical character from our toponimi dataset
    pers = ""
    if key in person_by_place:
        pers = person_by_place[key][0]
    elif r["indirizzo"]:
        st_clean = r["indirizzo"].split(",")[0].strip().lower()
        if (r["comune"].lower(), st_clean) in person_by_place:
            pers = f"{person_by_place[(r['comune'].lower(), st_clean)][0]} ({r['indirizzo'].split(',')[0]})"

    curated_items.append({
        "comune": r["comune"],
        "nome": r["nome"],
        "macro_categoria": r["macro_categoria"],
        "sottocategoria": r["sottocategoria"],
        "indirizzo": r["indirizzo"],
        "telefono": r["telefono"],
        "email": r["email"],
        "sito_web": r["sito_web"],
        "orari_apertura": r["orari_apertura"] or "Consultare il sito web / contatto per orari aggiornati",
        "eventi_e_servizi_al_pubblico": r["eventi_e_servizi_al_pubblico"] or r["titolo_sito"] or f"{r['sottocategoria']} a {r['comune']}",
        "days_open": days,
        "hours_range": ranges,
        "open_sunday": open_sun,
        "open_evening": open_eve,
        "free_first_sunday": free_1st,
        "seasonal_months": months,
        "personaggio": pers
    })
    seen_names.add(key)

print("Total rich items prepared for interactive dashboard:", len(curated_items))
with open("/Users/dany/genova/dashboard_items.json", "w", encoding="utf-8") as f:
    json.dump(curated_items, f, indent=2, ensure_ascii=False)
