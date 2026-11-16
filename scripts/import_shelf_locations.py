#!/usr/bin/env python3
"""Review/import staff CSV exports into a version-controlled physical shelf registry.

Never run this against live Shopify inventory. It changes only site/physical_locations.json.
Default is dry-run. Require --write after physical location verification.
"""
import argparse
import csv
import datetime
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "site"))
from locator_feature import normalize_locations

def prepare(rows, known_ids, existing):
    merged = {k: list(v) for k, v in existing.items()}
    skipped = []
    accepted = 0
    for n, row in enumerate(rows, start=2):
        product_id = str(row.get("product_id") or "").strip()
        if product_id not in known_ids:
            skipped.append((n, "Unknown Shopify product ID"))
            continue
        incoming = {product_id: [{
            "code": (row.get("code") or "").strip().upper(),
            "kind": row.get("kind") or "sales-floor",
            "verified_at": row.get("verified_at") or "",
        }]}
        checked = normalize_locations({"items": incoming}, known_ids)
        if product_id not in checked:
            skipped.append((n, "Invalid code, kind, or date"))
            continue
        item = checked[product_id][0]
        prev = merged.get(product_id, [])
        merged[product_id] = [x for x in prev if not (x["code"] == item["code"] and x["kind"] == item["kind"])] + [item]
        accepted += 1
    return merged, accepted, skipped

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("csv_path", help="CSV exported from /staff/shelf-scan/")
    p.add_argument("--write", action="store_true", help="Write validated assignments after reviewing physical shelf codes")
    args = p.parse_args()
    catalog_path = os.path.join(ROOT, "data", "all_products.json")
    locations_path = os.path.join(ROOT, "site", "physical_locations.json")
    if not os.path.isfile(catalog_path):
        p.error("Missing data/all_products.json. Run python3 scripts/fetch.py first.")
    catalog = json.load(open(catalog_path, encoding="utf-8"))
    known_ids = {str(x["id"]) for x in catalog}
    source = json.load(open(locations_path, encoding="utf-8"))
    existing = normalize_locations(source, known_ids)
    with open(args.csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        expected = {"product_id", "code", "kind", "verified_at"}
        if not expected.issubset(reader.fieldnames or []):
            p.error("CSV must contain columns: " + ", ".join(sorted(expected)))
        merged, accepted, skipped = prepare(reader, known_ids, existing)
    print(f"Accepted {accepted} shelf assignments, rejected {len(skipped)}; {len(merged)} products mapped.")
    for line, reason in skipped[:30]:
        print(f"  CSV line {line}: {reason}")
    if skipped:
        print("Resolve rejected rows before publishing the map.")
        sys.exit(1)
    if not args.write:
        print("Dry run only. Review real shelf locations, then rerun with --write.")
        return
    new_data = {
        "version": 1,
        "description": "Staff-verified physical locations. Online subject aisles are not physical shelf codes.",
        "items": dict(sorted(merged.items())),
    }
    with open(locations_path + ".tmp", "w", encoding="utf-8") as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(locations_path + ".tmp", locations_path)
    print("Updated site/physical_locations.json. Review and commit to the source repository.")

if __name__ == "__main__":
    main()
