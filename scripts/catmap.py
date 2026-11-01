"""Incense aisles for Namaste Incense: product_type + title rules over the namastebookshop.com catalog."""
import re
CATS = {
 'sticks':  ('Incense Sticks', 'Masala, dhoop and charcoal-free sticks from India, Japan, Tibet and the American Southwest.'),
 'cones':   ('Cones & Backflow Cones', 'Classic cones and backflow cones that send smoke pouring down a fountain burner.'),
 'resins':  ('Sacred Resins', 'Frankincense, myrrh, copal, benzoin, dragon\'s blood, amber and bakhoor to burn on charcoal.'),
 'smudge':  ('Sage, Palo Santo & Smudge', 'White sage, blue sage, cedar, sweetgrass, palo santo and ready-made cleansing kits.'),
 'holders': ('Holders & Ash Catchers', 'Wood boats, coffin boxes, ceramic and brass holders that catch every bit of ash.'),
 'burners': ('Burners, Backflow & Charcoal', 'Censers, cauldrons, smudge bowls, backflow fountains, charcoal tablets and tongs.'),
 'candles': ('Ritual & Aromatherapy Candles', 'Herbal, smudge, chakra, intention and ritual candles to burn beside your incense.'),
}
TYPE2CAT = {
 'Incense Sticks': 'sticks', 'Incense': 'sticks', 'Incense Cones': 'cones',
 'Resin Incense': 'resins', 'Incense Chips': 'resins',
 'Sage': 'smudge', 'Palo Santo': 'smudge', 'Smudging': 'smudge', 'Energy Cleansing Kit': 'smudge',
 'Incense Holder': 'holders', 'Incense Burner': 'burners',
 'Ritual Candle': 'candles', 'Reiki Herbal Pillar Candle': 'candles', 'Soy Herbal Votive Candle': 'candles',
}
TITLE_TYPES = {'', 'Spiritual Kit & Bundle', 'Herbs', 'Herb', 'Wall Hanging', 'Statue', 'Candle', 'Candles', 'Oil Burner'}
NOT_INCENSE = re.compile(r'statue|figurine|oil\b|spray|mist|soap|book|deck|tarot|crystal point|gemstone assorted|fluorite|black ritual salt|tortoise box', re.I)
CANDLE_OK = re.compile(r'ritual|reiki|smudg|chakra|herbal|affirmation|mojo|astro magic|7 days|prayer|good karma|sage|palo santo|aromatherapy|beeswax|frankincense|myrrh|blessed|lakshmi|ganesh|diya', re.I)

def _by_title(t):
    if re.search(r'charcoal|backflow.*burner|burner|censer|cauldron|smudge (pot|bowl)|tongs', t, re.I): return 'burners'
    if re.search(r'holder|ash ?catcher|incense (box|boat|sled)', t, re.I): return 'holders'
    if re.search(r'cone', t, re.I) and re.search(r'incense|dhoop|backflow|copal', t, re.I): return 'cones'
    if re.search(r'smudge kit|smudge stick|sage stick|white sage|blue sage|sweet ?grass|palo santo|cedar|cleansing bundle', t, re.I) and not re.search(r'incense', t, re.I): return 'smudge'
    if re.search(r'resin incense|copal|frankincense|myrrh|benzoin|bakhoor|dragon.?s blood resin', t, re.I) and not re.search(r'stick|candle', t, re.I): return 'resins'
    if re.search(r'incense|agarbatti|dhoop|masala', t, re.I): return 'sticks'
    return None

def category(p):
    t, ty = p['title'], p.get('product_type', '')
    if re.search(r'\bby [A-Z]', t): return None  # books
    if re.search(r'charcoal (tablet|briquette)|swift.?lite|charcoal \d|charcoal tongs', t, re.I): return 'burners'
    if ty in ('Candle', 'Candles'):
        if re.search(r'incense matches', t, re.I): return 'burners'
        if re.search(r'holder', t, re.I) and re.search(r'incense', t, re.I): return 'holders'
        return 'candles' if CANDLE_OK.search(t) else None
    if ty in TYPE2CAT:
        c = TYPE2CAT[ty]
        if ty == 'Resin Incense' and re.search(r'charcoal', t, re.I): return 'burners'
        if ty == 'Resin Incense' and re.search(r'ritual salt', t, re.I): return None
        if ty == 'Smudging' and re.search(r'fluorite|gemstone|crystal', t, re.I): return None
        if ty == 'Incense Burner' and re.search(r'holder|ash catcher', t, re.I) and not re.search(r'charcoal|backflow|resin', t, re.I): return 'holders'
        if ty == 'Incense Holder' and re.search(r'backflow|charcoal|cauldron', t, re.I): return 'burners'
        return c
    if ty in TITLE_TYPES:
        if ty == 'Statue' and not re.search(r'incense', t, re.I): return None
        if ty == 'Oil Burner': return None
        if ty in ('Herbs', 'Herb') and not re.search(r'sage|palo|cedar|sweetgrass', t, re.I): return None
        if ty != 'Statue' and NOT_INCENSE.search(t) and not re.search(r'incense', t, re.I): return None
        if re.search(r'candle', t, re.I): return 'candles' if CANDLE_OK.search(t) else None
        return _by_title(t)
    return None
