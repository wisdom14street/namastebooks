#!/usr/bin/env python3
"""Audit every in-stock book against the shelf rules.

Run after scripts/fetch.py. A failure means a title's main subject landed on a misleading shelf,
or a calendar, journal, audio title, DVD, or unphotographed book was dropped.
"""
import os, sys, json, re
from collections import Counter
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path[:0] = [os.path.join(ROOT, 'scripts'), os.path.join(ROOT, 'site')]
import sitecopy
from bookcls import book_kind, off_topic, is_spanish_title, split_author, title_parts, _TITLE_RULES, reviewed_shelf, SHELF_KEYS

RAW = json.load(open(os.path.join(ROOT, 'data', 'all_products.json')))
FAILS = []

def fail(msg):
    FAILS.append(msg)

def short_title(t):
    return split_author(t)[0]

stock = []
for p in RAW:
    if not book_kind(p): continue
    if not any(v.get('available') and float(v.get('price') or 0) > 0 for v in p['variants']): continue
    stock.append(p)

kept, dropped = [], []
for p in stock:
    shelf = sitecopy.category(p)
    (kept if shelf else dropped).append((p, shelf))

print(f'stock books {len(stock)}  kept {len(kept)}  dropped {len(dropped)}')
counts = Counter(s for _, s in kept)
for k, n in counts.most_common():
    print(f'  {n:4}  {k}')

# ---- nothing leaves the catalog unless it is outside the bookstore ----
for p, _ in dropped:
    if not off_topic(p['title']):
        fail(f'dropped a bookstore title: {p["title"][:140]}')
for p, shelf in kept:
    if book_kind(p) == 'book' and off_topic(p['title']):
        fail(f'off-topic title still listed: {p["title"][:140]}')

# calendars, audio, DVDs, and books with no photo stay
kinds = Counter()
nophoto = 0
for p, shelf in kept:
    ty = (p.get('product_type') or '').strip().lower()
    kinds[ty] += 1
    if not p.get('images'): nophoto += 1
    if ty == 'almanacs & calendars' and shelf != 'journals':
        fail(f'calendar not on the journal shelf: {p["title"][:120]} -> {shelf}')
    if ty in ('dvd', 'spiritual dvd', 'audio course') and not shelf:
        fail(f'missing av title: {p["title"][:120]}')
if nophoto < 1:
    fail('no unphotographed titles survived; they are supposed to stay')
if kinds.get('almanacs & calendars', 0) < 1:
    fail('no calendars in the catalog')
print(f'no-photo kept {nophoto}  dvds {kinds.get("dvd",0)+kinds.get("spiritual dvd",0)}  audio {kinds.get("audio course",0)}  calendars {kinds.get("almanacs & calendars",0)}')

# one known shelf per book
for p, shelf in kept:
    if shelf not in sitecopy.AISLES:
        fail(f'unknown shelf {shelf} for {p["title"][:100]}')

def subject_rows():
    """Titles whose shelf is a subject, not language, format, or a boxed set."""
    out = []
    for p, shelf in kept:
        if shelf in ('spanish', 'journals', 'sets'): continue
        out.append((shelf, short_title(p['title']), p['title']))
    return out

rows = subject_rows()

def expect(rx, shelf, why):
    rx = re.compile(rx, re.I)
    for got, short, full in rows:
        if rx.search(short) and got != shelf:
            fail(f'{why}: {full[:130]} -> {got}, expected {shelf}')

def expect_head(rx, shelf, why):
    """The subject has to be in the main title. A subtitle mention does not decide the shelf."""
    rx = re.compile(rx, re.I)
    for p, got in kept:
        if got in ('spanish', 'journals', 'sets'): continue
        head, _ = title_parts(p['title'])
        if rx.search(head) and got != shelf:
            fail(f'{why}: {p["title"][:130]} -> {got}, expected {shelf}')

def forbid(shelf, rx, why):
    rx = re.compile(rx, re.I)
    for got, short, full in rows:
        if got == shelf and rx.search(short):
            fail(f'{why}: {full[:130]}')

# Lead subject. Multi-subject titles are allowed to follow the subject the title leads with,
# so these patterns are the ones that should not lose to a vaguer shelf.
expect(r'tao te ching', 'feng-shui', 'Tao Te Ching is Taoism, not Buddhism')
expect_head(r'\bqigong\b|chi kung', 'energy', 'qigong in the main title is energy work')
expect_head(r'\btarot\b', 'tarot', 'tarot in the main title is a tarot book')
expect(r"philosopher'?s stone", 'esoteric', "the philosopher's stone is alchemy")
expect(r'bhagavad gita', 'hindu-yoga', 'the Gita is Hindu philosophy')
expect(r'\b(norse|greek|celtic|slavic|egyptian) myths\b', 'mythology', 'myth anthologies are not practice manuals')
expect(r"world's greatest myths", 'mythology', 'myth anthologies are not practice manuals')

forbid('buddhism', r'tao te ching|descartes|yoga nidra', 'Buddhism shelf is Buddhist teaching, not Taoism, Descartes, or yoga nidra')
forbid('astrology', r'saving the planet|prenatal shadow|cancer diagnosis|from cancer', 'planet, natal, and the disease cancer are not astrology')
forbid('crystals', r'\baristotle\b|philosopher|joshua stone|gabriel stone', 'a person named Stone, or alchemy, is not a crystal book')
forbid('witchcraft', r"world's greatest myths|\b(norse|greek|celtic|slavic) myths\b|fairy tales", 'myth and fairy-tale collections are not witchcraft')
forbid('hindu-yoga', r'pilates|stretching anatomy', 'fitness manuals are not yoga philosophy')
forbid('meditation', r'benjamin franklin|what happened to you|way: a novel', 'a virtues list, a trauma book, and a novel are not meditation')
forbid('tarot', r'the blessed life', 'a discourse titled The Blessed Life is not a tarot book')
forbid('feng-shui', r'\bikigai\b', 'ikigai is not feng shui')
forbid('self-help', r'dalai lama|thich nhat|pema chodron|tenzin palmo|\blojong\b', 'Buddhist teachers are not filed as self-help')
forbid('esoteric', r"world's greatest myths|\bgreek myths\b|\begyptian myths\b", 'myth retellings are not the mystery schools')
forbid('divination', r'^the art of war\b|^art of war\b', 'the Art of War is strategy, not divination')

# A folklore/myth/legend word that appears only after the colon cannot pull a book onto Myths
# when the main title already names another subject. Myth collections stay on Myths.
_MYTH_WORD = re.compile(r'\bmyths?\b|\bmythology\b|\bfolklore\b|\blegends?\b|\bfairy tales\b|\bepic tales\b', re.I)
for p, shelf in kept:
    if shelf in ('spanish', 'journals', 'sets'): continue
    head, sub = title_parts(p['title'])
    low = p['title'].lower()
    if low.startswith('herbal magick') and shelf != 'herbs':
        fail(f'Herbal Magick belongs with herbs, not {shelf}')
    if 'women who run with the wolves' in low and shelf != 'mythology':
        fail(f'Women Who Run with the Wolves is a myth collection, not {shelf}')
    if 'guide to divination' in head.lower() and shelf != 'divination':
        fail(f'a divination guide belongs on divination, not {shelf}: {p["title"][:100]}')
    if shelf != 'mythology' or not sub or _MYTH_WORD.search(head): continue
    if any(s != 'mythology' and w >= 8 and rx.search(head) for s, w, rx in _TITLE_RULES):
        fail(f'subtitle put this on Myths: {p["title"][:140]}')

# language shelf, checked on the full title
for p, shelf in kept:
    if shelf in ('journals', 'sets'): continue
    if is_spanish_title(p['title'], p.get('tags') or []) and shelf != 'spanish':
        fail(f'Spanish title not on the Spanish shelf: {p["title"][:130]} -> {shelf}')

# publishers used as brand are never the shop or a wholesaler
for vendor, expected in (('Namaste Bookshop', ''), ('Llewellyn Worldwide Ltd.', 'Llewellyn'), ('Simon & Schuster', 'Simon & Schuster')):
    got = sitecopy.publisher_name(vendor)
    if got != expected:
        fail(f'publisher {vendor!r} -> {got!r}, expected {expected!r}')

# a few titles that have to be present in this catalog; skip quietly if the shop sells out
MUST_CONTAIN = [
    ('tao te ching', 'feng-shui'),
    ('four agreements', 'shamanism'),
    ('start where you are', 'buddhism'),
    ('metaphysics by aristotle', 'spirit'),
    ('usted puede sanar', 'spanish'),
    ('power of now', 'spirit'),
    ('celtic tales', 'mythology'),
    ('hands of light', 'energy'),
]
lookup = [(p['title'].lower(), shelf) for p, shelf in kept]
for needle, shelf in MUST_CONTAIN:
    hits = [s for t, s in lookup if needle in t]
    if not hits:
        print(f'  (not in stock) {needle}')
        continue
    if shelf not in hits:
        fail(f'{needle!r} in stock but not on {shelf}: {set(hits)}')

if set(sitecopy.AISLES) != set(SHELF_KEYS):
    fail(f'SHELF_KEYS drifted from AISLES: {sorted(set(sitecopy.AISLES) ^ set(SHELF_KEYS))}')

def _fake(title, tags, typ='books'):
    return {'title': title, 'handle': 'fixture', 'product_type': typ, 'tags': tags, 'body_html': '',
            'variants': [{'sku': '9780000000001', 'price': '12.00', 'available': True}]}

herb = 'Herbal Magick: A Guide to Herbal Enchantments, Folklore, and Divination'
if sitecopy.category(_fake(herb, [])) != 'herbs':
    fail('untagged Herbal Magick should stay on herbs')
if sitecopy.category(_fake(herb, ['nb-shelf:mythology'])) != 'mythology':
    fail('nb-shelf:mythology should override the keyword shelf')
if sitecopy.category(_fake(herb, ['NB-Shelf:Witchcraft'])) != 'witchcraft':
    fail('nb-shelf tag should be read case-insensitively')
if sitecopy.category(_fake(herb, ['nb-shelf:herbs', 'nb-shelf:mythology'])) != 'herbs':
    fail('two nb-shelf tags should fall back to the keyword shelf')
if sitecopy.category(_fake(herb, ['nb-shelf:not-a-shelf'])) != 'herbs':
    fail('an unknown nb-shelf value should be ignored')
if sitecopy.category(_fake('Usted puede sanar su vida', ['nb-shelf:tarot'])) != 'tarot':
    fail('an explicit shelf should beat the Spanish-language rule')
if sitecopy.category(_fake('Hellboy Seed Of Destruction', [])) is not None:
    fail('an untagged off-topic book should stay off the site')
if sitecopy.category(_fake('Hellboy Seed Of Destruction', ['nb-shelf:spirit'])) != 'spirit':
    fail('a reviewed shelf should keep a book the keyword filter would drop')
if sitecopy.category(_fake('Llewellyn Tarot Calendar 2027', ['nb-shelf:tarot'], typ='Almanacs & Calendars')) != 'tarot':
    fail('a reviewed shelf should beat the automatic journal shelf')
if reviewed_shelf(_fake('Tao Te Ching', ['nb-shelf:feng-shui'])) != 'feng-shui':
    fail('reviewed_shelf should return the tag key')

if FAILS:
    print(f'\n{len(FAILS)} FAILURES')
    for f in FAILS[:80]:
        print(' -', f)
    sys.exit(1)
print(f'\nfull catalog ok ({len(kept)} titles, {len(counts)} shelves)')
