#!/usr/bin/env python3
"""Download the public catalog from namastebookshop.com (only products published to the Online Store)."""
import json, urllib.request, os, sys, time
OUT = os.path.join(os.path.dirname(__file__), '..', 'data', 'all_products.json')
allp = []
for page in range(1, 1000):  # loop until Shopify returns an empty page
    req = urllib.request.Request(f"https://namastebookshop.com/products.json?limit=250&page={page}",
                                 headers={"User-Agent": "NamasteIncenseSites-build/1.0"})
    for attempt in range(6):  # Shopify occasionally answers 429/5xx under load; back off and retry
        try:
            d = json.load(urllib.request.urlopen(req, timeout=60)); break
        except Exception as e:
            if attempt == 5: raise
            print(f"page {page}: {e}; retrying", file=sys.stderr); time.sleep(15 * (attempt + 1))
    if not d['products']:
        break
    allp += d['products']
    print(f"page {page}: {len(allp)}", file=sys.stderr)
    time.sleep(0.5)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(allp, open(OUT, 'w'))
print(f"saved {len(allp)} products")
