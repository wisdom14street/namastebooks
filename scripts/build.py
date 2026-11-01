#!/usr/bin/env python3
"""Static-site engine for namastebooks.com (adapted from the Namaste storefront engine). Everything site-specific (name, domain, colors, product mix, copy) lives in ./site/:
  site/config.json   settings, including REVIEW_URL and GOOGLE_SITE_VERIFICATION
  site/sitecopy.py   aisles, product mix rules and all page copy
Usage: python3 scripts/build.py [--preview] [--site=https://example.com]
"""
import json, os, re, sys, html, shutil, datetime
from collections import Counter
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path[:0] = [HERE, os.path.join(ROOT, 'site')]
from catmap import category
import brands as BR
import sitecopy as C
# optional per-site overrides (used by non-incense sites such as the crystal market)
category = getattr(C, 'category', category)
BR = getattr(C, 'BR', BR)
FAM_LABEL, FAM_ALL = getattr(C, 'FAM_LABEL', 'Scent family'), getattr(C, 'FAM_ALL', 'All scents')
STYLE_LABEL, STYLE_ALL = getattr(C, 'STYLE_LABEL', 'Style'), getattr(C, 'STYLE_ALL', 'All styles')

CFG = json.load(open(os.path.join(ROOT, 'site', 'config.json')))
DIST = os.path.join(ROOT, 'dist')
PREVIEW = '--preview' in sys.argv
SITE = CFG['site_url'].rstrip('/')
for a in sys.argv:
    if a.startswith('--site='): SITE = a.split('=', 1)[1].rstrip('/')
REVIEW_URL = (CFG.get('REVIEW_URL') or '').strip()
GSV = (CFG.get('GOOGLE_SITE_VERIFICATION') or '').strip()
GA_ID = (CFG.get('GA_MEASUREMENT_ID') or '').strip()
BRAND = CFG['brand']; LEGAL = f'{BRAND} is a brand of Wealth Edge Ventures Inc.'
SHOP = 'https://namastebookshop.com'
CART_ATTR = '?attributes%5BStorefront%5D=' + CFG['storefront'].replace(' ', '%20')
E = html.escape
GA_HEAD = '' if (PREVIEW or not GA_ID) else (f'<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>'
    f'<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag("js",new Date());gtag("config","{GA_ID}",' + json.dumps({'site_brand': BRAND}).replace('</', '<\\/') + ');</script>')
GA_FOOT = '<script src="/assets/ga.js" defer></script>' if GA_HEAD else ''
CART_DOMAIN = SITE.split('://', 1)[-1].split('/')[0].removeprefix('www.')
def single_vid(x):
    """variant id when a card can go straight to the cart (one listing, one in-stock option), else 0"""
    av = [v for v in x['variants'] if v['available']]
    return av[0]['id'] if len(x['group']) == 1 and len(av) == 1 else 0
def atc_btn(x):
    vid = single_vid(x)
    if not vid: return f'<a class="atc" href="/products/{x["handle"]}/" aria-label="Choose options for {E(x["title"])}">Choose options</a>'
    v = next(v for v in x['variants'] if v['id'] == vid)
    return (f'<button type="button" class="atc" data-atc data-v="{vid}" data-h="{x["handle"]}" data-t="{E(x["title"])}" data-p="{float(v["price"]):.2f}" '
            f'data-i="{E(img(x["images"][0], 400))}" data-c="{x["aisle"]}" data-k="{x["base"]}" aria-label="Add {E(x["title"])} to cart">Add to cart</button>')
CART_ICON = '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M5 8h14l-1.2 11.2a2 2 0 0 1-2 1.8H8.2a2 2 0 0 1-2-1.8z"/><path d="M9 8V6.5a3 3 0 0 1 6 0V8"/></svg>'
_CART_CFG = None
def cart_boot():
    global _CART_CFG
    if _CART_CFG is None:
        _CART_CFG = json.dumps({'shop': SHOP, 'shopName': 'namastebookshop.com', 'attr': CART_ATTR, 'brand': BRAND, 'domain': CART_DOMAIN,
                                'ref': CART_DOMAIN.split('.')[0], 'pickup': bool(PICKUP_ON), 'ready': READY, 'street': STORE_STREET, 'addr': STORE_ADDR,
                                'pair': getattr(C, 'PAIR', {}), 'pairTitle': getattr(C, 'CART_PAIR_TITLE', 'Goes well with your cart')}).replace('</', '<\\/')
    return (f'<div class="cdim" data-cart-close hidden></div><aside id="cart" class="cdrawer" role="dialog" aria-modal="true" aria-labelledby="ctitle" hidden>'
            f'<div class="chead"><h2 id="ctitle">Your cart</h2><button type="button" class="cx" data-cart-close aria-label="Close cart">&times;</button></div>'
            f'<p class="cmsg" id="cmsg" role="status" aria-live="polite"></p><div class="cbody" data-cart-body></div></aside>'
            f'<script>window.NI_CART={_CART_CFG}</script><script src="/assets/cart.js" defer></script>')
STORE_STREET = '2 West 14th Street'; STORE_CITY, STORE_REGION, STORE_ZIP = 'New York', 'NY', '10011'
STORE_ADDR = f'{STORE_STREET}, {STORE_CITY}, {STORE_REGION} {STORE_ZIP}'
PHONE, TEL = '212-645-0141', '+12126450141'
GEO = (40.73602, -73.99404)
HOURS = [('Monday to Thursday', '11 AM to 8 PM'), ('Friday and Saturday', '11 AM to 9 PM'), ('Sunday', '11 AM to 7 PM')]
HOURS_LD = [(['Monday', 'Tuesday', 'Wednesday', 'Thursday'], '11:00', '20:00'), (['Friday', 'Saturday'], '11:00', '21:00'), (['Sunday'], '11:00', '19:00')]
MAP_Q = '2+West+14th+Street,+New+York,+NY+10011'
MAP_EMBED = f'https://www.google.com/maps/embed?origin=mfe&pb=!1m3!2m1!1s{MAP_Q}!6i16'
MAP_LINK = f'https://www.google.com/maps/search/?api=1&query={MAP_Q}'
DIRECTIONS = f'https://www.google.com/maps/dir/?api=1&destination={MAP_Q}'

FAMILIES = [
 ('nag-champa', 'Nag Champa', r'nag ?champa|champa'),
 ('resinous', 'Resinous & Sacred', r'frankincense|myrrh|copal|benzoin|dragon.?s ?blood|amber|guggul|church|oud|bakhoor|agar'),
 ('woods', 'Woods & Earth', r'sandal|chandan|cedar|palo santo|pine|pinon|pi\u00f1on|juniper|vetiver|patchoul|musk|earth|forest'),
 ('herbal', 'Sage & Herbal', r'sage|eucalyptus|rosemary|mint|green tea|matcha|tulsi|lemongrass|sweet ?grass|cannabis|aloe|herbal|bamboo'),
 ('floral', 'Floral', r'rose|jasmine|lavender|lotus|gardenia|lilac|honeysuckle|violet|orchid|ylang|mimosa|magnolia|night queen|blossom|flower|floral|neroli|frangipani'),
 ('sweet', 'Sweet & Spice', r'vanilla|cinnamon|coconut|strawberry|cherry|apple|honey|chocolate|coffee|spice|orange|lemon|mango|fruit|opium|ginger|citron'),
]
FAMILIES = getattr(C, 'FAMILIES', FAMILIES)
FAM_NAME = {k: n for k, n, _ in FAMILIES}
def family_of(t):
    for k, _, rx in FAMILIES:
        if re.search(rx, t, re.I): return k
    return ''
def style_of(t, b):
    l = t.lower()
    if 'tibet' in l or 'nepal' in l: return 'Tibetan'
    if b in ('morning-star', 'herb-earth') or 'japan' in l: return 'Japanese'
    if b in ('fred-soll',) or 'resin incense' in l and 'stick' in l: return 'Resin sticks'
    if b in ('hem', 'satya', 'prabhujis', 'auroshikha', 'kamini', 'tulasi', 'song-of-india', 'nandita') or re.search(r'dhoop|masala|agarbatti|nag champa', l): return 'Indian'
    if b in ('escential-essences', 'suns-eye', 'fred-soll', 'wolf-spirit'): return 'American'
    return ''
MULTI = re.compile(r'pack of \d+|\d+\s?-?\s?pack|\(\s?(?:[2-9]|\d{2,})\s?\)|\b\d{2,}\s?(?:sticks|cones|pcs|pieces)\b|\b(?:50|60|100|180|200|250|500)\s?(?:g|gm|gram|grams)\b|\bbox\b|bulk|set of|\bset\b|\b\d+ ?pc|\bx ?\d+ boxes', re.I)
GIFTY = re.compile(r'kit|gift|set\b|bundle|sampler|collection', re.I)

NOIMG = '/assets/no-photo.svg'
def img(u, w): return (u if u == NOIMG else f"{u}{'&' if '?' in u else '?'}width={w}") if u else ''
def srcset(u, ws): return u if u == NOIMG else ', '.join(f'{img(u, w)} {w}w' for w in ws)
def money(v): return f"${float(v):,.2f}"

# ---------- data ----------
raw = json.load(open(os.path.join(ROOT, 'data', 'all_products.json')))
def _load(n, d):
    p = os.path.join(ROOT, 'data', n)
    return json.load(open(p)) if os.path.exists(p) else d
PICKUP = _load('pickup.json', {}); RANK = _load('bestsellers.json', {})
products = []
for p in raw:
    base = category(p)
    if not base or (not p.get('images') and not CFG.get('include_no_photo', True)): continue
    vs = [v for v in p['variants'] if float(v['price']) > 0]
    avail = [v for v in vs if v['available']]
    if not avail: continue
    t = p['title'].strip(); b = BR.brand_of(t, p.get('vendor', ''))
    x = {'id': p['id'], 'handle': p['handle'], 'title': t, 'base': base, 'brand': b, 'vendor': p.get('vendor', ''),
         'family': family_of(t) if base not in getattr(C, 'NO_FAMILY', ('holders', 'burners')) else '', 'style': C.style_of(t, b, base) if hasattr(C, 'style_of') else (style_of(t, b) if base in ('sticks', 'cones') else ''),
         'price': min(float(v['price']) for v in avail), 'images': [i['src'] for i in p['images'][:6]] or [NOIMG], 'noimg': not p.get('images'),
         'multi': bool(MULTI.search(t)), 'gift': bool(GIFTY.search(t)), 'created': p.get('created_at', ''),
         'rank': RANK.get(p['handle'], 2.0), 'type': p.get('product_type', '')}
    cmp_ = [float(v['compare_at_price']) for v in avail if v.get('compare_at_price') and float(v['compare_at_price']) > float(v['price'])]
    x['compare'] = max(cmp_) if cmp_ else None
    x['variants'] = [{'id': v['id'], 'title': v['title'], 'price': v['price'], 'available': v['available'], 'sku': v.get('sku') or ''} for v in vs]
    x['aisle'] = C.assign(x)
    if not x['aisle']: continue
    x['pickup'] = next((PICKUP[str(v['id'])] for v in avail if PICKUP.get(str(v['id']), {}).get('available')), None)
    products.append(x)
products.sort(key=lambda x: x['created'], reverse=True)
AISLES = C.AISLES
AISLE_KEYS = list(AISLES)
cat_count = Counter(x['aisle'] for x in products)
AISLE_KEYS = [k for k in AISLE_KEYS if cat_count[k]]
fam_count = Counter(x['family'] for x in products if x['family'])
brand_count = Counter(x['brand'] for x in products if x['brand'])
style_count = Counter(x['style'] for x in products if x['style'])
PICKUP_ON = sum(1 for x in products if x['pickup']) >= 0.5 * max(1, len(products))
_ready = [x['pickup']['ready'] for x in products if x['pickup']]
READY = max(set(_ready), key=_ready.count) if _ready else ''
HAS_RANK = sum(1 for x in products if x['rank'] < 2) >= 0.3 * len(products)

# group near-identical listings
parent = {}
def find(a):
    while parent.setdefault(a, a) != a: parent[a] = parent[parent[a]]; a = parent[a]
    return a
for x in products:
    h = ('h', x['handle'])
    parent[find(h)] = find(('t', x['aisle'], re.sub(r'\s+', ' ', x['title'].lower())))
    if not x['noimg']: parent[find(h)] = find(('i', x['aisle'], x['images'][0].split('?')[0].rsplit('/', 1)[-1]))
groups = {}
for x in products: groups.setdefault(find(('h', x['handle'])), []).append(x)
for g in groups.values():
    g.sort(key=lambda y: y['price']); same = len({y['title'] for y in g}) == 1
    for y in g: y['group'] = g; y['label'] = (y['variants'][0]['sku'] or y['title']) if same else y['title']
leaders, _seen = [], set()
for x in products:
    if id(x['group']) not in _seen: _seen.add(id(x['group'])); leaders.append(x['group'][0])
def by_rank(xs): return sorted(xs, key=lambda x: (x['noimg'], x['rank'], x['price']))
def photo(xs): return [x for x in xs if not x['noimg']]

class S:  # context handed to sitecopy
    pass
for k, v in dict(BRAND=BRAND, LEGAL=LEGAL, SITE=SITE, SHOP=SHOP, STORE_STREET=STORE_STREET, STORE_ADDR=STORE_ADDR, PHONE=PHONE, TEL=TEL,
                 DIRECTIONS=DIRECTIONS, HOURS=HOURS, PICKUP_ON=PICKUP_ON, READY=READY, N=len(products), money=money, E=E,
                 cat_count=cat_count, fam_count=fam_count, brand_count=brand_count, style_count=style_count, AISLES=AISLES,
                 AISLE_KEYS=AISLE_KEYS, FAM_NAME=FAM_NAME, BRAND_NAME=BR.NAME, FACTS=BR.FACTS, products=products, leaders=leaders,
                 by_rank=by_rank, HAS_RANK=HAS_RANK).items():
    setattr(S, k, v)
S.MIN_PRICE = min(x['price'] for x in products)
S.MIN_STICK = min([x['price'] for x in products if x['base'] == 'sticks'] or [S.MIN_PRICE])
S.UNDER10 = sum(1 for x in products if x['price'] < 10); S.UNDER20 = sum(1 for x in products if x['price'] < 20)
S.ABOUT_N = int(round(len(products), -2)) if len(products) >= 150 else (len(products) // 10 * 10 or len(products))
S.MULTI_N = sum(1 for x in products if x['multi'])

def match(x, f):
    if not f: return True
    if f.get('aisle') and x['aisle'] not in f['aisle']: return False
    if f.get('base') and x['base'] not in f['base']: return False
    if f.get('fam') and x['family'] not in f['fam']: return False
    if f.get('brand') and x['brand'] not in f['brand']: return False
    if f.get('style') and x['style'] not in f['style']: return False
    if f.get('maxp') is not None and x['price'] >= f['maxp']: return False
    if f.get('minp') is not None and x['price'] < f['minp']: return False
    if f.get('multi') and not x['multi']: return False
    if f.get('gift') and not x['gift']: return False
    if f.get('q') and not re.search(f['q'], x['title'], re.I): return False
    return True
S.match = match

# ---------- html helpers ----------
def hours_html():
    return '<dl class="hours">' + ''.join(f'<div><dt>{d}</dt><dd>{h}</dd></div>' for d, h in HOURS) + '</dl>'
def visit_buttons(light=False):
    return (f'<div class="cta"><a class="btn" href="{DIRECTIONS}" rel="noopener" target="_blank">Get directions</a>'
            f'<a class="btn{" ghost" if light else " alt"}" href="tel:{TEL}">Call {PHONE}</a></div>')
def visit_block(full=False):
    pk = (f'<p><b>Order now, collect later.</b> Pick Pickup when you check out; books are {READY.lower()}.</p>' if PICKUP_ON else
          f'<p><b>After one particular title?</b> Ring {PHONE} and the shop can check the shelf.</p>')
    return f'''<div class="visit"><div class="vinfo"><p class="eyebrow dark">{E(C.VISIT_EYEBROW)}</p><h2>{STORE_STREET}</h2>
<p class="addr">{STORE_ADDR}<br>The books are shelved at <b>Namaste Bookshop</b>, mid-block on the south side of West 14th Street by the Fifth Avenue corner; Union Square station is a short walk east.</p>
<h3>Hours</h3>{hours_html()}<p class="small">Holidays can change the schedule, so ring {PHONE} if you are making a special trip.</p>
{pk}{visit_buttons()}{'' if full else '<p><a href="/visit/">Routes, trains and how collection works &rarr;</a></p>'}</div>
<div class="vmap"><iframe title="Map to {STORE_ADDR}" src="{MAP_EMBED}" loading="lazy" referrerpolicy="no-referrer-when-downgrade" allowfullscreen></iframe></div></div>'''
S.visit_block = visit_block; S.visit_buttons = visit_buttons; S.hours_html = hours_html
def store_ld():
    return {"@context": "https://schema.org", "@type": CFG.get('store_type', 'Store'), "@id": SITE + '/#store', "name": BRAND, "url": SITE + '/',
            "image": photo(products)[0]['images'][0], "logo": SITE + '/icon-512.png', "description": C.STORE_DESC(S), "telephone": TEL, "priceRange": "$",
            "address": {"@type": "PostalAddress", "streetAddress": STORE_STREET, "addressLocality": STORE_CITY, "addressRegion": STORE_REGION, "postalCode": STORE_ZIP, "addressCountry": "US"},
            "geo": {"@type": "GeoCoordinates", "latitude": GEO[0], "longitude": GEO[1]}, "hasMap": MAP_LINK,
            "openingHoursSpecification": [{"@type": "OpeningHoursSpecification", "dayOfWeek": d, "opens": o, "closes": c} for d, o, c in HOURS_LD],
            "parentOrganization": {"@type": "Organization", "name": "Wealth Edge Ventures Inc."}, "containedInPlace": BOOKSHOP}
def ldjson(o): return f'<script type="application/ld+json">{json.dumps(o)}</script>'
def faq_ld(qas): return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": re.sub('<[^>]+>', '', q), "acceptedAnswer": {"@type": "Answer", "text": re.sub('<[^>]+>', '', a)}} for q, a in qas]}
def faq_html(qas): return '<div class="faq">' + ''.join(f'<details><summary>{q}</summary><div>{a}</div></details>' for q, a in qas) + '</div>'
def crumbs_ld(items): return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": SITE + u} for i, (n, u) in enumerate(items)]}
def crumbs_html(items): return '<nav class="wrap crumbs" aria-label="Breadcrumb"><ol>' + ''.join(f'<li><a href="{u}">{E(n)}</a></li>' if i < len(items) - 1 else f'<li aria-current="page">{E(n)}</li>' for i, (n, u) in enumerate(items)) + '</ol></nav>'

def review_block():
    if not REVIEW_URL: return ''
    import segno
    q = segno.make(REVIEW_URL, error='m')
    svg = q.svg_inline(scale=4, dark=CFG['theme']['ink'], light='#ffffff', border=2)
    return f'''<section class="wrap"><div class="review"><div><h2>{E(C.REVIEW_TITLE)}</h2><p>{E(C.REVIEW_TEXT)}</p>
<a class="btn" href="{E(REVIEW_URL)}" rel="noopener" target="_blank">Review us on Google</a></div><figure class="qr" aria-label="QR code that opens our Google review page">{svg}<figcaption>Scan to leave a review</figcaption></figure></div></section>'''
S.review_block = review_block

# ---------- layout ----------
def logo(): return f'<span class="mark" aria-hidden="true">{C.LOGO_SVG}</span><span class="wordmark">{C.WORDMARK}</span>'
def nav():
    links = '' if not getattr(C, 'NAV_AISLES', True) else ''.join(f'<a href="/shop/{AISLES[k][2]}/"><i style="background:{AISLES[k][4]}"></i>{E(AISLES[k][1])}</a>' for k in AISLE_KEYS)
    return f'''<a class="skip" href="#main">Skip to content</a><header class="top"><div class="bar"><a href="/visit/">{P2C["bar"]}</a><span>Open every day from 11 AM</span>{'<span>Order online, collect on 14th St</span>' if PICKUP_ON else ''}</div>
<div class="nav wrap"><a class="logo" href="/" aria-label="{E(BRAND)} home">{logo()}</a>
<form class="search" action="/shop/" role="search" autocomplete="off"><label class="sr" for="hq">Search {E(BRAND)}</label><input id="hq" name="q" type="search" placeholder="{E(C.SEARCH_PLACEHOLDER)}" aria-autocomplete="list" aria-controls="sugg" aria-expanded="false"><ul id="sugg" class="sugg" role="listbox" hidden></ul></form>
<a class="cartbtn" href="/cart/" data-cart-open aria-label="Cart, 0 items">{CART_ICON}<span class="cartn" data-cart-count hidden>0</span></a>
<button class="menu" aria-label="Menu" aria-expanded="false" aria-controls="mainnav"><span></span><span></span></button>
<nav class="links" id="mainnav" aria-label="Main"><a href="/visit/" class="vlink">Visit</a><a href="/shop/">Shop all</a>{links}{getattr(C, 'NAV_EXTRA', '')}{'<a href="/authors/">Authors</a>' if getattr(C, 'NAV_BRANDS', True) else ''}{f'<a href="/{C.QUIZ["slug"]}/">{E(C.QUIZ["nav"])}</a>' if C.QUIZ else ''}</nav></div></header>'''
def footer():
    sib = ''.join(f'<a href="{u}" rel="noopener">{E(n)}</a>' for n, u in CFG.get('siblings', []))
    expl = ''.join(f'<a href="{u}">{E(n)}</a>' for n, u in C.FOOTER_EXPLORE(S))
    return f'''<footer class="foot"><div class="wrap grid4">
<div><a class="logo light" href="/">{logo()}</a><p class="legal">{LEGAL}</p><p class="small">{E(C.FOOT_BLURB)}</p><p class="small findnote">{P2C["foot"]} <a href="/visit/">How to find us &rarr;</a></p>
<p class="small">Payment and shipping are handled by namastebookshop.com on Shopify, from New York City.</p></div>
<div><h2 class="fh">Shop</h2>{''.join(f'<a href="/shop/{AISLES[k][2]}/">{E(AISLES[k][0])}</a>' for k in AISLE_KEYS)}<a href="/authors/">Authors A&ndash;Z</a></div>
<div><h2 class="fh">Explore</h2>{expl}<a href="/faq/">FAQ</a></div>
<div><h2 class="fh">Visit</h2><p class="small foottxt">{STORE_ADDR}</p>{''.join(f'<p class="small foottxt">{d}: {h}</p>' for d, h in HOURS)}<a href="tel:{TEL}">Call {PHONE}</a><a href="{DIRECTIONS}" rel="noopener" target="_blank">Get directions</a><a href="/visit/">Visit &amp; pickup info</a>
<h2 class="fh mt">Help</h2><a href="/about/">About us</a><a href="/shipping/">Shipping</a><a href="/returns/">Returns</a><a href="/privacy/">Privacy</a><a href="/terms/">Terms</a>
{f'<h2 class="fh mt">Our other shops</h2>{sib}' if sib else ''}</div>
</div>{p2_popular()}<div class="wrap legalline">{LEGAL} &copy; {datetime.date.today().year} Wealth Edge Ventures Inc.</div></footer>'''

SITEMAP = []
OG_DEFAULT = SITE + '/og.jpg'
def page(path, title, desc, body, extra_head='', canonical=True, index=True, og_image=None):
    url = SITE + path; ogi = og_image if (og_image and path.startswith('/products/') and og_image.startswith('http')) else OG_DEFAULT; ogcard = ogi == OG_DEFAULT
    ogx = (f'<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:type" content="image/jpeg">' if ogcard else '') + f'<meta property="og:image:alt" content="{E(BRAND + ': ' + P2C['og_tag'] + '. Inside Namaste Bookshop, 2 W 14th St, NYC') if ogcard else E(title)}"><meta name="twitter:image:alt" content="{E(BRAND) if ogcard else E(title)}">'
    robots = '<meta name="robots" content="noindex,nofollow">' if PREVIEW else ''
    gsv = f'<meta name="google-site-verification" content="{E(GSV)}">' if GSV and path == '/' else ''
    doc = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">{GA_HEAD}
<title>{E(title)}</title><meta name="description" content="{E(desc)}">{robots}{gsv}{f'<link rel="canonical" href="{url}">' if canonical else ''}
<meta property="og:site_name" content="{E(BRAND)}"><meta property="og:type" content="website"><meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}"><meta property="og:url" content="{url}"><meta property="og:image" content="{E(ogi)}">{ogx}{ogx}{ogx}
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{E(title)}"><meta name="twitter:description" content="{E(desc)}"><meta name="twitter:image" content="{E(ogi)}">
<meta name="theme-color" content="{CFG['theme']['ink']}"><link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="icon" href="/icon-192.png" sizes="192x192" type="image/png"><link rel="apple-touch-icon" href="/apple-touch-icon.png"><link rel="manifest" href="/site.webmanifest">
<link rel="preconnect" href="https://cdn.shopify.com"><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="{CFG['theme']['fonts']}" rel="stylesheet">
<link rel="stylesheet" href="/assets/site.css"><link rel="stylesheet" href="/assets/theme.css"><link rel="stylesheet" href="/assets/cart.css"><link rel="stylesheet" href="/assets/ux.css">{extra_head}</head>
<body>{nav()}<main id="main">{body}</main>{footer()}<div class="actionbar"><a href="tel:{TEL}">Call</a><a href="{DIRECTIONS}" rel="noopener" target="_blank">Directions</a><a href="/visit/">Hours</a></div>{cart_boot()}<script src="/assets/site.js" defer></script><script src="/assets/ux.js" defer></script>{GA_FOOT}</body></html>'''
    out = os.path.join(DIST, path.strip('/'), 'index.html') if path.endswith('/') else os.path.join(DIST, path.strip('/'))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, 'w').write(doc)
    if index and canonical: SITEMAP.append(path)

def tag_of(x): return C.CARD_TAG(x) if hasattr(C, 'CARD_TAG') else (FAM_NAME.get(x['family']) or AISLES[x['aisle']][0])
def _card(x, eager=False):
    n = len(x['group'])
    pre = f'<small>{n} options from</small> ' if n > 1 else (f'<s>{money(x["compare"])}</s> ' if x['compare'] else '')
    u = x['images'][0]
    return (f'<a class="card" href="/products/{x["handle"]}/"><div class="ph"><img {"" if eager else "loading=\"lazy\" "}decoding="async" src="{img(u,400)}" srcset="{srcset(u,(300,400,600))}" sizes="(min-width:1050px) 25vw,(min-width:700px) 33vw,50vw" alt="{E(x["title"])}" width="400" height="400"></div>'
            f'<div class="meta"><span class="tag" style="--c:{AISLES[x["aisle"]][4]}">{E(tag_of(x))}</span><h3>{E(x["title"])}</h3><p class="price">{pre}{money(x["price"])}</p></div></a>')
def card(x, eager=False): return _card(x, eager).replace('<a class="card" ', '<div class="card"><a class="clink" ', 1) + atc_btn(x) + '</div>'
S.card = card; S.img = img; S.srcset = srcset; S.NOIMG = NOIMG; S.single_vid = single_vid; S.photo = photo
def grid(xs): return f'<div class="grid">{"".join(card(x) for x in xs)}</div>'
S.grid = grid
S.p2_badges = lambda compact=False: p2_badges(compact)
# ==== part2: find-us + sales upgrade (generated by cartkit/part2.py; copy lives in scripts/p2site.py) ====
import p2site as P2
P2C = P2.COPY
BOOKSHOP = {"@type": "BookStore", "name": "Namaste Bookshop", "url": "https://namastebookshop.com", "telephone": TEL,
            "address": {"@type": "PostalAddress", "streetAddress": STORE_STREET, "addressLocality": STORE_CITY, "addressRegion": STORE_REGION, "postalCode": STORE_ZIP, "addressCountry": "US"},
            "geo": {"@type": "GeoCoordinates", "latitude": GEO[0], "longitude": GEO[1]}, "hasMap": MAP_LINK}
INSTORE_LINE = 'On the shelf at Namaste Bookshop on West 14th Street; pickup orders are usually ready within about 2 hours'
def p2_badges(compact=False):
    return (f'<ul class="badges{" compact" if compact else ""}" aria-label="Shopping with {E(BRAND)}">'
            + ''.join(f'<li><b>{E(t)}</b><span>{E(s)}</span></li>' for t, s in P2C['badges']) + '</ul>')
def p2_chips():
    out = []
    for label, href, f in P2C['chips']:
        n = sum(1 for x in products if match(x, f)) if f else 0
        if f and not n: continue
        out.append(f'<a class="chip" href="{href}">{E(label)}{f" <small>{n}</small>" if n else ""}</a>')
    if not out: return ''
    return f'<section class="wrap"><div class="sechead"><h2>{E(P2C["chips_title"])}</h2><a href="/shop/">Shop all &rarr;</a></div><div class="chips">{"".join(out)}</div></section>'
def _p2_grid(spec, need_rank=False):
    if not spec or (need_rank and not HAS_RANK): return ''
    xs = by_rank(photo([x for x in leaders if match(x, spec.get('filter') or {})]))[:8]
    if len(xs) < 4: return ''
    return section({'type': 'grid', 'title': spec['title'], 'select': lambda S_: xs, 'href': spec['href'], 'link': spec['link'], 'intro': spec.get('intro', '')})
def p2_home_top():
    return (f'<section class="wrap">{p2_badges()}</section>' + p2_chips() + '<section class="wrap" data-recent hidden></section>' + _p2_grid(P2C.get('best'), True))
def p2_gift(): return _p2_grid(P2C.get('gift'))
def p2_item(y):
    v = next(v for v in y['variants'] if v['id'] == single_vid(y))
    return {'v': str(v['id']), 'h': y['handle'], 't': y['title'], 'p': f"{float(v['price']):.2f}", 'i': img(y['images'][0], 400), 'c': y['aisle'], 'k': y['base']}
def p2_set(x, cands):
    seen, picks = {id(x['group'])}, []
    for y in cands:
        if id(y['group']) in seen or not single_vid(y) or y['noimg']: continue
        seen.add(id(y['group'])); picks.append(y)
    lead = [x] if single_vid(x) else []
    items = lead + picks[:3 - len(lead)]
    if len(items) < 2: return ''
    data = [p2_item(y) for y in items]
    lis = ''.join(f'<li><label><input type="checkbox" checked aria-label="Include {E(y["title"])}"><img src="{img(y["images"][0], 120)}" alt="" width="56" height="56" loading="lazy">'
                  f'<span>{"<b>This item:</b> " if y is x else ""}{E(y["title"])}</span><b>{money(d["p"])}</b></label></li>' for y, d in zip(items, data))
    js_ = E(json.dumps(data))
    return (f'<div class="bundle"><h2>Read alongside</h2><p class="small">{E(P2C["set_sub"])}</p><ul>{lis}</ul>'
            f'<div class="btot"><span>Together: <b data-bundle-total>{money(sum(float(d["p"]) for d in data))}</b></span>'
            f'<button type="button" class="btn" data-bundle="{js_}" data-atc-items="{js_}">Add all {len(items)} to cart</button></div></div>')
def p2_instore(x): return f'<p class="instore">{INSTORE_LINE}. <a href="/visit/">How to find us</a></p>' if x['pickup'] else ''
def p2_sticky(x, v0):
    return (f'<div class="stickybuy" role="region" aria-label="Quick add to cart"><div><span class="sbt">{E(x["title"])}</span><b data-sb-price>{money(v0["price"])}</b></div>'
            f'<button type="button" class="btn">Add to cart</button></div>')
def p2_popular(): return '<nav class="wrap popular" aria-label="Popular on this site"><b>Popular:</b>' + ''.join(f'<a href="{h}">{E(l)}</a>' for l, h in P2C['popular']) + '</nav>'
def p2_visit():
    c = P2C
    walk = lambda steps: '<ol class="walk">' + ''.join(f'<li>{s}</li>' for s in steps) + '</ol>'
    pick = [f'Put your books in the {E(BRAND)} cart and press <b>Check out</b>.',
            'You land on Shopify at namastebookshop.com. Switch delivery to <b>Pickup</b>; collecting costs nothing.',
            f'Books are {(READY or "usually ready the same day").lower()}. Hold off until the email says your order is ready.',
            f'Stop by Namaste Bookshop, {STORE_STREET}, while it is open and tell the counter the name the order is under.']
    return (f'<p class="lead">{c["visit_lead"]}</p>'
            f'<div class="findbox"><h2>Finding the shop</h2><p>{c["sign"]}</p>'
            f'<p><b>{E(BRAND)}</b>, inside Namaste Bookshop<br>{STORE_ADDR}<br>On West 14th Street, south sidewalk, near the Fifth Avenue corner</p>'
            f'<div class="cta"><a class="btn" href="{DIRECTIONS}" rel="noopener" target="_blank">Map it in Google Maps</a><a class="btn alt" href="tel:{TEL}">Call {PHONE}</a></div></div>'
            f'{visit_block(full=True)}'
            f'<h2>On foot from Union Square</h2>{walk(c["union"])}<h2>On foot from Sixth Avenue</h2>{walk(c["sixth"])}'
            f'<h2>Trains, PATH and buses</h2>{TRANSIT}'
            f'<h2>Collecting a book order</h2><p>{c["pickup_intro"]}</p>{walk(pick)}'
            f'<h2>Before you come</h2>{faq_html(c["vfaq"])}{review_block()}')
AI_BOTS = ['Googlebot', 'Bingbot', 'OAI-SearchBot', 'ChatGPT-User', 'GPTBot', 'PerplexityBot', 'Perplexity-User', 'Google-Extended',
           'ClaudeBot', 'Claude-SearchBot', 'Claude-User', 'Applebot', 'Applebot-Extended', 'DuckDuckBot']
def p2_robots():
    return 'User-agent: *\nAllow: /\n\n' + ''.join(f'User-agent: {b}\nAllow: /\n\n' for b in AI_BOTS) + f'Sitemap: {SITE}/sitemap.xml\n'
def p2_llms():
    L = [f'# {BRAND}', '', f'> {P2C["llms"]}', '',
         f'{BRAND} is a brand of Wealth Edge Ventures Inc. Its books are kept at Namaste Bookshop, {STORE_ADDR}, on West 14th Street by Fifth Avenue in Manhattan. Phone {PHONE}.',
         'Hours: ' + '; '.join(f'{d}, {h}' for d, h in HOURS) + '.',
         f'Checkout runs on Shopify through namastebookshop.com, which takes payment and ships from New York City.' + (f' Free in-store pickup: choose Pickup at checkout; orders are {READY.lower()}.' if PICKUP_ON else ''),
         f'Roughly {S.ABOUT_N:,} books are listed; the list, prices and stock refresh every day and product pages read live stock.', '',
         '## Shop'] + [f'- [{AISLES[k][0]}]({SITE}/shop/{AISLES[k][2]}/): {AISLES[k][3]}' for k in AISLE_KEYS] + [
         f'- [All products]({SITE}/shop/)', f'- [Authors A to Z]({SITE}/authors/)', '',
         '## Visit and help', f'- [How to find us]({SITE}/visit/): walking routes, subway lines, hours and pickup steps', f'- [FAQ]({SITE}/faq/)',
         f'- [About]({SITE}/about/)', f'- [Shipping]({SITE}/shipping/)', f'- [Returns]({SITE}/returns/)', '',
         *getattr(C, 'LLMS_EXTRA', lambda S_: [])(S), '## Optional', f'- [Sitemap]({SITE}/sitemap.xml)', f'- [Catalog JSON]({SITE}/data/catalog.json): one row per listing with handle (h), title (t), price in USD (p) and image (i)', '']
    return '\n'.join(L)
# ==== end part2 ====

# ---------- build ----------
if os.path.exists(DIST): shutil.rmtree(DIST)
os.makedirs(os.path.join(DIST, 'data'))
shutil.copytree(os.path.join(ROOT, 'src', 'assets'), os.path.join(DIST, 'assets'))
shutil.copy(os.path.join(ROOT, 'site', 'theme.css'), os.path.join(DIST, 'assets', 'theme.css'))
for f in os.listdir(os.path.join(ROOT, 'src', 'static')): shutil.copy(os.path.join(ROOT, 'src', 'static', f), DIST)
shutil.copy(os.path.join(ROOT, 'site', 'favicon.svg'), DIST)
# app icons rendered from the theme colors
try:
    from PIL import Image, ImageDraw, ImageFont
    for size, name in ((180, 'apple-touch-icon.png'), (192, 'icon-192.png'), (512, 'icon-512.png')):
        im = Image.new('RGB', (size, size), CFG['theme']['ink']); d = ImageDraw.Draw(im)
        s = size / 40
        if getattr(C, 'ICON', '') == 'gem':
            d.polygon([(a*s, b*s) for a, b in ((12,15),(28,15),(33,21),(20,35),(7,21))], fill=CFG['theme']['accent'])
            d.line([(a*s, b*s) for a, b in ((7,21),(33,21))], fill=CFG['theme']['ink'], width=max(1, int(s)))
            im.save(os.path.join(DIST, name)); continue
        if hasattr(C, 'ICON_DRAW'):
            C.ICON_DRAW(d, s, CFG['theme']); im.save(os.path.join(DIST, name)); continue
        d.line([(20*s, 34*s), (20*s, 23*s)], fill=CFG['theme']['accent'], width=max(2, int(2.6*s)))
        for pts in ([(20,22),(15,18),(22,14),(18,9),(22,5),(21,2)], [(24,20),(27,17),(22,15),(25,12)]):
            d.line([(a*s, b*s) for a, b in pts], fill=CFG['theme']['paper'], width=max(2, int(1.8*s)), joint='curve')
        r = 2*s; d.ellipse([20*s-r, 23*s-r, 20*s+r, 23*s+r], fill=CFG['theme']['accent'])
        im.save(os.path.join(DIST, name))
except Exception as e:
    print('icon render skipped:', e)
json.dump({"name": BRAND, "short_name": CFG.get('short_name', BRAND), "start_url": "/", "display": "standalone", "background_color": CFG['theme']['paper'], "theme_color": CFG['theme']['ink'],
           "icons": [{"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"}, {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png"}]},
          open(os.path.join(DIST, 'site.webmanifest'), 'w'))

compact = [{'h': x['handle'], 't': x['title'], 'c': x['aisle'], 'k': x['base'], 'f': x['family'], 'b': x['brand'], 's': x['style'], 'p': x['price'],
            'o': x['compare'] if len(x['group']) == 1 else None, 'n': len(x['group']), 'i': img(x['images'][0], 400), 'v': single_vid(x), 'm': 1 if x['multi'] else 0,
            'g': 1 if x['gift'] else 0, 'x': 1 if x['noimg'] else 0, 'r': round(min(y['rank'] for y in x['group']), 4), 'd': max(y['created'] for y in x['group'])[:10]} for x in leaders]
json.dump(compact, open(os.path.join(DIST, 'data', 'catalog.json'), 'w'), separators=(',', ':'))
json.dump({'aisles': {k: {'name': AISLES[k][0], 'slug': AISLES[k][2], 'color': AISLES[k][4]} for k in AISLE_KEYS}, 'fams': FAM_NAME,
           'brands': {k: BR.NAME[k] for k in brand_count}, 'built': datetime.datetime.now().isoformat(timespec='minutes')},
          open(os.path.join(DIST, 'data', 'meta.json'), 'w'))

# ---- home ----
def collage():
    picks = [x for x in by_rank(photo(leaders)) if x['base'] in C.HERO_BASES][:4]
    return '<div class="collage" aria-hidden="true">' + ''.join(f'<img src="{img(x["images"][0],500)}" srcset="{srcset(x["images"][0],(300,500))}" sizes="(min-width:900px) 18vw,40vw" alt="" width="500" height="500"{" fetchpriority=\"high\"" if i==0 else " loading=\"lazy\""}>' for i, x in enumerate(picks)) + '</div>'
def section(sec):
    t = sec['type']
    if t == 'visit': return f'<section class="wrap">{visit_block()}</section>'
    if t == 'review': return review_block()
    if t == 'html': return sec['html'](S)
    if t == 'collections':
        tiles = ''
        for it in sec['items']:
            pool = by_rank(photo([x for x in leaders if match(x, it['filter'])]))
            if not pool: continue
            tiles += f'''<a class="coll" href="{it['href']}"><img loading="lazy" src="{img(pool[0]['images'][0],500)}" srcset="{srcset(pool[0]['images'][0],(300,500))}" sizes="(min-width:900px) 30vw,50vw" alt="" width="500" height="500"><div><h3>{E(it['title'])}</h3><p>{E(it['blurb'])}</p><span>{sum(1 for x in products if match(x, it['filter']))} items &rarr;</span></div></a>'''
        return f'<section class="wrap"><div class="sechead"><h2>{E(sec["title"])}</h2></div><div class="colls">{tiles}</div></section>'
    if t == 'grid':
        xs = sec['select'](S)
        if not xs: return ''
        return f'<section class="wrap"><div class="sechead"><h2>{E(sec["title"])}</h2>{f"<a href=\"{sec["href"]}\">{E(sec["link"])} &rarr;</a>" if sec.get("href") else ""}</div>{f"<p class=\"intro\">{sec["intro"]}</p>" if sec.get("intro") else ""}{grid(xs)}</section>'
    if t == 'brands':
        chips = ''.join(f'<a class="chip" href="/authors/{k}/">{E(BR.NAME[k])} <small>{n}</small></a>' for k, n in brand_count.most_common(sec.get('n', 12)))
        return f'<section class="wrap"><div class="sechead"><h2>{E(sec["title"])}</h2><a href="/authors/">Authors A&ndash;Z &rarr;</a></div><div class="chips">{chips}</div></section>'
    if t == 'whys':
        return f'<section class="wrap"><div class="sechead"><h2>{E(sec["title"])}</h2></div><ul class="whys">' + ''.join(f'<li><b>{a}</b><span>{b}</span></li>' for a, b in sec['items'](S) if a) + '</ul></section>'
    if t == 'quiz' and C.QUIZ:
        return f'<section class="wrap"><div class="quizcta"><div><h2>{E(sec["title"])}</h2><p>{E(sec["text"])}</p></div><a class="btn" href="/{C.QUIZ["slug"]}/">{E(C.QUIZ["cta"])}</a></div></section>'
    if t == 'band':
        steps = ''.join(f'<li><b>{a}</b><span>{b}</span></li>' for a, b in sec['steps'](S))
        return f'<section class="band"><div class="wrap band-in"><div><h2>{E(sec["title"])}</h2><p>{sec["text"](S)}</p>{visit_buttons(True)}</div><ol class="steps">{steps}</ol></div></section>'
    return ''
S.section = section; S.visit_block = visit_block
H = C.HERO(S)
home = f'''<section class="hero"><div class="wrap hero-in"><div class="htext"><p class="eyebrow">{H['eyebrow']}</p><h1>{H['h1']}</h1><p class="lede">{H['lede']}</p>
<div class="cta"><a class="btn" href="{P2C['cta'][1]}">{E(P2C['cta'][0])} &rarr;</a><a class="btn ghost" href="/visit/">How to find us</a><a class="btn ghost" href="{DIRECTIONS}" rel="noopener" target="_blank">Directions</a></div><p class="heroloc">{P2C['heroloc']}</p></div>{collage()}</div></section>
{p2_home_top()}{''.join(section(s) for s in C.HOME_SECTIONS[:2])}{p2_gift()}{''.join(section(s) for s in C.HOME_SECTIONS[2:])}'''
if hasattr(C, 'HOME_BODY'): home = C.HOME_BODY(S)
page('/', C.HOME_TITLE(S), C.HOME_DESC(S), home, ldjson({"@context": "https://schema.org", "@type": "WebSite", "name": BRAND, "url": SITE + '/',
     "potentialAction": {"@type": "SearchAction", "target": SITE + "/shop/?q={search_term_string}", "query-input": "required name=search_term_string"}}) + (''.join(ldjson(o) for o in C.HOME_LD(S)) if hasattr(C, 'HOME_LD') else ldjson(store_ld())))

# ---- shop pages ----
def shop_page(path, title, desc, h1, sub, preset=None, intro='', crumbs=None, extra_html='', extra_ld=''):
    preset = preset or {}
    chips = '<button class="f on" data-cat="">All</button>' + ''.join(f'<button class="f" data-cat="{k}" style="--c:{AISLES[k][4]}">{E(AISLES[k][1])} <small>{cat_count[k]}</small></button>' for k in AISLE_KEYS)
    fams = f'<option value="">{E(FAM_ALL)}</option>' + ''.join(f'<option value="{k}">{E(n)}</option>' for k, n, _ in FAMILIES if fam_count[k])
    brands = '<option value="">All authors</option>' + ''.join(f'<option value="{k}">{E(BR.NAME[k])}</option>' for k in sorted(brand_count, key=lambda k: BR.NAME[k].lower()))
    styles = f'<option value="">{E(STYLE_ALL)}</option>' + ''.join(f'<option>{E(s)}</option>' for s in sorted(style_count))
    pool = [x for x in leaders if match(x, preset)]
    pool = (C.SHOP_ORDER(pool) if hasattr(C, 'SHOP_ORDER') else (by_rank(pool) if HAS_RANK else pool))[:48]
    body = f'''{crumbs_html(crumbs) if crumbs else ''}<section class="wrap shophead"><h1>{E(h1)}</h1><p>{E(sub)}</p>{intro}</section>
<section class="wrap shop" data-preset='{E(json.dumps(preset))}' data-sort="{getattr(C, 'DEFAULT_SORT', '')}">
<div class="filters"><div class="fcats" role="group" aria-label="Aisles">{chips}</div><div class="frow"><label class="sr" for="q">Search</label><input type="search" id="q" placeholder="{E(C.SEARCH_PLACEHOLDER)}">
<label class="sr" for="fam">{E(FAM_LABEL)}</label><select id="fam">{fams}</select><label class="sr" for="brand">Author</label><select id="brand">{brands}</select><label class="sr" for="sty">{E(STYLE_LABEL)}</label><select id="sty">{styles}</select>
<label class="sr" for="price">Price</label><select id="price"><option value="">Any price</option>{getattr(C, 'PRICE_OPTS', '<option value="0-5">Under $5</option><option value="0-10">Under $10</option><option value="0-20">Under $20</option><option value="20-99999">$20 and up</option>')}</select>
<label class="sr" for="sort">Sort</label><select id="sort">{'<option value="best">Best selling</option>' if HAS_RANK else ''}<option value="new">Newest</option>{getattr(C, 'SORT_EXTRA', '')}<option value="lo">Price: low to high</option><option value="hi">Price: high to low</option><option value="az">A to Z</option></select></div>
<p class="count" id="count" aria-live="polite"></p></div><div class="grid" id="grid">{''.join(card(x) for x in pool)}</div><div class="more"><button class="btn" id="more" hidden>Show more</button></div></section>{extra_html}'''
    page(path, title, desc, body, (ldjson(crumbs_ld(crumbs)) if crumbs else '') + extra_ld)
S.shop_page = shop_page
shop_page('/shop/', C.SHOP_TITLE(S), C.SHOP_DESC(S), C.SHOP_H1, C.SHOP_SUB(S), crumbs=[('Home', '/'), ('Shop', '/shop/')])
for k in AISLE_KEYS:
    a = AISLES[k]
    shop_page(f'/shop/{a[2]}/', C.AISLE_TITLE(S, k), C.AISLE_DESC(S, k), a[0], a[3], {'aisle': [k]}, crumbs=[('Home', '/'), ('Shop', '/shop/'), (a[0], f'/shop/{a[2]}/')])
for L in C.LANDINGS(S):
    if any(match(x, L['filter']) for x in products):
        shop_page(L['path'], L['title'], L['desc'], L['h1'], L['sub'], L['filter'], L.get('intro', ''), crumbs=[('Home', '/'), (L['h1'], L['path'])])

# ---- brand pages ----
def brand_stats(k):
    xs = [x for x in products if x['brand'] == k]
    return {'n': len(xs), 'min': min(x['price'] for x in xs), 'max': max(x['price'] for x in xs), 'xs': xs,
            'aisles': Counter(x['aisle'] for x in xs), 'pickup': sum(1 for x in xs if x['pickup']), 'fams': Counter(x['family'] for x in xs if x['family'])}
dir_items = []
for k in sorted(brand_count, key=lambda k: BR.NAME[k].lower()):
    st = brand_stats(k); name = BR.NAME[k]; rich = st['n'] >= 5
    lead = [x for x in leaders if x['brand'] == k]
    intro = C.brand_intro(S, k, st)
    qas = C.brand_faq(S, k, st)
    parts = [f'<div class="bintro">{intro}</div>',
             '<ul class="bstats">' + f'<li><b>{st["n"]}</b> in stock</li><li><b>{money(st["min"])}</b>{" to " + money(st["max"]) if st["max"] > st["min"] else ""}</li>' + ''.join(f'<li><b>{c}</b> {E(AISLES[a][0])}</li>' for a, c in st['aisles'].most_common(3)) + '</ul>']
    if rich:
        top = by_rank(lead)[:4] if HAS_RANK else lead[:4]
        parts.append(f'<h2>{"Most popular" if HAS_RANK else "A few to start with"}</h2>{grid(top)}')
        bands = getattr(C, 'PRICE_BANDS', [(f'Under $5', 0, 5), ('$5 to $15', 5, 15), ('$15 and up', 15, 1e9)])
        filled = [(label, [x for x in (by_rank(lead) if HAS_RANK else lead) if lo <= x['price'] < hi][:4]) for label, lo, hi in bands]
        filled = [(l, b) for l, b in filled if b]
        if len(filled) > 1:
            parts.append('<h2>By price</h2>' + ''.join(f'<h3 class="pband">{l}</h3>{grid(b)}' for l, b in filled))
    parts.append(f'<h2>All {E(name)} ({len(lead)})</h2>{grid(by_rank(lead) if HAS_RANK else lead)}')
    if qas: parts.append(f'<h2>{E(name)} questions</h2>{faq_html(qas)}')
    cr = [('Home', '/'), ('Authors', '/authors/'), (name, f'/authors/{k}/')]
    body = f'{crumbs_html(cr)}<section class="wrap brandpage"><h1>{E(C.BRAND_H1(S, k))}</h1>{"".join(parts)}<p class="legal">{LEGAL}</p></section>'
    page(f'/authors/{k}/', C.BRAND_TITLE(S, k, st), C.BRAND_DESC(S, k, st), body,
         ldjson(crumbs_ld(cr)) + (ldjson(faq_ld(qas)) if qas else '') + ldjson({"@context": "https://schema.org", "@type": "CollectionPage", "name": C.BRAND_H1(S, k), "url": f"{SITE}/authors/{k}/", "about": C.BRAND_ABOUT(name) if hasattr(C, "BRAND_ABOUT") else {"@type": "Brand", "name": name}}),
         og_image=img(by_rank(lead)[0]['images'][0], 1200) if not by_rank(lead)[0]['noimg'] else None)
    dir_items.append((name, k, st['n']))
letters = {}
for name, k, n in dir_items: letters.setdefault(name[0].upper() if name[0].isalpha() else '#', []).append((name, k, n))
az = '<nav class="az" aria-label="Jump to letter">' + ''.join(f'<a href="#l-{L}">{L}</a>' for L in sorted(letters)) + '</nav>' + ''.join(
    f'<h2 id="l-{L}">{L}</h2><ul class="dir">' + ''.join(f'<li><a href="/authors/{k}/">{E(nm)}</a> <span class="small">{n} item{"s" if n != 1 else ""}</span></li>' for nm, k, n in items) + '</ul>' for L, items in sorted(letters.items()))
page('/authors/', C.BRANDS_TITLE(S), C.BRANDS_DESC(S), f'{crumbs_html([("Home", "/"), ("Authors", "/authors/")])}<section class="wrap prose"><h1>{E(C.BRANDS_H1)}</h1><p class="lead">{C.BRANDS_LEAD(S, len(dir_items))}</p>{az}</section>',
     ldjson(crumbs_ld([("Home", "/"), ("Authors", "/authors/")])))

# ---- product pages ----
for x in products:
    a = AISLES[x['aisle']]
    avail = [v for v in x['variants'] if v['available']]; v0 = avail[0]
    imgs = x['images']
    gallery = ''.join(f'<button class="th{" on" if i==0 else ""}" data-src="{img(u,1200)}" aria-label="Show photo {i+1}"><img loading="lazy" src="{img(u,160)}" alt="" width="80" height="80"></button>' for i, u in enumerate(imgs))
    opts = ''
    if len(x['variants']) > 1:
        opts = '<label class="vlab">Option<select id="variant">' + ''.join(f'<option value="{v["id"]}"{" disabled" if not v["available"] else ""}{" selected" if v is v0 else ""}>{E(v["title"])}{"" if v["available"] else " (sold out)"}</option>' for v in x['variants']) + '</select></label>'
    facts = [('Aisle', f'<a href="/shop/{a[2]}/">{E(a[0])}</a>')]
    if x['family']: facts.append((FAM_LABEL, E(FAM_NAME[x['family']])))
    if x['brand']: facts.append(('Author', f'<a href="/authors/{x["brand"]}/">{E(BR.NAME[x["brand"]])}</a>'))
    if x['style']: facts.append((STYLE_LABEL, E(x['style'])))
    if v0['sku'] and not hasattr(C, 'FACTS_EXTRA'): facts.append(('SKU', E(v0['sku'])))
    if hasattr(C, 'FACTS_EXTRA'): facts += C.FACTS_EXTRA(S, x, v0)
    facts.append(('Ships from', 'New York City'))
    if x['pickup']: facts.append(('Pickup', f'<a href="/visit/">{STORE_STREET}</a>'))
    def rel(pred, n=4, exclude=()):
        pool = [y for y in leaders if y['group'] is not x['group'] and y not in exclude and pred(y)]
        return (by_rank(pool) if HAS_RANK else pool)[:n]
    same_brand = rel(lambda y: x['brand'] and y['brand'] == x['brand'])
    same_scent = rel(lambda y: x['family'] and y['family'] == x['family'] and y['aisle'] == x['aisle'], exclude=same_brand)
    pair_bases = C.PAIR.get(x['base'], [])
    pair = rel(lambda y: y['base'] in pair_bases)
    more = rel(lambda y: y['aisle'] == x['aisle'], exclude=same_brand + same_scent)
    sibs = ''
    if len(x['group']) > 1:
        sibs = '<div class="sibs"><h2>Other copies</h2><p class="small">Each copy is listed separately, with its own price.</p>' + ''.join(
            f'<a class="sib{" on" if y is x else ""}" href="/products/{y["handle"]}/"{" aria-current=\"page\"" if y is x else ""}><img loading="lazy" src="{img(y["images"][0],120)}" alt="" width="60" height="60"><span>{E(y["label"])}</span><b>{money(y["price"])}</b></a>' for y in x['group']) + '</div>'
    desc = C.describe(S, x)
    p2set = p2_set(x, rel(lambda y: y['base'] in pair_bases and bool(single_vid(y)) and not y['noimg'], n=6) + rel(lambda y: y['aisle'] == x['aisle'] and bool(single_vid(y)) and not y['noimg'], n=6))
    p2tail = '<section class="wrap" data-recent hidden></section>' + p2_sticky(x, v0)
    cr = [('Home', '/'), ('Shop', '/shop/'), (a[0], f'/shop/{a[2]}/'), (x['title'], f"/products/{x['handle']}/")]
    ld = {"@context": "https://schema.org", "@type": "Product", "name": x['title'], "image": [SITE + u if u == NOIMG else img(u, 1200) for u in imgs[:3]], "sku": v0['sku'] or str(v0['id']),
          "brand": {"@type": "Brand", "name": BR.NAME.get(x['brand'], BRAND)}, "category": a[0], "url": f"{SITE}/products/{x['handle']}/",
          "description": html.unescape(re.sub('<[^>]+>', '', ' '.join(desc))),
          "offers": {"@type": "Offer", "price": f"{float(v0['price']):.2f}", "priceCurrency": "USD", "availability": "https://schema.org/InStock", "itemCondition": "https://schema.org/NewCondition",
                     "url": f"{SITE}/products/{x['handle']}/", "seller": {"@type": "Organization", "name": "Wealth Edge Ventures Inc."},
                     **({"availableAtOrFrom": {"@id": SITE + '/#store'}} if x['pickup'] else {})}}
    _sku = v0['sku'] or ''
    if _sku.isdigit() and len(_sku) in (8, 12, 13, 14): ld['gtin' + str(len(_sku))] = _sku
    if hasattr(C, 'LD_EXTRA'): ld.update(C.LD_EXTRA(S, x, v0))
    ld = {k: v for k, v in ld.items() if v is not None}
    cmp_ = f'<s id="cmp">{money(x["compare"])}</s>' if x['compare'] else '<s id="cmp" hidden></s>'
    btns = f'<div class="pbtns"><a href="{DIRECTIONS}" rel="noopener" target="_blank">Directions</a><a href="tel:{TEL}">Call</a><a href="/visit/">Hours</a></div>'
    pk = (f'<div class="pickup"><h2>Collect it on 14th Street</h2><p>This book can wait for you at <b>Namaste Bookshop, {STORE_STREET}</b>, by the Fifth Avenue end of the block. {E(x["pickup"]["ready"])}.</p><p class="small">Check out and switch to <b>Pickup</b>. Any questions, ring <a href="tel:{TEL}">{PHONE}</a>.</p>{btns}</div>'
          if x['pickup'] else f'<div class="pickup"><h2>Browse it on the shelf</h2><p>Namaste Bookshop is at <b>{STORE_ADDR}</b>. Ring <a href="tel:{TEL}">{PHONE}</a> first to confirm the copy is there.</p>{btns}</div>')
    rows = ''
    for title, xs in ((C.REL_BRAND.format(brand=BR.NAME.get(x['brand'], '')), same_brand), (C.REL_SCENT.format(scent=FAM_NAME.get(x['family'], '').lower()), same_scent), (C.REL_PAIR, pair), (C.REL_MORE.format(aisle=a[0].lower()), more)):
        if xs: rows += f'<section class="wrap"><div class="sechead"><h2>{E(title)}</h2></div>{grid(xs)}</section>'
    body = f'''{crumbs_html(cr)}<section class="wrap pdp" data-handle="{x['handle']}"><div class="gallery"><div class="main"><img id="mainimg" src="{img(imgs[0],1200)}" srcset="{srcset(imgs[0],(600,900,1200))}" sizes="(min-width:900px) 55vw,100vw" alt="{E(x['title'])}" width="1200" height="1200" fetchpriority="high"></div>{f'<div class="thumbs">{gallery}</div>' if len(imgs)>1 else ''}</div>
<div class="info"><span class="tag" style="--c:{a[4]}">{E(a[0])}</span><h1>{E(x['title'])}</h1><p class="pprice">{cmp_} <span id="price">{money(v0['price'])}</span></p><p class="stock" id="stock"><i></i><span>In stock</span></p>{p2_instore(x)}{opts}{sibs}
<button type="button" class="btn buy" id="buy" data-atc data-v="{v0['id']}" data-h="{x['handle']}" data-t="{E(x['title'])}" data-vt="{E(v0['title']) if len(x['variants']) > 1 else ''}" data-p="{float(v0['price']):.2f}" data-i="{E(img(imgs[0], 400))}" data-c="{x['aisle']}" data-k="{x['base']}">Add to cart</button>
{p2_badges(True)}{p2set}
<p class="note">You finish the order on Shopify at namastebookshop.com, picking delivery{" or pickup" if x['pickup'] else ""} and checking everything before you pay.</p>
{pk}<div class="desc">{''.join(f'<p>{s}</p>' for s in desc)}</div><dl class="facts">{''.join(f'<div><dt>{p}</dt><dd>{q}</dd></div>' for p, q in facts)}</dl><p class="small"><a href="/shipping/">Shipping</a> &middot; <a href="/returns/">Returns</a></p></div></section>{rows}{p2tail}'''
    page(f"/products/{x['handle']}/", f"{x['title']} | {BRAND}", C.PRODUCT_DESC(S, x, v0), body,
         ldjson(ld) + ldjson(crumbs_ld(cr)) + f'<script>window.NI_PRODUCT={json.dumps({"handle": x["handle"], "cartAttr": CART_ATTR, "shop": SHOP})}</script>', og_image=None if x['noimg'] else img(imgs[0], 1200))

# ---- info pages ----
def info(path, title, desc, h1, body_html, extra_head='', crumbs=True, wide=False, cr=None):
    cr = cr or [('Home', '/'), (re.sub('<[^>]+>', '', h1), path)]
    page(path, f'{title} | {BRAND}', desc, f'{crumbs_html(cr) if crumbs else ""}<section class="wrap{"" if wide else " prose"}"><h1>{h1}</h1>{body_html}<p class="legal">{LEGAL}</p></section>', (ldjson(crumbs_ld(cr)) if crumbs else '') + extra_head)
S.info = info; S.ldjson = ldjson; S.store_ld = store_ld; S.faq_html = faq_html; S.faq_ld = faq_ld
info('/about/', 'About', C.ABOUT_DESC(S), C.ABOUT_H1, C.ABOUT(S), ldjson(store_ld()))
TRANSIT = '''<ul class="transit"><li><b>14 St&ndash;Union Square</b> <span class="lines">4 5 6 L N Q R W</span><br>The closest big station: a few minutes on foot heading west on 14th Street.</li>
<li><b>14 St/6 Av</b> <span class="lines">F M L</span>, connected to <b>14 St</b> <span class="lines">1 2 3</span><br>At Sixth Avenue; walk east on 14th Street for a few minutes.</li>
<li><b>PATH:</b> the 14th Street stop sits at Sixth Avenue.</li><li><b>Buses:</b> the M14A and M14D travel 14th Street.</li></ul>
<p class="small">Not every line runs at all hours; check MTA service before heading out.</p>'''
S.TRANSIT = TRANSIT
info('/visit/', P2C['visit_title'], P2C['visit_desc'], P2C['visit_h1'], p2_visit(), ldjson(store_ld()) + ldjson(faq_ld(P2C['vfaq'])))
faqs = C.FAQ(S)
info('/faq/', 'Bookstore Questions', C.FAQ_DESC(S), C.FAQ_H1, faq_html(faqs), ldjson(faq_ld(faqs)))
for g in C.GUIDES(S):
    info(g['path'], g['title'], g['desc'], g['h1'], g['html'], (ldjson(store_ld()) if g.get('store_ld') else '') + ''.join(ldjson(o) for o in g.get('ld', [])), wide=g.get('wide', False), cr=g.get('crumbs'))
if C.QUIZ:
    Q = C.QUIZ
    qhtml = ''.join(f'<fieldset class="qq"><legend>{i+1}. {E(q["q"])}</legend>' + ''.join(f'<label><input type="radio" name="q{i}" value="{j}"{" required" if j==0 else ""}> {E(o["label"])}</label>' for j, o in enumerate(q['options'])) + '</fieldset>' for i, q in enumerate(Q['questions']))
    info(f'/{Q["slug"]}/', Q['title'], Q['desc'], Q['h1'], f'''<p class="lead">{Q['lead']}</p><form id="quiz" class="quiz">{qhtml}<button class="btn" type="submit">{E(Q['submit'])}</button></form>
<div id="quizout" aria-live="polite"></div><script>window.NI_QUIZ={json.dumps([[o['filter'] for o in q['options']] for q in Q['questions']])}</script>''')
def policy(path, title, slug, intro):
    info(path, title, f'{title} for {BRAND} orders.', title, f'<p class="lead">{intro}</p><p>Orders are fulfilled by the Namaste Shopify store, so the official {title.lower()} lives there:</p><p><a class="btn" href="{SHOP}/policies/{slug}">Read the full {title.lower()}</a></p>')
policy('/shipping/', 'Shipping Policy', 'shipping-policy', f'Books leave from New York City, and you see the delivery choices and their price before paying.{" Prefer to collect? Pick Pickup and get your books at " + STORE_ADDR + "." if PICKUP_ON else ""}')
policy('/returns/', 'Refund Policy', 'refund-policy', 'Received the wrong book or a damaged copy? The refund policy explains what qualifies and how to send it back.')
policy('/privacy/', 'Privacy Policy', 'privacy-policy', 'This site does not use accounts or collect payment details; checkout and payment are handled by Shopify. This site uses Google Analytics to count visits and see which pages and products are viewed; Google may set cookies to do this. The privacy policy below covers the data collected at checkout.')
policy('/terms/', 'Terms of Service', 'terms-of-service', 'Purchases made through this site are completed on Shopify and governed by the terms below.')
page('/cart/', f'Your cart | {BRAND}', f'Your {BRAND} cart. Check out on Shopify, or collect for free at {STORE_ADDR}.',
     f'<section class="wrap prose cartpage"><h1>Your cart</h1><p class="cmsg" role="status" aria-live="polite"></p><div data-cart-page><div class="cbody" data-cart-body><p>Loading your cart&hellip;</p></div></div>'
     f'<noscript><p>The cart needs JavaScript. Call <a href="tel:{TEL}">{PHONE}</a> and we will set your order aside.</p></noscript></section>',
     '<meta name="robots" content="noindex">', canonical=False, index=False)
page('/404.html', f'Page not found | {BRAND}', 'Page not found', f'<section class="wrap prose"><h1>{E(C.NOT_FOUND)}</h1><p>This page may have been reshelved or removed.</p><p><a class="btn" href="/shop/">Back to the shop</a></p></section>', canonical=False, index=False)

# ---- sitemap / robots / CNAME ----
open(os.path.join(DIST, '.nojekyll'), 'w').write('')
if SITE.startswith('https://') and 'github.io' not in SITE: open(os.path.join(DIST, 'CNAME'), 'w').write(SITE.split('://', 1)[1] + '\n')
today = datetime.date.today().isoformat()
open(os.path.join(DIST, 'sitemap.xml'), 'w').write('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join(f'<url><loc>{SITE}{u}</loc><lastmod>{today}</lastmod></url>' for u in SITEMAP) + '</urlset>')
open(os.path.join(DIST, 'robots.txt'), 'w').write('User-agent: *\nDisallow: /\n' if PREVIEW else p2_robots())
open(os.path.join(DIST, 'llms.txt'), 'w').write(p2_llms())
summary = {'site': SITE, 'count': len(products), 'cards': len(leaders), 'aisles': {AISLES[k][0]: cat_count[k] for k in AISLE_KEYS}, 'brands': {BR.NAME[k]: n for k, n in brand_count.most_common()},
           'brand_pages': len(dir_items), 'pages': len(SITEMAP), 'pickup_on': PICKUP_ON, 'ready': READY, 'ranked': HAS_RANK, 'min_stick': S.MIN_STICK, 'under10': S.UNDER10,
           'review_url_set': bool(REVIEW_URL), 'gsc_set': bool(GSV)}
json.dump(summary, open(os.path.join(ROOT, 'data', 'summary.json'), 'w'), indent=1)
print(json.dumps({k: v for k, v in summary.items() if k != 'brands'}))
