import re
BOOK_TYPES = {'books','book','spiritual book','tarot book','eastern spirituality books','christianity books','spiritual biography','spiritual memoir','yoga memoir','chakra healing book','wellness book',
 'root chakra book','chakra movement book','spiritual guidebook','relationship book','spiritual reflections','spiritual guidance','spiritual comparative text','comparative religion','yoga philosophy',
 'cultural travel book','yoga book','pilgrimage memoir','spiritual culture book','tantric spirituality book','beginner chakra book','spirituality & wellness book','chakra reference book','yoga chakra book',
 'sound healing book','witchcraft book','mindfulness golf book','spiritual scripture','epic fiction','religious text','daily reader','almanacs & calendars'}
DECK = re.compile(r'\b(deck|oracle cards?|tarot cards|card set|lenormand|affirmation cards|playing cards|flash ?cards|\d+ cards)\b', re.I)
SETOK = re.compile(r'(?<!guide)book ?(and|&|/) ?(deck|cards)|(deck|cards) ?(and|&|/) ?(?<!guide)book\b|illustrated book|book (box )?set|box set: .*book', re.I)
NOTBOOK = re.compile(r'reading with|\bmins?\b|minute reading|calendar|bookmark|book ?end|bookstand|book stand|journal|notebook|candle|incense|bracelet|necklace|pendant|\bring\b|crystal tumbled|statue|pouch|bag\b|calendar 20', re.I)
def is_isbn(s): return bool(re.fullmatch(r'97[89]\d{10}', s or '')) or bool(re.fullmatch(r'\d{9}[\dX]', s or ''))
def book_kind(p):
    """'book', 'set' (book-and-deck set) or None"""
    t, ty = p['title'], (p.get('product_type') or '').strip().lower()
    sku = (p['variants'][0].get('sku') or '').strip()
    if ty in ('tarot deck','oracle cards','oracle deck','lenormand deck','mini deck','affirmation deck','tarot set','tarot kit','celtic oracle deck','dream oracle deck','astrology oracle deck','inspirational cards','affirmation cards','inspiration cards','collectable cards','playing cards'):
        return 'set' if SETOK.search(t) or (ty in ('tarot set','tarot kit') and re.search(r'book', t, re.I)) else None
    if ty == 'journals' or ty == 'greeting cards': return None
    bookish = ty in BOOK_TYPES or (ty == '' and (is_isbn(sku) or re.search(r'\bby [A-Z][\w.\'-]+', t)))
    if not bookish: return None
    if NOTBOOK.search(t) and not re.search(r'\bbook\b|guide', t, re.I): return None
    if DECK.search(t): return 'set' if SETOK.search(t) else None
    return 'book'
SHELVES = [
 ('tarot', r'\btarot|lenormand|cartomancy|major arcana|minor arcana', ('tarot book','beginner tarot','learning tarot','tarot')),
 ('divination', r'\brunes?\b|pendulum|i ching|numerolog|palmistry|palm reading|oracle|divination|tea leaf|tea leaves|scrying|dowsing|geomancy|psychic|clairvoyan|mediumship|intuition', ('pendulum books','intuition')),
 ('astrology', r'astrolog|zodiac|horoscope|birth chart|natal|planets?\b|\bsun signs?|moon signs?|saturn return|vedic astrology|jyotish|mercury retrograde', ('astrology',)),
 ('witchcraft', r'witch|wicca|wiccan|pagan|magick|spells?\b|spellcraft|grimoire|hoodoo|conjure|folk magic|occult|sabbat|samhain|beltane|coven|goddess|druid|norse|celtic|faery|fairy|fae\b', ('divination and wicca',)),
 ('crystals', r'crystal|gemstone|\bstones?\b|minerals?', ('crystal book','crystals','stones')),
 ('buddhism', r'buddh|\bzen\b|dharma|dalai lama|thich|nhat hanh|tibetan|lama\b|vipassana|bodhi|sutra(?!s)|pema ch|mindful|meditat|koan|tao\b|taois|tao te|lao tzu|chuang', ('buddhism','meditation','mindfulness','thich nath hanh')),
 ('hindu-yoga', r'\byoga|vedant|vedic|veda\b|vedas|gita|hindu|krishna|shiva|ganesh|upanishad|ramayana|mahabharata|yogananda|ramana|ayurved|tantra|kundalini|sanskrit|mantra|bhakti|patanjali|advaita|swami|guru|devi|kali\b|hanuman|sri |osho|kriya', ('yoga & ayurveda','tantra','bhagavad gita','hinduism','osho','vedanta','yoga','kriya yoga','ayurveda','patanjali','yoga sutras','indian philosophy','eastern spirituality')),
 ('angels', r'\bangel|archangel|spirit guide|ascended master|guardian', ('angels','angel books')),
 ('dreams', r'\bdream|lucid|sleep|astral|out-of-body|out of body', ('dreams','intent-sleep-dreams')),
 ('energy', r'chakra|reiki|aura\b|auras|energy healing|energy medicine|subtle body|qigong|chi gung|reflexolog|sound healing|singing bowl|acupress|acupunct', ('chakras','reiki','bodywork/reiki','energy healing','chakra healing','energy medicine','sound healing')),
 ('herbs', r'\bherb|aromatherap|essential oil|plant medicine|botanical|flower essence|incense|smudg', ('aromatherapy herbs & oils','essential oils')),
 ('shamanism', r'shaman|medicine wheel|native american|ayahuasca|animal spirit|spirit animal|totem|power animal|plant spirit|curandera|toltec|mayan|aztec|andean', ('shamanism',)),
 ('esoteric', r'kabbal|qabal|hermetic|alchem|gnost|rosicruc|thoth|tarot of|esoteric|mystic|mysteries|theosoph|ancient wisdom|atlantis|egyptian|freemason|sacred geometry|secret teachings|manly p', ('esoteric philosophy','ancient tradition philosophy','western spirituality')),
 ('religions', r'christ|jesus|bible|gospel|islam|quran|koran|sufi|rumi|hafiz|judaism|jewish|torah|kabbalah|jain|sikh|saint|prayer|catholic|mary\b', ('christianity','islam','judaism','jainism')),
 ('feng-shui', r'feng shui|i ching|confuci|chinese medicine|qi\b', ('asian philosophy/ feng shui',)),
 ('self-help', r'manifest|law of attraction|abundance|self-help|self help|happiness|habits|success|healing your|heal your|anxiety|confidence|self-esteem|relationships?|love\b|forgive|grief|purpose|mindset|motivation|wisdom|life\b|power of|journey', ('self help','manifestation','personal growth','self-help','intent-money-abundance','intent-manifestation')),
]
SPANISH = re.compile(r'\b(el|la|los|las|del|para|de la|tu|sus|con)\b.*\b(de|y|el|la)\b|ñ|á|é|í|ó|ú', re.I)
def shelf_of(p):
    t = p['title']; tags = [x.lower() for x in p.get('tags', [])]
    if 'spanish' in tags: return 'spanish'
    tl = re.sub(r'\bby [A-Z].*$', '', t)
    for k, rx, tg in SHELVES:
        if re.search(rx, tl, re.I): return k
    for k, rx, tg in SHELVES:
        if any(x in tg for x in tags): return k
    body = re.sub('<[^>]+>', ' ', p.get('body_html') or '')[:600]
    for k, rx, tg in SHELVES:
        if k in ('self-help',): continue
        if re.search(rx, body, re.I): return k
    return 'self-help' if re.search(SHELVES[-1][1], body, re.I) else 'spirit'
def split_author(t):
    m = re.search(r'\s+by\s+([A-Z][^()|]+?)\s*$', t)
    if not m: return t.strip(), ''
    a = m.group(1).strip(' .,-')
    a = re.split(r'\s*(?:,|;|&| and | with | \(|foreword|illustrated)\s*', a)[0].strip()
    if len(a) > 40 or len(a.split()) > 5: return t.strip(), ''
    return t[:m.start()].strip(' -:'), a
