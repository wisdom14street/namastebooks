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
from bookcls import book_kind, off_topic, is_spanish_title, split_author, title_parts, _TITLE_RULES, reviewed_shelf, SHELF_KEYS, is_isbn, isbn_of

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
    reviewed = reviewed_shelf(p)
    if reviewed and shelf != reviewed:
        fail(f'reviewed tag {reviewed} was not kept: {p["title"][:100]} -> {shelf}')
    if ty == 'almanacs & calendars' and not reviewed and shelf != 'journals':
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
    for p, got in kept:
        if reviewed_shelf(p): continue
        if got in ('spanish', 'journals', 'sets'): continue
        if rx.search(short_title(p['title'])) and got != shelf:
            fail(f'{why}: {p["title"][:130]} -> {got}, expected {shelf}')

def expect_head(rx, shelf, why):
    """The subject has to be in the main title. A subtitle mention does not decide the shelf.
    A reviewed nb-shelf tag is allowed to choose a different shelf."""
    rx = re.compile(rx, re.I)
    for p, got in kept:
        if reviewed_shelf(p): continue
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
    if low.startswith('herbal magick') and not reviewed_shelf(p) and shelf != 'herbs':
        fail(f'Herbal Magick belongs with herbs, not {shelf}')
    if 'women who run with the wolves' in low and not reviewed_shelf(p) and shelf != 'mythology':
        fail(f'Women Who Run with the Wolves is a myth collection, not {shelf}')
    if 'guide to divination' in head.lower() and shelf != 'divination':
        fail(f'a divination guide belongs on divination, not {shelf}: {p["title"][:100]}')
    if reviewed_shelf(p) or shelf != 'mythology' or not sub or _MYTH_WORD.search(head): continue
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
lookup = [(p['title'].lower(), shelf) for p, shelf in kept if not reviewed_shelf(p)]
for needle, shelf in MUST_CONTAIN:
    hits = [s for t, s in lookup if needle in t]
    if not hits:
        print(f'  (reviewed or not in stock) {needle}')
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
if sitecopy.category(_fake('Flame Tree Pocket Notebook With Assorted Designs', [])) is not None:
    fail('a blank notebook is not a book and stays off the site')
if sitecopy.category(_fake('Hellboy Seed Of Destruction', ['nb-shelf:spirit'])) != 'spirit':
    fail('a reviewed shelf should override the fiction title rule')
if sitecopy.category(_fake('Llewellyn Tarot Calendar 2027', ['nb-shelf:tarot'], typ='Almanacs & Calendars')) != 'tarot':
    fail('a reviewed shelf should beat the automatic journal shelf')
if reviewed_shelf(_fake('Tao Te Ching', ['nb-shelf:feng-shui'])) != 'feng-shui':
    fail('reviewed_shelf should return the tag key')

def _shelf(title, tags=None, typ='books'):
    return sitecopy.category(_fake(title, tags or [], typ))
if _shelf('Japanese Papers (includes CD) by Varios autores') != 'art-design':
    fail('Japanese Papers is an art reference, not a spiritual book')
if _shelf('Massage Bible The Definitive Guide to Soothing Aches and Pains By Susan Mumford') != 'body-wellness':
    fail('Massage Bible is physical massage, not religion or energy work')
if _shelf('A Week to Change Your Life Harness the Power of Your Birthday and the 7-Day Cycle That Rules Your Health by Olivia Audrey') != 'body-wellness':
    fail('A Week to Change Your Life is a health program, not a spiritual shelf')
if _shelf('John Macmurray: A Biography by John E. Costello') != 'spirit':
    fail('John Macmurray is a philosophy biography and stays on spirit')
if _shelf('Reiki Bible: The Definitive Guide to Healing with Energy By Eleanor McKenzie') == 'body-wellness':
    fail('a Reiki Bible is not the bodywork shelf')
if _shelf('Yoga Bible By Christina Brown') == 'body-wellness':
    fail('a yoga bible is not the bodywork shelf')
if _shelf('Some Design Annual', ['nb-shelf:art-design']) != 'art-design':
    fail('nb-shelf:art-design should be accepted')
if _shelf('A Practical Nutrition Program', ['nb-shelf:body-wellness']) != 'body-wellness':
    fail('nb-shelf:body-wellness should be accepted')
if _shelf("The Land of Stories: An Author's Odyssey by Chris Colfer") != 'fiction':
    fail('Land of Stories is fiction')
if _shelf('Short Stories from the Age of Queen Victoria (Gothic Fantasy) edited by Peter Garratt') != 'fiction':
    fail('the Victorian anthology is fiction')
if _shelf('A Point of Beauty: True Stories of Holding On and Letting Go by The Moth') != 'memoir-essays':
    fail('A Point of Beauty is memoir and essays')
if _shelf('Stretching Anatomy by Arnold G. Nelson') != 'body-wellness':
    fail('Stretching Anatomy is a fitness book on the bodywork shelf')
if _shelf('A Novel Someone Reviewed', ['nb-shelf:fiction']) != 'fiction':
    fail('nb-shelf:fiction should be accepted')
if _shelf('Essays Someone Reviewed', ['nb-shelf:memoir-essays']) != 'memoir-essays':
    fail('nb-shelf:memoir-essays should be accepted')
if _shelf('Hellboy Seed Of Destruction') != 'fiction':
    fail('Hellboy is a book and belongs on fiction')
if _shelf('Climate Courage: How Tackling Climate Change Can Build Community by Andreas Karelas') != 'nature-environment':
    fail('Climate Courage is nature and environment, not a spiritual shelf')
if _shelf('Oceans of Thoughts Book One: An Inspirational Walk through the Inner Self by Rosalind Severin McClean') != 'poetry':
    fail('Oceans of Thoughts is poetry')
if _shelf('Zen and the Art of Saving the Planet by Thich Nhat Hanh') == 'nature-environment':
    fail('a mindfulness book about the planet stays with its tradition')
if _shelf('A Field Guide', ['nb-shelf:nature-environment']) != 'nature-environment':
    fail('nb-shelf:nature-environment should be accepted')
if _shelf('Selected Poems', ['nb-shelf:poetry']) != 'poetry':
    fail('nb-shelf:poetry should be accepted')
cartomancy = _fake('Reading Fortune Telling Cards Book: A Romani Approach Featuring the Gypsy Witch Deck by Fabio Vinago', ['nb-shelf:divination'])
cartomancy['id'] = 7640001380430
cartomancy['product_type'] = ''
cartomancy['variants'][0]['sku'] = '9781646710508'
if sitecopy.category(cartomancy) != 'divination':
    fail('the verified cartomancy guide should be included on divination')
deck = _fake('Everyday Tarot Deck', ['nb-shelf:tarot'], typ='Tarot Deck')
deck['id'] = 999
deck['variants'][0]['sku'] = '9781646710508'
if sitecopy.category(deck) is not None:
    fail('a deck is not included just because the ISBN matches a verified book')
if _shelf('The Perfumed Garden by Captain Sir Richard F. Burton') != 'sexuality-relationships':
    fail('The Perfumed Garden is sexuality and relationship literature')
if _shelf('The Perfumed Garden by Captain Sir Richard F. Burton') in ('self-help', 'religions'):
    fail('The Perfumed Garden is not self-help or world religions')
if _shelf('Luminous Kashi to Vibrant Varanasi by K. Chandramouli') != 'history-culture-travel':
    fail('Luminous Kashi is history, culture, and travel')
if _shelf('Bhagavad Gita by Vyasa') == 'history-culture-travel':
    fail('a scripture stays with its tradition')
if _shelf('A Field Guide to Love', ['nb-shelf:sexuality-relationships']) != 'sexuality-relationships':
    fail('nb-shelf:sexuality-relationships should be accepted')
if _shelf('A City History', ['nb-shelf:history-culture-travel']) != 'history-culture-travel':
    fail('nb-shelf:history-culture-travel should be accepted')
discovery = _fake('Discovery Tarot Path: A New Model for Self-Reading with the Rider-Waite-Smith Deck By Stephanie Leon Neal', ['nb-shelf:tarot'])
discovery['id'] = 7640120852558
discovery['product_type'] = ''
discovery['variants'][0]['sku'] = '9781618521248'
if sitecopy.category(discovery) != 'tarot':
    fail('the verified Discovery Tarot Path paperback should be included on tarot')
same_title = _fake('Discovery Tarot Path: A New Model for Self-Reading with the Rider-Waite-Smith Deck By Stephanie Leon Neal', ['nb-shelf:tarot'])
same_title['id'] = 1
same_title['product_type'] = ''
same_title['variants'][0]['sku'] = '9781618521248'
if sitecopy.category(same_title) is not None:
    fail('the same title is not included without the verified product id')
coventry = _fake('Coventry Magic with Candles, Oils, and Herbs by Jacki Smith', ['nb-shelf:witchcraft'], typ='')
coventry['variants'][0]['sku'] = '9781578635108'
if sitecopy.category(coventry) != 'witchcraft':
    fail('Coventry Magic is already a book from its blank type and ISBN, on witchcraft')
magic = _fake('It’s All Magic: 365 Reflections on Astrology, Tarot, and Manifestation by Aliza Kelly', ['nb-shelf:spirit'], typ='Tarot Deck')
magic['id'] = 7639463460942
magic['variants'][0]['sku'] = '9781401978693'
if sitecopy.category(magic) != 'spirit':
    fail('the verified It\'s All Magic paperback should be included on spirit, not dropped as a deck')
other_deck = _fake('It’s All Magic: 365 Reflections on Astrology, Tarot, and Manifestation by Aliza Kelly', ['nb-shelf:spirit'], typ='Tarot Deck')
other_deck['id'] = 42
other_deck['variants'][0]['sku'] = '9781401978693'
if sitecopy.category(other_deck) is not None:
    fail('a Tarot Deck product is not included just because the ISBN matches It\'s All Magic')
wrong_isbn = _fake('It’s All Magic: 365 Reflections on Astrology, Tarot, and Manifestation by Aliza Kelly', ['nb-shelf:spirit'], typ='Tarot Deck')
wrong_isbn['id'] = 7639463460942
wrong_isbn['variants'][0]['sku'] = '9780000000001'
if sitecopy.category(wrong_isbn) is not None:
    fail('the It\'s All Magic product id is not enough without its ISBN')
if _shelf('The First Female Pharaoh: Sobekneferu, Goddess of the Seven Stars by Andrew Collins', ['nb-shelf:history-culture-travel']) != 'history-culture-travel':
    fail('a reviewed history tag should file First Female Pharaoh on history')
if is_isbn('824297633389'):
    fail('a 12-digit UPC is not an ISBN')
arcana = _fake('The Arcana of Freemasonry: A History of Masonic Signs and Symbols by Albert Churchward', ['nb-shelf:esoteric'])
arcana['id'] = 7639974641742
arcana['handle'] = 'arcana-fixture'
arcana['variants'][0]['sku'] = '824297633389'
if sitecopy.category(arcana) != 'esoteric':
    fail('Arcana of Freemasonry is already a book from its type and belongs on esoteric')
if sitecopy.INFO['arcana-fixture']['isbn'] != '9781578633388':
    fail('the verified ISBN should be recorded for the Arcana UPC stock code')
other_upc = _fake('The Arcana of Freemasonry: A History of Masonic Signs and Symbols by Albert Churchward', ['nb-shelf:esoteric'])
other_upc['id'] = 99
other_upc['handle'] = 'other-upc-fixture'
other_upc['variants'][0]['sku'] = '824297633389'
if sitecopy.category(other_upc) != 'esoteric' or sitecopy.INFO['other-upc-fixture']['isbn']:
    fail('the same UPC on another product is not given this ISBN')
upc_deck = _fake('Everyday Oracle Deck', ['nb-shelf:esoteric'], typ='Oracle Cards')
upc_deck['id'] = 7639974641742
upc_deck['variants'][0]['sku'] = '824297633389'
if sitecopy.category(upc_deck) is not None:
    fail('the verified ISBN pair does not turn a deck into a book')
if isbn_of(other_upc):
    fail('isbn_of should ignore a UPC that is not the verified pair')

if FAILS:
    print(f'\n{len(FAILS)} FAILURES')
    for f in FAILS[:80]:
        print(' -', f)
    sys.exit(1)
print(f'\nfull catalog ok ({len(kept)} titles, {len(counts)} shelves)')
