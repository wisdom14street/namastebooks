# Namaste Book Finder — Physical Discovery and Lost-Sale Recovery

**Owner priority:** customers and staff physically finding books in the shop, not merely improving ecommerce SEO.

**Store context:** Namaste Bookshop at 2 West 14th Street, NYC. Main Shopify store: `namastebookshop.com`. Book-only discovery website: `namastebooks.com`, GitHub Pages site `wisdom14street/namastebooks`. The latter uses the former's public online product feed and Shopify checkout. Grok/Cursor is actively improving the catalog; **do not overwrite, reclassify or freeze its ongoing work.**

## Decision: two kinds of shelves must never be conflated

1. **Virtual subject shelf** (31 site categories such as Tarot or Buddhism). In code this is `x['aisle']` and is derived by `site/bookcls.py` using catalog classification. A virtual shelf is a website category **NOT** a physical shelf.
2. **Physical location** (e.g., `B-04-02`, section-bookcase-level). These require on-site mapping and human verification and may have multiple assignments per book (sales-floor copy and backstock). None should be invented from the virtual shelf.

## Source-of-truth ownership

| Field | Authority | Policy |
|---|---|---|
| Title, price, variants, product type, handle/URL, catalog publication | Shopify | Read-only in finder; existing Grok audit owns improvements |
| Inventory quantities by Shopify location | Shopify inventory | Prefer Admin inventory by location for staff; never infer from physical shelf or a website's count |
| ISBN/barcode | Shopify variant SKU/barcode; human-reviewed enrichment | Do not treat a UPC as ISBN without verification; match edition |
| Subject shelves | Existing book classifier | Preserve and enhance only in independently reviewed catalog work |
| Physical section/bookcase/shelf, verified_at, staff reviewer | New physical location store | Independent registry with audit history |
| Staff identity/roles | Dedicated secured auth system | Do not rely on browser localStorage in production |
| Failed lookup/search analytics | Finder event pipeline | Anonymous aggregated data; no customer PII by default |

The public site and finder must **never** write to Shopify inventory. Any adjustments remain a separate staff-authenticated Shopify workflow.

## Counting issue: stop comparing unlike totals

Observed on 2026-11-07:
- NamasteBooks.com home screen: 3,361 books in stock, across 31 virtual subject shelves.
- Shopify Admin: 20,440 total products; 4,135 products typed exactly `Books`; 4,583 products in collection handle `books` (exact queries).
- Main storefront visible Books collection displayed 4,163 as an on-page product count; it is not identical to Admin collection membership.
- Grok reported 2,731 individually researched/updated plus one updated product offline (research progress, not necessarily catalog total).

Reasons for legitimate differences include: Online Store publication, item stock availability, book classifier inclusion, variant availability and price, product type versus collection membership, and duplicate grouped cards. **Do not assert which specific event caused a count change without previous-vs-current product-ID snapshots**.

Build reconciliation should store per-run counters:
1. All Shopify products (Admin);
2. Published to Online Store;
3. Product type and collection membership;
4. Passed book-vs-deck classifier;
5. In-stock / out-of-stock / unavailable variants;
6. Generated public book listings by distinct Shopify product ID;
7. Number of grouped storefront cards;
8. Mapped sales-floor locations and unmapped books.

Keep a daily per-product ID / timestamp diff to identify newly visible, disappeared, out-of-stock, reclassified and added inventory. Log failures; never silently claim a stale feed is current.

## Verified Shopify stock locations — decisive constraint

Read-only Shopify Admin lookup on 2026-11-07 confirmed TWO active fulfillment locations:
- **Bookshop**: `gid://shopify/Location/74879041614`, **2 West 14th Street, New York, NY 10011**
- **Crystalshop**: `gid://shopify/Location/74884939854`, **6 West 14th Street, New York, NY 10011**

Both have `fulfillsOnlineOrders=true`. General online availability can aggregate across locations and must **never** be labeled "available at Bookshop." For real in-store stock, read a product variant's inventory item and inventory levels for **Bookshop** specifically. Display separate public statuses for (1) online listing, (2) stock verified at the Bookshop fulfillment location, (3) physically mapped sales-floor location. Publish neither staff/backroom quantities nor staff identities. On-location spot checks remain necessary even when Shopify shows a positive Bookshop quantity.

A read-only sample of 40 available `Books` products had positive Bookshop quantities; this sample does **not** establish whether the full book catalog includes Crystalshop-only stock.

## Phase 0: Existing integration verified

- `scripts/fetch.py` reads only published products from Shopify public products.json;
- `scripts/build.py` excludes unavailable and zero/invalid-price variants, uses `site/bookcls.py` subject classification and groups editions in shopper cards;
- `.github/workflows/deploy.yml` deploys site to GitHub Pages on pushes to main and on a daily timer. Rebuild frequency is **not real-time inventory**.
- Site already supports author/title search, collection browsing, Shopify checkout/pickup info.
- No physical verified shelf locations in existing store website.

## Phase 1: Customer finder + mapping pilot (this draft PR)

- `/find/`: responsive customer lookup by title, author, subject, ISBN/SKU/Shopify ID, list results with cover and virtual subject, clear "location unknown" state and a large show-to-employee screen.
- `/kiosk/`: full-touch search layout and automatic 120s inactivity reset, no customer login required.
- `/staff/shelf-scan/`: barcode scanner (keyboard wedge) or typed SKU/ISBN/Shopify ID, physical shelf code, local browser draft, CSV export **only**, no shared persistence.
- `site/physical_locations.json`: reviewed version-controlled registry; `scripts/import_shelf_locations.py`: validated dry-run CSV importer.
- No fake map or fake shelf labels; zero verified shelf assignments until actual staff verification.
- No production rollout until automated checks and owner review. Don't disturb Grok's working `main` branch.

**Critical limitation:** local-only staff scanner is **not an authenticated staff app**. It is a temporary prototype. The /staff route is public and cannot store private staff data or act as a multi-device authoritative source.

## Phase 2: Make it operationally reliable

**Dedicated secured backend.** Choose a separate database/project for book location data; verify costs and ownership first. Store `store_location`, `section`, `bookcase`, `shelf`, `product_variant`, `book_placement`, `placement_history`, `scan_event`, `unlocated_request`, `verification_state` and `inventory_feed_status`. 
- Every placement joins Shopify product ID and variant ID when edition-specific, records `bookcase_id`, `shelf_level`, `kind = sales-floor / backstock / display`, `verified_by`, `verified_at`, and `last_seen_at`.
- Multiple locations per edition allowed; one location can contain many different titles.
- Soft delete/move audit rather than overwriting history. Support `unshelved`, `customer-held`, `being-restocked`, `needs-check` to distinguish exceptions.
- Enforce staff auth with server-side role checks, Supabase RLS (if chosen), private service credentials, audit trail. Public finder sees only safe verified physical codes and product availability; never sees staff names, credentials or security notes.
- Sync Shopify Admin APIs using an authorized backend for stock *per store location*. Webhooks plus periodic reconciliation; a failed sync shows a freshness warning rather than stale quantities as guaranteed truth.
- Account for missing ISBN/SKU and mismatched UPC, duplicates and editions.

**Physical setup.** Number bookcases before mass-scan. Use the real floor and existing Matterport walkthrough as planning aids, then verify each bookcase by walking the shop. A color-coded section label plus bookcase number plus shelf level is more actionable than a complex floor map alone. Mark location codes on ends of shelves and returns carts. Keep 1 primary location and optional secondary display/backstock locations.

**Fast employee loop:**
1. Scan shelf tag (locks active shelf).
2. Scan book back-cover barcode; disambiguate editions or missing SKU.
3. Confirm “Book [title] → B-04-02” in one tap, store staff identity and timestamp.
4. Use an exception queue for “Unknown ISBN”, “Inventory says in stock but not found”, “Already on another shelf”.
5. Rescan periodically after replenishment or staff moving books. Staff can look up, move or mark missing in seconds.

## Phase 3: Recover lost sales before building fancy map

At search time:
- If found and shelf verified, show "Go to [section], bookcase [number], shelf [level]" plus a simple plan/photo.
- If listed as in stock but unlocated: show staff request / nearby employee alert, alternate edition or related title, and online order/pickup path.
- If no Shopify stock: show out-of-stock and reorder/notify path, not a bogus exact shelf.
- Capture non-PII `search`, `found`, `requested staff`, `not found`, `substitute sold`, `sale recovered` events. Associate completed purchase using opt-in in-store transaction handoff, not a speculative marketing attribution.
- Optional "hold at counter" workflow only after reliable stock and reservations; don't promise reserves in phase 1.

## Phase 4: In-store directions + kiosk + analytics

- Map real bookcase polygons/coordinates, confirm entrance, paths and accessible routes; Matterport imagery can guide floor-map construction but doesn't tell which books live on each shelf.
- Kiosk near entry with large touch targets, read-only public access, screen reset, locked-down browser, fallback when offline, sturdy power/ethernet, protected admin settings.
- Generate QR codes per bookcase/section that deep-link to `/find/?q=...` or a verified subject/search page. Do not expose unverified codes.
- Namaste HQ analytics: top customer queries, no-result searches, stock/floor mismatch, mapped percentage by product/units, average time to locate, sales recovered from staff intervention, repeated "can't find" titles.
- Sell the idea to staff as **fewer interruptions and fewer lost sales**, not an extra bureaucratic inventory chore.

## Rollout KPIs / pilot gate

Before claiming success, test a pilot of **200-500 actual bestselling/high-ask book SKUs**, plus one troublesome section. Define these before the trial:
- Accuracy: at least 95% verified-placement hit rate in 100 random in-person spot checks (target; adjust after baseline).
- Speed: customer search + employee retrieval median under 60 seconds for mapped titles (target).
- Unmapped requests: log baseline then target a 50% reduction in unlocated “in-stock” requests for pilot titles.
- Maintenance: reshelving/moving a book must take at most two barcode scans and one confirmation.
- Accessibility: staff can use a phone, and customers can use the kiosk with one hand and readable text.

Only then scale to the rest of the ~3,000–4,000 book catalog, and later other product categories if desired. **Do not equate online item count with shelf assignments.**

## Deployment risks

- Grok/Cursor updates the default branch frequently; use a feature branch, test and merge only after checking against latest main. Preserve its work.
- Never mutate Shopify prices, inventory, product type, SEO, canonical URLs or Grok's audit during finder work.
- Customer search should support small-screen iOS, kiosk touch, keyboard, screen reader and accessible focus.
- Static daily catalog can be stale. Warn openly and offer employee verification. In phase 2 use live backend and circuit-breaker/freshness state.
- Do not create new Supabase project or billing without owner selecting the organization and approving any cost.

## Decision needed for production staff app

Which account/organization should own a separate Namaste Book Finder secure database? Existing Supabase connections relate to readers, live shopping and HQ; none was a clear dedicated fit. Site phase 1 requires no database. Phase 2 needs one.
