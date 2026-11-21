import urllib.request
import urllib.parse
import json
import time
import os as _os
_DATA_DIR = _os.environ.get("GENOVA_DATA_DIR") or _os.path.dirname(_os.path.abspath(__file__))

with open(f"{_DATA_DIR}/osm_esercenti_provincia_raw.json") as f:
    existing = json.load(f).get("elements", [])

all_elements = {f"{el['type']}_{el['id']}": el for el in existing}
print("Starting with:", len(all_elements))

FINAL_TILES = [
    ("Pegli_Multedo", 44.415, 8.80, 44.445, 8.845),
    ("Sestri_Ponente_Cornigliano", 44.405, 8.845, 44.44, 8.885),
    ("Sampierdarena_SanTeodoro", 44.40, 8.885, 44.425, 8.92),
    ("Quarto_Quinto_Nervi", 44.37, 8.985, 44.405, 9.06),
    ("ValBisagno_Molassana_Struppa_Bavari", 44.405, 8.97, 44.48, 9.06),
]

ENDPOINTS = [
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter"
]

for name, lat1, lon1, lat2, lon2 in FINAL_TILES:
    bbox = f"{lat1},{lon1},{lat2},{lon2}"
    query = f"""[out:json][timeout:25];
(
  node["shop"]["name"]({bbox});
  way["shop"]["name"]({bbox});
  node["craft"]["name"]({bbox});
  way["craft"]["name"]({bbox});
  node["amenity"="pharmacy"]["name"]({bbox});
  node["amenity"="marketplace"]["name"]({bbox});
  node["amenity"="car_repair"]["name"]({bbox});
  node["amenity"="veterinary"]["name"]({bbox});
);
out center tags;
"""
    for ep in ENDPOINTS:
        try:
            req = urllib.request.Request(
                ep,
                data=urllib.parse.urlencode({"data": query}).encode("utf-8"),
                headers={"User-Agent": "GenovaEsercenti/2.2"}
            )
            with urllib.request.urlopen(req, timeout=25) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                elems = data.get("elements", [])
                for el in elems:
                    all_elements[f"{el['type']}_{el['id']}"] = el
                print(f"[OK] {name}: {len(elems)} elements via {ep} (Total unique: {len(all_elements)})")
                break
        except Exception as e:
            print(f"  [Retry] {name} on {ep}: {e}")
            time.sleep(1)

with open(f"{_DATA_DIR}/osm_esercenti_provincia_raw.json", "w", encoding="utf-8") as f:
    json.dump({"elements": list(all_elements.values())}, f, ensure_ascii=False)

print("FINAL COMPLETE ESERCENTI TOTAL:", len(all_elements))
