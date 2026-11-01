"""Shared presentation helpers for the Namaste storefront engine: display titles, cleaned product
descriptions (original store copy, sanitized, with health-claim sentences removed) and typographic
placeholders for products the store has not photographed yet."""
import re, html
from html.parser import HTMLParser

E = html.escape
SMALL = {'a', 'an', 'and', 'as', 'at', 'but', 'by', 'for', 'in', 'nor', 'of', 'on', 'or', 'the', 'to', 'with', 'w/', 'from'}
KEEP_UP = {'OSHO', 'DVD', 'CD', 'USA', 'NYC', 'II', 'III', 'IV', 'VI', 'VII', 'D/T', 'AA', 'AAA', 'XL', 'XXL', 'LED', 'POF', 'UV'}
def smart_case(t):
    letters = [c for c in t if c.isalpha()]
    if not letters or sum(c.isupper() for c in letters) < 0.6 * len(letters): return t
    out = []
    for i, w in enumerate(t.split(' ')):
        core = re.sub(r'[^\w/]', '', w).upper()
        if core in KEEP_UP or re.fullmatch(r'[\dX]+["\u2033\u201d]?\w{0,2}', w): out.append(w); continue
        lw = w.lower()
        out.append(lw if (i and lw in SMALL) else lw[:1].upper() + lw[1:])
    return ' '.join(out)

JUNK = [r'^new age imports\s+', r'\s*[-\u2013|]\s*choose$', r'\s*\|\s*namaste.*$', r'\s*-\s*nirvana inc$', r'\s+-\s*$', r'\s*\(\s*\)\s*', r'\s*[-\u2013]?\s*herbal supplement\b', r'^biodynamic\s+(?=\w+.*flower essence)']
def clean_title(t):
    s = re.sub(r'\s+', ' ', html.unescape(t or '')).strip()
    for rx in JUNK: s = re.sub(rx, ' ', s, flags=re.I).strip()
    s = re.sub(r'\bKates\'?s\'? Magik\b', "Kate's Magik", s)
    s = smart_case(s)
    s = re.sub(r'\s+([,:;])', r'\1', s)
    s = re.sub(r'\s{2,}', ' ', s).strip(' -\u2013|')
    return s or (t or '').strip()

# ---------- descriptions ----------
OK_TAGS = {'p', 'br', 'ul', 'ol', 'li', 'b', 'strong', 'i', 'em'}
BLOCK = {'p', 'div', 'section', 'blockquote', 'tr'}
HEAD = {'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}
DROP = {'script', 'style', 'iframe', 'table', 'img', 'video', 'svg', 'button', 'form', 'noscript', 'object'}
class _P(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True); self.out = []; self.skip = 0; self.cur = []; self.blocks = []; self.list = None
    def flush(self):
        t = re.sub(r'\s+', ' ', ''.join(self.cur)).strip(); self.cur = []
        if t: self.blocks.append(('p', t))
    def handle_starttag(self, tag, a):
        if tag in DROP: self.skip += 1; return
        if self.skip: return
        if tag in BLOCK: self.flush()
        elif tag in HEAD: self.flush(); self.inh = True
        elif tag == 'br': self.cur.append('\n')
        elif tag in ('ul', 'ol'): self.flush(); self.list = []
        elif tag == 'li': self.flush()
        elif tag in ('b', 'strong'): self.cur.append('\x01')
    def handle_endtag(self, tag):
        if tag in DROP: self.skip = max(0, self.skip - 1); return
        if self.skip: return
        if tag in ('b', 'strong'): self.cur.append('\x02')
        elif tag == 'li':
            t = re.sub(r'\s+', ' ', ''.join(self.cur)).strip(); self.cur = []
            if t and self.list is not None: self.list.append(t)
            elif t: self.blocks.append(('p', t))
        elif tag in ('ul', 'ol'):
            self.flush()
            if self.list: self.blocks.append(('ul', self.list))
            self.list = None
        elif tag in BLOCK: self.flush()
        elif tag in HEAD:
            t = re.sub(r'\s+', ' ', ''.join(self.cur)).strip(); self.cur = []
            if t: self.blocks.append(('h', t))
    def handle_data(self, d):
        if not self.skip: self.cur.append(d)
    def close(self):
        super().close(); self.flush()
        if self.list: self.blocks.append(('ul', self.list))
        return self.blocks

HEALTH = re.compile(r'\b(heal(s|ed|ing|er|ers)?|cures?|cured|curing|treat(s|ed|ing|ment|ments)?|remed(y|ies)|reliev\w*|relief|pain\w*|aches?|anxiety|anxious|depress\w*|insomnia|immun\w*|detox\w*|diseases?|illness\w*|ailments?|symptoms?|inflamm\w*|blood|circulat\w*|digest\w*|headaches?|migraines?|arthritis|cancer|tumou?rs?|medic(al|ine|inal|ation)\w*|therap(y|ies|eutic)\w*|health\w*|wellness|metabolism|fertility|hormon\w*|acne|eczema|weight loss|nervous system|organs?|kidneys?|liver|lungs?|heart rate|fda|diagnos\w*|prescri\w*|physicians?|doctors?|stress|nausea|fatigue|sleep (aid|better|disorders?))\b', re.I)
BOOK_CLAIM = re.compile(r'\b(cures?|cured|fda|diagnos\w*|prescri\w*|not intended to)\b', re.I)
METAPHYS = re.compile(r'\b(chakras?|energ(y|ies|etic)|vibration\w*|metaphysical|aura|negativ\w*|protect\w*|amplif\w*|manifest\w*|intentions?|zodiac|spiritual\w*|psychic|meditat\w*|reiki|soul|karm\w*|cleans\w*|ground(ing|s)?|balanc\w*|believed|said to|known as a stone|associated with|abundance|optimism|positivity|luck|prosper\w*|calm\w*|peace\w*|clarity|courage|love|crystal lovers|altar|healers?|practitioners?|ritual\w*)\b', re.I)
SHOPJUNK = re.compile(r'(see more in|compare similar|or see (the full|everything)|^brand: |^brand/supplier|^supplier:|union square|manhattan|14th st|west 14th|\b212[-. ]?\d|\bcall\b|browse (our|the)|our [\w &\-]+ collection|you may also like|looking for more|gift idea|meaningful (gift|present)|perfect gift|shop local|see it in person|in person|available online|order online|our shop|our staff|questions before you buy|published or distributed by|is a book available|^product: |^type: |^form: |^stone: |^product details|why you will love|what makes it special|^highlights$|^details$|^at a glance$|^specifications$|namaste ?bookshop|free shipping|ships? (in|within)|call us|email us|visit (our|us)|in[- ]store|our store|click here|add to cart|buy now|limited stock|while supplies|sku\b|item ?#|wholesale|disclaimer|please note that (this|these) (statements?|products?)|not been evaluated|consult (a|your)|for entertainment|copyright|all rights reserved|https?://|www\.)', re.I)
def _sentences(t): return [s for s in re.split(r'(?<=[.!?])\s+(?=[A-Z0-9"\u201c(])', t) if s.strip()]
def clean_body(body_html, mode='strict', limit=1600, title=''):
    """mode: 'book' (only strips outright medical claims), 'strict' (no health language),
    'mineral' (no health or metaphysical-property language). Returns safe HTML or ''."""
    if not body_html: return ''
    p = _P()
    try: p.feed(body_html); blocks = p.close()
    except Exception: return ''
    bad = BOOK_CLAIM if mode == 'book' else HEALTH
    tkey = re.sub(r'\W+', '', (title or '').lower())[:28]
    def ok(s):
        k = re.sub(r'\W+', '', s.lower())
        if tkey and len(tkey) >= 12 and k.startswith(tkey) and len(s) < len(title) + 60: return False
        if mode != 'book' and s.strip().endswith('?') and len(s) < 90: return False
        if SHOPJUNK.search(s) or bad.search(s): return False
        if mode == 'mineral' and METAPHYS.search(s): return False
        return True
    out, n, seen = [], 0, set()
    STOP = re.compile(r'question|faq|where (to|can i) buy|visit|why shop|related|you may also', re.I)
    for kind, v in blocks:
        if n >= limit: break
        if kind == 'h':
            if out and STOP.search(v): break
            continue
        if kind == 'ul':
            items = [re.sub(r'\s*\(as listed\)', '', re.sub(r'[\x01\x02]', '', i)) for i in v][:14]
            items = [i.rstrip('.') for i in items if ok(i) and len(i) < 220 and i.lower().rstrip('.') not in seen][:10]
            seen.update(i.lower().rstrip('.') for i in items)
            if items: out.append('<ul>' + ''.join(f'<li>{E(i)}</li>' for i in items) + '</ul>'); n += sum(map(len, items))
            continue
        lines = [l.strip() for l in v.split('\n') if l.strip()]
        keep = []
        for l in lines:
            l = re.sub(r'\s*\(as listed\)', '', l)
            if title and l.lower().startswith(title.lower() + ':'): l = l[len(title) + 1:].strip()
            ss = [s for s in _sentences(l) if ok(s) and s.strip().lower() not in seen]
            seen.update(x.strip().lower() for x in ss)
            if ss: keep.append(' '.join(ss))
        t = ' '.join(keep).strip()
        if title and re.sub(r'\W+', '', t.lower()) == re.sub(r'\W+', '', title.lower()): continue
        if len(re.sub(r'[\x01\x02]', '', t)) < 3: continue
        if len(t) + n > limit:
            ss = _sentences(t); t2 = ''
            for s in ss:
                if len(t2) + len(s) + n > limit: break
                t2 += (' ' if t2 else '') + s
            t = t2
            if not t: break
        h = E(t).replace('\x01', '<b>').replace('\x02', '</b>')
        if h.count('<b>') != h.count('</b>'): h = h.replace('<b>', '').replace('</b>', '')
        out.append(f'<p>{h}</p>'); n += len(t)
    return ''.join(out)
def body_text(h): return html.unescape(re.sub(r'<[^>]+>', ' ', h or '')).replace('  ', ' ').strip()

def placeholder(lines, cls='', label='Photo on request'):
    """typographic stand-in for an unphotographed product; lines = [(text, css_class), ...]"""
    inner = ''.join(f'<span class="{c}">{E(t)}</span>' for t, c in lines if t)
    return f'<div class="noph {cls}" role="img" aria-label="{E(lines[0][0] if lines else "")}: {E(label.lower())}">{inner}<em>{E(label)}</em></div>'
