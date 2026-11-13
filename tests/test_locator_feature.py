import datetime
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, "site"), os.path.join(ROOT, "scripts")]
from locator_feature import make_catalog, normalize_locations, public_sales_floor_locations
from import_shelf_locations import prepare


class LocatorTests(unittest.TestCase):
    def setUp(self):
        self.book = {
            "id": 1234, "handle": "example-book", "dtitle": "Example Book",
            "brand": "author-one", "aisle": "buddhism", "variants": [
                {"sku": "9781234567890"}, {"sku": "9781234567890"}],
            "images": ["/assets/no-photo.svg"], "price": 14.95,
            "created": "2026-11-01T00:00:00Z",
        }

    def test_catalog_keeps_stable_ids_and_valid_isbn(self):
        books = make_catalog([self.book, self.book], {"buddhism": ("Buddhism",)}, {"author-one": "Some Author"})
        self.assertEqual(len(books), 1)
        self.assertEqual(books[0]["id"], "1234")
        self.assertEqual(books[0]["sku"], ["9781234567890"])
        self.assertEqual(books[0]["author"], "Some Author")
        self.assertEqual(books[0]["subject"], "Buddhism")

    def test_unknown_and_unverified_shelves_are_never_published(self):
        src = {"items": {
            "1234": [
                {"code": "A-04-02", "kind": "sales-floor", "verified_at": "2026-11-01"},
                {"code": "MADE UP", "kind": "sales-floor", "verified_at": "2026-11-01"},
                {"code": "B-01-02", "kind": "sales-floor"},
                {"code": "C-01-04", "kind": "backstock", "verified_at": "2026-11-01"},
            ],
            "2222": [{"code": "A-01-01", "verified_at": "2026-11-01"}],
        }}
        out = normalize_locations(src, {"1234"})
        self.assertEqual(len(out), 1)
        self.assertEqual(len(out["1234"]), 2)
        self.assertEqual(out["1234"][0]["code"], "A-04-02")

    def test_future_verification_is_rejected(self):
        future = (datetime.date.today() + datetime.timedelta(days=3)).isoformat()
        out = normalize_locations({"items": {
            "1234": [{"code":"A-02-01","verified_at":future,"kind":"sales-floor"}]
        }}, {"1234"})
        self.assertEqual(out, {})

    def test_import_validates_and_merges(self):
        rows = [
            {"product_id":"1234", "code":"A-04-02","kind":"sales-floor","verified_at":"2026-11-01"},
            {"product_id":"nope", "code":"B-04-02","kind":"sales-floor","verified_at":"2026-11-01"},
        ]
        merged, n, skipped = prepare(rows, {"1234"}, {})
        self.assertEqual(n, 1)
        self.assertEqual(len(skipped), 1)
        self.assertEqual(merged["1234"][0]["code"], "A-04-02")


    def test_import_preserves_multiple_verified_sales_floor_locations(self):
        rows = [
            {"product_id":"1234", "code":"A-04-02", "kind":"sales-floor", "verified_at":"2026-11-01"},
            {"product_id":"1234", "code":"B-01-03", "kind":"sales-floor", "verified_at":"2026-11-01"},
        ]
        merged, accepted, skipped = prepare(rows, {"1234"}, {})
        self.assertEqual(accepted, 2)
        self.assertFalse(skipped)
        self.assertEqual({x["code"] for x in merged["1234"]}, {"A-04-02", "B-01-03"})


    def test_catalog_keeps_single_title_author_and_verified_isbn(self):
        self.book["brand"] = ""
        book = make_catalog(
            [self.book], {"buddhism": ("Buddhism",)}, {},
            {"example-book": {"author": "Solo Author", "isbn": "9781578633388", "kind": "book"}}
        )[0]
        self.assertEqual(book["author"], "Solo Author")
        self.assertEqual(book["isbn"], "9781578633388")
        self.assertEqual(book["format"], "book")


    def test_public_feed_never_exposes_backstock_codes(self):
        verified = {
            "1234": [
                {"code":"A-01-01","kind":"sales-floor","verified_at":"2026-11-01"},
                {"code":"BACK-22","kind":"backstock","verified_at":"2026-11-01"}
            ],
            "5678": [{"code":"BACK-10","kind":"backstock","verified_at":"2026-11-01"}]
        }
        public = public_sales_floor_locations(verified)
        self.assertEqual(list(public), ["1234"])
        self.assertEqual(public["1234"][0]["code"], "A-01-01")
        self.assertNotIn("BACK-22", str(public))


if __name__ == "__main__":
    unittest.main()
