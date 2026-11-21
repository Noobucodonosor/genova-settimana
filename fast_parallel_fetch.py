import urllib.request
import urllib.parse
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

with open("/Users/dany/genova/comuni_provincia_genova.json") as f:
    comuni = json.load(f)

missing = [c for c in comuni if not os.path.exists("/Users/dany/genova/comuni_raw/" + c["name"].replace(" ", "_") + ".json")]
print("Fetching remaining:", len(missing))

ENDPOINTS = [
    "https://overpass.private.coffee/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
    "https://z.overpass-api.de/api/interpreter"
]

def fetch_one(idx, c):
    area_id = 3600000000 + int(c["osm_rel"])
    fname = "/Users/dany/genova/comuni_raw/" + c["name"].replace(" ", "_") + ".json"
    query = f"""[out:json][timeout:30];
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
    # Rotate starting endpoint by idx so load is balanced across all 3 mirrors
    for attempt in range(3):
        ep = ENDPOINTS[(idx + attempt) % len(ENDPOINTS)]
        try:
            data = urllib.parse.urlencode({"data": query}).encode("utf-8")
            req = urllib.request.Request(ep, data=data, headers={"User-Agent": f"GenovaProvinciaExtractor/1.0-worker{idx%6}"})
            with urllib.request.urlopen(req, timeout=35) as resp:
                raw = resp.read()
                parsed = json.loads(raw)
                with open(fname, "wb") as out_f:
                    out_f.write(raw)
                return c["name"], len(parsed.get("elements", [])), ep.split("/")[2]
        except Exception as e:
            time.sleep(1.5)
    return c["name"], -1, "FAILED"

with ThreadPoolExecutor(max_workers=6) as ex:
    futures = [ex.submit(fetch_one, i, c) for i, c in enumerate(missing)]
    for fut in as_completed(futures):
        name, count, srv = fut.result()
        print(f"  {name}: {count} elements ({srv})")
