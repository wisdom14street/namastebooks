#!/usr/bin/env python3
"""Record namastebookshop.com's own 'Best selling' order for the incense-related collections.

Reads the public collection pages sorted by best-selling (the same order shoppers see) and writes
data/bestsellers.json: {"<handle>": percentile 0..1 (0 = top seller)}. Pages are fetched slowly to stay polite.
If anything fails, the file is simply left out and the site falls back to sorting by price.
"""
import json, os, re, sys, time, urllib.request
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
COLLECTIONS = json.load(open(os.path.join(ROOT, 'site', 'config.json'))).get('bestseller_collections') or ['incense', 'cleansing-smudging', 'candles', 'incense-burner-holder-accs']
UA = {'User-Agent': 'Mozilla/5.0 (compatible; NamasteIncense-build/1.0)'}
def get(url):
    for attempt in range(4):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40).read().decode('utf-8', 'replace')
        except Exception as e:
            time.sleep(10 * (attempt + 1))
    return None
rank = {}
for c in COLLECTIONS:
    order, page = [], 1
    while page < 120:
        html = get(f'https://namastebookshop.com/collections/{c}?sort_by=best-selling&page={page}')
        if html is None or 'Something went wrong' in html[:3000]:
            print(f'{c}: stopped at page {page}', file=sys.stderr); break
        hs = [h for h in dict.fromkeys(re.findall(r'href="/(?:collections/[^/"]+/)?products/([^"?#/]+)', html)) if h not in order]
        if not hs: break
        order += hs; page += 1; time.sleep(3)
    n = max(1, len(order))
    for i, h in enumerate(order):
        rank[h] = min(rank.get(h, 1.0), i / n)
    print(f'{c}: {len(order)} products ranked', file=sys.stderr)
if rank:
    json.dump(rank, open(os.path.join(ROOT, 'data', 'bestsellers.json'), 'w'))
print(f'bestsellers: {len(rank)} handles')
