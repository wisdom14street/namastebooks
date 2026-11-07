"""In-store book finder pages and public, independently verifiable location feed.

The parent site (namastebookshop.com / Shopify) remains the catalog and inventory
source. A "shelf" in site/bookcls.py is a subject, never a physical location.
Physical locations are published only when separately verified.
"""
import datetime
import html
import json
import os
import re

CODE = re.compile(r"^[A-Z][A-Z0-9]{0,11}(?:-[A-Z0-9]{1,12}){1,3}$")


def normalize_locations(source, known_ids):
    """Reject unknown/malformed/unverified shelf assignments, never guess."""
    rows = source.get("items", {}) if isinstance(source, dict) else {}
    if not isinstance(rows, dict):
        return {}
    valid = {}
    for product_id, entries in rows.items():
        pid = str(product_id)
        if pid not in known_ids or not isinstance(entries, list):
            continue
        kept = []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            code = str(entry.get("code") or "").strip().upper()
            when = str(entry.get("verified_at") or "")
            kind = entry.get("kind", "sales-floor")
            if not CODE.fullmatch(code) or kind not in ("sales-floor", "backstock"):
                continue
            try:
                datetime.date.fromisoformat(when)
            except ValueError:
                continue
            if datetime.date.fromisoformat(when) > datetime.date.today():
                continue
            kept.append({"code": code, "kind": kind, "verified_at": when})
        if kept:
            valid[pid] = kept
    return valid


def make_catalog(products, aisles, authors, infos=None):
    """Each Shopify product ID stays distinct even if shop cards group editions."""
    rows = []
    seen = set()
    infos = infos or {}
    for x in products:
        pid = str(x["id"])
        if pid in seen:
            continue
        seen.add(pid)
        info = infos.get(x["handle"], {})
        skus = sorted({str(v.get("sku") or "").strip() for v in x.get("variants", []) if v.get("sku")})
        cover = x["images"][0]
        if cover.startswith("https://") and "width=" not in cover:
            cover += ("&" if "?" in cover else "?") + "width=280"
        rows.append({
            "id": pid, "handle": x["handle"], "title": x["dtitle"],
            "author": info.get("author") or (authors.get(x["brand"], "") if x.get("brand") else ""),
            "subject": aisles[x["aisle"]][0],
            "isbn": info.get("isbn") or "",
            "format": info.get("kind") or "book",
            "sku": skus, "cover": cover, "price": x["price"],
            "created_at": x.get("created", "")[:10],
        })
    return rows


def publish(page, root, dist, products, aisles, authors, site, infos=None):
    rows = make_catalog(products, aisles, authors, infos)
    locations_path = os.path.join(root, "site", "physical_locations.json")
    with open(locations_path, encoding="utf-8") as f:
        raw_locations = json.load(f)
    locations = normalize_locations(raw_locations, {x["id"] for x in rows})
    today = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="minutes")
    with open(os.path.join(dist, "data", "locator-catalog.json"), "w", encoding="utf-8") as f:
        json.dump({"count": len(rows), "built_at": today, "books": rows}, f, ensure_ascii=False, separators=(",", ":"))
    with open(os.path.join(dist, "data", "physical-locations.json"), "w", encoding="utf-8") as f:
        json.dump({"version": 1, "verified_product_count": len(locations), "items": locations}, f, separators=(",", ":"))

    heads = '<link rel="stylesheet" href="/assets/locator.css"><script src="/assets/locator.js" defer></script>'
    intro = (
        '<div class="loc-wrap"><header class="loc-intro"><p class="loc-eyebrow">Namaste Bookshop · 2 W 14th Street, NYC</p>'
        '<h1>Find a book in our store</h1><p>Look up books by title, author, subject or ISBN/SKU. '
        'A subject category is not a physical shelf. Exact locations appear only after our team verifies them.</p></header>'
    )
    search = (
        '<section class="loc-tool" aria-label="Search for a book"><label for="loc-query">Which book are you looking for?</label>'
        '<input id="loc-query" type="search" enterkeyhint="search" autocomplete="off" autofocus '
        'placeholder="Book title, author, topic, ISBN or SKU">'
        '<div class="loc-toolbar"><span id="loc-status" role="status" aria-live="polite">Loading book catalog…</span>'
        '<button type="button" id="loc-clear">Clear search</button></div>'
        '<div id="loc-results" class="loc-results" aria-live="polite"></div>'
        '<button id="loc-more" type="button" hidden>Show more results</button></section>'
        '<dialog id="loc-dialog" class="loc-dialog"><button class="loc-close" type="button" aria-label="Close details">×</button>'
        '<div id="loc-details"></div></dialog></div>'
    )
    foot = (
        '<p class="loc-disclaimer">Catalog availability is refreshed from Shopify daily, not continuously. '
        'An online listing does not guarantee a copy is on the sales floor. '
        'If a location is not verified, show the book to an employee to help locate it.</p>'
    )
    page(
        "/find/", "Find a Book in Store | Namaste Books",
        "Search Namaste Bookshop's catalog and see verified in-store shelf locations where available.",
        '<div data-locator-mode="customer">' + intro + search + foot + "</div>", heads
    )
    page(
        "/kiosk/", "In-Store Book Finder Kiosk | Namaste Books",
        "Customer self-service book search at Namaste Bookshop.",
        '<div data-locator-mode="kiosk">' + intro.replace("Find a book in our store", "What book can we help you find?") +
        search + foot + '<p class="loc-reset">For your privacy, this screen automatically clears after inactivity.</p></div>',
        heads + '<meta name="robots" content="noindex,nofollow">', canonical=False, index=False
    )
    page(
        "/staff/shelf-scan/", "Staff Shelf-Mapping Pilot | Namaste Books",
        "Pilot tool for recording bookcase assignments on this device.",
        '<div data-locator-mode="staff" class="loc-wrap"><header class="loc-intro"><p class="loc-eyebrow">Staff mapping pilot</p>'
        '<h1>Scan books to map shelves</h1><p>This temporary tool saves drafts ONLY in this browser. '
        'It does not update Shopify, the public book finder, or other staff devices. Export your CSV after every session.</p></header>'
        '<section class="loc-tool"><label for="loc-shelf">Physical location code, for example A-04-02</label>'
        '<input id="loc-shelf" autocomplete="off" placeholder="SECTION-BAY-LEVEL" maxlength="24">'
        '<label for="loc-sku">Scan an ISBN/SKU, enter a Shopify product ID, or search by title</label>'
        '<input id="loc-sku" autocomplete="off" inputmode="text" placeholder="Scan barcode; press Enter">'
        '<p id="loc-staff-status" role="status" aria-live="polite"></p>'
        '<div id="loc-staff-matches"></div><h2>Saved on this device</h2><div id="loc-staff-assignments"></div>'
        '<div class="loc-staff-actions"><button type="button" id="loc-export">Export CSV</button>'
        '<button type="button" id="loc-reset-drafts">Clear local drafts</button></div></section></div>',
        heads + '<meta name="robots" content="noindex,nofollow">', canonical=False, index=False
    )
    return {"indexed_books": len(rows), "verified_locations": len(locations)}
