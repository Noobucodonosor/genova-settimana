import json
import csv
import glob
import os
import re
from collections import defaultdict

# Load our base classification rules
import sys
sys.path.append(_DATA_DIR)
import build_complete_dataset as bcd
import os as _os
_DATA_DIR = _os.environ.get("GENOVA_DATA_DIR") or _os.path.dirname(_os.path.abspath(__file__))

with open(f"{_DATA_DIR}/comuni_provincia_genova.json") as f:
    comuni_list = json.load(f)
ALL_67_COMUNI = {c["name"]: c for c in comuni_list}

# 1. Collect all raw place names per municipality from:
#    a) 39 OSM municipality files in <repo-root>/comuni_raw/*.json
#    b) 6,788 Wikidata items in <repo-root>/wikidata_all_provincia_items.json
#    c) 2,594 Wikidata P6375 postal addresses in <repo-root>/wikidata_addresses_provincia.json
#    d) 927 Wikidata P138 records in <repo-root>/wikidata_p138_provincia.json
#    e) Wikipedia full texts for the 28 municipalities in <repo-root>/wiki_28_comuni.json

places_by_comune = defaultdict(lambda: defaultdict(dict))

# Load Wikidata P138 province lookup
with open(f"{_DATA_DIR}/wikidata_p138_provincia.json") as f:
    wd_p138_prov = json.load(f)

wd_prov_lookup = {}
for b in wd_p138_prov:
    label = b.get("itemLabel", {}).get("value", "").strip()
    person = b.get("namedAfterLabel", {}).get("value", "").strip()
    desc = b.get("namedAfterDesc", {}).get("value", "").strip()
    comune = b.get("comuneLabel", {}).get("value", "").strip()
    if label and person:
        if person.lower() not in {"polcevera", "bisagno", "condotte d'acqua", "genova", "tigullio", "scrivia", "trebbia", "aveto", "stura", "lavagna"}:
            wd_prov_lookup[label.lower()] = (person, desc)
            if comune in ALL_67_COMUNI:
                places_by_comune[comune][label]["wd_person"] = (person, desc)

# Merge into bcd.wd_lookup so classify_place uses it automatically
bcd.wd_lookup.update(wd_prov_lookup)

# Load 39 OSM files
for rf in sorted(glob.glob(f"{_DATA_DIR}/comuni_raw/*.json")):
    cname = os.path.basename(rf)[:-5].replace("_", " ")
    # Normalize Sant'Olcese / etc. if needed
    matched_c = cname
    for real_c in ALL_67_COMUNI:
        if real_c.replace(" ", "_") == os.path.basename(rf)[:-5]:
            matched_c = real_c
            break
    with open(rf) as f:
        data = json.load(f)
    for el in data.get("elements", []):
        tags = el.get("tags", {})
        name = tags.get("name", "").strip()
        if not name:
            continue
        for k, v in tags.items():
            if k not in places_by_comune[matched_c][name]:
                places_by_comune[matched_c][name][k] = v

# Load 6,788 Wikidata items across the 67 municipalities
with open(f"{_DATA_DIR}/wikidata_all_provincia_items.json") as f:
    wd_all = json.load(f)

for b in wd_all:
    cname = b.get("comuneLabel", {}).get("value", "").strip()
    if cname not in ALL_67_COMUNI:
        continue
    label = b.get("itemLabel", {}).get("value", "").strip()
    if not label or label.startswith("Q"):
        continue
    # Capitalize first letter if lowercase (e.g. "piazza Cavour" -> "Piazza Cavour", "chiesa di San Siro" -> "Chiesa di San Siro")
    label_norm = label[0].upper() + label[1:] if label else label
    named_after = b.get("namedAfterLabel", {}).get("value", "").strip()
    named_desc = b.get("namedAfterDesc", {}).get("value", "").strip()
    inst = b.get("instanceOfLabel", {}).get("value", "").strip()
    if named_after and not named_after.startswith("Q"):
        bcd.wd_lookup[label_norm.lower()] = (named_after, named_desc or inst)
    if label_norm not in places_by_comune[cname]:
        places_by_comune[cname][label_norm] = {"name": label_norm, "instance_of": inst}

# Load 2,594 Wikidata P6375 street addresses
with open(f"{_DATA_DIR}/wikidata_addresses_provincia.json") as f:
    wd_addrs = json.load(f)

for b in wd_addrs:
    cname = b.get("comuneLabel", {}).get("value", "").strip()
    if cname not in ALL_67_COMUNI:
        continue
    addr = b.get("address", {}).get("value", "").strip()
    item_label = b.get("itemLabel", {}).get("value", "").strip()
    if item_label and not item_label.startswith("Q"):
        il_norm = item_label[0].upper() + item_label[1:]
        if il_norm not in places_by_comune[cname]:
            places_by_comune[cname][il_norm] = {"name": il_norm}
    # Extract street/square name from address (e.g., "Via Giuseppe Mazzini, 12 - Recco" -> "Via Giuseppe Mazzini")
    m = re.match(r"^((?:Via|Piazza|Piazzale|Piazzetta|Corso|Viale|Largo|Salita|Vico|Calata|Molo|Lungomare|Passeggiata|Ponte|Villa|Palazzo|Castello)\s+[^,\d\-–(]+)", addr, flags=re.IGNORECASE)
    if m:
        st_name = m.group(1).strip()
        st_name = st_name[0].upper() + st_name[1:]
        if st_name not in places_by_comune[cname]:
            places_by_comune[cname][st_name] = {"name": st_name}

# Parse Wikipedia articles for the 28 municipalities to extract streets, squares, palaces, villas, castles, churches, sanctuaries
with open(f"{_DATA_DIR}/wiki_28_comuni.json") as f:
    wiki_28 = json.load(f)

PATTERN_URBAN = re.compile(
    r"\b((?:Via|Piazza|Piazzale|Piazzetta|Corso|Viale|Largo|Salita|Vico|Calata|Molo|Lungomare|Passeggiata|Ponte|Galleria|Villa|Palazzo|Castello|Forte|Torre|Teatro|Museo|Biblioteca|Ospedale|Stadio|Giardini|Parco|Chiesa|Basilica|Santuario|Oratorio|Abbazia|Convento|Monumento)\s+(?:(?:di|del|della|dei|degli|delle| a| al| alla|San|Sant'|Santa|Santi|Padre|Don|Fra|Frà|Duca|Principe|Conte|Marchese|Capitano|Generale|Ammiraglio)\s+)*[A-ZÀÈÉÌÒÙ][a-zàèéìòù']+(?:\s+[A-ZÀÈÉÌÒÙa-zàèéìòù']+){0,3})"
)

for cname, text in wiki_28.items():
    if cname not in ALL_67_COMUNI:
        continue
    # Clean wiki markup brackets
    clean_text = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", text)
    clean_text = re.sub(r"'''|''", "", clean_text)
    for m in PATTERN_URBAN.finditer(clean_text):
        cand = m.group(1).strip()
        # Trim trailing stop words
        cand = re.sub(r"\s+(?:e|o|nel|nella|in|con|del|della|dove|che|fu|venne|costruito|situato|dedicato|intitolato)$", "", cand, flags=re.IGNORECASE).strip()
        cand_norm = cand[0].upper() + cand[1:]
        if len(cand_norm) > 6 and cand_norm not in places_by_comune[cname]:
            places_by_comune[cname][cand_norm] = {"name": cand_norm}

# Also add well-known historical streets/squares/landmarks for key coastal & inland municipalities in the 28 if not yet in wiki text
CURATED_PROVINCE_ADDITIONS = {
    "Portofino": [
        "Molo Umberto I", "Piazza Martiri dell'Olivetta", "Via Duca degli Abruzzi", "Castello Brown",
        "Chiesa di San Martino", "Chiesa di San Giorgio", "Oratorio di Santa Maria Assunta", "Villa Altachiara"
    ],
    "Recco": [
        "Piazza Nicoloso da Recco", "Lungomare Bettolo", "Via Giuseppe Verdi", "Via Camillo Benso Cavour",
        "Via Guglielmo Marconi", "Via Biagio Assereto", "Via San Francesco", "Piazza San Giovanni Bono",
        "Santuario di Nostra Signora del Suffragio", "Via Pisa", "Via Vastato"
    ],
    "Sestri Levante": [
        "Viale Giuseppe Mazzini", "Via XXV Aprile", "Piazza Giacomo Matteotti", "Corso Cristoforo Colombo",
        "Galleria Rizzi", "Palazzo Fascie Rossi", "Palazzo Durazzo-Pallavicini", "Villa Brignole-Balbi",
        "Castello Gualino", "Chiesa di San Nicolò dell'Isola", "Basilica di Santa Maria di Nazareth",
        "Via Eraldo Fico", "Piazza Francesco Bo", "Lungomare Giovanni Descalzo", "Via Vincenzo Fascie"
    ],
    "Moneglia": [
        "Corso Libero Longhi", "Via Vittorio Emanuele", "Piazza Gio Bono Tasso", "Via Luca Cambiaso",
        "Fortezza di Villafranca", "Castello di Monleone", "Chiesa di San Giorgio", "Chiesa di Santa Croce",
        "Oratorio dei Disciplinati", "Casa natale di Luca Cambiaso"
    ],
    "Zoagli": [
        "Piazza San Martino", "Via Giuseppe Mazzini", "Via Giuseppe Garibaldi", "Passeggiata Canevaro",
        "Castello Canevaro", "Villa Vicini", "Torre Saracena", "Chiesa di San Pantaleo"
    ],
    "Sori": [
        "Via Giuseppe Garibaldi", "Via Cristoforo Colombo", "Via Caorsi", "Piazza Edmondo De Amicis",
        "Via Antonio Stagno", "Chiesa di Santa Margherita", "Oratorio di Sant'Erasmo"
    ],
    "Pieve Ligure": [
        "Piazzale San Michele", "Via Roma", "Scalinata Massone", "Castello Cirla",
        "Chiesa di San Michele Arcangelo", "Oratorio di Sant'Antonio Abate"
    ],
    "Sant'Olcese": [
        "Piazza Guglielmo Marconi", "Via Antonio Gramsci", "Via Giacomo Matteotti", "Villa Serra di Comago",
        "Forte Diamante", "Chiesa di Sant'Olcese"
    ],
    "Serra Riccò": [
        "Via Medicina", "Piazza Carlo Canepa", "Castello di San Cipriano", "Santuario di Nostra Signora di Costantinopoli",
        "Chiesa di San Lorenzo", "Chiesa di San Cipriano e Santa Giustina"
    ],
    "Ronco Scrivia": [
        "Corso Italia", "Via Giuseppe Mazzini", "Via Guglielmo Marconi", "Piazza della Vittoria",
        "Castello di Borgo Fornari", "Chiesa di San Martino"
    ],
    "Rossiglione": [
        "Piazza Guglielmo Marconi", "Via Giuseppe Garibaldi", "Via Roma", "Via Caduti della Libertà",
        "Palazzo Pizzorni", "Chiesa di Santa Caterina"
    ],
    "Montoggio": [
        "Via Roma", "Piazza Balilla", "Castello dei Fieschi", "Chiesa di San Giovanni Decollato"
    ],
    "Santo Stefano d'Aveto": [
        "Piazza del Popolo", "Via Guglielmo Marconi", "Castello Malaspina-Doria", "Santuario di Nostra Signora di Guadalupe"
    ],
    "Uscio": [
        "Piazza Giacomo Matteotti", "Via Vittorio Veneto", "Via Roma", "Pieve di Sant'Ambrogio"
    ]
}

for cname, items in CURATED_PROVINCE_ADDITIONS.items():
    for it in items:
        if it not in places_by_comune[cname]:
            places_by_comune[cname][it] = {"name": it}

# Now run classification across all 67 municipalities
all_results = []
comune_counts = defaultdict(int)

for cname in sorted(ALL_67_COMUNI.keys()):
    c_places = places_by_comune[cname]
    for place_name in sorted(c_places.keys()):
        tags = c_places[place_name]
        ok, person, desc, prefix = bcd.classify_place(place_name, tags)
        if ok:
            rec = {
                "comune": cname,
                "toponimo": place_name,
                "tipo": prefix,
                "personaggio_o_casata": person,
                "descrizione_categoria": desc
            }
            all_results.append(rec)
            comune_counts[cname] += 1

print("TOTAL EXTRACTED ACROSS ALL 67 MUNICIPALITIES OF GENOVA PROVINCE:", len(all_results))
print("Municipalities with extracted person-named places:", len(comune_counts), "/ 67")

# Save JSON, CSV, and Markdown
with open(f"{_DATA_DIR}/toponimi_personaggi_provincia_genova.json", "w", encoding="utf-8") as f:
    json.dump(all_results, f, indent=2, ensure_ascii=False)

with open(f"{_DATA_DIR}/toponimi_personaggi_provincia_genova.csv", "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["comune", "toponimo", "tipo", "personaggio_o_casata", "descrizione_categoria"])
    writer.writeheader()
    writer.writerows(all_results)

with open(f"{_DATA_DIR}/elenco_integrale_provincia_genova.md", "w", encoding="utf-8") as f:
    f.write("# Censimento Integrale dei Toponimi della Provincia / Città Metropolitana di Genova (67 Comuni)\n\n")
    f.write(f"**Totale luoghi intitolati a personaggi o casate nell'intera Provincia di Genova:** `{len(all_results)}` distribuiti sui **67 Comuni**.\n\n")
    
    f.write("## 1. Riepilogo Statistico per Comune (67 Comuni)\n\n")
    f.write("| Comune | Luoghi intitolati a Personaggi/Casate |\n| :--- | :---: |\n")
    for cname, cnt in sorted(comune_counts.items(), key=lambda x: (-x[1], x[0])):
        f.write(f"| **{cname}** | {cnt} |\n")
    f.write("\n---\n\n")

    f.write("## 2. Formato Insieme Globale `Insieme_Provincia_Genova = ( ... )`\n\n```text\nInsieme_Toponimi_Personaggi_Provincia_Genova = (\n  ")
    f.write(";\n  ".join(f"[{r['comune']}] {r['toponimo']} ({r['personaggio_o_casata']})" for r in all_results))
    f.write("\n);\n```\n\n---\n\n")

    f.write("## 3. Elenco Dettagliato Comune per Comune (Tutti i 67 Comuni)\n\n")
    for cname in sorted(ALL_67_COMUNI.keys()):
        c_recs = [r for r in all_results if r["comune"] == cname]
        f.write(f"### {cname} ({len(c_recs)} voci)\n\n")
        for r in c_recs:
            f.write(f"- **{r['toponimo']}** → *{r['personaggio_o_casata']}* ({r['descrizione_categoria']})\n")
        f.write("\n")

print("Top 20 municipalities by count:")
for cname, cnt in sorted(comune_counts.items(), key=lambda x: -x[1])[:20]:
    print(f"  {cname}: {cnt}")
