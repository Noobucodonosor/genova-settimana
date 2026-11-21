import json
import csv
import math
from collections import defaultdict
import os as _os
_DATA_DIR = _os.environ.get("GENOVA_DATA_DIR") or _os.path.dirname(_os.path.abspath(__file__))

with open(f"{_DATA_DIR}/osm_esercenti_provincia_raw.json") as f:
    raw_elems = json.load(f)["elements"]

with open(f"{_DATA_DIR}/comuni_67_geo.json") as f:
    comuni_geo = json.load(f)

with open(f"{_DATA_DIR}/toponimi_personaggi_provincia_genova.json") as f:
    toponimi = json.load(f)

# Map (comune_lower, street_lower) -> (personaggio, categoria)
person_by_street = {}
for t in toponimi:
    person_by_street[(t["comune"].lower(), t["toponimo"].lower())] = t["personaggio_o_casata"]

# 25 Genoese districts with approximate center coordinates (lat, lon)
GENOVA_QUARTIERI = [
    ("Voltri / Crevari / Vesima", 44.428, 8.752),
    ("Pra' / Palmaro", 44.426, 8.788),
    ("Pegli / Multedo", 44.426, 8.818),
    ("Sestri Ponente", 44.424, 8.852),
    ("Cornigliano", 44.416, 8.872),
    ("Sampierdarena", 44.412, 8.898),
    ("San Teodoro / Dinegro", 44.414, 8.914),
    ("Rivarolo / Certosa", 44.442, 8.894),
    ("Bolzaneto / Murta", 44.460, 8.900),
    ("Pontedecimo / San Quirico", 44.492, 8.903),
    ("Centro Storico (Molo / Maddalena / Prè)", 44.408, 8.930),
    ("Portoria / Via XX Settembre / Carignano", 44.403, 8.938),
    ("Castelletto / Principe / Oregina", 44.417, 8.932),
    ("Brignole / San Vincenzo", 44.408, 8.947),
    ("Foce", 44.397, 8.948),
    ("Marassi / Quezzi", 44.418, 8.956),
    ("San Fruttuoso", 44.410, 8.958),
    ("Staglieno / Parenzo", 44.432, 8.955),
    ("Molassana / Struppa / Val Bisagno", 44.448, 8.985),
    ("San Martino / Borgoratti", 44.406, 8.972),
    ("Albaro", 44.394, 8.966),
    ("Sturla / Boccadasse", 44.392, 8.982),
    ("Quarto dei Mille", 44.389, 8.998),
    ("Quinto al Mare", 44.385, 9.018),
    ("Nervi / Sant'Ilario", 44.382, 9.042),
]

def dist_sq(lat1, lon1, lat2, lon2):
    # Cosine adjustment for longitude at 44.4 deg
    dlon = (lon1 - lon2) * 0.714
    dlat = (lat1 - lat2)
    return dlat*dlat + dlon*dlon

def resolve_comune_and_quartiere(lat, lon, tags):
    city_tag = (tags.get("addr:city") or tags.get("addr:city_extracted") or "").strip()
    if city_tag:
        # Match against the 67 official municipality names
        for c_name in comuni_geo:
            if c_name.lower() == city_tag.lower():
                city_tag = c_name
                break
    
    if not city_tag and lat and lon:
        # Check if within Genova municipal territory vs nearest municipality
        # First check closest among all 67 municipalities + Genova quartieri
        best_comune = "Genova"
        best_d = 999.0
        for c_name, c_info in comuni_geo.items():
            d = dist_sq(lat, lon, c_info["lat"], c_info["lon"])
            if d < best_d:
                best_d = d
                best_comune = c_name
        # Also check distance to closest Genova quartiere; if a point is in Pegli/Sestri/Nervi/Pontedecimo, its closest Genova quartiere is much closer than Genova center!
        best_q_d = min(dist_sq(lat, lon, q_lat, q_lon) for _, q_lat, q_lon in GENOVA_QUARTIERI)
        if best_q_d < best_d and lon >= 8.73 and lon <= 9.062 and lat <= 44.505:
            best_comune = "Genova"
        city_tag = best_comune
    elif not city_tag:
        city_tag = "Genova"

    # Determine Quartiere / Zona
    if city_tag == "Genova" and lat and lon:
        best_q = "Centro Storico (Molo / Maddalena / Prè)"
        best_qd = 999.0
        for q_name, q_lat, q_lon in GENOVA_QUARTIERI:
            d = dist_sq(lat, lon, q_lat, q_lon)
            if d < best_qd:
                best_qd = d
                best_q = q_name
        quartiere = f"Genova — {best_q}"
    else:
        quartiere = f"Provincia — {city_tag}"

    return city_tag, quartiere

# GDO / Chain brands to flag so the user can filter "Solo Indipendenti (Zero Catene)"
CHAINS_GDO = {
    "coop", "icoop", "in's", "basko", "pam", "panorama", "carrefour", "esselunga", "conad",
    "lidl", "eurospin", "penny", "aldi", "ekom", "gulliver", "todis", "tuodì", "md", "doro",
    "tigotà", "acqua & sapone", "acqua e sapone", "kasanova", "ikea", "leroy merlin", "bricoman",
    "tecnoimat", "obi", "mediaworld", "unieuro", "euronics", "trony", "expert", "gamestop",
    "zara", "h&m", "ovs", "upim", "coin", "calzedonia", "intimissimi", "tezenis", "goldenpoint",
    "yamamay", "benetton", "sisley", "motivi", "oltre", "fiorella rubino", "terranova", "calliope",
    "alcott", "piazza italia", "foot locker", "decathlon", "cisalfa", "aw lab", "scarpe&scarpe",
    "pittarosso", "deichmann", "geox", "bata", "sephora", "douglas", "marionnaud", "kiko",
    "wycon", "bottega verde", "l'erbolario", "equivalenza", "salmoiraghi", "viganò", "grandvision",
    "nau!", "visionottica", "amplifon", "audika", "mondadori", "feltrinelli", "ibs", "giunti",
    "tim", "vodafone", "windtre", "wind", "iliad", "fastweb", "sky", "poste italiane",
    "arcaplanet", "isola dei tesori", "maxi zoo", "fortesan", "tigros", "sogegross", "metro"
}

# Detailed taxonomy mapping raw OSM tag -> (MacroCategory, ItalianSubcategory, AntiAmazonKeywords)
TAXONOMY = {
    # 1. Ferramenta, Edilizia, Idraulica, Elettricità, Chiavi & Riparazioni Casa
    "hardware": ("1. Ferramenta, Vernici, Elettricità & Riparazioni Casa", "Ferramenta e Utensileria", "viti bulloni tasselli serrature chiavi attrezzi cacciaviti trapani colla silicone guarnizioni"),
    "doityourself": ("1. Ferramenta, Vernici, Elettricità & Riparazioni Casa", "Fai-da-te, Brico e Legname", "legno mensole compensato vernice attrezzi bricolage"),
    "paint": ("1. Ferramenta, Vernici, Elettricità & Riparazioni Casa", "Colorificio, Vernici e Belle Arti Tecniche", "pittura murale smalti pennelli rulli solventi stucco"),
    "locksmith": ("1. Ferramenta, Vernici, Elettricità & Riparazioni Casa", "Duplicazione Chiavi e Serrature", "chiavi cilindri serrature casseforti telecomandi cancelli"),
    "key_cutter": ("1. Ferramenta, Vernici, Elettricità & Riparazioni Casa", "Duplicazione Chiavi e Radiocomandi", "copia chiavi serrature gusci chiavi auto"),
    "electrical": ("1. Ferramenta, Vernici, Elettricità & Riparazioni Casa", "Materiale Elettrico e Componenti", "cavi prese interruttori lampadine led quadretti trasformatori"),
    "electrician": ("1. Ferramenta, Vernici, Elettricità & Riparazioni Casa", "Elettricista e Impianti Elettrici", "riparazione impianti elettrici salvavita citofoni antenne"),
    "plumber": ("1. Ferramenta, Vernici, Elettricità & Riparazioni Casa", "Idraulico e Termoidraulica", "perdite acqua rubinetti tubi scarichi caldaie scaldabagni"),
    "hvac": ("1. Ferramenta, Vernici, Elettricità & Riparazioni Casa", "Caldaie, Climatizzazione e Riscaldamento", "assistenza caldaie condizionatori pompe di calore termosifoni"),
    "air_conditioning": ("1. Ferramenta, Vernici, Elettricità & Riparazioni Casa", "Climatizzazione e Condizionatori", "climatizzatori filtri ricarica gas"),
    "glaziery": ("1. Ferramenta, Vernici, Elettricità & Riparazioni Casa", "Vetreria e Specchi su Misura", "vetri finestre specchi cristalli tavoli doppi vetri"),
    "window_construction": ("1. Ferramenta, Vernici, Elettricità & Riparazioni Casa", "Serramenti, Infissi e Finestre", "finestre persiane tapparelle zanzariere pvc alluminio"),
    "doors": ("1. Ferramenta, Vernici, Elettricità & Riparazioni Casa", "Porte, Portoni Blindati e Infissi", "porte interne portoni blindati maniglie"),
    "window_blind": ("1. Ferramenta, Vernici, Elettricità & Riparazioni Casa", "Tende da Sole, Tapparelle e Avvolgibili", "tapparelle tende da sole veneziane zanzariere"),
    "carpenter": ("1. Ferramenta, Vernici, Elettricità & Riparazioni Casa", "Falegnameria e Lavorazione Legno", "mobili su misura riparazione legno restauro porte tavoli"),
    "joiner": ("1. Ferramenta, Vernici, Elettricità & Riparazioni Casa", "Falegname e Ebanista", "arredi su misura legno massello incastri"),
    "blacksmith": ("1. Ferramenta, Vernici, Elettricità & Riparazioni Casa", "Fabbro e Lavorazione Ferro", "inferriate cancelli saldature ringhiere ferro battuto"),
    "metal_construction": ("1. Ferramenta, Vernici, Elettricità & Riparazioni Casa", "Carpenteria Metallica", "lavorazione metalli alluminio acciaio"),
    "stonemason": ("1. Ferramenta, Vernici, Elettricità & Riparazioni Casa", "Marmista e Lavorazione Ardesia", "marmo ardesia ligure piani cucina soglie"),
    "trade": ("1. Ferramenta, Vernici, Elettricità & Riparazioni Casa", "Forniture Edili, Idrauliche e Tecniche", "materiale edile piastrelle tubazioni cantieri"),
    "security": ("1. Ferramenta, Vernici, Elettricità & Riparazioni Casa", "Sistemi di Sicurezza, Allarmi e Casseforti", "antifurto videosorveglianza serrature sicurezza"),
    "gas": ("1. Ferramenta, Vernici, Elettricità & Riparazioni Casa", "Bombole Gas e Forniture Tecniche", "bombole gpl propano campeggio"),

    # 2. Elettronica, Informatica, Telefonia, Hi-Fi, Elettrodomestici & Riparazioni Tech
    "electronics": ("2. Elettronica, PC, Ricambi Elettrodomestici & Riparazioni Tech", "Elettronica, Componenti ed Elettrodomestici", "cavi alimentatori batterie piccoli elettrodomestici ricambi"),
    "electronics_repair": ("2. Elettronica, PC, Ricambi Elettrodomestici & Riparazioni Tech", "Laboratorio Riparazione Elettronica, TV e Schede", "riparazione schede elettroniche tv saldatura condensatori"),
    "computer": ("2. Elettronica, PC, Ricambi Elettrodomestici & Riparazioni Tech", "Negozio e Assistenza Computer / Informatica", "riparazione pc notebook ssd ram alimentatori assemblaggio"),
    "mobile_phone": ("2. Elettronica, PC, Ricambi Elettrodomestici & Riparazioni Tech", "Telefonia e Riparazione Smartphone / Vetri", "cambio schermo batteria smartphone cover pellicole"),
    "mobile_phone_accessories": ("2. Elettronica, PC, Ricambi Elettrodomestici & Riparazioni Tech", "Accessori Smartphone e Cavi", "caricabatterie cavi usb cover"),
    "telecommunication": ("2. Elettronica, PC, Ricambi Elettrodomestici & Riparazioni Tech", "Telefonia e Connettività", "sim telefoni fibra modem"),
    "appliance": ("2. Elettronica, PC, Ricambi Elettrodomestici & Riparazioni Tech", "Elettrodomestici e Ricambi Lavatrici/Frigo", "lavatrici frigoriferi forni ricambi resistenze pompe"),
    "hifi": ("2. Elettronica, PC, Ricambi Elettrodomestici & Riparazioni Tech", "Alta Fedeltà (Hi-Fi), Giradischi e Audio", "amplificatori casse acustiche giradischi puntine cavi audio"),
    "radiotechnics": ("2. Elettronica, PC, Ricambi Elettrodomestici & Riparazioni Tech", "Radiotecnica e Componentistica Elettronica", "transistor resistenze antenne radioamatori"),
    "printer_ink": ("2. Elettronica, PC, Ricambi Elettrodomestici & Riparazioni Tech", "Cartucce, Toner e Inchiostri Stampanti", "toner cartucce stampanti carta fotografica"),
    "photo": ("2. Elettronica, PC, Ricambi Elettrodomestici & Riparazioni Tech", "Fotografo, Sviluppo Rullini e Fototessere", "fototessera stampa foto rullini analogici cornici"),
    "photographer": ("2. Elettronica, PC, Ricambi Elettrodomestici & Riparazioni Tech", "Studio Fotografico e Stampa", "servizi fotografici fototessere restauro foto"),
    "camera": ("2. Elettronica, PC, Ricambi Elettrodomestici & Riparazioni Tech", "Fotocamere, Obiettivi e Usato Fotografico", "macchine fotografiche obiettivi reflex"),
    "video_games": ("2. Elettronica, PC, Ricambi Elettrodomestici & Riparazioni Tech", "Videogiochi, Console e Retrogaming", "console controller giochi usati"),

    # 3. Merceria, Sartoria, Tessuti, Calzolai, Pelletteria & Abbigliamento
    "haberdashery": ("3. Merceria, Sartoria, Calzolai, Tessuti & Abbigliamento", "Merceria (Bottoni, Cerniere, Filati, Lana)", "bottoni cerniere lampo fili aghi lana uncinetto nastri toppe"),
    "sewing": ("3. Merceria, Sartoria, Calzolai, Tessuti & Abbigliamento", "Cucito, Filati, Lana e Macchine per Cucire", "macchine da cucire Singer filati gomitoli lana ricamo"),
    "fabric": ("3. Merceria, Sartoria, Calzolai, Tessuti & Abbigliamento", "Tessuti a Metraggio e Stoffe", "stoffe scampoli cotone lino velluto fodere"),
    "textiles": ("3. Merceria, Sartoria, Calzolai, Tessuti & Abbigliamento", "Tessuti e Tendaggi", "tessuti biancheria stoffe"),
    "tailor": ("3. Merceria, Sartoria, Calzolai, Tessuti & Abbigliamento", "Sartoria, Orli e Riparazioni Sartoriali", "sarto orli cambio cerniere stringere abiti camicie su misura"),
    "shoe_repair": ("3. Merceria, Sartoria, Calzolai, Tessuti & Abbigliamento", "Calzolaio e Riparazione Scarpe/Borse", "risuolatura tacchi suole Vibram cucitura scarpe cinture"),
    "shoemaker": ("3. Merceria, Sartoria, Calzolai, Tessuti & Abbigliamento", "Calzolaio Artigiano", "riparazione calzature cuoio"),
    "leather": ("3. Merceria, Sartoria, Calzolai, Tessuti & Abbigliamento", "Pelletteria e Lavorazione Cuoio", "borse cinture portafogli pelle cuoio"),
    "bag": ("3. Merceria, Sartoria, Calzolai, Tessuti & Abbigliamento", "Borse, Valigeria e Zaini", "valigie trolley zaini borse"),
    "shoes": ("3. Merceria, Sartoria, Calzolai, Tessuti & Abbigliamento", "Calzature e Scarpe", "scarpe stivali sandali pantofole"),
    "clothes": ("3. Merceria, Sartoria, Calzolai, Tessuti & Abbigliamento", "Abbigliamento e Boutique", "vestiti camicie pantaloni giacche maglieria"),
    "baby_goods": ("3. Merceria, Sartoria, Calzolai, Tessuti & Abbigliamento", "Articoli per Neonati e Prima Infanzia", "passeggini carrozzine culle abbigliamento neonato"),
    "watches": ("3. Merceria, Sartoria, Calzolai, Tessuti & Abbigliamento", "Orologeria e Cambio Batterie/Cinturini", "orologi cambio pila cinturini revisione meccanica"),
    "clockmaker": ("3. Merceria, Sartoria, Calzolai, Tessuti & Abbigliamento", "Orologiaio Riparatore (Pendole e Polso)", "restauro orologi antichi pendole meccanismi"),
    "jewelry": ("3. Merceria, Sartoria, Calzolai, Tessuti & Abbigliamento", "Oreficeria, Gioielleria e Filigrana", "anelli collane riparazione gioielli argento oro filigrana di Campo Ligure"),
    "jeweller": ("3. Merceria, Sartoria, Calzolai, Tessuti & Abbigliamento", "Laboratorio Orafo", "creazione e riparazione gioielli incastonatura"),
    "laundry": ("3. Merceria, Sartoria, Calzolai, Tessuti & Abbigliamento", "Lavanderia e Stireria", "lavaggio piumoni tappeti camicie"),
    "dry_cleaning": ("3. Merceria, Sartoria, Calzolai, Tessuti & Abbigliamento", "Tintoria e Lavaggio a Secco", "lavaggio a secco abiti cappotti"),

    # 4. Casa, Casalinghi, Arredo, Tappezzeria, Pulizia & Giardinaggio
    "houseware": ("4. Casalinghi, Tappezzeria, Arredo & Vivaismo", "Casalinghi, Pentole, Coltelleria e Accessori Cucina", "pentole padelle caffettiere ricambi moka guarnizioni barattoli vetro"),
    "cleaning_supplies": ("4. Casalinghi, Tappezzeria, Arredo & Vivaismo", "Detersivi alla Spina e Prodotti Pulizia", "detersivi sfusi saponi spugne"),
    "upholsterer": ("4. Casalinghi, Tappezzeria, Arredo & Vivaismo", "Tappezziere in Stoffa e Rifacimento Divani/Sedie", "rivestimento divani poltrone sedie gommapiuma cuscini"),
    "curtain": ("4. Casalinghi, Tappezzeria, Arredo & Vivaismo", "Tendaggi su Misura e Bastoni Tende", "tende binari bastoni tessuti arredo"),
    "carpet": ("4. Casalinghi, Tappezzeria, Arredo & Vivaismo", "Tappeti, Restauro e Lavaggio", "tappeti persiani orientali"),
    "household_linen": ("4. Casalinghi, Tappezzeria, Arredo & Vivaismo", "Biancheria per la Casa, Mezzari e Tovagliati", "lenzuola asciugamani tovaglie mezzari genovesi"),
    "bed": ("4. Casalinghi, Tappezzeria, Arredo & Vivaismo", "Materassi, Reti e Cuscini", "materassi doghe guanciali"),
    "furniture": ("4. Casalinghi, Tappezzeria, Arredo & Vivaismo", "Mobili e Arredamento", "mobili tavoli sedie armadi librerie"),
    "kitchen": ("4. Casalinghi, Tappezzeria, Arredo & Vivaismo", "Cucine e Arredo Cucina", "cucine componibili top elettrodomestici"),
    "bathroom_furnishing": ("4. Casalinghi, Tappezzeria, Arredo & Vivaismo", "Arredo Bagno, Rubinetteria e Sanitari", "sanitari rubinetti box doccia piastrelle"),
    "lighting": ("4. Casalinghi, Tappezzeria, Arredo & Vivaismo", "Illuminazione, Lampadari e Paralumi", "lampadari applique portalampade paralumi"),
    "interior_decoration": ("4. Casalinghi, Tappezzeria, Arredo & Vivaismo", "Decorazione d'Interni e Oggettistica", "carte da parati complementi arredo"),
    "frame": ("4. Casalinghi, Tappezzeria, Arredo & Vivaismo", "Corniciaio su Misura e Stampe", "cornici quadri passepartout tele"),
    "antiques": ("4. Casalinghi, Tappezzeria, Arredo & Vivaismo", "Antiquariato, Modernariato e Restauro", "mobili antichi stampe oggetti d'epoca"),
    "second_hand": ("4. Casalinghi, Tappezzeria, Arredo & Vivaismo", "Mercatino dell'Usato e Riuso", "usato vintage mobili libri oggetti"),
    "pottery": ("4. Casalinghi, Tappezzeria, Arredo & Vivaismo", "Ceramiche Artigianali e Terracotta", "piatti vasi maioliche"),
    "candles": ("4. Casalinghi, Tappezzeria, Arredo & Vivaismo", "Candele, Cere e Profumi Ambiente", "candele cera d'api incensi"),
    "florist": ("4. Casalinghi, Tappezzeria, Arredo & Vivaismo", "Fiorista e Piante", "fiori freschi piante vasi bouquet"),
    "garden_centre": ("4. Casalinghi, Tappezzeria, Arredo & Vivaismo", "Vivaio, Sementi, Terricci e Agraria", "piante da orto basilico terriccio vasi concimi"),
    "agrarian": ("4. Casalinghi, Tappezzeria, Arredo & Vivaismo", "Consorzio Agrario, Sementi e Attrezzi Agricoli", "sementi mangimi attrezzi orto uliveto"),
    "agricultural_engines": ("4. Casalinghi, Tappezzeria, Arredo & Vivaismo", "Macchine Agricole, Motoseghe e Decespugliatori", "riparazione motoseghe tagliaerba decespugliatori motoagricole"),

    # 5. Cartolerie, Librerie, Copisterie, Belle Arti, Musica, Giocattoli & Modellismo
    "stationery": ("5. Cartolerie, Librerie, Belle Arti, Musica & Modellismo", "Cartoleria, Cancelleria e Articoli Scuola/Ufficio", "quaderni penne matite carta regalo raccoglitori zaini"),
    "copyshop": ("5. Cartolerie, Librerie, Belle Arti, Musica & Modellismo", "Copisteria, Rilegatura Tesi e Stampe Grandi Formati", "fotocopie stampe pdf rilegatura tesi plastificazione"),
    "printing": ("5. Cartolerie, Librerie, Belle Arti, Musica & Modellismo", "Tipografia e Stampa Litografica", "biglietti da visita locandine timbri"),
    "plaques": ("5. Cartolerie, Librerie, Belle Arti, Musica & Modellismo", "Incisioni, Timbri, Targhe e Coppe", "targhe ottone timbri punzoni ceralacca"),
    "books": ("5. Cartolerie, Librerie, Belle Arti, Musica & Modellismo", "Libreria (Nuovo, Scolastico e Usato)", "libri romanzi saggi testi scolastici"),
    "comics": ("5. Cartolerie, Librerie, Belle Arti, Musica & Modellismo", "Fumetteria, Manga e Giochi da Tavolo", "fumetti manga comics carte collezionabili"),
    "newsagent": ("5. Cartolerie, Librerie, Belle Arti, Musica & Modellismo", "Edicola e Giornali", "quotidiani riviste figurine"),
    "art": ("5. Cartolerie, Librerie, Belle Arti, Musica & Modellismo", "Belle Arti, Colori ad Olio/Acquerello e Gallerie", "tele pennelli colori acrilici acquerelli"),
    "craft": ("5. Cartolerie, Librerie, Belle Arti, Musica & Modellismo", "Artigianato Artistico e Hobbistica", "materiali creativi legno ceramica"),
    "handicraft": ("5. Cartolerie, Librerie, Belle Arti, Musica & Modellismo", "Laboratorio Artigianale Ligure", "artigianato locale fatto a mano"),
    "musical_instrument": ("5. Cartolerie, Librerie, Belle Arti, Musica & Modellismo", "Strumenti Musicali, Corde, Spartiti e Liuteria", "chitarre corde plettri pianoforti spartiti riparazione strumenti"),
    "music": ("5. Cartolerie, Librerie, Belle Arti, Musica & Modellismo", "Dischi in Vinile, CD e Musica", "vinili lp cd musica"),
    "toys": ("5. Cartolerie, Librerie, Belle Arti, Musica & Modellismo", "Giocattoli, Costruzioni e Giochi Educativi", "giocattoli legno lego bambole"),
    "games": ("5. Cartolerie, Librerie, Belle Arti, Musica & Modellismo", "Giochi di Società, Scacchi e Ruolo", "giochi da tavolo wargame puzzle"),
    "model": ("5. Cartolerie, Librerie, Belle Arti, Musica & Modellismo", "Modellismo Statico, Ferroviario e Navale", "modellini trenini aeromodellismo vernici modellismo"),
    "collector": ("5. Cartolerie, Librerie, Belle Arti, Musica & Modellismo", "Collezionismo, Filatelia e Numismatica", "francobolli monete cartoline storiche"),
    "party": ("5. Cartolerie, Librerie, Belle Arti, Musica & Modellismo", "Articoli per Feste e Palloncini", "palloncini addobbi candeline"),
    "gift": ("5. Cartolerie, Librerie, Belle Arti, Musica & Modellismo", "Idee Regalo e Artigianato", "regali oggettistica"),

    # 6. Alimentari di Quartiere: Forni/Focaccerie, Pastifici, Drogherie, Macellerie, Pescherie & Enoteche
    "bakery": ("6. Botteghe Alimentari: Forni, Pastifici, Macellerie, Pescherie & Sfuso", "Panificio, Focacceria e Forno Genovese", "focaccia genovese pane fresco farinata grissini pandolce"),
    "pasta": ("6. Botteghe Alimentari: Forni, Pastifici, Macellerie, Pescherie & Sfuso", "Pastificio Artigianale, Pansoti, Trofie e Pesto", "pasta fresca ravioli pansoti trofie pesto salsa di noci"),
    "pastry": ("6. Botteghe Alimentari: Forni, Pastifici, Macellerie, Pescherie & Sfuso", "Pasticceria Artigianale", "torte pasticcini pandolce sacripantina canestrelli"),
    "confectionery": ("6. Botteghe Alimentari: Forni, Pastifici, Macellerie, Pescherie & Sfuso", "Confetteria, Cioccolateria e Dolciumi", "cioccolato confetti canditi caramelle"),
    "butcher": ("6. Botteghe Alimentari: Forni, Pastifici, Macellerie, Pescherie & Sfuso", "Macelleria, Polleria e Tripperia", "carne fresca salumi cima alla genovese"),
    "seafood": ("6. Botteghe Alimentari: Forni, Pastifici, Macellerie, Pescherie & Sfuso", "Pescheria e Mercato del Pesce", "pesce fresco acciughe gamberi stoccafisso baccalà"),
    "greengrocer": ("6. Botteghe Alimentari: Forni, Pastifici, Macellerie, Pescherie & Sfuso", "Fruttivendolo e Ortofrutta Locale", "frutta verdura basilico genovese dop"),
    "deli": ("6. Botteghe Alimentari: Forni, Pastifici, Macellerie, Pescherie & Sfuso", "Salumeria, Gastronomia, Rostiggieria e Sciamadde", "salumi formaggi torte salate verdure ripiene friggitoria"),
    "cheese": ("6. Botteghe Alimentari: Forni, Pastifici, Macellerie, Pescherie & Sfuso", "Formaggeria e Latticini (Prescinsêua e Formaggi di Valle)", "formaggi prescinseua ricotta san ste"),
    "dairy": ("6. Botteghe Alimentari: Forni, Pastifici, Macellerie, Pescherie & Sfuso", "Latteria e Caseificio", "latte fresco burro yogurt formaggi"),
    "coffee": ("6. Botteghe Alimentari: Forni, Pastifici, Macellerie, Pescherie & Sfuso", "Torrefazione Caffè in Grani e Macinato", "caffè in grani miscele arabica cialde"),
    "tea": ("6. Botteghe Alimentari: Forni, Pastifici, Macellerie, Pescherie & Sfuso", "Tè Sfusi, Infusi e Tisane", "tè verde nero infusi teiere"),
    "wine": ("6. Botteghe Alimentari: Forni, Pastifici, Macellerie, Pescherie & Sfuso", "Enoteca e Vino Sfuso", "vini liguri vermentino pigato bianchetta vino sfuso"),
    "winery": ("6. Botteghe Alimentari: Forni, Pastifici, Macellerie, Pescherie & Sfuso", "Cantina Vinicola e Produttore", "produzione vino locale"),
    "brewery": ("6. Botteghe Alimentari: Forni, Pastifici, Macellerie, Pescherie & Sfuso", "Birrificio Artigianale", "birra artigianale luppolo"),
    "beekeeper": ("6. Botteghe Alimentari: Forni, Pastifici, Macellerie, Pescherie & Sfuso", "Apicoltore e Miele Locale", "miele di castagno acacia propoli cera"),
    "farm": ("6. Botteghe Alimentari: Forni, Pastifici, Macellerie, Pescherie & Sfuso", "Azienda Agricola e Vendita Diretta Km0", "prodotti agricoli uova olio extravergine"),
    "health_food": ("6. Botteghe Alimentari: Forni, Pastifici, Macellerie, Pescherie & Sfuso", "Alimentazione Biologica e Sfusa", "prodotti bio cereali legumi sfusi"),
    "fair_trade": ("6. Botteghe Alimentari: Forni, Pastifici, Macellerie, Pescherie & Sfuso", "Bottega Commercio Equo e Solidale", "equosolidale spezie cacao artigianato"),
    "marketplace": ("6. Botteghe Alimentari: Forni, Pastifici, Macellerie, Pescherie & Sfuso", "Mercato Coperto Rionale", "banchi mercato frutta pesce carne formaggi"),
    "convenience": ("6. Botteghe Alimentari: Forni, Pastifici, Macellerie, Pescherie & Sfuso", "Minimarket e Alimentari di Paese", "alimentari pane latte generi di prima necessità"),
    "supermarket": ("6. Botteghe Alimentari: Forni, Pastifici, Macellerie, Pescherie & Sfuso", "Supermercato", "spesa alimentare"),

    # 7. Bici, Moto, Auto, Ricambi, Nautica, Pesca & Sport/Outdoor
    "bicycle": ("7. Ciclofficine, Ricambi Moto/Auto, Nautica, Pesca & Sport", "Negozio Biciclette e Ciclofficina Riparazioni", "riparazione bici camere d'aria copertoni freni cambio e-bike"),
    "bicycle_rental": ("7. Ciclofficine, Ricambi Moto/Auto, Nautica, Pesca & Sport", "Noleggio e Assistenza Biciclette", "noleggio bici tour"),
    "motorcycle": ("7. Ciclofficine, Ricambi Moto/Auto, Nautica, Pesca & Sport", "Concessionario e Officina Scooter/Moto", "scooter moto caschi tagliando"),
    "motorcycle_repair": ("7. Ciclofficine, Ricambi Moto/Auto, Nautica, Pesca & Sport", "Meccanico Moto e Scooter", "riparazione scooter freni gomme tagliando"),
    "motorcycle_parts": ("7. Ciclofficine, Ricambi Moto/Auto, Nautica, Pesca & Sport", "Ricambi e Accessori Moto/Scooter", "ricambi scooter batterie pastiglie freni caschi bauletti"),
    "helmet": ("7. Ciclofficine, Ricambi Moto/Auto, Nautica, Pesca & Sport", "Caschi e Abbigliamento Tecnico Moto", "caschi guanti giacche moto"),
    "car_parts": ("7. Ciclofficine, Ricambi Moto/Auto, Nautica, Pesca & Sport", "Autoricambi, Batterie,Tergicristalli e Olio Motore", "batteria auto spazzole tergicristallo lampadine olio filtri"),
    "car_repair": ("7. Ciclofficine, Ricambi Moto/Auto, Nautica, Pesca & Sport", "Autofficina, Meccanico ed Elettrauto", "meccanico elettrauto revisione tagliando"),
    "car_bodyshop": ("7. Ciclofficine, Ricambi Moto/Auto, Nautica, Pesca & Sport", "Carrozzeria", "riparazione carrozzeria verniciatura"),
    "tyres": ("7. Ciclofficine, Ricambi Moto/Auto, Nautica, Pesca & Sport", "Gommista e Riparazione Pneumatici", "gomme pneumatici convergenza foratura"),
    "ship_chandler": ("7. Ciclofficine, Ricambi Moto/Auto, Nautica, Pesca & Sport", "Forniture Nautiche (Ship Chandler), Cime e Inox", "cime corde moschettoni acciaio inox vernici antivegetative nautica"),
    "nautical": ("7. Ciclofficine, Ricambi Moto/Auto, Nautica, Pesca & Sport", "Accessori per la Nautica", "dotazioni bordo cartografia nautica"),
    "boat": ("7. Ciclofficine, Ricambi Moto/Auto, Nautica, Pesca & Sport", "Nautica e Imbarcazioni", "barche motori fuoribordo"),
    "boatbuilder": ("7. Ciclofficine, Ricambi Moto/Auto, Nautica, Pesca & Sport", "Cantiere Navale e Maestro d'Ascia", "restauro barche legno vetroresina"),
    "fishing": ("7. Ciclofficine, Ricambi Moto/Auto, Nautica, Pesca & Sport", "Articoli da Pesca, Esche Vive e Canne", "canne da pesca mulinelli ami lenze esche"),
    "scuba_diving": ("7. Ciclofficine, Ricambi Moto/Auto, Nautica, Pesca & Sport", "Subacquea, Mute e Ricarica Bombole", "maschere pinne mute erogatori sub"),
    "outdoor": ("7. Ciclofficine, Ricambi Moto/Auto, Nautica, Pesca & Sport", "Trekking, Montagna, Campeggio e Alpinismo", "scarponi zaini tende sacchi a pelo bastoncini"),
    "sports": ("7. Ciclofficine, Ricambi Moto/Auto, Nautica, Pesca & Sport", "Articoli e Abbigliamento Sportivo", "attrezzatura sportiva calcio tennis corsa nuoto"),

    # 8. Salute, Erboristerie, Ottici, Ortopedie, Animali & Cura Persona
    "pharmacy": ("8. Erboristerie, Farmacie, Ottici, Ortopedie & Animali", "Farmacia e Preparazioni Galeniche", "farmaci medicazioni galenica"),
    "herbalist": ("8. Erboristerie, Farmacie, Ottici, Ortopedie & Animali", "Erboristeria, Rimedi Naturali e Oli Essenziali", "erbe officinali tisane tinture madri oli essenziali integratori"),
    "optician": ("8. Erboristerie, Farmacie, Ottici, Ortopedie & Animali", "Ottico Optometrista e Lenti", "occhiali da vista lenti a contatto riparazione montature"),
    "optics": ("8. Erboristerie, Farmacie, Ottici, Ortopedie & Animali", "Ottica, Binocoli e Strumenti Ottici", "occhiali binocoli lenti d'ingrandimento"),
    "medical_supply": ("8. Erboristerie, Farmacie, Ottici, Ortopedie & Animali", "Ortopedia, Sanitaria e Ausili Medici", "tutori plantari su misura stampelle carrozzine misuratori pressione"),
    "hearing_aids": ("8. Erboristerie, Farmacie, Ottici, Ortopedie & Animali", "Apparecchi Acustici e Batterie", "apparecchi acustici pile"),
    "perfumery": ("8. Erboristerie, Farmacie, Ottici, Ortopedie & Animali", "Profumeria e Cosmesi", "profumi saponi creme"),
    "cosmetics": ("8. Erboristerie, Farmacie, Ottici, Ortopedie & Animali", "Cosmetici e Prodotti Cura Persona", "cosmetici trucco"),
    "chemist": ("8. Erboristerie, Farmacie, Ottici, Ortopedie & Animali", "Igiene Persona e Casa", "igiene saponi"),
    "hairdresser": ("8. Erboristerie, Farmacie, Ottici, Ortopedie & Animali", "Barbiere e Parrucchiere", "taglio capelli barba"),
    "beauty": ("8. Erboristerie, Farmacie, Ottici, Ortopedie & Animali", "Centro Estetico", "estetica benessere"),
    "pet": ("8. Erboristerie, Farmacie, Ottici, Ortopedie & Animali", "Negozio per Animali (Cibo, Guinzagli, Acquariologia)", "crocchette cucce guinzagli lettiere acquari pesci"),
    "pet_grooming": ("8. Erboristerie, Farmacie, Ottici, Ortopedie & Animali", "Toelettatura Cani e Gatti", "lavaggio tosatura cani"),
    "veterinary": ("8. Erboristerie, Farmacie, Ottici, Ortopedie & Animali", "Ambulatorio Veterinario", "veterinario cura animali"),
}

records = []
seen = set()

for el in raw_elems:
    tags = el.get("tags", {})
    name = (tags.get("name") or "").strip()
    if not name:
        continue

    lat = el.get("lat") or (el.get("center", {}).get("lat"))
    lon = el.get("lon") or (el.get("center", {}).get("lon"))

    raw_type = (tags.get("craft") or tags.get("shop") or tags.get("amenity") or tags.get("office") or "shop").split(";")[0].strip()

    # Determine taxonomy
    if raw_type in TAXONOMY:
        macro, subcat, kw = TAXONOMY[raw_type]
    else:
        # Infer from name if raw_type is generic ('yes', 'general', etc.)
        nl = name.lower()
        if any(w in nl for w in ("ferramenta", "chiavi", "serrature", "colori", "vernici", "idraul", "elettric")):
            macro, subcat, kw = TAXONOMY["hardware"]
        elif any(w in nl for w in ("merceria", "bottoni", "filati", "lane", "tessuti", "scampoli", "sartoria")):
            macro, subcat, kw = TAXONOMY["haberdashery"]
        elif any(w in nl for w in ("cartoleria", "copisteria", "timbri", "stampe", "libri", "libreria")):
            macro, subcat, kw = TAXONOMY["stationery"]
        elif any(w in nl for w in ("panificio", "focacceria", "forno", "pastificio", "pasticceria", "drogheria", "macelleria", "pescheria")):
            macro, subcat, kw = TAXONOMY["bakery"]
        elif any(w in nl for w in ("computer", "pc", "riparazioni", "elettronica", "ricambi")):
            macro, subcat, kw = TAXONOMY["electronics"]
        elif any(w in nl for w in ("bici", "cicli", "moto", "nautica", "pesca", "sport")):
            macro, subcat, kw = TAXONOMY["bicycle"]
        elif any(w in nl for w in ("casalinghi", "tappezz", "cornici", "fiori", "vivaio", "agraria")):
            macro, subcat, kw = TAXONOMY["houseware"]
        else:
            macro = "9. Altri Servizi di Prossimità, Tabacchi & Studi"
            subcat = f"Esercizio / Attività ({raw_type})"
            kw = raw_type

    comune, quartiere = resolve_comune_and_quartiere(lat, lon, tags)

    street = (tags.get("addr:street") or "").strip()
    housenumber = (tags.get("addr:housenumber") or "").strip()
    addr = f"{street} {housenumber}".strip() if street else (tags.get("addr:full") or "").strip()

    phone = (tags.get("phone") or tags.get("contact:phone") or tags.get("mobile") or "").strip()
    web = (tags.get("website") or tags.get("contact:website") or tags.get("url") or tags.get("facebook") or tags.get("contact:facebook") or tags.get("instagram") or "").strip()
    if web and not web.startswith("http") and "." in web:
        web = "https://" + web
    oh = (tags.get("opening_hours") or "").strip()
    brand = (tags.get("brand") or tags.get("operator") or "").strip()
    desc = (tags.get("description") or tags.get("note") or "").strip()

    # Check if independent or chain/GDO
    nl_check = f"{name.lower()} {brand.lower()}"
    is_chain = False
    for ch in CHAINS_GDO:
        # exact word or prefix check
        if f" {ch} " in f" {nl_check} " or nl_check.startswith(ch + " "):
            is_chain = True
            break
    if raw_type in ("supermarket", "mall", "department_store"):
        is_chain = True

    dedup_key = (comune.lower(), name.lower(), street.lower(), raw_type)
    if dedup_key in seen:
        continue
    seen.add(dedup_key)

    personaggio = ""
    if street and (comune.lower(), street.lower()) in person_by_street:
        personaggio = person_by_street[(comune.lower(), street.lower())]

    records.append({
        "comune": comune,
        "quartiere_o_zona": quartiere,
        "nome": name,
        "macro_settore": macro,
        "categoria_specifica": subcat,
        "tag_osm": raw_type,
        "indipendente": not is_chain,
        "indirizzo": addr,
        "telefono": phone,
        "sito_o_social": web,
        "orari": oh,
        "cosa_trovi_qui": desc if desc else kw,
        "personaggio_via": personaggio,
        "lat": round(lat, 5) if lat else None,
        "lon": round(lon, 5) if lon else None
    })

# Also inject the hyper-specialized historical workshops if any weren't already matched with full details
SPECIAL_ARTISANS = [
    ("Genova", "Genova — Centro Storico (Molo / Maddalena / Prè)", "G.M. Luico — Il Re del Sughero", "4. Casalinghi, Tappezzeria, Arredo & Vivaismo", "Artigianato del Sughero e Tappi su Misura", "Salita Santa Caterina 17r", "010 589493", "https://www.botteghestorichegenova.it", "Mar-Sab 09:00-12:30, 15:30-19:00", "tappi sughero su misura damigiane bottiglie galleggianti pesca corteccia presepe isolanti"),
    ("Genova", "Genova — Centro Storico (Molo / Maddalena / Prè)", "Drogheria Torielli", "6. Botteghe Alimentari: Forni, Pastifici, Macellerie, Pescherie & Sfuso", "Drogheria, Spezie Sfuse, Cere e Gomma Arabica", "Via di San Bernardo 32r", "010 2468359", "https://www.botteghestorichegenova.it", "Mar-Sab 09:00-13:00, 15:30-19:30", "spezie sfuse tè pregiati incensi resine cera d'api gomma arabica vaniglia"),
    ("Genova", "Genova — Centro Storico (Molo / Maddalena / Prè)", "Busellato Incisioni, Timbri e Targhe", "5. Cartolerie, Librerie, Belle Arti, Musica & Modellismo", "Incisioni, Timbri, Targhe Ottone e Ceralacca", "Via al Ponte Reale 3r", "010 2470939", "https://www.busellato.it", "Lun-Ven 09:00-12:30, 14:30-18:30", "timbri targhe ottone incise punzoni sigilli ceralacca"),
    ("Genova", "Genova — Centro Storico (Molo / Maddalena / Prè)", "Giovanni Rivara fu Luigi — Mezzari e Tele", "4. Casalinghi, Tappezzeria, Arredo & Vivaismo", "Tessuti Lino, Cotone, Blue Jeans Storico e Mezzari", "Piazza San Lorenzo 36r", "010 2471115", "https://www.botteghestorichegenova.it", "Mar-Sab 09:30-12:30, 15:30-19:00", "mezzari genovesi teli arredo tela jeans tovaglie cotone lino"),
    ("Genova", "Genova — Castelletto / Principe / Oregina", "Antica Farmacia Sant'Anna dei Frati Carmelitani", "8. Erboristerie, Farmacie, Ottici, Ortopedie & Animali", "Spezieria ed Erboristeria Conventuale", "Piazza Sant'Anna 8r", "010 2513285", "https://www.erboristeriadeifrati.it", "Lun-Ven 08:30-12:30, 15:30-19:00; Sab 08:30-12:30", "rimedi galenici tisane miele sciroppo rose acqua di melissa"),
]
for com, qz, nm, mac, sub, ad, tel, wb, oh, kw in SPECIAL_ARTISANS:
    records.append({
        "comune": com, "quartiere_o_zona": qz, "nome": nm, "macro_settore": mac,
        "categoria_specifica": sub, "tag_osm": "craft", "indipendente": True,
        "indirizzo": ad, "telefono": tel, "sito_o_social": wb, "orari": oh,
        "cosa_trovi_qui": kw, "personaggio_via": "", "lat": 44.408, "lon": 8.932
    })

# Sort records: independent first, then those with address/phone/website/hours, then alphabetically
def rec_sort(x):
    s = 0
    if x["indipendente"]: s -= 10
    if x["indirizzo"]: s -= 3
    if x["telefono"]: s -= 4
    if x["sito_o_social"]: s -= 4
    if x["orari"]: s -= 3
    return (s, x["comune"], x["nome"])

records.sort(key=rec_sort)

with open(f"{_DATA_DIR}/esercenti_genova_provincia_db.json", "w", encoding="utf-8") as f:
    json.dump(records, f, indent=2, ensure_ascii=False)

with open(f"{_DATA_DIR}/esercenti_genova_provincia_db.csv", "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(records[0].keys()))
    writer.writeheader()
    writer.writerows(records)

indep_count = sum(1 for r in records if r["indipendente"])
print(f"Saved {len(records)} total businesses ({indep_count} independent / non-GDO)!")
by_m = defaultdict(int)
for r in records:
    by_m[r["macro_settore"]] += 1
for k in sorted(by_m):
    print(f"  {k}: {by_m[k]}")
