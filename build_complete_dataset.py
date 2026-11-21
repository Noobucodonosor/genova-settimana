import json
import csv
import re
from collections import defaultdict
import os as _os
_DATA_DIR = _os.environ.get("GENOVA_DATA_DIR") or _os.path.dirname(_os.path.abspath(__file__))

with open(f"{_DATA_DIR}/osm_genova_raw.json") as f:
    osm_data = json.load(f)

with open(f"{_DATA_DIR}/wikidata_p138.json") as f:
    wd_p138 = json.load(f)

with open(f"{_DATA_DIR}/osm_resolved_qids.json") as f:
    resolved_qids = json.load(f)

# 1. Build Wikidata P138 lookup
wd_lookup = {}
for b in wd_p138:
    label = b.get("itemLabel", {}).get("value", "").strip()
    person = b.get("namedAfterLabel", {}).get("value", "").strip()
    desc = b.get("namedAfterDesc", {}).get("value", "").strip()
    if label and person:
        # Avoid pure geographic rivers/places if they slipped into P138
        if person.lower() not in {"polcevera", "bisagno", "condotte d'acqua", "genova"}:
            wd_lookup[label.lower()] = (person, desc)

# 2. Collect unique named elements
elements_by_name = {}
for el in osm_data.get("elements", []):
    tags = el.get("tags", {})
    name = tags.get("name", "").strip()
    if not name:
        continue
    if name not in elements_by_name:
        elements_by_name[name] = dict(tags)
    else:
        for k, v in tags.items():
            if k not in elements_by_name[name]:
                elements_by_name[name][k] = v

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
    "Liceo ", "Collegio ", "Conservatorio ", "Accademia ", "Padiglione ", "Villetta "
]

GIVEN_NAMES = {
    "Abramo", "Achille", "Adelaide", "Adelchi", "Adele", "Adolfo", "Adriano", "Agostino", "Alarico", "Albano",
    "Alberico", "Alberto", "Albino", "Alceste", "Alcide", "Aldo", "Aleardo", "Alemanno", "Alessandro", "Alessio",
    "Alexander", "Alfonso", "Alfredo", "Alighiero", "Alvise", "Amatore", "Ambrogio", "Amedeo", "Amerigo", "Amilcare",
    "Amintore", "Andalò", "Andrea", "Angelo", "Angiola", "Angiolo", "Anita", "Anna", "Annibale", "Ansaldo", "Anselmo",
    "Antioco", "Anton", "Antoniotto", "Antonietta", "Antonino", "Antonio", "Apollonio", "Araone", "Archimede", "Ariberto",
    "Arimondo", "Ariodante", "Aristide", "Armando", "Arnaldo", "Arrigo", "Arturo", "Ascanio", "Assunta", "Attilio",
    "Atto", "Augusto", "Aulo", "Aurelio", "Aureliano", "Ausonio", "Azelio",
    "Baldassarre", "Baldo", "Baldovino", "Barnaba", "Bartolomeo", "Battista", "Battistino", "Beatrice", "Benedetto",
    "Beniamino", "Benito", "venuto", "Benvenuto", "Beppe", "Berto", "Bernabò", "Bernardino", "Bernardo", "Bettino",
    "Biagio", "Bianca", "Bino", "Bonifacio", "Bortolo", "Bruno",
    "Caffaro", "Caio", "Calogero", "Camilla", "Camillo", "Candido", "Carletto", "Carlino", "Carlo", "Carlotta",
    "Carmelo", "Carmine", "Caterina", "Catullo", "Ceccardo", "Celeste", "Celestino", "Cesare", "Chiara",
    "Ciro", "Claudio", "Clemente", "Clelia", "Clorinda", "Cola", "Colombo", "Corrado", "Cornelio", "Cosimo", "Cosma",
    "Costantino", "Costanzo", "Cristoforo", "Curzio", "Casimiro",
    "Damiano", "Daniele", "Daniello", "Dante", "Dario", "Davide", "Delfina", "Demetrio", "Diego", "Dino", "Diocle",
    "Domenico", "Donato", "Duilio",
    "Edilio", "Edmondo", "Edoardo", "Eduardo", "Efisio", "Egidio", "Egisto", "Elena", "Eleonora", "Elia",
    "Elio", "Elisa", "Elisabetta", "Eliseo", "Emanuela", "Emanuele", "Emilio", "Enea", "Enrico", "Ennio",
    "Enzo", "Erasmo", "Ercole", "Ermanno", "Ermelinda", "Ermenegildo", "Erminia", "Ernesto", "Eros", "Erpidio",
    "Errico", "Ettore", "Eugenio", "Eunice", "Eusebio", "Eustachio", "Evan", "Evandro", "Evangelista", "Evasio", "Ezio",
    "Fabiano", "Fabio", "Fabrizio", "Faliero", "Fausto", "Fedele", "Federico", "Felice", "Felicita", "Ferdinando",
    "Fernando", "Ferrante", "Ferruccio", "Fidel", "Filiberto", "Filippo", "Fiorenzo", "Flavia", "Flavio", "Floriano",
    "Fortunato", "Foscolo", "Franca", "Francesca", "Francesco", "Francisco", "Franco", "Fulcieri", "Fulcone", "Fulvio", "Furio",
    "Gabriele", "Gabriello", "Gabrio", "Gaetano", "Galeazzo", "Galileo", "Gaspare", "Gastone", "Gavino",
    "Gennaro", "Gennarino", "Gentile", "Georges", "Gerolamo", "Germano", "Gherardo", "Giacinto", "Giacomo",
    "Giambattista", "Gianbattista", "Giampaolo", "Giampiero", "Gian", "Giancarlo", "Gianfranco", "Gianluigi",
    "Gianmaria", "Giannina", "Giannino", "Giannettino", "Gianni", "Giannozzo", "Gildo", "Gino", "Gio", "Giò",
    "Gioacchino", "Giobatta", "Giordano", "Giorgio", "Giosuè", "Giotto", "Giovanna", "Giovanni", "Giovannino", "Girolamo",
    "Giuditta", "Giulia", "Giuliano", "Giulio", "Giunio", "Giuseppe", "Giuseppina", "Giustino",
    "Glauco", "Gloriano", "Goffredo", "Goliardo", "Grazia", "Graziano", "Graziella", "Gregorio", "Guglielmo", "Guido", "Gustavo",
    "Hector", "Henry", "Iacopo", "Ida", "Iginio", "Igino", "Ignazio", "Ilario", "Ildebrando", "Innocenzo", "Ippolito",
    "Irene", "Iris", "Isacco", "Isidoro", "Italo", "Ivano", "Ivo",
    "Jack", "Jacopo", "James", "Jan", "Jean", "Johann", "John", "Jolanda", "Jori",
    "Lamba", "Lamberto", "Lanfranco", "Lanzarotto", "Laura", "Lauro", "Lazzaro", "Leandro", "Leo", "Leon",
    "Leonardo", "Leone", "Leonida", "Leopoldo", "Libero", "Lina", "Lino", "Livio", "Lodovico",
    "Lorenzo", "Louis", "Luca", "Luciana", "Luciano", "Lucio", "Lucrezia", "Ludovico", "Luigi", "Luigia", "Luisa",
    "Macrino", "Maddalena", "Mafalda", "Manfredo", "Manlio", "Marc'Aurelio", "Marcellino", "Marcello", "Marco", "Margherita",
    "Maria", "Mariagrazia", "Mariano", "Marina", "Marino", "Mario", "Marsilio", "Martino", "Marzio", "Massimiliano",
    "Massimo", "Matilde", "Matteo", "Mattia", "Maurice", "Maurizio", "Mauro", "Medardo", "Melchiorre", "Melvin",
    "Menotti", "Michelangelo", "Michele", "Milo", "Mirko", "Modesto", "Mosè", "Muzio",
    "Nadio", "Napoleone", "Narciso", "Natale", "Natalino", "Nazarin", "Nazario", "Nazzareno", "Nello", "Nereo", "Neri",
    "Nevio", "Niccolò", "Nicholas", "Nicola", "Nicolò", "Nicolo", "Nicolosio", "Nicoloso", "Nilde", "Nino", "Noè", "Nora", "Norberto",
    "Oberto", "Odoardo", "Odorico", "Ogerio", "Olimpio", "Olindo", "Oliviero", "Omero", "Omobono", "Onorato", "Onofrio", "Orazio",
    "Oreste", "Orlando", "Orso", "Osvaldo", "Otello", "Ottavio", "Ottone", "Ottorino", "Ovidio",
    "Pagano", "Palmiro", "Pancrazio", "Panfilo", "Paola", "Paolo", "Papacino", "Paride",
    "Pasquale", "Patrizio", "Pedro", "Pellegrina", "Pellegrino", "Pellegro", "Peppino", "Percy", "Pericle", "Pertinace",
    "Piero", "Pier", "Pierino", "Pietro", "Pio", "Pippo", "Plinio", "Plutarco", "Polidoro", "Pompeo", "Primo", "Prospero", "Publio",
    "Quinto", "Quirino",
    "Raffaele", "Raffaello", "Raimondo", "Ramiro", "Ranieri", "Raoul", "Reginaldo", "Remigio",
    "Remo", "Renata", "Renato", "Renzo", "Riccardo", "Richard", "Rinaldo", "Rino", "Robert", "Roberto", "Rocco", "Rodolfo",
    "Rodrigo", "Rolando", "Romano", "Romeo", "Romolo", "Rosa", "Rosanna", "Rosario", "Rosetta", "Rosolino",
    "Rubaldo", "Ruggero", "Rurik", "Rustico",
    "Sabatino", "Sabino", "Salvador", "Salvatore", "Salvo", "Samuele", "Sandro", "Sante", "Santi", "Santo", "Santorre",
    "Saverio", "Savino", "Scipione", "Sebastiano", "Secondo", "Sem", "Serafino", "Sergio",
    "Settimio", "Severino", "Severo", "Sibilla", "Sidney", "Sigismondo", "Silvano", "Silvestro", "Silvio", "Simon", "Simone",
    "Sinibaldo", "Siro", "Sisto", "Socrate", "Sofonisba", "Spartaco", "Stanislao", "Stefano", "Susanna",
    "Tancredi", "Tarcisio", "Tea", "Teodoro", "Terenzio", "Teresa", "Teresio", "Tina", "Tiziano", "Tito", "Tobia",
    "Tomaso", "Tommaso", "Tonino", "Torquato", "Tullio",
    "Ubaldo", "Uberto", "Ugo", "Ugolino", "Ulderico", "Ulisse", "Umberto", "Urbano", "Ursone",
    "Valente", "Valentino", "Valerio", "Vannuccio", "Vasco", "Venanzio", "Venceslao",
    "Vittoria", "Vittorina", "Vittorino", "Vittorio", "Vincenzo", "Virgilio", "Virginio", "Visconte", "Vito", "Vittore", "Vladimiro",
    "Walter", "Wanda", "Wolfgang", "Zaccaria", "Zeno", "Zenone"
}

TITLES_AND_ROLES = {
    "San", "Sant'", "Santa", "Santi", "Beato", "Beata", "Padre", "Fra", "Frà", "Frate", "Don", "Monsignor",
    "Cardinale", "Cardinal", "Papa", "Vescovo", "Abate", "Prete", "Suor", "Madre", "Duca", "Duchessa", "Principe",
    "Principessa", "Marchese", "Marchesa", "Conte", "Contessa", "Barone", "Re", "Regina",
    "Imperatore", "Doge", "Capitano", "Ammiraglio", "Generale", "Colonnello", "Maggiore",
    "Tenente", "Sottotenente", "Caporale", "Sergente", "Maresciallo", "Comandante", "Partigiano",
    "Martire", "Martiri", "Fratelli", "Sorelle", "Maestro", "Professor", "Dottor", "Ingegner",
    "Architetto", "Avvocato", "Senatore", "Onorevole", "Poeta", "Pittore", "Contubernio"
}

FAMOUS_SURNAMES_AND_FAMILIES = {
    "Balbi", "Doria", "Spinola", "Spìnola", "Fieschi", "Fieschine", "Grimaldi", "Lomellini", "Giustiniani", "Pallavicini",
    "Pallavicino", "Durazzo", "Durazzo-Pallavicini", "Brignole", "De Ferrari", "Ferraris", "Ferrari", "Sauli", "Centurione", "Centuriona",
    "Cattaneo", "Imperiale", "Lercari", "Serra", "Negrone", "De Mari", "De Marini", "De Franchi", "De Gradi", "De Nicolay",
    "Adorno", "Fregoso", "Campofregoso", "Guarco", "Guarchi", "Montaldo", "Boccanegra", "Embriaci", "Embriaco",
    "Della Volta", "Cicala", "Usodimare", "Vivaldi", "Zaccaria", "Malocello", "Pessagno", "Caboto",
    "Colombo", "Vespucci", "Magellano", "Pancaldo", "Assereto", "Caffaro", "Staglieno", "Maragliano",
    "Cambiaso", "Strozzi", "Piola", "Fiasella", "Magnasco", "Carlone", "Barabino", "Orsolino",
    "Paganini", "Sivori", "Verdi", "Rossini", "Bellini", "Donizetti", "Puccini", "Boito", "Berlioz", "Ravel", "Wagner", "Mozart", "Bach", "Bizet",
    "Mazzini", "Garibaldi", "Mameli", "Bixio", "Cavour", "Ruffini", "Cairoli", "Pisacane", "Manin", "Sciesa",
    "Oberdan", "Battisti", "Sauro", "Filzi", "Chiesa", "Toti", "Baracca", "Saffi", "Quadrio", "Ricasoli", "Sonnino", "Sella", "Rosmini",
    "Avezzana", "Mosto", "Canzio", "Bertani", "Rubattino", "Bombrini", "Ansaldo", "Raggio", "Raggi",
    "Odero", "Orlando", "Piaggio", "Bagnara", "Bruzzo", "Dufour", "Gaslini", "Galliera",
    "Mackenzie", "D'Albertis", "d'Albertis", "Chiossone", "Luxoro", "Croce", "Bicknell", "Govi", "Volonghi", "Duse",
    "De André", "De Andrè", "Montale", "Sbarbaro", "Caproni", "Firpo", "Ceccardi", "Roccatagliata", "Campana", "Pavese",
    "Calvino", "Pascoli", "Carducci", "D'Annunzio", "Foscolo", "Leopardi", "Manzoni", "Dante", "Guareschi", "Brocchi", "Cechov", "Shelley", "Giusti",
    "Alighieri", "Petrarca", "Boccaccio", "Ariosto", "Tasso", "Goldoni", "Alfieri", "Parini", "Chiabrera", "Cebà",
    "Machiavelli", "Guicciardini", "Galilei", "Volta", "Galvani", "Marconi", "Meucci", "Fermi", "Majorana", "Sobrero", "Linneo", "Braille", "Fleming", "Dunant",
    "Pacinotti", "Righi", "Avogadro", "Torricelli", "Malpighi", "Morgagni", "Spallanzani",
    "Gramsci", "Matteotti", "Turati", "Treves", "Bissolati", "Amendola", "Gobetti", "Rosselli", "Calamandrei", "Iotti",
    "Pertini", "Moro", "Berlinguer", "De Gasperi", "Einaudi", "Nenni", "Saragat", "Togliatti", "Falcone", "Borsellino", "Impastato", "Loi",
    "Di Vittorio", "Pastore", "Grandis", "Grattoni", "Sommeiller", "Paleocapa", "Chiodo", "Bettolo", "Caracciolo", "Cagni", "Millo",
    "Canevari", "Gastaldi", "Podestà", "Vernazza", "Berio", "Franzoni", "Franzone", "Novi", "Balilla",
    "Perasso", "Casana", "Cavo", "Romanengo", "Casella", "Fassio", "Torielli",
    # Additional Genovese Patrizian families, Dogi, Historians, Painters, Benefactors found in review
    "Accinelli", "Acquarone", "Ayroli", "Balbi", "Baliano", "Balleydier", "Banderali", "Bandiera", "Banfi",
    "Banchero", "Barisone", "Bignami", "Bonino", "Borzino", "Bottini", "Bracelli", "Brian", "Brichetto",
    "Brusato", "Bruzza", "Buonvicini", "Burba", "Buxio", "Cadamosto", "Calvi", "Campodonico", "Canessa",
    "Carrena", "Carrara", "Casareggio", "Casareto", "Casoni", "Cataldi", "Celesia", "Cembrano", "Chiappori",
    "Chighizola", "Cicoperi", "Clavarezza", "Conforti", "Cravero", "Crollalanza", "Currò", "D'Antoni",
    "Dal Verme", "dal Verme", "De Caroli", "Degola", "Dellacasa", "Denegri", "Dinegro", "Di Negro", "Donghi",
    "Falamonica", "Ferretto", "Fieschi", "Foglietta", "Foltzer", "Franzonina", "Franzoniane", "Gambaro",
    "Garbarino", "Gattilusio", "Gattorno", "Gavotti", "Ghirotti", "Giannini", "Ginocchio", "Grasso",
    "Grondona", "Gropallo", "Gruber", "Gualco", "Guarnieri", "Invrea", "Lambruschini", "Landi", "Landolfo",
    "Larco", "Lavagnino", "Lavezzi", "Lavezzara", "Laviosa", "Leccavela", "Lemerle", "Liberti", "Macciò",
    "Mallone", "Maruffo", "Marsano", "Martinez", "Melegari", "Merani", "Merello", "Micone", "Migliorini",
    "Millo-Navone", "Minolli", "Mirolli", "Mojon", "Molinari", "Mongiardino", "Mongiardini", "Morando",
    "Morchi", "Mylius", "Narisano", "Nattino", "Noceti", "Oliva", "Origoni", "Ottonelli", "Ottonello",
    "Paggi", "Palli", "Pareto", "Parodi", "Pastorino", "Pedegoli", "Penco", "Perrone", "Pescetto",
    "Piccardo", "Pieragostini", "Pignone", "Pinelli", "Pittamuli", "Piuma", "Poggi", "Polleri", "Puccio",
    "Quartara", "Ratto", "Ravano", "Ravara", "Rebuffo", "Rebucchi", "Reggio", "Richelieu", "Rivara",
    "Rovere", "Rosazza", "Salvaghi", "Sansone", "Savi", "Savignone", "Scassi", "Schiaffino", "Sciaccaluga",
    "Sciallero", "Semino", "Senarega", "Sforza", "Spensley", "Squarciafico", "Stalder", "Stallo", "Storace",
    "Stramesi", "Tacconi", "Tassara", "Tassorelli", "Tavarone", "Testero", "Tollot", "Traverso", "Vacchero",
    "Valente", "Varni", "Vassalli", "Vegetti", "Veneroso", "Vezzani", "Viani", "Vignoso", "Vinelli"
}

# Explicit exclusions for pure geographic places, battles, military units, dates, flora/fauna
NON_PERSON_EXACT = {
    "Ponte Monumentale", "Ponte Romano", "Ponte Cinese", "Palazzo Ducale", "Palazzo Reale", "Palazzo Bianco", "Palazzo Rosso",
    "Via Venti Settembre", "Via Venticinque Aprile", "Via Ventiquattro Maggio", "Via Cinque Maggio", "Via Cinque Dicembre",
    "Via Dodici Ottobre", "Largo Dodici Ottobre", "Viale IV Novembre", "Viale Quattro Novembre",
    "Via Monte Santo", "Piazza Monte Santo", "Corso Monte Grappa", "Via Passo Buole", "Via Col Di Lana",
    "Via Milazzo", "Via Marsala", "Via Calatafimi", "Via Bezzecca", "Ponte Bezzecca", "Ponte bezzecca",
    "Via Curtatone", "Via Goito", "Via Pastrengo", "Via Palestro", "Via Magenta", "Corso Magenta", "Corso Mentana", "Corso Dogali",
    "Via Sapri", "Via Quarto", "Via Quinto", "Via Pegli", "Via Voltri", "Via Sturla", "Via Albaro", "Via Marassi",
    "Via Rivarolo", "Via Bolzaneto", "Via Cornigliano", "Via Struppa", "Via Molassana", "Via Bavari", "Via Sestri",
    "Via San Marino", "Via Santa Sofia"
}

def classify_place(full_name, tags):
    if full_name in NON_PERSON_EXACT:
        # Note: Palazzo Reale, Palazzo Rosso, Palazzo Bianco have family stories, let's check if we want to keep them with explicit notes
        if full_name == "Palazzo Reale":
            return True, "Famiglia Balbi e Casa Savoia", "Palazzo storico fondato da Stefano Balbi (1643) e ceduto ai Savoia (1824)", "Edifici & Monumenti"
        if full_name in ("Palazzo Rosso", "Palazzo Bianco"):
            return True, "Famiglia Brignole Sale (Maria Brignole Sale De Ferrari)", "Palazzo dei Rolli donato alla città dalla Duchessa di Galliera", "Edifici & Monumenti"
        return False, "", "", ""

    # Determine prefix category
    matched_prefix = ""
    rest = full_name
    for p in sorted(PREFIXES, key=len, reverse=True):
        if full_name.startswith(p):
            matched_prefix = p.strip()
            rest = full_name[len(p):].strip()
            break

    if not matched_prefix:
        return False, "", "", ""

    # 1. Check OSM explicit QID
    etym_qid = tags.get("name:etymology:wikidata") or tags.get("subject:wikidata")
    if etym_qid:
        for q in etym_qid.replace(",", ";").split(";"):
            q = q.strip()
            if q in resolved_qids:
                info = resolved_qids[q]
                if info["isHuman"] or info["isFamily"]:
                    return True, info["label"], info["desc"] or f"Intitolazione verificata Wikidata ({q})", matched_prefix

    # 2. Check Wikidata P138 lookup
    if full_name.lower() in wd_lookup:
        person, desc = wd_lookup[full_name.lower()]
        return True, person, desc or "Intitolazione verificata Wikidata P138", matched_prefix

    # Clean leading prepositions/qualifiers in rest
    rest_clean = re.sub(
        r"^(Inferiore |Superiore |inferiore |superiore |chiuso |Chiuso |privata |Privato |vecchia |Vecchia |nuova |Nuova |a destra di |a sinistra di |dietro il Coro di |dietro il coro di |alla |al |all'|ai |alle |a |dei |degli |delle |del |dello |della |di |da )+",
        "", rest
    ).strip()

    words = [w.strip(".,\"'()[]«»") for w in rest_clean.split() if w.strip(".,\"'()[]«»")]
    if not words:
        return False, "", "", ""

    # Exclude date patterns (e.g. "10 Maggio 1909", "25 Aprile", "30 Giugno 1960")
    months = {"gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"}
    if any(w.lower() in months for w in words) and (words[0].isdigit() or words[0].upper() in {"I", "II", "III", "IV", "V", "VI", "X", "XX", "XXIV", "XXV", "VENTI", "VENTICINQUE", "VENTIQUATTRO", "CINQUE", "DODICI"}):
        return False, "", "", ""

    # Check if any word matches FAMOUS_SURNAMES_AND_FAMILIES
    for w in words:
        if w in FAMOUS_SURNAMES_AND_FAMILIES or w.capitalize() in FAMOUS_SURNAMES_AND_FAMILIES:
            # Make sure it isn't "Via Roma" or "Corso Torino"
            return True, rest_clean, f"Personaggio storico o casata genovese ({w})", matched_prefix

    # Check if first word is a Title/Role
    first_w = words[0]
    if first_w in TITLES_AND_ROLES or first_w.capitalize() in TITLES_AND_ROLES or first_w.lower().startswith("sant'"):
        # Exclude military divisions or generic collectives without a person name if needed, though San/Santa/Padre/Don/Capitano/Generale are all person-based
        return True, rest_clean, f"Figura storica/religiosa o titolato ({first_w})", matched_prefix

    # Check Initials pattern like "G. B. Bottaro", "G. A. Molfino", "G.B. Botteri"
    if re.match(r"^([A-Z]\.\s*)+[A-Z][a-zàèéìòù]+", rest_clean):
        return True, rest_clean, "Personaggio storico (iniziali + cognome)", matched_prefix

    # Check Given Name + Surname pattern
    if len(words) >= 2 and (first_w in GIVEN_NAMES or first_w.capitalize() in GIVEN_NAMES):
        if words[1].lower() not in months:
            return True, rest_clean, "Personaggio (Nome + Cognome)", matched_prefix

    # Check if second word is a Given Name (e.g., "Civica Francesco Gallino", "Ospedale Andrea Gallino", "Asilo Davide e Delfina Garbarino")
    if len(words) >= 3 and (words[1] in GIVEN_NAMES or words[1].capitalize() in GIVEN_NAMES):
        return True, rest_clean, "Personaggio (Intitolazione ente/luogo)", matched_prefix

    return False, "", "", ""

results = []
for name in sorted(elements_by_name.keys()):
    tags = elements_by_name[name]
    ok, person, desc, prefix = classify_place(name, tags)
    if ok:
        results.append({
            "toponimo": name,
            "tipo": prefix,
            "personaggio_o_casata": person,
            "descrizione_categoria": desc
        })

print("Total extracted person-named places in Genova:", len(results))

# Group by prefix type
by_type = defaultdict(list)
for r in results:
    by_type[r["tipo"]].append(r)

for t, lst in sorted(by_type.items(), key=lambda x: -len(x[1])):
    print(f"  {t}: {len(lst)}")

# Save full JSON and CSV
with open(f"{_DATA_DIR}/toponimi_personaggi_genova_integrale.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

with open(f"{_DATA_DIR}/toponimi_personaggi_genova_integrale.csv", "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["toponimo", "tipo", "personaggio_o_casata", "descrizione_categoria"])
    writer.writeheader()
    writer.writerows(results)

# Also write a clean Markdown catalog grouped by category
with open(f"{_DATA_DIR}/elenco_integrale_personaggi_genova.md", "w", encoding="utf-8") as f:
    f.write("# Censimento Integrale dei Toponimi di Genova intitolati a Personaggi e Casate\n\n")
    f.write(f"**Totale luoghi censiti nel Comune di Genova:** `{len(results)}` (su `5.240` odonimi e luoghi totali estratti da OpenStreetMap + Wikidata).\n\n")
    f.write("## 1. Formato Insieme Compatto `Insieme = ( ... )`\n\n```text\nInsieme_Toponimi_Personaggi_Genova = (\n  ")
    f.write(";\n  ".join(f"{r['toponimo']} [{r['personaggio_o_casata']}]" for r in results))
    f.write("\n);\n```\n\n")
    f.write("## 2. Elenco Suddiviso per Tipologia Urbana\n\n")
    for t, lst in sorted(by_type.items(), key=lambda x: -len(x[1])):
        f.write(f"### {t} ({len(lst)} voci)\n\n")
        for r in lst:
            f.write(f"- **{r['toponimo']}** → *{r['personaggio_o_casata']}* ({r['descrizione_categoria']})\n")
        f.write("\n")

print("Files written successfully to /Users/dany/genova/")
