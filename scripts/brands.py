"""Brands we can identify in the namastebookshop.com incense catalog.

A product belongs to a brand when its title matches the brand pattern OR its Shopify vendor field is the brand
itself. Distributor codes in the vendor field (NAGIMPINC, BNJINT, KHPINT, DSGNBDK, OCNLKW, Nirvana Inc, World Buyers,
Benjamin International, Namaste Bookshop) are wholesalers, not brands, so they never create a brand page.

FACTS hold only details checked on a public source (listed in `src`), Oct 29, 2026. Sites phrase them in their own words.
"""
import re
BRANDS = [
 # key, display name, title regex, vendor names that are this brand
 ('hem', 'HEM', r'\bhem\b', []),
 ('satya', 'Satya', r'\bsatya\b', []),
 ('morning-star', 'Morning Star', r'morning star', []),
 ('herb-earth', 'Herb & Earth', r'herb ?& ?earth', []),
 ('good-karma', 'Good Karma', r'good karma', ['Zensual']),
 ('escential-essences', 'Escential Essences', r'escential essences', []),
 ('sonavi', 'SONAVI', r'sonavi', []),
 ('prabhujis', "Prabhuji's Gifts", r'prabhuji', ["Prabhuji's Gifts"]),
 ('coventry-creations', 'Coventry Creations', r'coventry|wicked witch mojo|blessed herbal', ['Coventry Creations']),
 ('wolf-spirit', 'Wolf Spirit Sage', r'wolf.?s? spirit', []),
 ('suns-eye', "Sun's Eye", r"sun.?s eye", ["Sun's Eye"]),
 ('little-smudgies', 'Little Smudgies', r'smudgies', []),
 ('soul-sticks', 'Soul Sticks', r'soul sticks', []),
 ('archangel-incense', 'Archangel Incense', r'archangel incense', []),
 ('fred-soll', 'Fred Soll', r'fred ?soll', ['fredsoll']),
 ('aloha-bay', 'Aloha Bay', r'aloha bay', ['Aloha Bay']),
 ('jens', "Jen's Reiki Candles", r"\bjen'?s\b", ['Jens Candles']),
 ('auroshikha', 'Auroshikha', r'auroshikha', []),
 ('kamini', 'Kamini', r'kamini', []),
 ('swift-lite', 'Swift-Lite', r'swift.?lite', []),
 ('song-of-india', 'Song of India', r'song of india|india temple incense', []),
 ('astro-magic', 'Astro Magic', r'astro magic', []),
 ('manifest-it', 'Manifest It!', r'manifest it!', []),
 ('magic-mini-candles', 'Magic Mini Candles', r'magic mini candles', []),
 ('ispalla', 'Ispalla', r'ispalla', []),
 ('elysian', 'Elysian', r'\belysian\b', []),
 ('nandita', 'Nandita', r'nandita', []),
 ('good-earth-scents', 'Good Earth Scents', r'good earth scents', []),
 ('moldavite-man', 'Moldavite Man', r'^$', ['Moldavite Man']),
 ('tulasi', 'Tulasi', r'tulasi', []),
]
NAME = {k: n for k, n, _, _ in BRANDS}
_RX = [(k, re.compile(rx, re.I)) for k, _, rx, _ in BRANDS]
_V = {v: k for k, _, _, vs in BRANDS for v in vs}

def brand_of(title, vendor=''):
    for k, rx in _RX:
        if rx.search(title): return k
    return _V.get(vendor or '', '')

FACTS = {
 'hem': {'maker': 'HEM Corporation', 'where': 'India, with factories in Mumbai and Bengaluru', 'since': 'founded in 1983 by three brothers of the Shah family', 'note': "its flagship 'HEM Precious' range dates from 1988", 'src': 'https://www.hemincense.com/about-hem/'},
 'satya': {'maker': 'Shrinivas Sugandhalaya', 'where': 'Bangalore, India', 'note': 'the house behind the original Sai Baba Nag Champa; the sticks are hand-rolled masala incense', 'src': 'https://www.namaste-uk.com/section.php/1002/1/satya-nag-champa-original-sai-baba-superhit-incense-sticks-cones-fragrance'},
 'morning-star': {'maker': 'Nippon Kodo', 'where': 'Japan', 'note': 'thin, low-smoke sticks, usually sold with a small holder', 'src': 'https://www.nipponkodo.com/incense/'},
 'herb-earth': {'maker': 'Nippon Kodo', 'note': 'a low-smoke bamboo-stick line in natural scents such as sandalwood, lavender, frankincense, matcha and white sage', 'src': 'https://www.nipponkodo.com/collection/herb-earth.html'},
 'good-karma': {'maker': 'Zensual, the Good Karma Candle Company', 'where': 'Southern California', 'note': 'soy-blend candles hand-poured in the USA in recyclable tins, each pairing a scent with an intention', 'src': 'https://www.zensual.com/'},
 'escential-essences': {'maker': 'the Escential Essences line represented by Matchless Gifts', 'where': 'the USA', 'note': 'hand-dipped sticks and 1-inch cones made with cosmetic-grade oils', 'src': 'https://matchlesswholesale.com/premiumquality-dippedstickincense-packaged.aspx'},
 'sonavi': {'maker': 'New Age Imports, Inc.', 'where': 'Placentia, California', 'note': 'incense sticks, bakhoor chips and beeswax candles', 'src': 'https://newageincense.com/'},
 'prabhujis': {'maker': "Prabhuji's Gifts", 'note': "a Green America certified business whose incense is handmade by artisans in India's cottage industry, packed in recycled cardboard", 'src': 'https://greenamerica.org/green-business/prabhujis-gifts'},
 'coventry-creations': {'maker': 'Coventry Creations (now Coventry Products)', 'where': 'Ferndale, Michigan', 'note': 'a family- and female-owned maker of handmade intention candles, best known for its Blessed Herbal line', 'src': 'https://www.coventryproducts.com/about-us/about-us'},
 'wolf-spirit': {'maker': 'Wolf Spirit Sage', 'where': 'the United States', 'note': 'sage, natural resin incense, smudge sticks and smokeless sprays, made in the US with pickers in California and the High Plains', 'src': 'https://www.faire.com/brand/b_cnyjz71eya'},
 'suns-eye': {'maker': "Sun's Eye", 'where': 'Central Florida', 'note': 'incense, oils and sprays', 'src': 'https://www.sunseye.com/about-us/'},
 'little-smudgies': {'maker': 'Soul Sticks', 'note': 'mini soy-wax smudge candles, 12 to a pack, made with lead-free wicks, herbs and crystals, each burning about 4 hours', 'src': 'https://www.faire.com/product/p_jwbedadyec'},
 'soul-sticks': {'maker': 'Soul Sticks', 'note': 'masala and plant-based incense, smudge kits and intention kits', 'src': 'https://tabarnam.com/company/soul-sticks'},
 'archangel-incense': {'maker': 'Jabou', 'where': 'Canada', 'note': 'natural hand-dipped sticks, 20 to a pack, one blend per archangel', 'src': 'https://www.kheopsinternational.com/p/archangel-incense-20-sticks-haniel/72504.html'},
 'fred-soll': {'maker': "Fred Soll's", 'where': 'Tijeras, New Mexico, about 10 miles east of Albuquerque', 'note': "'Resin on a Stick' incense hand-dipped in pinon and other resins; each stick is burned lying flat and lasts 1 to 2.5 hours", 'src': 'https://www.fredsoll.com/about-the-company/'},
 'aloha-bay': {'maker': 'Aloha Bay', 'where': 'Lower Lake, California', 'since': 'making candles since 1993', 'note': 'chakra candles in RSPO certified palm wax; a member of the World Fair Trade Organization', 'src': 'https://www.alohabay.com/fairtrade/index.php'},
 'auroshikha': {'maker': 'Auroshikha Agarbathies, a unit of Sri Aurobindo Ashram', 'where': 'Pondicherry, India', 'since': 'making incense since 1973', 'note': 'hand-rolled sticks and cones; its fragrances follow IFRA guidelines', 'src': 'https://www.auroshikha.com/about.php'},
 'kamini': {'maker': 'Kamini Aromatics', 'where': 'Bangalore, India', 'note': 'natural masala incense sticks and cones', 'src': 'https://wholesale.incensewarehouse.com/KAMINI-_c_422.html'},
 'swift-lite': {'maker': 'Swift-Lite International Ltd', 'where': 'Ashford, Kent, in the UK', 'since': 'established in 1957', 'note': 'fast-lighting charcoal originally designed for burning religious incense', 'src': 'https://www.swift-lite.com/'},
 'song-of-india': {'maker': 'Song of India (R. Expo)', 'where': 'India and Auburn, Washington', 'since': 'with roots in a Delhi perfumery founded in 1932', 'note': 'its India Temple incense is one of its best-known scents', 'src': 'https://songofindia.com/pages/about-us'},
}
