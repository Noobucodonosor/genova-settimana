import urllib.request
import urllib.parse
import json
import os
import time

with open("/Users/dany/genova/comuni_provincia_genova.json") as f:
    comuni = json.load(f)

missing = []
for c in comuni:
    fname = "/Users/dany/genova/comuni_raw/" + c["name"].replace(" ", "_") + ".json"
    if not os.path.exists(fname):
        missing.append(c)

print(f"Downloaded so far: {len(comuni) - len(missing)}/67. Missing: {len(missing)}")

# Fetch missing in batches of 8 municipalities per query so we only make 4 requests total!
BATCH_SIZE = 8
for i in range(0, len(missing), BATCH_SIZE):
    batch = missing[i:i+BATCH_SIZE]
    subqueries = []
    for c in batch:
        aid = 3600000000 + int(c["osm_rel"])
        subqueries.append(f'area({aid})->.a_{c["osm_rel"]};(way["highway"]["name"](area.a_{c["osm_rel"]});nwr["place"="square"]["name"](area.a_{c["osm_rel"]});nwr["amenity"~"theatre|hospital|university|library|arts_centre|cinema|school|townhall"]["name"](area.a_{c["osm_rel"]});nwr["leisure"~"stadium|park|garden|sports_centre"]["name"](area.a_{c["osm_rel"]});nwr["historic"~"castle|monument|memorial|manor|palace|fort|tower"]["name"](area.a_{c["osm_rel"]});nwr["tourism"~"museum|attraction"]["name"](area.a_{c["osm_rel"]});nwr["man_made"~"bridge|pier"]["name"](area.a_{c["osm_rel"]}););out tags;')
    
    # Wait: if we do one query per batch, how do we know which element belongs to which municipality?
    # In Overpass QL, we can output a separator node or we can query with `out center tags;` and match by bounding box / centroid, OR even simpler: use `foreach` or run 4 parallel requests!
