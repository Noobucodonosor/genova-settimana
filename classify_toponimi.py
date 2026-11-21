import os
import json
import re
from collections import defaultdict

with open(os.path.expanduser("~/genova/osm_genova_raw.json")) as f:
    osm_data = json.load(f)

with open(os.path.expanduser("~/genova/wikidata_p138.json")) as f:
    wd_p138 = json.load(f)

with open(os.path.expanduser("~/genova/osm_resolved_qids.json")) as f:
    resolved_qids = json.load(f)

# Build lookup from Wikidata P138
wd_lookup = {}
for b in wd_p138:
    label = b.get("itemLabel", {}).get("value", "").strip()
    person = b.get("namedAfterLabel", {}).get("value", "").strip()
    desc = b.get("namedAfterDesc", {}).get("value", "").strip()
    if label and person:
        wd_lookup[label.lower()] = (person, desc)

# Collect all unique named elements
elements_by_name = {}
for el in osm_data.get("elements", []):
    tags = el.get("tags", {})
    name = tags.get("name", "").strip()
    if not name:
        continue
    if name not in elements_by_name:
        elements_by_name[name] = tags
    else:
        for k, v in tags.items():
            if k not in elements_by_name[name]:
                elements_by_name[name][k] = v

# Urban prefixes of interest
PREFIXES = [
    "Via ", "Piazza ", "Piazzale ", "Piazzetta ", "Largo ", "Corso ", "Viale ",
    "Salita ", "Vico ", "Passo ", "Scalinata ", "Lungomare ", "Lungobisagno ",
    "Calata ", "Ponte ", "Molo ", "Galleria ", "Viadotto ", "Sopraelevata ",
    "Giardini ", "Giardino ", "Parco ", "Villa ", "Palazzo ", "Castello ",
    "Teatro ", "Stadio ", "Museo ", "Biblioteca ", "Ospedale ", "Istituto ",
    "Forte ", "Torre ", "Belvedere ", "Passeggiata ", "Rampa ", "Archivolto ",
    "Arena ", "Piscina ", "Mercato ", "Cimitero ", "Chiesa ", "Basilica ",
    "Santuario ", "Oratorio ", "Abbazia ", "Convento ", "Monumento ", "Busto ",
    "Targa ", "Lapide ", "Scoglio ", "Porta ", "Mura ", "Caserma ", "Scuola ",
    "Liceo ", "Collegio ", "Conservatorio ", "Accademia ", "Padiglione "
]

# Famous Italian/Ligurian given names to detect person streets
GIVEN_NAMES = {
    "Achille", "Adelaide", "Adelchi", "Adolfo", "Adriano", "Agostino", "Alarico", "Albano",
    "Alberto", "Albino", "Alceste", "Alcide", "Aldo", "ardo", "Alessandro", "Alessio",
    "Alfonso", "Alfredo", "Alighiero", "Ambrogio", "Amedeo", "Amerigo", "Amilcare", "Amintore",
    "Andrea", "Angelo", "angiolo", "Anita", "Anna", "Annibale", "Ansaldo", "Anselmo",
    "Anton", "Antoniotto", "Antonio", "Apollonio", "Arimondo", "Ariodante", "Aristide", "Arnaldo",
    "Arrigo", "Arturo", "Ascanio", "Attilio", "Augusto", "Aurelio", "Azelio",
    "Baldassarre", "Baldo", "Barnaba", "Bartolomeo", "Battista", "Beatrice", "Benedetto", "Beniamino",
    "Benito", "Beppe", "Berto", "Bernardo", "Biagio", "Bianca", "Bino", "Bonifacio", "Bortolo", "Bruno",
    "Caffaro", "Caio", "Calogero", "Camilla", "Camillo", "Candido", "Carlo", "Carlotta", "Carmelo",
    "aterina", "Caterina", "Catullo", "Ceccardo", "Celeste", "Celestino", "Cesare", "Chiara",
    "Ciro", "Claudio", "Clemente", "Clelia", "Clorinda", "Cola", "Colombo", "Corrado", "Cosimo",
    "Costantino", "Costanzo", "Cristoforo", "Curzio",
    "Damiano", "Daniele", "Dante", "Dario", "Davide", "Demetrio", "Diego", "Dino", "Diocle",
    "Domenico", "Donato", "Duilio",
    "Edilio", "Edmondo", "Edoardo", "Efisio", "Egidio", "Egisto", "Elena", "Eleonora", "Elia",
    "Elio", "Elisa", "Elisabetta", "Eliseo", "Emanuele", "Emilio", "Enea", "Enrico", "Ennio",
    "Enzo", "Erasmo", "Ercole", "Ermanno", "Ermenegildo", "Erminia", "Ernesto", "Eros", "Ettore",
    "Eugenio", "Eusebio", "Evangelista", "Evan", "Ezio",
    "Fabiano", "Fabio", "Fabrizio", "Fausto", "Fedele", "Federico", "Felice", "Ferdinando",
    "Ferruccio", "Fidel", "Filiberto", "Filippo", "Fiorenzo", "Flavio", "Floriano", "Fortunato",
    "Foscolo", "Franca", "Francesco", "Franco", "Fulvio", "Furio",
    "Gabriele", "Gabriello", "Gaetano", "Galeazzo", "Galileo", "Gaspare", "Gastone", "Gavino",
    "Gennaro", "Gennarino", "Gentile", "Gerolamo", "Germano", "Gherardo", "Giacinto", "Giacomo",
    "Giambattista", "Giampaolo", "Giampiero", "Gian", "Giancarlo", "Gianfranco", "Gianluigi",
    "Gianmaria", "Giannina", "Giannino", "Giannettino", "Giannozzo", "Gino", "Gio", "Gioacchino",
    "Giobatta", "Giordano", "Giorgio", "Giosuè", "Giotto", "Giovanna", "Giovanni", "Girolamo",
    "Giuditta", "Giulia", "Giuliano", "Giulio", "Giunio", "Giuseppe", "Giuseppina", "Giustino",
    "Glauco", "Goffredo", "Goliardo", "Grazia", "Graziano", "Gregorio", "Guglielmo", "Guido", "Gustavo",
    "Iacopo", "Ida", "Iginio", "Igino", "Ignazio", "Ilario", "Ildebrando", "Innocenzo", "Ippolito",
    "Irene", "Iris", "Isacco", "Isidoro", "Italo", "ivano", "Ivo",
    "Jacopo", "Jori",
    "Lamba", "Lamberto", "Lanfranco", "Lanzarotto", "Lauro", "Lazzaro", "Leandro", "Leo",
    "Leonardo", "Leone", "Leonida", "Leopoldo", "Libero", "Lina", "Lino", "Livio", "Lodovico",
    "Lorenzo", "Luca", "Luciano", "Lucio", "Lucrezia", "Ludovico", "Luigi", "Luigia", "Luisa",
    "Macrino", "Maddalena", "Manfredo", "Manlio", "Marcellino", "Marcello", "Marco", "Margherita",
    "Maria", "Mariano", "Marino", "Mario", "Marsilio", "Martino", "Marzio", "Massimiliano",
    "Massimo", "Matilde", "Matteo", "Mattia", "Maurizio", "Mauro", "Medardo", "Melchiorre",
    "Menotti", "Michele", "Milo", "Mirko", "Modesto", "Mosè", "Muzio",
    "Nadio", "Napoleone", "Narciso", "Natale", "Nazarin", "Nazario", "Nello", "Neri", "Niccolò",
    "Nicola", "Nicolò", "Nicolosio", "Nicoloso", "Nino", "Noè", "Norberto", "Nino",
    "Oberto", "Odorico", "Olimpio", "Olindo", "iviero", "Omobono", "Onorato", "Onofrio", "Orazio",
    "Oreste", "Orlando", "Orso", "Osvaldo", "Otello", "Ottavio", "Ottone", "Ovidio",
    "Pacinotti", "Pagano", "Palmiro", "Pancrazio", "Panfilo", "Paola", "Paolo", "Paride",
    "Pasquale", "Patrizio", "Pellegrino", "Pericle", "Piero", "Pier", "Pietro", "Pio", "Pippo",
    "Plinio", "Plutarco", "Polidoro", "Pompeo", "Primo", "Prospero", "Publio",
    "Quinto", "Quirino",
    "Raffaele", "Raffaello", "Raimondo", "Ranieri", "Raoul", "Redipuglia", "Reginaldo", "Remigio",
    "Remo", "Renato", "Renzo", "Riccardo", "Rinaldo", "Rino", "Roberto", "Rocco", "Rodolfo",
    "Rodrigo", "Rolando", "Romano", "Romeo", "Romolo", "Rosa", "Rosanna", "Rosario", "Rosolino",
    "Ruggero", "Rustico",
    "Sabatino", "Sabino", "Salvatore", "Salvo", "Samuele", "Sandro", "Sante", "anti", "Santo",
    "Saverio", "Savino", "Scipione", "Sebastiano", "Secondo", "Sem", "Serafino", "Sergio",
    "Settimio", "Severino", "Severo", "Sigismondo", "Silvano", "Silvestro", "Silvio", "Simone",
    "Sinibaldo", "Siro", "Sisto", "Socrate", "Sofonisba", "Spartaco", "Stanislao", "Stefano",
    "Tancredi", "Tarcisio", "Torquato", "Tiziano", "Tito", "Tobia", "Tommaso", "Tonino", "Tullio",
    "Ubaldo", "Uberto", "Ugo", "Ugolino", "Ulderico", "Ulisse", "Umberto", "Urbano",
    "Valente", "entino", "Valentino", "Valerio", "Vasco", "Venanzio", "Venceslao", "Verdi",
    "Vittorino", "Vittorio", "Vincenzo", "Virgilio", "Virginio", "Vito", "Vittore", "Vladimiro",
    "Walter", "Wanda", "Zaccaria", "Zeno", "Zenone"
}

# Known Genovese/Historical Surnames, Families, Titles, Saints
TITLES_AND_ROLES = {
    "San", "Sant'", "Santa", "Santi", "Beato", "Beata", "Padre", "Fra", "Frate", "Don", "Monsignor",
    "Cardinale", "Papa", "Vescovo", "Abate", "Suor", "Madre", "Duca", "Duchessa", "Principe",
    "Principessa", "Marchese", "Marchesa", "Conte", "Contessa", "Barone", "Re", "Regina",
    "Imperatore", "Doge", "Capitano", "Ammiraglio", "Generale", "Colonnello", "Maggiore",
    "Tenente", "Sottotenente", "Caporale", "Sergente", "Maresciallo", "Comandante", "Partigiano",
    "Martire", "Martiri", "Fratelli", "Sorelle", "Maestro", "Professor", "Dottor", "Ingegner",
    "Architetto", "Avvocato", "Senatore", "Onorevole", "Poeta", "Pittore"
}

FAMOUS_FAMILIES_AND_PERSONS = {
    "Balbi", "Doria", "Spinola", "Fieschi", "Grimaldi", "Lomellini", "Giustiniani", "Pallavicini",
    "Pallavicino", "Durazzo", "Brignole", "De Ferrari", "Ferraris", "Sauli", "Centurione",
    "Cattaneo", "Imperiale", "Lercari", "Serra", "Negrone", "De Mari", "De Marini", "De Franchi",
    "Adorno", "Fregoso", "Campofregoso", "Guarco", "Montaldo", "Boccanegra", "Embriaci", "Embriaco",
    "Della Volta", "Cicala", "Usodimare", "Vivaldi", "Zaccaria", "Malocello", "Pessagno", "Caboto",
    "Colombo", "Vespucci", "Magellano", "Pancaldo", "Assereto", "Caffaro", "Staglieno", "Maragliano",
    "Cambiaso", "Strozzi", "Piola", "Fiasella", "Magnasco", "Carlone", "Barabino", "Orsolino",
    "Paganini", "Sivori", "Verdi", "Rossini", "Bellini", "Donizetti", "Puccini", "Boito",
    "Mazzini", "Garibaldi", "Mameli", "Bixio", "Cavour", "Ruffini", "Cairoli", "Pisacane",
    "Oberdan", "Battisti", "Sauro", "Filzi", "Chiesa", "Toti", "Baracca", "Saffi", "Quadrio",
    "Avezzana", "Mosto", "Canzio", "Bertani", "Rubattino", "Bombrini", "Ansaldo", "Raggio",
    "Odero", "Orlando", "Piaggio", "Bagnara", "Bruzzo", "Dufour", "Gaslini", "Galliera",
    "Mackenzie", "D'Albertis", "Chiossone", "Luxoro", "Croce", "Bicknell", "Govi", "Volonghi",
    "De André", "Montale", "Sbarbaro", "Caproni", "Firpo", "Ceccardi", "Campana", "Pavese",
    "Calvino", "Pascoli", "Carducci", "D'Annunzio", "Foscolo", "Leopardi", "Manzoni", "Dante",
    "Alighieri", "Petrarca", "Boccaccio", "Ariosto", "Tasso", "Goldoni", "Alfieri", "Parini",
    "Machiavelli", "Guicciardini", "Galilei", "Volta", "Galvani", "Marconi", "Meucci", "Fermi",
    "Pacinotti", "Righi", "Avogadro", "Torricelli", "Malpighi", "Morgagni", "Spallanzani",
    "Gramsci", "Matteotti", "Turati", "Treves", "Bissolati", "Amendola", "Gobetti", "Rosselli",
    "Pertini", "Moro", "Berlinguer", "De Gasperi", "Einaudi", "Nenni", "Saragat", "Togliatti",
    "Di Vittorio", "Pastore", "Grandis", "Grattoni", "Sommeiller", "Paleocapa", "Chiodo",
    "Canevari", "Gastaldi", "Podestà", "Vernazza", "Berio", "Franzoni", "Novi", "Balilla",
    "Perasso", "Casana", "Cavo", "Romanengo", "Casella", "Fassio", "Torielli"
}

# Non-person exclusions (cities, regions, dates, generic nature/flora/fauna/trades)
GEO_OR_DATES = {
    "Genova", "Roma", "Milano", "Torino", "Venezia", "Firenze", "Napoli", "Bologna", "Palermo",
    "Bari", "Trieste", "Trento", "Gorizia", "Pola", "Fiume", "Zara", "Istria", "Dalmazia",
    "Corsica", "Sardegna", "Sicilia", "Liguria", "Piemonte", "Lombardia", "Veneto", "Toscana",
    "Emilia", "Romagna", "Umbria", "Marche", "Lazio", "Abruzzo", "Molise", "Campania", "Puglia",
    "Basilicata", "Calabria", "Italia", "Europa", "Francia", "Spagna", "Inghilterra", "Germania",
    "Svizzera", "Austria", "Grecia", "Oriente", "Levante", "Ponente", "Settentrione", "Meridione",
    "Mare", "Monte", "Monti", "Colle", "Colli", "Valle", "Valli", "Fiume", "Torrente", "Rio",
    "Lago", "Bosco", "Prato", "Prati", "Campo", "Campi", "Orto", "Orti", "Giardino", "Vigna",
    "Vigne", "Olivo", "Ulivi", "Pino", "Pini", "Cedro", "Cedri", "Castagno", "Castagna",
    "Quercia", "Leccio", "Palme", "Magnolie", "Rose", "Viola", "Viole", "Giglio", "Gigli",
    "Gerani", "Ciclamini", "Mimose", "Ginestre", "camelie", "Ortensie",
    "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto",
    "Settembre", "Ottobre", "Novembre", "Dicembre", "XX", "XXV", "IV", "II", "V", "Primo",
    "Statuto", "Libertà", "Indipendenza", "Unità", "Vittoria", "Pace", "Repubblica", "Costituzione",
    "Lavoro", "Commercio", "Industria", "Marina", "Porto", "Molo", "Faro", "Lanterna",
    "Stazione", "Ferrovia", "Mercato", "Macelli", "Erbe", "Fieno", "Legna", "Carbone", "Sale",
    "Orefici", "Scurreria", "Soziglia", "Ravecca", "Pré", "Banchi", "Sottoripa", "Portoria",
    "Sarzano", "Carignano", "Castelletto", "Marassi", "Staglieno", "Albaro", "Boccadasse",
    "Sturla", "Quarto", "Quinto", "Nervi", "Sampierdarena", "Cornigliano", "Sestri", "Pegli",
    "Pra'", "Voltri", "Rivarolo", "Bolzaneto", "Pontedecimo", "Struppa", "Molassana", "Bavari",
    "Quezzi", "Oregina", "Lagaccio", "Foce", "Brignole", "Principe"
}

def extract_person_candidate(full_name, tags):
    # Check OSM explicit etymology first
    etym_qid = tags.get("name:etymology:wikidata") or tags.get("subject:wikidata")
    if etym_qid:
        for q in etym_qid.replace(",", ";").split(";"):
            q = q.strip()
            if q in resolved_qids:
                info = resolved_qids[q]
                if info["isHuman"] or info["isFamily"]:
                    return True, info["label"], info["desc"], "OSM+Wikidata"
    
    # Check Wikidata P138 lookup
    if full_name.lower() in wd_lookup:
        person, desc = wd_lookup[full_name.lower()]
        return True, person, desc, "Wikidata P138"

    # Strip prefix
    rest = full_name
    matched_prefix = ""
    for p in sorted(PREFIXES, key=len, reverse=True):
        if full_name.startswith(p):
            matched_prefix = p.strip()
            rest = full_name[len(p):].strip()
            break
    
    if not matched_prefix:
        return False, "", "", ""

    # Clean prepositions at start of rest
    rest_clean = re.sub(r"^(dei |degli |delle |del |dello |della |di |da |a |al |alla |ai |alle )", "", rest, flags=re.IGNORECASE).strip()
    words = [w.strip(".,\"'()[]") for w in rest_clean.split() if w.strip(".,\"'()[]")]
    if not words:
        return False, "", "", ""

    # Exclude pure dates like "XX Settembre", "25 Aprile", "IV Novembre", "Cinque Maggio"
    if len(words) == 2 and words[1].capitalize() in {"Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"}:
        return False, "", "", ""

    # Check if first word is a Title/Role (San, Padre, Generale, Capitano, Duca, Fratelli, etc.)
    first_cap = words[0].capitalize()
    if first_cap in TITLES_AND_ROLES or words[0].startswith("Sant'"):
        # Make sure it's not a generic place like "Ponte Monumentale"
        return True, rest_clean, f"Intitolazione con titolo/ruolo ({first_cap})", "Pattern Titolo/Ruolo"

    # Check if any word is in FAMOUS_FAMILIES_AND_PERSONS
    for w in words:
        if w in FAMOUS_FAMILIES_AND_PERSONS or w.capitalize() in FAMOUS_FAMILIES_AND_PERSONS:
            return True, rest_clean, f"Personaggio o casata storica ({w})", "Casata/Personaggio Storico"

    # Check if first word (or second word after title) is a Given Name AND there is at least a surname
    if len(words) >= 2 and first_cap in GIVEN_NAMES:
        # Exclude if second word is a month
        if words[1].capitalize() not in {"Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"}:
            return True, rest_clean, "Nome e cognome di personaggio", "Pattern Nome+Cognome"

    return False, "", "", ""

person_places = []
for name in sorted(elements_by_name.keys()):
    tags = elements_by_name[name]
    ok, person, desc, source = extract_person_candidate(name, tags)
    if ok:
        person_places.append({
            "place_name": name,
            "person": person,
            "description": desc,
            "source": source
        })

print("Total person/family-named places extracted:", len(person_places))
by_source = defaultdict(int)
for p in person_places:
    by_source[p["source"]] += 1
print("Breakdown by detection source:", dict(by_source))
for p in person_places[:40]:
    print(f"  {p['place_name']}  -->  {p['person']} ({p['description']})")
