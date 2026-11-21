import urllib.request
import json
import xml.etree.ElementTree as ET
import time

with open("/Users/dany/genova/osm_esercenti_provincia_raw.json") as f:
    existing = json.load(f).get("elements", [])

all_elements = {f"{el['type']}_{el['id']}": el for el in existing}
print("Starting with:", len(all_elements))

# Small bboxes for api.openstreetmap.org/api/0.6/map (lon_min, lat_min, lon_max, lat_max)
BBOXES = [
    ("Sestri_Ponente_Centro_ViaSestri", 8.842, 44.418, 8.865, 44.432),
    ("Cornigliano_Centro", 8.865, 44.410, 8.885, 44.425),
    ("Sampierdarena_ViaCantore_ViaRolando", 8.885, 44.406, 8.908, 44.420),
    ("Sampierdarena_Fiumara_SanTeodoro", 8.908, 44.406, 8.922, 44.422),
    ("Quarto_Quinto_Mare", 8.988, 44.382, 9.025, 44.398),
    ("Nervi_Centro_Capolungo", 9.025, 44.378, 9.058, 44.392),
    ("Molassana_Struppa_ValBisagno", 8.972, 44.435, 9.005, 44.462),
]

KEEP_AMENITIES = {"pharmacy", "marketplace", "veterinary", "car_repair", "bicycle_rental", "post_office", "copyshop", "internet_cafe", "coworking_space", "atelier"}

for label, lon1, lat1, lon2, lat2 in BBOXES:
    url = f"https://api.openstreetmap.org/api/0.6/map?bbox={lon1},{lat1},{lon2},{lat2}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "GenovaEsercenti/2.3"})
        with urllib.request.urlopen(req, timeout=25) as resp:
            raw_xml = resp.read()
        root = ET.fromstring(raw_xml)
        added = 0
        for elem in root:
            if elem.tag in ("node", "way"):
                tags = {t.attrib["k"]: t.attrib["v"] for t in elem.findall("tag")}
                if "name" not in tags:
                    continue
                if "shop" in tags or "craft" in tags or tags.get("amenity") in KEEP_AMENITIES:
                    el_obj = {
                        "type": elem.tag,
                        "id": int(elem.attrib.get("id", 0)),
                        "tags": tags
                    }
                    if "lat" in elem.attrib and "lon" in elem.attrib:
                        el_obj["lat"] = float(elem.attrib["lat"])
                        el_obj["lon"] = float(elem.attrib["lon"])
                    all_elements[f"{el_obj['type']}_{el_obj['id']}"] = el_obj
                    added += 1
        print(f"[OK] {label}: +{added} shops/crafts (Total unique: {len(all_elements)})")
    except Exception as e:
        print(f"[ERR] {label}: {e}")
    time.sleep(0.2)

with open("/Users/dany/genova/osm_esercenti_provincia_raw.json", "w", encoding="utf-8") as f:
    json.dump({"elements": list(all_elements.values())}, f, ensure_ascii=False)

print("FINAL COMPLETE ESERCENTI TOTAL:", len(all_elements))
