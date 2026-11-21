import urllib.request
import urllib.parse
import json
import time

# 6 geographic tiles covering the entire Metropolitan City of Genoa (from Cogoleto/Tiglieto to Moneglia/Santo Stefano d'Aveto)
TILES = [
    ("Ponente_e_Valli_Stura_Orba", 44.36, 8.55, 44.62, 8.85),
    ("Genova_Centro_Ponente_Polcevera", 44.38, 8.85, 44.52, 8.94),
    ("Genova_Centro_Levante_Bisagno", 44.37, 8.94, 44.50, 9.06),
    ("Val_Scrivia_e_Val_Trebbia", 44.48, 8.85, 44.68, 9.35),
    ("Golfo_Paradiso_e_Tigullio_Ovest", 44.28, 9.06, 44.48, 9.28),
    ("Tigullio_Est_Val_Fontanabuona_Aveto", 44.20, 9.28, 44.62, 9.56),
]

ENDPOINTS = [
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
    "https://overpass-api.de/api/interpreter"
]

all_elements = {}

for name, lat1, lon1, lat2, lon2 in TILES:
    bbox = f"{lat1},{lon1},{lat2},{lon2}"
    query = f"""[out:json][timeout:35];
(
  node["shop"]["name"]({bbox});
  way["shop"]["name"]({bbox});
  node["craft"]["name"]({bbox});
  way["craft"]["name"]({bbox});
  node["amenity"~"pharmacy|marketplace|veterinary|car_repair|bicycle_rental|post_office|copyshop|Internet_cafe|coworking_space|atelier|music_school|language_school|driving_school"]["name"]({bbox});
  way["amenity"~"pharmacy|marketplace|veterinary|car_repair|bicycle_rental|post_office|copyshop|Internet_cafe|coworking_space|atelier|music_school|language_school|driving_school"]["name"]({bbox});
  node["office"~"lawyer|accountant|architect|engineer|notary|IT|Coworking|employment_agency|insurance|estate_agent|travel_agent|therapist"]["name"]({bbox});
);
out center tags;
"""
    fetched = False
    for ep in ENDPOINTS:
        try:
            req = urllib.request.Request(
                ep,
                data=urllib.parse.urlencode({"data": query}).encode("utf-8"),
                headers={"User-Agent": "GenovaEsercenti/2.0"}
            )
            with urllib.request.urlopen(req, timeout=38) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                elems = data.get("elements", [])
                for el in elems:
                    key = f"{el['type']}_{el['id']}"
                    all_elements[key] = el
                print(f"[OK] {name}: {len(elems)} elements via {ep} (Total unique: {len(all_elements)})")
                fetched = True
                break
        except Exception as e:
            print(f"  [WARN] {name} failed on {ep}: {e}")
            time.sleep(1)
    if not fetched:
        print(f"[ERROR] Could not fetch {name}")
    time.sleep(0.5)

with open("/Users/dany/genova/osm_esercenti_provincia_raw.json", "w", encoding="utf-8") as f:
    json.dump({"elements": list(all_elements.values())}, f, ensure_ascii=False)

print("FINAL TOTAL UNIQUE ESERCENTI:", len(all_elements))
