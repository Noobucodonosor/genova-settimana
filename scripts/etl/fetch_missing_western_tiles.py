import urllib.request
import urllib.parse
import json
import time
import os as _os
_DATA_DIR = _os.environ.get("GENOVA_DATA_DIR") or _os.path.dirname(_os.path.abspath(__file__))

with open(f"{_DATA_DIR}/osm_esercenti_provincia_raw.json") as f:
    existing = json.load(f).get("elements", [])

all_elements = {f"{el['type']}_{el['id']}": el for el in existing}
print("Loaded existing elements:", len(all_elements))

# Split the 3 missing western/central regions into smaller, super-fast sub-tiles
SUB_TILES = [
    ("Ponente_Riviera_Cogoleto_Arenzano_Voltri", 44.36, 8.55, 44.45, 8.80),
    ("Valle_Stura_Masone_Campo_Rossiglione", 44.45, 8.55, 44.62, 8.80),
    ("Genova_Pegli_Sestri_Cornigliano", 44.38, 8.80, 44.45, 8.89),
    ("Val_Polcevera_Rivarolo_Bolzaneto_Pontedecimo", 44.43, 8.85, 44.54, 8.94),
    ("Genova_Sampierdarena_Dinegro", 44.40, 8.88, 44.43, 8.92),
    ("Genova_Centro_Storico_Porto_Carignano", 44.39, 8.92, 44.415, 8.945),
    ("Genova_Castelletto_Brignole_Marassi_Staglieno", 44.405, 8.935, 44.46, 8.97),
    ("Genova_Foce_Albaro_SanMartino_Sturla", 44.385, 8.945, 44.415, 8.995),
    ("Genova_Quarto_Quinto_Nervi_ValBisagno", 44.37, 8.985, 44.48, 9.06),
]

ep = "https://maps.mail.ru/osm/tools/overpass/api/interpreter"

for name, lat1, lon1, lat2, lon2 in SUB_TILES:
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
    for attempt in range(2):
        try:
            req = urllib.request.Request(
                ep,
                data=urllib.parse.urlencode({"data": query}).encode("utf-8"),
                headers={"User-Agent": "GenovaEsercenti/2.1"}
            )
            with urllib.request.urlopen(req, timeout=28) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                elems = data.get("elements", [])
                for el in elems:
                    all_elements[f"{el['type']}_{el['id']}"] = el
                print(f"[OK] {name}: {len(elems)} elements (Total unique: {len(all_elements)})")
                break
        except Exception as e:
            print(f"  [Retry {attempt+1}] {name}: {e}")
            time.sleep(1.5)
    time.sleep(0.3)

with open(f"{_DATA_DIR}/osm_esercenti_provincia_raw.json", "w", encoding="utf-8") as f:
    json.dump({"elements": list(all_elements.values())}, f, ensure_ascii=False)

print("COMPLETE PROVINCE ESERCENTI TOTAL:", len(all_elements))
