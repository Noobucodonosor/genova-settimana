import urllib.request, urllib.parse, json, os
import os as _os
_DATA_DIR = _os.environ.get("GENOVA_DATA_DIR") or _os.path.dirname(_os.path.abspath(__file__))

with open(f"{_DATA_DIR}/comuni_provincia_genova.json") as f:
    comuni = json.load(f)

missing = [c for c in comuni if not os.path.exists(f"{_DATA_DIR}/comuni_raw/" + c["name"].replace(" ", "_") + ".json")]
print("Remaining:", len(missing))

# Single foreach query on kumi.systems for all 28 missing!
area_ids = ",".join(str(3600000000 + int(c["osm_rel"])) for c in missing)
query = f"""[out:json][timeout:60];
area(id:{area_ids})->.all_areas;
.all_areas foreach -> .a (
  .a out tags;
  (
    way["highway"]["name"](area.a);
    nwr["place"="square"]["name"](area.a);
    nwr["amenity"~"theatre|hospital|university|library|arts_centre|cinema|school|townhall"]["name"](area.a);
    nwr["leisure"~"stadium|park|garden|sports_centre"]["name"](area.a);
    nwr["historic"~"castle|monument|memorial|manor|palace|fort|tower"]["name"](area.a);
    nwr["tourism"~"museum|attraction"]["name"](area.a);
    nwr["man_made"~"bridge|pier"]["name"](area.a);
  );
  out tags;
);"""

for url in ["https://overpass.kumi.systems/api/interpreter", "https://overpass.private.coffee/api/interpreter"]:
    try:
        data = urllib.parse.urlencode({"data": query}).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=65) as resp:
            raw = resp.read()
            parsed = json.loads(raw)
            print("SUCCESS via", url, "Elements:", len(parsed.get("elements", [])))
            with open(f"{_DATA_DIR}/remaining_28_batch.json", "wb") as out_f:
                out_f.write(raw)
            break
    except Exception as e:
        print("Error on", url, ":", e)
