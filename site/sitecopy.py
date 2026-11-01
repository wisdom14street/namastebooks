"""Namaste Books (namastebooks.com): a browsable bookstore for the spiritual, metaphysical and philosophy shelves of the
Namaste inventory. Books only (plus true book-and-deck sets). Copy written for this site only."""
import re, os, json, types, collections
from bookcls import book_kind, shelf_of, split_author, is_isbn
E = __import__('html').escape
ICON = 'book'
FAM_LABEL, FAM_ALL, STYLE_LABEL, STYLE_ALL = 'Kind of book', 'Every kind', 'Edition', 'All editions'
NO_FAMILY = ()
QUIZ = None
NAV_AISLES = False
PRICE_OPTS = '<option value="0-12">Under $12</option><option value="0-18">Under $18</option><option value="0-25">Under $25</option><option value="25-99999">$25 and up</option>'
PRICE_BANDS = [('Under $15', 0, 15), ('$15 to $25', 15, 25), ('$25 and up', 25, 1e9)]

SPANISH_RX = re.compile(r'spanish edition|\(spanish\)|en espa[nñ]ol|edici[oó]n|\bgu[ií]a\b|hechizo|espiritualidad|\bmagia\b|\blibro\b|\bel poder\b|\bde la\b|\bpara\b.*\bel\b', re.I)
INFO = {}   # handle -> {'author','isbn','kind','shelf','short','publisher','lang'}
PUBLISHERS = {'Llewellyn Worldwide Ltd.': 'Llewellyn', 'Llewellyn Publications': 'Llewellyn', 'Red Wheel/Weiser': 'Red Wheel/Weiser', 'New World Library': 'New World Library',
              'Self-Realization Fellowship': 'Self-Realization Fellowship', 'Lotus Press': 'Lotus Press', 'Schiffer Publishing': 'Schiffer Publishing', 'Shambhala Publications': 'Shambhala',
              'Hay House': 'Hay House', 'Crystal Clarity Publishers': 'Crystal Clarity Publishers', 'DK Publishing': 'DK'}
def category(p):
    k = book_kind(p)
    if not k: return None
    t = p['title']; sku = (p['variants'][0].get('sku') or '').strip()
    short, author = split_author(t)
    if not author:
        m = re.search(r'\s[-\u2013]\s([A-Z][\w.\' ]{3,38})$', t)   # "Title - Author" style
        if m and len(m.group(1).split()) <= 4: short, author = t[:m.start()].strip(), m.group(1).strip()
    shelf = 'sets' if k == 'set' else ('spanish' if SPANISH_RX.search(t) or 'Spanish' in p.get('tags', []) else shelf_of(p))
    INFO[p['handle']] = {'author': author, 'isbn': sku if is_isbn(sku) else '', 'kind': k, 'shelf': shelf, 'short': short or t,
                         'publisher': PUBLISHERS.get(p.get('vendor', ''), ''), 'lang': 'es' if shelf == 'spanish' else 'en'}
    return shelf
def assign(x): return x['base']

_K = [('For beginners', r"beginner|\b101\b|for dummies|introduct|\bbasics\b|starter|first steps|made easy|simple guide|essential guide|complete guide|handbook|a guide to|learn"),
      ('Workbooks & daily practice', r'workbook|journal|daily|365|a day\b|every day|practice|rituals?\b|exercises|spells for|meditations for|deck and book'),
      ('Sacred texts & classics', r'gita|sutras?\b|upanishad|dhammapada|tao te ching|bible|quran|koran|book of the dead|kybalion|emerald tablet|corpus hermeticum|yoga vasistha|ramayana|mahabharata|classic|translated|translation|commentary'),
      ('Lives & memoirs', r'memoir|biograph|autobiograph|life of|my life|story of|journey of|letters'),
      ('Pocket & gift editions', r'pocket|little book|mini\b|tiny|small book|gift edition|hardcover gift')]
def _slug(n): return re.sub(r'[^a-z0-9]+', '-', n.lower()).strip('-')
FAMILIES = [(_slug(n), n, rx) for n, rx in _K]
def style_of(t, b, base):
    if base == 'sets': return 'Book & deck set'
    if base == 'spanish': return 'Spanish-language edition'
    return ''

# ---- authors (shown as "brand" by the engine): only authors with 3 or more titles in stock get a page
def _author_counts():
    p = os.path.join(os.path.dirname(__file__), '..', 'data', 'all_products.json')
    c = collections.Counter()
    try:
        for q in json.load(open(p)):
            if not any(v['available'] and float(v['price']) > 0 for v in q['variants']): continue
            if not book_kind(q): continue
            a = split_author(q['title'])[1]
            if a: c[_slug(a)] += 1
    except Exception:
        pass
    return c
_AC = _author_counts(); _AN = {}
def _brand_of(title, vendor=''):
    a = split_author(title)[1]
    if not a: return ''
    k = _slug(a)
    if _AC.get(k, 0) < 3: return ''
    _AN.setdefault(k, a); return k
BR = types.SimpleNamespace(NAME=_AN, brand_of=_brand_of, FACTS={})
def BRAND_ABOUT(name): return {"@type": "Person", "name": name}

AISLES = {
 'tarot':      ('Tarot Books', 'Tarot', 'tarot-books', 'Card-by-card references, spread books and histories of the tarot.', '#7a3b8f'),
 'divination': ('Runes, Pendulums & Psychic Arts', 'Divination', 'divination-psychic-books', 'Runes, pendulums, numerology, palmistry, oracles and developing intuition.', '#5b5fa8'),
 'astrology':  ('Astrology', 'Astrology', 'astrology-books', 'Birth charts, planets, houses, transits and the signs, Western and Vedic.', '#1f5f8b'),
 'witchcraft': ('Witchcraft, Wicca & Paganism', 'Witchcraft', 'witchcraft-wicca-pagan-books', 'Spellbooks, grimoires, the wheel of the year, folk magic and pagan paths.', '#3d2b4f'),
 'crystals':   ('Crystals & Stones', 'Crystals', 'crystal-books', 'Crystal references and stone lore, the books people keep next to their collection.', '#2f8f83'),
 'buddhism':   ('Buddhism, Zen & Meditation', 'Buddhism', 'buddhism-meditation-books', 'Dharma teachers, Zen, Tibetan traditions, Taoism and how-to-sit meditation books.', '#a0522d'),
 'hindu-yoga': ('Hinduism, Yoga & Vedanta', 'Yoga & Vedanta', 'hinduism-yoga-vedanta-books', 'The Gita and Upanishads, yoga philosophy, tantra, saints and gurus.', '#c2571a'),
 'angels':     ('Angels & Spirit Guides', 'Angels', 'angel-spirit-guide-books', 'Angels, archangels, guides and the ascended masters.', '#b08a2e'),
 'dreams':     ('Dreams & Astral Travel', 'Dreams', 'dream-books', 'Dream dictionaries, lucid dreaming and astral projection.', '#3a4d7a'),
 'energy':     ('Chakras, Reiki & Energy Work', 'Energy work', 'chakra-reiki-energy-books', 'The chakra system, Reiki manuals, auras, qigong and sound.', '#8f3b5c'),
 'herbs':      ('Herbs, Oils & Plant Lore', 'Herbs', 'herbal-aromatherapy-books', 'Herbals, aromatherapy, incense making and the folklore of plants.', '#4f7a2e'),
 'shamanism':  ('Shamanism & Earth Traditions', 'Shamanism', 'shamanism-books', 'Shamanic journeying, power animals, Toltec wisdom and land-based traditions.', '#7a5a2e'),
 'esoteric':   ('Esoteric, Occult & Mystery Schools', 'Esoteric', 'esoteric-occult-books', 'Hermeticism, Kabbalah, alchemy, ceremonial magic and the Western mystery schools.', '#2b2b2b'),
 'religions':  ('World Religions & Mystics', 'World religions', 'world-religion-books', 'Christian mystics, Sufism and Rumi, Judaism, Islam, Jainism and comparative religion.', '#5a6b2e'),
 'feng-shui':  ('Feng Shui & Chinese Wisdom', 'Feng shui', 'feng-shui-chinese-wisdom-books', 'Feng shui, the I Ching and classical Chinese thought.', '#a33a2e'),
 'self-help':  ('Self-Help & Personal Growth', 'Self-help', 'self-help-personal-growth-books', 'Manifesting, habits, relationships, purpose and the inner work of everyday life.', '#c48a1a'),
 'spirit':     ('Spirituality & Philosophy', 'Spirituality', 'spirituality-philosophy-books', 'Awakening, consciousness, Stoics and sages: the shelf that does not fit a single tradition.', '#6b4f3a'),
 'spanish':    ('Libros en Espa\u00f1ol', 'En espa\u00f1ol', 'libros-en-espanol', 'Spanish-language titles on tarot, magic, spirituality and self-help.', '#b03a5b'),
 'sets':       ('Book & Deck Sets', 'Book & deck sets', 'book-and-deck-sets', 'Boxed sets where a full book comes with its own deck of cards.', '#4a3b8f'),
}
def CARD_TAG(x): return INFO.get(x['handle'], {}).get('author') or AISLES[x['aisle']][1]
SHOP_ORDER = None
del SHOP_ORDER

VISIT_EYEBROW = 'Rather browse the real shelves?'
def STORE_DESC(S): return f'Online bookstore for spiritual, metaphysical and philosophy books, with about {S.ABOUT_N:,} titles on {len(S.AISLE_KEYS)} shelves, supplied from Namaste Bookshop near Union Square.'
REVIEW_TITLE = 'Found a good book here?'
REVIEW_TEXT = 'A short Google review helps other readers find these shelves.'
LOGO_SVG = '<svg viewBox="0 0 40 40"><path d="M6 9c5-2 10-2 14 1v23c-4-3-9-3-14-1z" fill="none" stroke="#d9a441" stroke-width="2.2" stroke-linejoin="round"/><path d="M34 9c-5-2-10-2-14 1v23c4-3 9-3 14-1z" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linejoin="round"/></svg>'
WORDMARK = 'Namaste <b>Books</b>'
SEARCH_PLACEHOLDER = 'Search titles or authors: Pema Chodron, runes, Gita'
NAV_EXTRA = ('<a href="/shelves/">All shelves</a><a href="/shop/tarot-books/">Tarot</a><a href="/shop/astrology-books/">Astrology</a><a href="/shop/witchcraft-wicca-pagan-books/">Witchcraft</a>'
             '<a href="/shop/buddhism-meditation-books/">Buddhism</a><a href="/shop/hinduism-yoga-vedanta-books/">Yoga &amp; Vedanta</a><a href="/new-arrivals/">Just added</a>')

def FOOTER_EXPLORE(S):
    return [('Every shelf', '/shelves/'), ('Just added', '/new-arrivals/'), ('Books under $15', '/books-under-15/'), ('How to choose a first book', '/guide/choosing-your-first-book/'),
            ('Authors A to Z', '/authors/'), ('Book a reading at Namaste', 'https://namastebookshop.com/pages/book-a-reading')]
FOOT_BLURB = 'A bookstore you can browse shelf by shelf: tarot to Taoism, astrology to Advaita, sorted the way a bookseller would sort them.'
HERO_BASES = ('tarot',)
def HERO(S): return {'eyebrow': '', 'h1': '', 'lede': ''}

def _new(S): return sorted([x for x in S.leaders if not x['noimg']], key=lambda x: x['created'], reverse=True)
def _pop(S, xs): return S.by_rank(xs) if S.HAS_RANK else sorted(xs, key=lambda x: x['created'], reverse=True)
def shelf_row(S, title, xs, href, link, sub=''):
    xs = [x for x in xs if not x['noimg']][:12]
    if len(xs) < 4: return ''
    return (f'<section class="wrap shelfsec"><div class="sechead"><h2>{E(title)}</h2><a href="{href}">{E(link)} &rarr;</a></div>{f"<p class=\"intro\">{sub}</p>" if sub else ""}'
            f'<div class="grid shelf">{"".join(S.card(x) for x in xs)}</div></section>')
HOME_ORDER = ['tarot', 'astrology', 'witchcraft', 'buddhism', 'hindu-yoga', 'crystals', 'divination', 'energy', 'esoteric', 'self-help', 'angels', 'dreams', 'shamanism', 'herbs', 'religions', 'spirit', 'feng-shui', 'sets', 'spanish']
def _spines(S):
    return '<nav class="spines" aria-label="Shelves">' + ''.join(f'<a href="/shop/{S.AISLES[k][2]}/" style="--c:{S.AISLES[k][4]}"><span>{E(S.AISLES[k][1])}</span><small>{S.cat_count[k]}</small></a>' for k in HOME_ORDER if k in S.AISLE_KEYS) + '</nav>'
def HOME_BODY(S):
    top = f'''<section class="bookhead"><div class="wrap"><h1>Namaste Books <span>spiritual, metaphysical &amp; philosophy books</span></h1>
<p class="small">{S.N:,} books in stock, sorted onto {len(S.AISLE_KEYS)} shelves. The books come from <a href="{S.SHOP}">Namaste Bookshop</a> at 2 W 14th St, NYC, which ships them or holds them for pickup.</p>{_spines(S)}</div></section>'''
    rows = []
    if S.HAS_RANK: rows.append(shelf_row(S, 'Popular at Namaste right now', S.by_rank(S.leaders), '/shop/', 'Browse all books', 'Ordered by what sells most at Namaste Bookshop.'))
    rows.append(shelf_row(S, 'Just added to the shelves', _new(S), '/new-arrivals/', 'Everything just added'))
    for k in HOME_ORDER[:6]:
        if k in S.AISLE_KEYS: rows.append(shelf_row(S, S.AISLES[k][0], _pop(S, [x for x in S.leaders if x['aisle'] == k]), f'/shop/{S.AISLES[k][2]}/', f'All {S.cat_count[k]}'))
    authors = sorted(S.brand_count.items(), key=lambda kv: -kv[1])[:16]
    au = ('<section class="wrap"><div class="sechead"><h2>Authors with a full shelf</h2><a href="/authors/">Authors A&ndash;Z &rarr;</a></div><div class="chips">' +
          ''.join(f'<a class="chip" href="/authors/{k}/">{E(S.BRAND_NAME[k])} <small>{n}</small></a>' for k, n in authors) + '</div></section>') if authors else ''
    more = []
    for k in HOME_ORDER[6:12]:
        if k in S.AISLE_KEYS: more.append(shelf_row(S, S.AISLES[k][0], _pop(S, [x for x in S.leaders if x['aisle'] == k]), f'/shop/{S.AISLES[k][2]}/', f'All {S.cat_count[k]}'))
    lists = ''.join(f'<a class="chip" href="{L["path"]}">{E(L["h1"])}</a>' for L in LANDINGS(S) if L['path'].startswith('/reading-list/') and sum(1 for x in S.products if S.match(x, L['filter'])) >= 4)
    rl = f'<section class="wrap"><div class="sechead"><h2>Reading lists</h2></div><div class="chips">{lists}</div></section>' if lists else ''
    return top + ''.join(rows[:2]) + f'<section class="wrap">{S.p2_badges()}</section>' + ''.join(rows[2:]) + au + rl + ''.join(more) + S.section({'type': 'visit'}) + S.section({'type': 'review'})

def HOME_TITLE(S): return 'Namaste Books | Spiritual, Tarot, Astrology & Philosophy Bookstore Online'
def HOME_DESC(S): return f'Browse {S.N:,} spiritual and metaphysical books by shelf: tarot, astrology, witchcraft, Buddhism, yoga philosophy, crystals and more. Ships from NYC or pick up at Namaste Bookshop, 2 W 14th St.'
def SHOP_TITLE(S): return 'All Books | Namaste Books'
def SHOP_DESC(S): return f'Search and filter {S.N:,} spiritual, metaphysical and philosophy books by shelf, author, kind of book and price. Ships from New York City.'
SHOP_H1 = 'Every book on our shelves'
def SHOP_SUB(S): return f'{S.N:,} titles. Pick a shelf, type an author or title, or sort by price.'
def AISLE_TITLE(S, k): return f'{AISLES[k][0]} | Namaste Books' if 'Books' in AISLES[k][0] or k == 'spanish' else f'{AISLES[k][0]} Books | Namaste Books'
def AISLE_DESC(S, k): return f'{S.cat_count[k]} books on the {AISLES[k][1].lower()} shelf. {AISLES[k][3]} Shipped from NYC or held for pickup on West 14th Street.'

def _lists():
    return [('/reading-list/learning-tarot/', 'Learning tarot: books to read with your first deck', {'aisle': ['tarot'], 'q': r'beginner|learn|101|guide|easy|simple|essential|complete|handbook|made easy'},
             'Titles that teach the cards from the start, with meanings and spreads you can try the same evening.'),
            ('/reading-list/meditation-to-start/', 'Starting to meditate', {'aisle': ['buddhism', 'spirit', 'self-help'], 'q': r'meditat|mindful|breath|sit\b|stillness'},
             'Short, practical books on sitting, breathing and paying attention, from several traditions.'),
            ('/reading-list/bhagavad-gita/', 'Bhagavad Gita editions and commentaries', {'q': r'gita'}, 'Different translators and teachers on the same 700 verses, so you can pick the voice that suits you.'),
            ('/reading-list/spellbooks-and-grimoires/', 'Spellbooks and grimoires', {'aisle': ['witchcraft', 'esoteric', 'spanish'], 'q': r'spell|grimoire|book of shadows|hechiz|charms|magic\b|magick'},
             'Collections of spells, charms and workings, from kitchen witchcraft to ceremonial texts.'),
            ('/reading-list/moon-books/', 'Books about the moon', {'q': r'\bmoon|lunar'}, 'Moon phases, lunar astrology and moon rituals, gathered from every shelf.'),
            ('/reading-list/tao-and-zen/', 'The Tao and Zen', {'q': r'\btao|zen\b|koan|chuang'}, 'Lao Tzu, Chuang Tzu and the Zen teachers, in translations and modern retellings.'),
            ('/reading-list/chakra-books/', 'Understanding the chakras', {'q': r'chakra'}, 'Maps of the chakra system and books on working with it in yoga and energy practice.')]
def LANDINGS(S):
    L = []
    for path, h1, f, intro in _lists():
        n = sum(1 for x in S.products if S.match(x, f))
        if n < 4: continue
        L.append({'path': path, 'title': f'{h1} ({n} books) | Namaste Books', 'desc': f'{intro} {n} in stock at Namaste Books.', 'h1': h1, 'sub': f'{n} books in stock.', 'filter': f,
                  'intro': f'<p class="intro">{E(intro)}</p>'})
    L.append({'path': '/books-under-15/', 'title': 'Spiritual Books Under $15 | Namaste Books', 'desc': 'Paperbacks and pocket editions under $15 from every shelf of Namaste Books.',
              'h1': 'Books under $15', 'sub': 'Paperbacks, pocket books and small editions.', 'filter': {'maxp': 15}})
    return L

def brand_intro(S, k, st):
    sh = ' and '.join(S.AISLES[a][0].lower() for a, _ in st['aisles'].most_common(2))
    return f'<p>{st["n"]} books by {E(S.BRAND_NAME[k])} in stock, shelved under {E(sh)}. Prices from {S.money(st["min"])}.</p>'
def brand_faq(S, k, st):
    n = S.BRAND_NAME[k]
    return [(f'How many {n} books does Namaste Books have?', f'{st["n"]} titles are in stock today; the list updates every day.'),
            (f'Can I pick up a {n} book in Manhattan?', 'Yes. Choose Pickup at checkout and collect it inside Namaste Bookshop at 2 W 14th St.')]
def BRAND_H1(S, k): return f'Books by {S.BRAND_NAME[k]}'
def BRAND_TITLE(S, k, st): return f'{S.BRAND_NAME[k]} Books ({st["n"]} in stock) | Namaste Books'
def BRAND_DESC(S, k, st): return f'{st["n"]} books by {S.BRAND_NAME[k]} with prices beginning at {S.money(st["min"])}. Order online for delivery or reserve a copy for the 14th Street counter.'
def BRANDS_TITLE(S): return 'Authors A to Z | Namaste Books'
def BRANDS_DESC(S): return 'Authors with three or more books in stock at Namaste Books, A to Z.'
BRANDS_H1 = 'Authors A to Z'
def BRANDS_LEAD(S, n): return f'{n} authors have three or more titles in stock. Every other author is findable with the search box or on the <a href="/shelves/">shelves</a>.'

PAIR = {k: [k] for k in AISLES}
CART_PAIR_TITLE = 'From the same shelf'
REL_BRAND = 'More by {brand}'
REL_SCENT = 'Also {scent}'
REL_PAIR = 'Readers also browse'
REL_MORE = 'More from the {aisle} shelf'
SHELF_LINE = {
 'tarot': 'It sits with our tarot books, where card meanings, spreads and tarot history live.',
 'divination': 'It is shelved with divination: runes, pendulums, numbers, palms and intuition.',
 'astrology': 'You will find it on the astrology shelf, next to chart guides and books on the planets.',
 'witchcraft': 'It lives on the witchcraft and pagan shelf, among spellbooks and seasonal practice.',
 'crystals': 'It belongs to the crystals and stones shelf.',
 'buddhism': 'It is on the Buddhism, Zen and meditation shelf.',
 'hindu-yoga': 'It is on the shelf for Hinduism, yoga philosophy and Vedanta.',
 'angels': 'It is shelved with books on angels and spirit guides.',
 'dreams': 'It sits on the dreams and astral travel shelf.',
 'energy': 'It is shelved with chakra, Reiki and energy-work books.',
 'herbs': 'It is on the herbs, oils and plant lore shelf.',
 'shamanism': 'It is on the shamanism and earth traditions shelf.',
 'esoteric': 'It sits with the esoteric and occult titles: Hermetic, Kabbalistic and ceremonial.',
 'religions': 'It is on the world religions and mystics shelf.',
 'feng-shui': 'It is shelved with feng shui and classical Chinese thought.',
 'self-help': 'It is on the self-help and personal growth shelf.',
 'spirit': 'It is on the general spirituality and philosophy shelf.',
 'spanish': 'Es un libro en espa\u00f1ol, en nuestra secci\u00f3n de libros en espa\u00f1ol.',
 'sets': 'It is a boxed set: a full book together with its own deck of cards.',
}
def describe(S, x):
    i = INFO.get(x['handle'], {})
    s = [f"<b>{E(i.get('short') or x['title'])}</b>" + (f" by {E(i['author'])}" if i.get('author') else '') + '.', SHELF_LINE.get(x['aisle'], '')]
    if i.get('publisher'): s.append(f"Published by {E(i['publisher'])}.")
    if i.get('isbn'): s.append(f"ISBN {E(i['isbn'])}.")
    s.append('Ships from New York City, or choose Pickup at checkout and collect it inside Namaste Bookshop at 2 West 14th Street.')
    return [t for t in s if t]
def PRODUCT_DESC(S, x, v0):
    i = INFO.get(x['handle'], {})
    return f"{i.get('short') or x['title']}" + (f" by {i['author']}" if i.get('author') else '') + f", {S.money(v0['price'])}. {AISLES[x['aisle']][1]} shelf at Namaste Books. Ships from NYC or pick up at 2 W 14th St."
def FACTS_EXTRA(S, x, v0):
    i = INFO.get(x['handle'], {}); f = []
    if i.get('author') and not x['brand']: f.append(('Author', E(i['author'])))
    if i.get('publisher'): f.append(('Publisher', E(i['publisher'])))
    if i.get('isbn'): f.append(('ISBN', E(i['isbn'])))
    if i.get('lang') == 'es': f.append(('Language', 'Spanish'))
    return f
def LD_EXTRA(S, x, v0):
    i = INFO.get(x['handle'], {})
    d = {'@type': ['Product', 'Book'] if i.get('kind') == 'book' else 'Product', 'inLanguage': 'es' if i.get('lang') == 'es' else None,
         'brand': {'@type': 'Brand', 'name': i['publisher']} if i.get('publisher') else None}
    if i.get('author'): d['author'] = {'@type': 'Person', 'name': i['author']}
    if i.get('isbn') and i.get('kind') == 'book': d['isbn'] = i['isbn']
    if i.get('publisher'): d['publisher'] = {'@type': 'Organization', 'name': i['publisher']}
    return d

def ABOUT_DESC(S): return 'About Namaste Books: an online bookstore for the spiritual and metaphysical shelves of Namaste Bookshop, run by Wealth Edge Ventures Inc.'
ABOUT_H1 = 'About Namaste Books'
def ABOUT(S):
    return f'''<p class="lead">Namaste Books is the bookstore half of Namaste, put online so you can browse it the way you would browse a shop: shelf by shelf.</p>
<p>About {S.ABOUT_N:,} titles are listed on {len(S.AISLE_KEYS)} shelves, from tarot and astrology to Zen, Vedanta, Hermeticism and self-help. Each book is filed on one shelf, and authors with several books in stock get their own page so you can read through them.</p>
<h2>Where the books come from</h2><p>{S.LEGAL} The books are the same stock carried by Namaste Bookshop, a New York shop on West 14th Street owned by the same company. When you check out, the order is placed with <a href="{S.SHOP}" rel="noopener">namastebookshop.com</a> on Shopify, which takes payment and ships from New York City.</p>
<h2>How we decide what is "popular"</h2><p>{'Rows labeled popular follow the best-selling order on namastebookshop.com. We do not invent staff picks or reviews.' if S.HAS_RANK else 'Until sales order is available, rows are sorted by when books were added. We do not invent staff picks or reviews.'}</p>
<h2>Pick up in person</h2><p>Any book can be collected inside Namaste Bookshop at {S.STORE_ADDR}. Call <a href="tel:{S.TEL}">{S.PHONE}</a> or email <a href="mailto:info@namastebookshop.com">info@namastebookshop.com</a>.</p>{S.hours_html()}{S.visit_buttons()}'''
def FAQ_DESC(S): return 'Namaste Books questions: shipping, pickup on 14th Street, ordering a title you cannot find, Spanish-language books and book-and-deck sets.'
FAQ_H1 = 'Bookstore questions'
def FAQ(S):
    return [('Are these new books?', 'Yes. Listings are new stock from Namaste Bookshop unless a listing says otherwise.'),
            ("I can't find a title. Can you get it?", f'Call <a href="tel:{S.TEL}">{S.PHONE}</a> or email <a href="mailto:info@namastebookshop.com">info@namastebookshop.com</a> and ask; the shop can tell you whether it can be ordered.'),
            ('Do you sell tarot decks here?', 'This site is for books. The only decks here are boxed sets that include a full book. Namaste Bookshop sells decks on its own site.'),
            ('Do you have books in Spanish?', 'Yes, see <a href="/shop/libros-en-espanol/">Libros en Espa\u00f1ol</a>.'),
            ('How does shipping work?', 'Checkout runs on Shopify through namastebookshop.com. You see every delivery option and its price before paying; parcels leave from New York.'),
            ('Can I pick up instead?', f'Yes. Choose Pickup at checkout and collect at Namaste Bookshop, {S.STORE_ADDR}.' + (f' Orders are {S.READY.lower()}.' if S.READY else '')),
            ('How are books sorted onto shelves?', 'By the main subject of the title. A book on tarot and astrology lands on whichever subject leads; use the search box to find it either way.')]

def GUIDES(S):
    tiles = ''.join(f'<li><a href="/shop/{S.AISLES[k][2]}/"><b>{E(S.AISLES[k][0])}</b></a> <span class="small">{S.cat_count[k]} books</span><br><span class="small">{E(S.AISLES[k][3])}</span></li>' for k in HOME_ORDER if k in S.AISLE_KEYS)
    return [
     {'path': '/shelves/', 'title': 'Every Shelf in the Store', 'desc': f'The {len(S.AISLE_KEYS)} shelves of Namaste Books with what each covers and how many books are on it.', 'h1': 'Every shelf in the store',
      'html': f'<p class="lead">Start from a subject. Each shelf opens with its most-read titles, then every book on it.</p><ul class="dir shelves">{tiles}</ul>'},
     {'path': '/new-arrivals/', 'title': 'Just Added', 'desc': 'The books most recently added to Namaste Books, newest first.', 'h1': 'Just added to the shelves', 'wide': True,
      'html': f'<p class="lead">The latest titles to arrive, newest first. This list refreshes every day.</p>{S.grid(_new(S)[:48])}<p><a class="btn" href="/shop/?sort=new">See every book, newest first</a></p>'},
     {'path': '/guide/choosing-your-first-book/', 'title': 'How to Choose Your First Spiritual Book', 'desc': 'A bookseller-style way to pick a first book on tarot, astrology, meditation or magic: start with a question, check the shelf, read the first page.', 'h1': 'Choosing your first book on a new subject',
      'html': '''<p class="lead">Walking into a new subject is easier with one good book than with ten. A few habits help you find it.</p>
<h2>Start with a question, not a topic</h2><p>"Tarot" is huge. "How do I read three cards for myself?" is a question a single book can answer. Pick the question, then look for a title that promises to answer it.</p>
<h2>Check which shelf it sits on</h2><p>The shelf tells you the angle. A book on the moon can be astrology, witchcraft or a meditation guide. Our <a href="/shelves/">shelf list</a> shows what each one covers.</p>
<h2>Prefer a practice book first, a history second</h2><p>Hands-on titles (spreads to try, a sitting routine, a first spell) keep you going. Histories and deep references make more sense once you have tried the practice.</p>
<h2>Follow one author for a while</h2><p>Many writers here have several books in stock. If the first one clicks, the <a href="/authors/">author pages</a> make the next pick easy.</p>
<h2>Ask at the shop</h2><p>Namaste Bookshop's staff on West 14th Street can point you along the shelves in person.</p><p><a class="btn" href="/reading-list/learning-tarot/">Books for learning tarot</a></p>'''},
    ]
NOT_FOUND = 'That page is not on our shelves'
def ICON_DRAW(d, s, th):
    w = max(2, int(2.2 * s))
    d.line([(6*s, 10*s), (20*s, 12*s), (20*s, 33*s), (6*s, 31*s), (6*s, 10*s)], fill=th['accent'], width=w, joint='curve')
    d.line([(34*s, 10*s), (20*s, 12*s), (20*s, 33*s), (34*s, 31*s), (34*s, 10*s)], fill=th['paper'], width=w, joint='curve')
HOME_SECTIONS = []
