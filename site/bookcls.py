import re
BOOK_TYPES = {'books','book','spiritual book','tarot book','eastern spirituality books','christianity books','spiritual biography','spiritual memoir','yoga memoir','chakra healing book','wellness book',
 'root chakra book','chakra movement book','spiritual guidebook','relationship book','spiritual reflections','spiritual guidance','spiritual comparative text','comparative religion','yoga philosophy',
 'cultural travel book','yoga book','pilgrimage memoir','spiritual culture book','tantric spirituality book','beginner chakra book','spirituality & wellness book','chakra reference book','yoga chakra book',
 'sound healing book','witchcraft book','mindfulness golf book','spiritual scripture','epic fiction','religious text','daily reader','almanacs & calendars'}
DECK = re.compile(r'\b(deck|oracle cards?|tarot cards|card set|lenormand|affirmation cards|playing cards|flash ?cards|\d+ cards)\b', re.I)
SETOK = re.compile(r'(?<!guide)book ?(and|&|/) ?(deck|cards)|(deck|cards) ?(and|&|/) ?(?<!guide)book\b|illustrated book|book (box )?set|box set: .*book', re.I)
JOURNAL = re.compile(r'\bjournal\b|workbook|guided prompts|prompt book', re.I)
NOTBOOK = re.compile(r'reading with|\bmins?\b|minute reading|calendar|bookmark|book ?end|bookstand|book stand|journal|notebook|candle|incense|bracelet|necklace|pendant|\bring\b|crystal tumbled|statue|pouch|bag\b|calendar 20', re.I)
def is_isbn(s): return bool(re.fullmatch(r'97[89]\d{10}', s or '')) or bool(re.fullmatch(r'\d{9}[\dX]', s or ''))
def book_kind(p):
    """'book', 'set' (book-and-deck set) or None"""
    t, ty = p['title'], (p.get('product_type') or '').strip().lower()
    sku = (p['variants'][0].get('sku') or '').strip()
    if ty in ('tarot deck','oracle cards','oracle deck','lenormand deck','mini deck','affirmation deck','tarot set','tarot kit','celtic oracle deck','dream oracle deck','astrology oracle deck','inspirational cards','affirmation cards','inspiration cards','collectable cards','playing cards'):
        return 'set' if SETOK.search(t) or (ty in ('tarot set','tarot kit') and re.search(r'book', t, re.I)) else None
    if ty == 'greeting cards': return None
    if re.search(r'reading with|\bmins?\b|minute reading|witch talk|hypnotherapy|energy cleansing with', t, re.I): return None
    if ty == 'almanacs & calendars' or re.search(r'\b20\d\d\b.*\bcalendar\b|\bcalendar\b.*\b20\d\d\b', t, re.I): return 'journal'
    if ty in ('audio course', 'dvd', 'spiritual dvd'): return 'book'
    bookish = ty in BOOK_TYPES or (ty in ('', 'home decor', 'journal', 'journals', 'gifts') and (is_isbn(sku) or re.search(r'\b[Bb]y [A-Z][\w.\'-]+', t)) and not re.search(r'deck of cards|notebook|wall poster', t, re.I))
    if not bookish: return None
    if JOURNAL.search(t) and not re.search(r'notebook|blank|handcrafted paper|assorted designs', t, re.I) and (is_isbn(sku) or re.search(r'\b[Bb]y [A-Z]', t)): return 'journal'
    if re.search(r'\balmanac|datebook|day planner|planner\b', t, re.I) and not re.search(r'wall calendar', t, re.I): return 'journal'
    st, au = split_author(t)
    if au and (ty in BOOK_TYPES or ty == ''):
        # a titled book with a named author: only rule out decks, kits and blank stationery
        if SETOK.search(t): return 'set'
        if ':' not in st and re.search(r'(\bdeck|\bcards|\bkit)\s*$', st, re.I) and not re.search(r'guide|understanding|reading|hidden|code|book', st, re.I): return None
        if re.search(r'\b\d+\s*cards\b|\b(deck|cards) (and|&) guide|blank|bookmark|wall calendar|art notebook', st, re.I): return None
        if re.search(r'reading with|\bmins?\b|minute reading', st, re.I): return None
        return 'book'
    if NOTBOOK.search(t) and not re.search(r'\bbook\b|guide', t, re.I): return None
    if DECK.search(t): return 'set' if SETOK.search(t) else None
    return 'book'
# Scored shelves. A title can mention several subjects; the strongest specific signal wins.
# Broad words (life, love, stone, planet, meditation-as-a-prefix, goddess, bare "magic") are not shelves by themselves.
# Blurbs are not used: a passing mention was filing Aristotle under crystals and myth collections under witchcraft.
TITLE_RULES = [
 # Practical references that are not spiritual practice. These outrank a stray word such as "bible".
 ('art-design', 12, r'\bjapanese papers\b'),
 ('body-wellness', 12, r'\bmassage bible\b|\ba week to change your life\b'),
 ('tarot', 10, r'\btarot\b|major arcana|minor arcana|rider[\s-]waite|medicine woman inner guidebook'),
 ('divination', 10, r'\blenormand\b|\brunes?\b|\bpendulums?\b|\bi ching\b|\byi jing\b|numerolog|palmistry|palm reading|\boracles?\b|\bdivination\b|tea[\s-]leaves?|scrying|\bdowsing\b|geomancy|clairvoyan|cartomancy|psychometr|\bpsychic\b|mediumship|mind[\s-]reading|psychomancy|crystal gazing|\bcayce\b|messages in the numbers|beyond the veil'),
 ('astrology', 10, r'astrolog|zodiac|horoscope|birth chart|natal chart|\bsun signs?\b|\bmoon signs?\b|rising sign|jyotish|vedic astrology|mercury retrograde|moonology'),
 ('astrology', 8, r'\blunar\b|\bplanetary\b|\bastro\b'),
 ('astrology', 8, r'\b(aries|taurus|gemini|virgo|libra|scorpio|sagittarius|capricorn|aquarius|pisces)\b|self-care for (?:aries|taurus|gemini|cancer|leo|virgo|libra|scorpio|sagittarius|capricorn|aquarius|pisces)\b'),
 ('witchcraft', 10, r'\bwitch|\bwicca|\bpagans?\b|\bpaganism\b|\bmagick|\bspells?\b|spellcraft|\bgrimoires?\b|\bhoodoo\b|\bconjure|folk magic|book of shadows|\bsabbats?\b|samhain|beltane|imbolc|lughnasadh|\byule\b|\bostara\b|\bmabon\b|\bcovens?\b|\bdruids?\b|\bhekate\b|\bhecate\b|\bmorrigan\b|\bbrigid\b|\bfreya\b|\bfrigg\b|cunning (folk|craft)|\bpentacles?\b|\bpentagrams?\b|\bsorcery\b|\blittle book of death\b'),
 ('witchcraft', 9, r'moon magic|lunar magic|candle magic|folk magic|sex magic|sexual magic|norse magic|cord magic|chaos magic|fairy magic|\bfairies\b|\bfaeries\b|\bfaery\b|\bsigils?\b'),
 ('witchcraft', 4, r'\bmagic\b'),
 ('crystals', 10, r'\bcrystals?\b|\bgemstones?\b|\bminerals?\b|\bmoldavite\b|healing stones|book of stones'),
 ('buddhism', 10, r'\bbuddh|\bdharma\b|\bzen\b|dalai lama|\bthich\b|nhat hanh|pema ch|vajrayana|theravada|mahayana|vipassana|bodhisattva|dhammapada|\bkoans?\b|\bsangha\b|\brinpoche\b|\blojong\b|\btonglen\b|\bsiddhartha\b|heart sutra|diamond sutra|lotus sutra|blooming of a lotus'),
 ('meditation', 8, r'\bmeditation\b|\bmeditating\b|\bmindfulness\b|\bmindful\b'),
 ('hindu-yoga', 10, r'\byogas?\b|\byoga\b|vedant|\bvedic\b|\bveda\b|\bvedas\b|bhagavad|\bgita\b|\bhindu|\bkrishna\b|\bshiva\b|\bganesh\b|ganapati|upanishad|ramayana|mahabharata|yogananda|\bramana\b|kundalini|\bsanskrit\b|\bmantras?\b|\bbhakti\b|patanjali|advaita|\bswamis?\b|\byogis?\b|\bkriya\b|\bdevi\b|\bkali\b|\bhanuman\b|\bosho\b|sri aurobindo|nisargadatta|ram dass|krishnamurti|sai baba|amritanandamayi|\bammas?\b|vaisnav|vaishnav|bhagavat|\bsavitri\b|\btantras?\b|\btantric\b|\bshakti\b|\brudra\b|\bpuranas?\b'),
 ('herbs', 10, r'\bherbs?\b|\bherbal\b|aromatherap|essential oils?|flower essences?|plant medicine|\bayurved|smudg|\bincense\b|traditional chinese medicine|\bchinese medicine\b'),
 ('herbs', 8, r'\bcannabis\b|\bpsilocybin\b|magic mushrooms|\bbotanicals?\b'),
 ('energy', 10, r'\bchakras?\b|\breiki\b|\bauras?\b|energy healing|energy medicine|energy field|subtle body|qigong|qi ?gong|chi gung|chi kung|reflexolog|sound healing|singing bowls?|acupressure|acupuncture'),
 ('dreams', 10, r'\bdreams?\b|lucid dream|\bastral\b|out-of-body|out of body|\bdreamwork\b'),
 ('angels', 10, r'\bangels?\b|\barchangels?\b|spirit guides?|ascended masters?'),
 ('shamanism', 10, r'\bshamans?\b|shamanic|medicine wheel|ayahuasca|power animals?|spirit animals?|animal totems?|\btotems?\b|curander[ao]|\btoltec\b|castaneda|miguel ruiz|jose ruiz'),
 ('shamanism', 8, r'animal magic|\baztec wisdom\b|\bmayan wisdom\b|native american (spirituality|shaman|medicine)|\bpsychedelics?\b|\bnavajo\b|\blakota\b|\bhozho\b|ancestral (medicine|healing)'),
 ('esoteric', 12, r'occult (philosophy|primer|science|history|book)|ceremonial magic|chaos magic'),
 ('esoteric', 10, r'kabb?al|qabb?al|hermetic|\balchem|\bgnos[ti]|rosicruc|theosoph|sacred geometry|emerald tablet|\bkybalion\b|\bcrowley\b|\bthelema\b|golden dawn|freemason|\bakash|book of the dead|\bthoth\b|\bankhs?\b|egyptian magic|\bkemetic\b|\bmaat\b|\bbaphomet\b|ars notoria|key of solomon|magic of solomon|lesser key|\bsolomonic\b|\bgurdjieff\b|\bpleiadian\b|seth book'),
 ('esoteric', 7, r'\boccult\b|\batlantis\b|\bhieroglyph'),
 ('religions', 10, r'\bchristian|\bjesus\b|\bbible\b|\bgospels?\b|\bislam\b|\bqur.?an\b|\bkoran\b|\bsufis?\b|\bsufism\b|\brumi\b|\bhafiz\b|\bjudaism\b|\bjewish\b|\btorah\b|\btalmud\b|\bjain\b|\bsikhs?\b|\bsikhism\b|\bcatholic\b|teresa of avila|john of the cross|meister eckhart|cloud of unknowing|zoroastr|medjugorje|\blourdes\b|virgin mary|song of solomon|\bimams?\b|\ballah\b|\bbukhari\b|\bhadith\b|prophet muhammad|\bif[aá]\b|\bobatala\b|\bshango\b|\belegba\b|\borishas?\b'),
 ('religions', 8, r'\bvodou\b|\bvoodoo\b|\bsanter[ií]a\b|\bgibran\b'),
 ('feng-shui', 10, r'feng[\s-]?shui|\btaoism\b|\btaoist\b|tao te|\blaozi\b|\blao tzu\b|chuang tzu|zhuangzi|zhuang zi|\bconfucius\b|\bconfucian\b|sun tzu|art of war|\bthe tao\b|tao of\b|\btao\b'),
 ('feng-shui', 8, r'\btai chi\b|\bshaolin\b|five rings|miyamoto|musashi'),
 ('mythology', 12, r'\bmyths?\b|\bmythology\b|folk (?:&|and) fairy tales|\bfairy tales\b|\blegends\b|\bepic tales\b|\bfolklore\b|\btales of the\b|(?:celtic|norse|greek|egyptian|irish|scottish|slavic|welsh|arthurian) (?:folk )?(?:tales|myths|legends)\b'),
 ('self-help', 9, r'\bbig magic\b|magic of believing|three magic words|\benneagram\b|\bikigai\b'),
 ('self-help', 8, r'self-help|self help|law of attraction|\bmanifest(?:ing|ation|s)?\b|\babundance\b|personal growth|self-esteem|self esteem|\bhabits?\b|codependen|inner child|shadow work|\bgrief\b|\bforgive(?:ness)?\b|\banxiety\b'),
 ('self-help', 6, r'\brelationships?\b'),
 ('spirit', 8, r'\bfalun\b'),
 ('spirit', 7, r'\bphilosophy\b|\baristotle\b|\bplato\b|\bsocrates\b|marcus aurelius|\bstoicism\b|\bstoic\b'),
 ('spirit', 6, r'\benlightenment\b|\bconsciousness\b|\bstoics\b'),
]
AUTHOR_RULES = [
 ('buddhism', r'pema ch|chodron|thich nhat|nhat hanh|dalai lama|chogyam trungpa|jack kornfield|sharon salzberg|tulku thondup|\bbhante\b|\bajahn\b|thubten|yongey mingyur|tsoknyi|tenzin palmo|lobsang tenzin'),
 ('hindu-yoga', r'yogananda|ram dass|krishnamurti|paramahansa|\bosho\b|sri aurobindo|nisargadatta|amritanandamayi|satchidananda|vivekananda|ramakrishna|sai baba|shiva rea|\bprabhuji\b'),
 ('spirit', r'eckhart tolle|neale donald walsch|david r\.?\s*hawkins|michael a\.?\s*singer'),
 ('self-help', r'louise hay|rhonda byrne|wayne dyer|gabrielle bernstein|napoleon hill|og mandino'),
 ('shamanism', r'miguel ruiz|jos[eé] ruiz|alberto villoldo|sandra ingerman'),
 ('witchcraft', r'\bstarhawk\b|scott cunningham|judika illes'),
 ('astrology', r'liz greene|steven forrest|robert hand|linda goodman'),
 ('esoteric', r'aleister crowley|manly p\.?\s*hall|dion fortune|israel regardie|lon milo|regardie|peter j\.?\s*carroll'),
 ('energy', r'barbara brennan|mantak chia'),
 ('meditation', r'kabat[\s-]?zinn'),
]
# Only subject tags that name the shelf directly. Keyword-soup tags and the shop's broad
# department labels (self help, mindfulness, esoteric philosophy, divination and wicca) misfile titles.
TAG_RULES = {
 'buddhism': {'thich nath hanh'},
 'hindu-yoga': {'yoga & ayurveda', 'tantra', 'bhagavad gita', 'hinduism', 'osho', 'vedanta', 'yoga', 'kriya yoga', 'patanjali', 'yoga sutras', 'indian philosophy'},
 'angels': {'angels', 'angel books'},
 'dreams': {'dreams', 'intent-sleep-dreams'},
 'energy': {'chakras', 'reiki', 'chakra healing', 'energy healing', 'energy medicine', 'sound healing'},
 'religions': {'christianity', 'islam', 'judaism', 'jainism'},
 'divination': {'pendulum books'},
}
# More specific shelf wins a tie. Spirit is the leftover shelf, not a competing subject.
TIE_ORDER = ['tarot', 'astrology', 'divination', 'crystals', 'dreams', 'angels', 'energy', 'herbs', 'shamanism', 'witchcraft', 'buddhism', 'meditation', 'hindu-yoga', 'feng-shui', 'esoteric', 'religions', 'mythology', 'self-help', 'art-design', 'body-wellness', 'spirit']
_TITLE_RULES = [(s, w, re.compile(rx, re.I)) for s, w, rx in TITLE_RULES]
_AUTHOR_RULES = [(s, re.compile(rx, re.I)) for s, rx in AUTHOR_RULES]
_MYTH_SKIP = re.compile(r'\b(witch|wicca|pagans?|paganism|spells?|grimoires?|shamans?|shamanic)\b', re.I)
_ES_MARK = re.compile(r'spanish edition|\(spanish\)|en espa[nñ]ol|edici[oó]n en espa', re.I)
_ES_WORD = re.compile(r"\b(el|la|los|las|del|una|unos|para|con|por|su|sus|al|que|como|más|mas|pero|este|esta|usted|puede|libro|gu[ií]a|magia|brujer[ií]a|ángeles|angeles|secreto|poder|vida|amor|meditaci[oó]n|espiritual|hechizo|astrolog[ií]a|cuando|sobre|desde|hacia|también|tambien|palabras|todo|sanar|curaci[oó]n|maestr[ií]a|acuerdos?|camino|sueños|suenos|método|metodo|cómo|como|ñ)\b", re.I)
_ES_ACCENT = re.compile(r'[áéíóúñ¿¡]', re.I)
_FR = re.compile(r'\b(médecine|spirituelle|une histoire|le livre|des |et les)\b', re.I)
_OFF = [
 re.compile(r'^stretching anatomy\b', re.I),
 re.compile(r'^pilates (anatomy|body|for everyone)\b', re.I),
 re.compile(r'\btrim healthy mama\b', re.I),
 re.compile(r'\bhellboy\b', re.I),
 re.compile(r'\bland of stories\b', re.I),
 re.compile(r'short stories from the age of queen victoria', re.I),
 re.compile(r'endless apocalypse short stories', re.I),
 re.compile(r'^until august\b', re.I),
 re.compile(r'history of horror, fear, and the uncanny', re.I),
]
def _norm(s):
    s = re.sub(r'[\u00a0\u202f\u2007\u2009\u200a]', ' ', s or '')
    s = re.sub(r'[\u2010\u2011\u2012\u2013\u2014\u2212]', '-', s)
    return s.replace('\u2019', "'").replace('\u2018', "'")

def is_spanish_title(title, tags=()):
    """Language shelf, decided from the title rather than a subject guess."""
    tags = [t.lower() for t in (tags or [])]
    if 'spanish' in tags or _ES_MARK.search(title or ''): return True
    t = _norm(title)
    if _FR.search(t) and not re.search(r'[ñ¿¡]|ción\b|brujer', t, re.I): return False
    hits = {m.group(0).lower() for m in _ES_WORD.finditer(t)}
    accents = len(_ES_ACCENT.findall(t))
    if accents and len(hits) >= 2: return True
    if len(hits) >= 3: return True
    if re.search(r'\b(brujer[ií]a|hechizos?|astrolog[ií]a|ángeles|espiritualidad|meditaci[oó]n)\b', t, re.I): return True
    return False

def off_topic(title):
    """Books the shop stocks that are not part of this bookstore: fitness manuals, diet cookbooks, comics, and general fiction.
    Calendars, journals, audio, and DVDs are not decided here."""
    t = _norm(title)
    return any(rx.search(t) for rx in _OFF)

def title_parts(title):
    """Split a display title into the main title and the subtitle after a colon.
    'Herbal Magick: A Guide to Folklore' is a herbal-magick book; the subtitle is extra description."""
    t = _norm(split_author(title or '')[0])
    m = re.match(r'^([^:]{3,}?):\s+(\S.*)$', t)
    if not m: return t, ''
    return m.group(1).strip(), m.group(2).strip()

def _add_rules(scores, text):
    if not text: return
    for shelf, w, rx in _TITLE_RULES:
        if shelf == 'mythology' and _MYTH_SKIP.search(text): continue
        if rx.search(text): scores[shelf] += w

def _best(scores):
    return max(scores.values()) if scores else 0

def score_shelf(p):
    """Return (shelf, score-map). One shelf per book.
    A subject named in the main title beats a different subject that shows up only in the subtitle."""
    from collections import Counter
    full = _norm(p.get('title') or '')
    short, author = split_author(full)
    title = _norm(short)
    head, sub = title_parts(title)
    tags = {t.lower() for t in (p.get('tags') or [])}
    scores = Counter()
    _add_rules(scores, head)
    # Weight 8 and up is a real subject (meditation, herbal, tarot). Weaker hits such as a bare "magic" stay open to the subtitle.
    head_locked = _best(scores) >= 8
    if sub and not head_locked:
        _add_rules(scores, sub)
    scope = head if head_locked else title
    who = f'{author} {full}'
    for shelf, rx in _AUTHOR_RULES:
        if rx.search(who): scores[shelf] += 8
    for shelf, names in TAG_RULES.items():
        if tags & names: scores[shelf] += 6
    if scores.get('buddhism') and scores.get('meditation') and re.search(r'buddh|dharma|\bzen\b|dalai|thich|pema|vipassana|sutra|koan|rinpoche|lojong|siddhartha|nhat hanh', who, re.I):
        scores['buddhism'] += 3
    if re.search(r'\byoga\b', scope, re.I) and scores.get('hindu-yoga') and scores.get('herbs'): scores['hindu-yoga'] += 2
    if re.search(r'qigong|qi gong|chi kung|chi gung', scope, re.I) and scores.get('energy'): scores['energy'] += 2
    if re.search(r'\b(i ching|yi jing)\b', scope, re.I) and not re.search(r'feng shui|\btao', scope, re.I): scores['divination'] += 2
    if re.search(r'\btaoism\b|\btaoist\b|tao te|\blao tzu\b|\blaozi\b', scope, re.I) and scores.get('feng-shui'): scores['feng-shui'] += 2
    if re.search(r'notoria|\bsolomon\b|hermetic|kybalion|crowley|golden dawn|ceremonial|book of the dead', scope, re.I): scores['esoteric'] += 3
    if re.search(r'\b(vodou|voodoo|hoodoo)\b', scope, re.I) and re.search(r'\b(magic|magick|spells?)\b', scope, re.I):
        scores['witchcraft'] = max(scores.get('witchcraft', 0), 11)
    # "Tarot" in the main title keeps the book on the tarot shelf. A subtitle mention does not.
    if re.search(r'\btarot\b', scope, re.I) and scores:
        scores['tarot'] = max(scores.get('tarot', 0), max(scores.values()) + 1)
    if not scores: return 'spirit', {}
    best = max(scores.values())
    if best < 5: return 'spirit', dict(scores)
    winners = [k for k, v in scores.items() if v == best]
    # When the main title already names a subject, a tie breaks toward whichever word comes first.
    # Other ties keep the usual shelf order, so books without a subtitle do not move.
    if head_locked and sub:
        winners.sort(key=lambda k: (_first_at(head, k), TIE_ORDER.index(k) if k in TIE_ORDER else 50))
    else:
        winners.sort(key=lambda k: TIE_ORDER.index(k) if k in TIE_ORDER else 50)
    return winners[0], dict(scores)

def _first_at(text, shelf):
    pos = 10**6
    for s, w, rx in _TITLE_RULES:
        if s != shelf: continue
        m = rx.search(text or '')
        if m: pos = min(pos, m.start())
    return pos

def shelf_of(p):
    return score_shelf(p)[0]

# Reviewed shelf assignments. One tag, exactly `nb-shelf:<key>`, wins over title rules.
# Keys match site/sitecopy.py AISLES. Existing subject tags are hints only and are not this contract.
SHELF_KEYS = frozenset({
    'tarot', 'astrology', 'divination', 'crystals', 'dreams', 'angels', 'energy', 'herbs',
    'shamanism', 'witchcraft', 'buddhism', 'meditation', 'hindu-yoga', 'feng-shui', 'esoteric',
    'religions', 'mythology', 'self-help', 'spirit', 'spanish', 'journals', 'sets',
    'art-design', 'body-wellness',
})
_SHELF_TAG = re.compile(r'^nb-shelf:([a-z0-9-]+)$')

def reviewed_shelf(p):
    """The bookseller's shelf, if this product carries exactly one valid nb-shelf tag. Otherwise None."""
    found = []
    for raw in (p.get('tags') or []):
        m = _SHELF_TAG.match((raw or '').strip().lower())
        if m and m.group(1) in SHELF_KEYS and m.group(1) not in found:
            found.append(m.group(1))
    if len(found) == 1:
        return found[0]
    return None
def split_author(t):
    m = re.search(r'\s+[Bb]y\s+((?:[A-Z]|don |bell )[^()|]+?)\s*$', t)
    if not m: return t.strip(), ''
    a = m.group(1).strip(' .,-')
    a = re.split(r'\s*(?:,|;|&| and | with | \(|foreword|illustrated)\s*', a)[0].strip()
    if len(a) > 40 or len(a.split()) > 5: return t.strip(), ''
    return t[:m.start()].strip(' -:'), a
