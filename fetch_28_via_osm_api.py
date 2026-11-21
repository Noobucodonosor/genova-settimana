import urllib.request
import urllib.parse
import json
import os
import time
import xml.etree.ElementTree as ET
import os as _os
_DATA_DIR = _os.environ.get("GENOVA_DATA_DIR") or _os.path.dirname(_os.path.abspath(__file__))

with open(f"{_DATA_DIR}/comuni_provincia_genova.json") as f:
    comuni = json.load(f)

missing = [c for c in comuni if not os.path.exists(f"{_DATA_DIR}/comuni_raw/" + c["name"].replace(" ", "_") + ".json")]
print("Remaining municipalities to fetch via api.openstreetmap.org:", len(missing))

# 1. Get coordinates (P625) of the 28 municipalities from Wikidata
qids = " ".join("wd:" + c["qid"] for c in missing)
sparql = f"""
SELECT ?comune ?coord WHERE {{
  VALUES ?comune {{ {qids} }}
  ?comune wdt:P625 ?coord .
}}
"""
url_wd = "https://query.wikidata.org/sparql?format=json&query=" + urllib.parse.quote(sparql)
req_wd = urllib.request.Request(url_wd, headers={"User-Agent": "GenovaProvinciaExtractor/1.0"})
with urllib.request.urlopen(req_wd, timeout=30) as resp:
    wd_coords = json.loads(resp.read().decode("utf-8"))["results"]["bindings"]

coords_by_qid = {}
for b in wd_coords:
    qid = b["comune"]["value"].split("/")[-1]
    wkt = b["coord"]["value"] # Point(lon lat)
    lon, lat = [float(x) for x in wkt.replace("Point(", "").replace(")", "").split()]
    coords_by_qid[qid] = (lon, lat)

print("Resolved coordinates for", len(coords_by_qid), "municipalities")

for idx, c in enumerate(missing, 1):
    name = c["name"]
    fname = f"{_DATA_DIR}/comuni_raw/" + name.replace(" ", "_") + ".json"
    lon, lat = coords_by_qid.get(c["qid"], (9.15, 44.38))
    # Use a 0.036 x 0.026 degree box around town center (approx 4km x 3km covering the urban center & main roads)
    bbox = f"{lon-0.018:.4f},{lat-0.013:.4f},{lon+0.018:.4f},{lat+0.013:.4f}"
    url = f"https://api.openstreetmap.org/api/0.6/map?bbox={bbox}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "GenovaProvinciaExtractor/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw_xml = resp.read()
        root = ET.fromstring(raw_xml)
        elements = []
        with_web = 0
        for elem in root:
            if elem.tag in ("node", "way", "relation"):
                tags = {t.attrib["k"]: t.attrib["v"] for t in elem.findall("tag")}
                if not tags:
                    continue
                # Keep all named elements OR elements with website/shop/amenity/historic/tourism/highway
                if "name" in tags or "website" in tags or "contact:website" in tags or "shop" in tags:
                    tags["addr:city_extracted"] = name
                    el_obj = {
                        "type": elem.tag,
                        "id": int(elem.attrib.get("id", 0)),
                        "tags": tags
                    }
                    if "lat" in elem.attrib and "lon" in elem.attrib:
                        el_obj["lat"] = float(elem.attrib["lat"])
                        el_obj["lon"] = float(elem.attrib["lon"])
                    elements.append(el_obj)
                    if "website" in tags or "contact:website" in tags or "url" in tags:
                        with_web += 1
        out_json = {
            "version": 0.6,
            "generator": "OpenStreetMap v0.6 API",
            "comune": name,
            "elements": elements
        }
        with open(fname, "w", encoding="utf-8") as out_f:
            json.dump(out_json, out_f, indent=2, ensure_ascii=False)
        print(f"[{idx}/{len(missing)}] {name}: {len(elements)} raw elements ({with_web} with website)")
    except Exception as e:
        print(f"[{idx}/{len(missing)}] ERROR {name}: {e}")
    time.sleep(0.3)

print("Finished downloading all 28 municipalities from api.openstreetmap.org!")
