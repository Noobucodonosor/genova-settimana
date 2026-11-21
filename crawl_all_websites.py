import json
import re
import ssl
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from html.parser import HTMLParser

with open("/Users/dany/genova/osm_provincia_raw.json") as f:
    osm_elements = json.load(f)["elements"]

with open("/Users/dany/genova/wikidata_rich_provincia.json") as f:
    wd_rich = json.load(f)

with open("/Users/dany/genova/wikidata_all_provincia_items.json") as f:
    wd_all = json.load(f)

# Build QID -> instanceOfLabel lookup from wd_all
inst_by_label = {}
for b in wd_all:
    lbl = b.get("itemLabel", {}).get("value", "").strip()
    inst = b.get("instanceOfLabel", {}).get("value", "").strip()
    if lbl and inst:
        inst_by_label[lbl.lower()] = inst

# 1. Collect all unique places that either have a website OR have opening_hours/public access in OSM/Wikidata
places_registry = {}

for el in osm_elements:
    t = el.get("tags", {})
    name = t.get("name", "").strip()
    comune = t.get("comune", "Genova").strip()
    web = (t.get("website") or t.get("contact:website") or t.get("url") or t.get("facebook") or t.get("contact:facebook") or "").strip()
    if web and not web.startswith("http"):
        web = "https://" + web
    oh = (t.get("opening_hours") or "").strip()
    phone = (t.get("phone") or t.get("contact:phone") or "").strip()
    email = (t.get("email") or t.get("contact:email") or "").strip()
    cat = (t.get("amenity") or t.get("tourism") or t.get("historic") or t.get("shop") or t.get("leisure") or t.get("office") or "").strip()
    addr = (t.get("addr:street", "") + (" " + t.get("addr:housenumber", "") if t.get("addr:housenumber") else "")).strip()
    if not addr:
        addr = t.get("addr:full", "").strip()
    wiki = (t.get("wikipedia") or t.get("wikipedia:url") or "").strip()
    fee = (t.get("fee") or "").strip()
    wheelchair = (t.get("wheelchair") or "").strip()

    if web or oh or cat in {"library", "museum", "theatre", "cinema", "arts_centre", "castle", "palace", "monument", "hospital", "university", "stadium", "park", "garden"}:
        if not name:
            continue
        key = (comune.lower(), name.lower())
        if key not in places_registry:
            places_registry[key] = {
                "comune": comune,
                "nome": name,
                "categoria": cat or inst_by_label.get(name.lower(), "luogo pubblico"),
                "url": web,
                "orari_osm": oh,
                "telefono": phone,
                "email": email,
                "indirizzo": addr,
                "wikipedia": wiki,
                "ingresso_a_pagamento": fee,
                "accessibilita": wheelchair
            }
        else:
            rec = places_registry[key]
            if web and not rec["url"]: rec["url"] = web
            if oh and not rec["orari_osm"]: rec["orari_osm"] = oh
            if phone and not rec["telefono"]: rec["telefono"] = phone
            if email and not rec["email"]: rec["email"] = email
            if addr and not rec["indirizzo"]: rec["indirizzo"] = addr
            if cat and rec["categoria"] == "luogo pubblico": rec["categoria"] = cat

for b in wd_rich:
    name = b.get("itemLabel", {}).get("value", "").strip()
    comune = b.get("comuneLabel", {}).get("value", "").strip()
    web = b.get("website", {}).get("value", "").strip()
    addr = b.get("address", {}).get("value", "").strip()
    wiki = b.get("wiki", {}).get("value", "").strip()
    if not name or name.startswith("Q"):
        continue
    if web:
        key = (comune.lower(), name.lower())
        if key not in places_registry:
            places_registry[key] = {
                "comune": comune,
                "nome": name,
                "categoria": inst_by_label.get(name.lower(), "ente / istituzione / monumento"),
                "url": web,
                "orari_osm": "",
                "telefono": "",
                "email": "",
                "indirizzo": addr,
                "wikipedia": wiki,
                "ingresso_a_pagamento": "",
                "accessibilita": ""
            }
        else:
            if not places_registry[key]["url"]:
                places_registry[key]["url"] = web
            if addr and not places_registry[key]["indirizzo"]:
                places_registry[key]["indirizzo"] = addr

print("Total public places / websites in registry:", len(places_registry))
unique_urls = sorted(list({r["url"] for r in places_registry.values() if r["url"] and r["url"].startswith("http")}))
print("Unique HTTP/HTTPS URLs to crawl:", len(unique_urls))

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_script_style = False
        self.in_title = False
        self.title = []
        self.text_chunks = []
        self.meta_desc = ""

    def handle_starttag(self, tag, attrs):
        tag_l = tag.lower()
        if tag_l in ("script", "style", "noscript", "svg"):
            self.in_script_style = True
        elif tag_l == "title":
            self.in_title = True
        elif tag_l == "meta":
            attr_d = {k.lower(): (v or "") for k, v in attrs}
            if attr_d.get("name", "").lower() == "description" or attr_d.get("property", "").lower() == "og:description":
                if attr_d.get("content") and not self.meta_desc:
                    self.meta_desc = attr_d["content"].strip()

    def handle_endtag(self, tag):
        tag_l = tag.lower()
        if tag_l in ("script", "style", "noscript", "svg"):
            self.in_script_style = False
        elif tag_l == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title.append(data.strip())
        elif not self.in_script_style:
            cleaned = " ".join(data.split())
            if cleaned:
                self.text_chunks.append(cleaned)

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

RE_HOURS = re.compile(
    r"((?:orari[o]?|apertur[ae]|aperto|visite|luned[ìi]|marted[ìi]|mercoled[ìi]|gioved[ìi]|venerd[ìi]|sabato|domenica|dal\s+luned|tutti\s+i\s+giorni|da\s+marted)[^.;\n]{3,140}(?:\d{1,2}[:.]\d{2})[^.;\n]{0,80})",
    re.IGNORECASE
)
RE_EVENTS = re.compile(
    r"((?:eventi|mostr[ae]|spettacol[io]|concert[io]|visite\s+guidate|stagione\s+teatrale|programma|calendario| rassegna|laboratori|prenotazion[ei]|bigliett[io]|ingresso)[^.;\n]{10,160})",
    re.IGNORECASE
)

def fetch_url_info(url):
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "it-IT,it;q=0.9,en;q=0.8"
            }
        )
        with urllib.request.urlopen(req, timeout=8, context=ctx) as resp:
            ctype = resp.headers.get("Content-Type", "")
            raw = resp.read(250000) # Read up to 250KB per page
            text_html = raw.decode("utf-8", errors="ignore")
            parser = TextExtractor()
            parser.feed(text_html)
            full_text = " | ".join(parser.text_chunks)
            title = " ".join(parser.title).strip()

            hours_found = []
            for m in RE_HOURS.finditer(full_text):
                s = m.group(1).strip(" |,-:")
                if len(s) > 12 and s not in hours_found:
                    hours_found.append(s)
                if len(hours_found) >= 3:
                    break

            events_found = []
            for m in RE_EVENTS.finditer(full_text):
                s = m.group(1).strip(" |,-:")
                if len(s) > 15 and s not in events_found:
                    events_found.append(s)
                if len(events_found) >= 3:
                    break

            return url, {
                "status": "OK",
                "http_code": resp.status,
                "title": title[:160],
                "meta_desc": parser.meta_desc[:240],
                "orari_estratti_dal_sito": " ; ".join(hours_found)[:350],
                "eventi_e_apertura_pubblico": " ; ".join(events_found)[:350]
            }
    except Exception as e:
        return url, {
            "status": "OFFLINE_OR_PROTECTED",
            "http_code": 0,
            "title": "",
            "meta_desc": "",
            "orari_estratti_dal_sito": "",
            "eventi_e_apertura_pubblico": "",
            "error": str(e)[:80]
        }

url_results = {}
with ThreadPoolExecutor(max_workers=35) as ex:
    futures = [ex.submit(fetch_url_info, u) for u in unique_urls]
    done_cnt = 0
    for fut in as_completed(futures):
        u, info = fut.result()
        url_results[u] = info
        done_cnt += 1
        if done_cnt % 100 == 0 or done_cnt == len(unique_urls):
            print(f"  Crawled {done_cnt}/{len(unique_urls)} websites...")

ok_count = sum(1 for v in url_results.values() if v["status"] == "OK")
with_hours = sum(1 for v in url_results.values() if v.get("orari_estratti_dal_sito"))
with_events = sum(1 for v in url_results.values() if v.get("eventi_e_apertura_pubblico"))
print(f"Crawl complete! Reachable sites: {ok_count}/{len(unique_urls)}, Extracted site hours: {with_hours}, Extracted events/public info: {with_events}")

with open("/Users/dany/genova/crawled_urls_cache.json", "w", encoding="utf-8") as f:
    json.dump(url_results, f, indent=2, ensure_ascii=False)
