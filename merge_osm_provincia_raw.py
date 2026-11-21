import json
import glob
import os

with open("/Users/dany/genova/comuni_provincia_genova.json") as f:
    comuni_list = json.load(f)
ALL_67 = {c["name"].replace(" ", "_"): c["name"] for c in comuni_list}

# Also load Wikidata rich metadata (P856 website, P625 coords, P6375 address, wikipedia) to enrich OSM elements or add missing Wikidata items with websites
with open("/Users/dany/genova/wikidata_rich_provincia.json") as f:
    wd_rich = json.load(f)

wd_by_qid = {}
wd_by_name_comune = {}
for b in wd_rich:
    qid = b["item"]["value"].split("/")[-1]
    cname = b.get("comuneLabel", {}).get("value", "")
    label = b.get("itemLabel", {}).get("value", "")
    website = b.get("website", {}).get("value")
    address = b.get("address", {}).get("value")
    wiki = b.get("wiki", {}).get("value")
    commons = b.get("commons", {}).get("value")
    info = {}
    if website: info["website"] = website
    if address: info["addr:full"] = address
    if wiki: info["wikipedia:url"] = wiki
    if commons: info["wikimedia_commons"] = f"Category:{commons}"
    if info:
        wd_by_qid[qid] = info
        if label and cname:
            wd_by_name_comune[(cname.lower(), label.lower())] = (qid, info)

all_elements = []
seen_comuni = set()
websites_count = 0

for rf in sorted(glob.glob("/Users/dany/genova/comuni_raw/*.json")):
    base = os.path.basename(rf)[:-5]
    cname = ALL_67.get(base, base.replace("_", " "))
    seen_comuni.add(cname)
    with open(rf) as f:
        data = json.load(f)
    for el in data.get("elements", []):
        tags = el.get("tags", {})
        if not tags:
            continue
        tags["comune"] = cname
        # Enrich with Wikidata website/wikipedia if matching QID or name
        qid = tags.get("wikidata")
        if qid and qid in wd_by_qid:
            for k, v in wd_by_qid[qid].items():
                if k not in tags:
                    tags[k] = v
        name = tags.get("name", "")
        if name and (cname.lower(), name.lower()) in wd_by_name_comune:
            q_match, info_match = wd_by_name_comune[(cname.lower(), name.lower())]
            if "wikidata" not in tags:
                tags["wikidata"] = q_match
            for k, v in info_match.items():
                if k not in tags:
                    tags[k] = v
        if any(k in tags for k in ("website", "contact:website", "url", "facebook", "contact:facebook", "instagram")):
            websites_count += 1
        all_elements.append(el)

out_raw = {
    "version": 0.6,
    "generator": "OpenStreetMap + Wikidata Unified Raw Extractor (67 Comuni Provincia di Genova)",
    "total_comuni": len(seen_comuni),
    "total_elements": len(all_elements),
    "elements_with_web_links": websites_count,
    "elements": all_elements
}

with open("/Users/dany/genova/osm_provincia_raw.json", "w", encoding="utf-8") as f:
    json.dump(out_raw, f, indent=2, ensure_ascii=False)

print(f"Created /Users/dany/genova/osm_provincia_raw.json: {len(all_elements)} elements across {len(seen_comuni)} municipalities ({websites_count} with web/social links)")
