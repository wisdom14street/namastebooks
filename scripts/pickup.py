#!/usr/bin/env python3
"""Record Shopify Local Pickup availability for each in-stock incense product.

Reads the store's public pickup-availability section for the first available variant of each product
(the same text shoppers see on namastebookshop.com) and writes data/pickup.json:
  {"<variant_id>": {"available": true, "location": "Bookshop", "ready": "Usually ready in 2 hours"}}
Products that cannot be checked are simply left out; the site then shows call-ahead wording instead.
"""
import json, os, re, sys, time, urllib.request, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'site'))
from catmap import category
try:
    import sitecopy
    category = getattr(sitecopy, 'category', category)
except Exception:
    pass
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
raw = json.load(open(os.path.join(ROOT, 'data', 'all_products.json')))
vids = []
for p in raw:
    if category(p):
        av = [v for v in p['variants'] if v['available'] and float(v['price']) > 0]
        vids += [v['id'] for v in av[:1]]  # one check per product keeps the load on the store light

def check(vid):
    url = f"https://namastebookshop.com/variants/{vid}/?section_id=pickup-availability"
    for attempt in range(3):
        try:
            t = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'NamasteIncenseSites-build/1.0'}), timeout=30).read().decode('utf-8', 'replace')
            t = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', t))
            m = re.search(r'Pickup available at (.+?) (Usually ready in [^.<]+?|Ready in [^.<]+?) (?:View|Check|$)', t)
            if m:
                return vid, {'available': True, 'location': m.group(1).strip(), 'ready': m.group(2).strip()}
            if re.search(r'Pickup currently unavailable', t):
                return vid, {'available': False}
            return vid, None
        except Exception:
            time.sleep(2 * (attempt + 1))
    return vid, None

out = {}
with cf.ThreadPoolExecutor(4) as ex:
    for vid, r in ex.map(check, vids):
        if r is not None:
            out[str(vid)] = r
json.dump(out, open(os.path.join(ROOT, 'data', 'pickup.json'), 'w'))
ok = sum(1 for r in out.values() if r['available'])
print(f"pickup checked {len(out)}/{len(vids)} variants, available for {ok}")
