import urllib.request
import urllib.parse
import json
import time
import os
import os as _os
_DATA_DIR = _os.environ.get("GENOVA_DATA_DIR") or _os.path.dirname(_os.path.abspath(__file__))

with open(f"{_DATA_DIR}/comuni_provincia_genova.json") as f:
    comuni = json.load(f)

missing = [c for c in comuni if not os.path.exists(f"{_DATA_DIR}/comuni_raw/{c['name'].replace(' ', '_')}.json")]
print("Remaining municipalities to fetch:", len(missing))

ENDPOINTS = [
    "https://lz4.overpass-api.de/api/interpreter",
    "https://z.overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter"
]

for idx, c in enumerate(missing, 1):
    area_id = 3600000000 + int(c["osm_rel"])
    fname = f"{_DATA_DIR}/comuni_raw/{c['name'].replace(' ', '_')}.json"
    # Fast query without full-area unindexed scan
    query = f"""[out:json][timeout:45];
area({area_id})->.a;
(
  way["highway"]["name"](area.a);
  nwr["place"="square"]["name"](area.a);
  nwr["amenity"~"theatre|hospital|university|library|arts_centre|cinema|school|townhall"]["name"](area.a);
  nwr["leisure"~"stadium|park|garden|sports_centre"]["name"](area.a);
  nwr["historic"~"castle|monument|memorial|manor|palace|fort|tower"]["name"](area.a);
  nwr["tourism"~"museum|attraction"]["name"](area.a);
  nwr["man_made"~"bridge|pier"]["name"](area.a);
);
out tags;"""
    success = False
    for ep in ENDPOINTS:
        try:
            data = urllib.parse.urlencode({"data": query}).encode("utf-8")
            req = urllib.request.Request(ep, data=data, headers={"User-Agent": "GenovaProvinciaExtractor/1.0"})
            with urllib.request.urlopen(req, timeout=50) as resp:
                raw = resp.read()
                parsed = json.loads(raw)
                with open(fname, "wb") as out_f:
                    out_f.write(raw)
                print(f"[{idx}/{len(missing)}] {c['name']}: {len(parsed.get('elements', []))} elements (via {ep.split('/')[2]})")
                success = True
                break
        except Exception as e:
            print(f"  Retry {c['name']} on next endpoint ({e})")
            time.sleep(2)
    if not success:
        print(f"FAILED {c['name']}")
    time.sleep(1.0)

