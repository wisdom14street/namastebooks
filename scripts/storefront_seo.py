#!/usr/bin/env python3
"""Join Shopify Storefront SEO and image alt text onto the catalog by handle.

Reads SHOPIFY_STOREFRONT_TOKEN and SHOPIFY_STORE_DOMAIN. Writes
data/storefront_seo.json. A missing token or an API error leaves an empty
file and exits 0 so the site still builds from the generated fallbacks.
The token is never printed.
"""
import json, os, sys, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), 'data', 'storefront_seo.json')
API = '2025-01'
QUERY = '''
query Seo($cursor: String) {
  products(first: 100, after: $cursor) {
    pageInfo { hasNextPage endCursor }
    edges {
      node {
        handle
        seo { title description }
        images(first: 20) { edges { node { url altText } } }
      }
    }
  }
}
'''

def _write(data):
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w') as f:
        json.dump(data, f)

def _key(url):
    return (url or '').split('?', 1)[0].rstrip('/').lower()

def _redact(text, token):
    text = text or ''
    if token:
        text = text.replace(token, '[redacted]')
    return text[:300]

def fetch(domain, token):
    url = f'https://{domain}/api/{API}/graphql.json'
    out = {}
    cursor = None
    for _ in range(500):
        body = json.dumps({'query': QUERY, 'variables': {'cursor': cursor}}).encode()
        req = urllib.request.Request(url, data=body, method='POST', headers={
            'Content-Type': 'application/json',
            'X-Shopify-Storefront-Access-Token': token,
            'User-Agent': 'NamasteBooks-build/1.0',
        })
        with urllib.request.urlopen(req, timeout=60) as resp:
            payload = json.load(resp)
        if payload.get('errors'):
            raise RuntimeError('graphql error')
        data = (payload.get('data') or {}).get('products') or {}
        for edge in data.get('edges') or []:
            node = edge.get('node') or {}
            handle = (node.get('handle') or '').strip()
            if not handle:
                continue
            seo = node.get('seo') or {}
            alts = {}
            for im in ((node.get('images') or {}).get('edges') or []):
                img = im.get('node') or {}
                alt = (img.get('altText') or '').strip()
                key = _key(img.get('url'))
                if key and alt:
                    alts[key] = alt
                    alts[key.rsplit('/', 1)[-1]] = alt
            out[handle] = {
                'title': (seo.get('title') or '').strip(),
                'description': (seo.get('description') or '').strip(),
                'alts': alts,
            }
        page = data.get('pageInfo') or {}
        if not page.get('hasNextPage'):
            break
        cursor = page.get('endCursor')
        if not cursor:
            break
    return out

def main():
    token = (os.environ.get('SHOPIFY_STOREFRONT_TOKEN') or '').strip()
    domain = (os.environ.get('SHOPIFY_STORE_DOMAIN') or '').strip().removeprefix('https://').strip('/')
    if not token or not domain:
        print('storefront seo skipped: credentials not set', file=sys.stderr)
        _write({})
        return 0
    try:
        data = fetch(domain, token)
    except urllib.error.HTTPError as e:
        print(f'storefront seo unavailable: HTTP {e.code}', file=sys.stderr)
        _write({})
        return 0
    except Exception as e:
        print(f'storefront seo unavailable: {type(e).__name__}: {_redact(str(e), token)}', file=sys.stderr)
        _write({})
        return 0
    _write(data)
    print(f'storefront seo joined {len(data)} products')
    return 0

if __name__ == '__main__':
    sys.exit(main())
