import urllib.request
import urllib.parse
import json
import time
import os

with open("/Users/dany/genova/comuni_provincia_genova.json") as f:
    comuni = json.load(f)

os.makedirs("/Users/dany/genova/comuni_raw", exist_ok=True)

# 1. Fetch Wikidata P138 across the entire Metropolitan City / Province of Genoa
sparql = """
SELECT DISTINCT ?item ?itemLabel ?comuneLabel ?namedAfter ?namedAfterLabel ?namedAfterDesc WHERE {
  { ?comune wdt:P131 wd:Q18288152 . } UNION { ?comune wdt:P131 wd:Q15111 . }
  ?item wdt:P131* ?comune .
  ?item wdt:P138 ?namedAfter .
  OPTIONAL { ?namedAfter schema:description ?namedAfterDesc FILTER(LANG(?namedAfterDesc) = "it") }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "it,en". }
}
"""
url_wd = "https://query.wikidata.org/sparql?format=json&query=" + urllib.parse.quote(sparql)
req_wd = urllib.request.Request(url_wd, headers={"User-Agent": "GenovaProvinciaExtractor/1.0"})
try:
    with urllib.request.urlopen(req_wd, timeout=45) as resp:
        wd_prov = json.loads(resp.read().decode("utf-8"))["results"]["bindings"]
    with open("/Users/dany/genova/wikidata_p138_provincia.json", "w") as f:
        json.dump(wd_prov, f, indent=2, ensure_ascii=False)
    print("Wikidata P138 provincia fetched:", len(wd_prov))
except Exception as e:
    print("Wikidata error:", e)

# 2. Copy Genova (44875) from already downloaded osm_genova_raw.json
if os.path.exists("/Users/dany/genova/osm_genova_raw.json") and not os.path.exists("/Users/dany/genova/comuni_raw/Genova.json"):
    with open("/Users/dany/genova/osm_genova_raw.json") as src, open("/Users/dany/genova/comuni_raw/Genova.json", "w") as dst:
        dst.write(src.read())

# 3. Fetch the remaining 66 municipalities in batches of 6
other_comuni = [c for c in comuni if c["name"] != "Genova" and not os.path.exists(f"/Users/dany/genova/comuni_raw/{c['name'].replace(' ', '_')}.json")]
print("Remaining municipalities to fetch from Overpass:", len(other_comuni))

ENDPOINTS = [
    "https://lz4.overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter"
]

for idx, c in enumerate(other_comuni, 1):
    area_id = 3600000000 + int(c["osm_rel"])
    fname = f"/Users/dany/genova/comuni_raw/{c['name'].replace(' ', '_')}.json"
    query = f"""[out:json][timeout:35];
area({area_id})->.a;
(
  way["highway"]["name"](area.a);
  nwr["place"="square"]["name"](area.a);
  nwr["amenity"~"theatre|hospital|university|library|arts_centre|cinema|school|townhall"]["name"](area.a);
  nwr["leisure"~"stadium|park|garden|sports_centre"]["name"](area.a);
  nwr["historic"~"castle|monument|memorial|manor|palace|fort|tower"]["name"](area.a);
  nwr["tourism"~"museum|attraction"]["name"](area.a);
  nwr["man_made"~"bridge|pier"]["name"](area.a);
  nwr["name:etymology:wikidata"](area.a);
);
out tags;"""
    success = False
    for ep in ENDPOINTS:
        try:
            data = urllib.parse.urlencode({"data": query}).encode("utf-8")
            req = urllib.request.Request(ep, data=data, headers={"User-Agent": "GenovaProvinciaExtractor/1.0"})
            with urllib.request.urlopen(req, timeout=40) as resp:
                raw = resp.read()
                parsed = json.loads(raw)
                with open(fname, "wb") as out_f:
                    out_f.write(raw)
                print(f"[{idx}/{len(other_comuni)}] {c['name']}: {len(parsed.get('elements', []))} elements")
                success = True
                break
        except Exception as e:
            print(f"  Retry {c['name']} on next endpoint ({e})")
            time.sleep(1.5)
    if not success:
        print(f"FAILED {c['name']}")
    time.sleep(0.4)

print("All municipalities processed!")
