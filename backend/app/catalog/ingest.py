"""
Turns a shop owner's messy product sheet into the clean Catalog shape.

Plain version for now: expects a CSV with columns
  name, price_rupees, category, sku (optional)
and produces one Product+Variant per row.

This is the piece that could later get smarter with AI (reading a messy
Excel export, guessing categories, splitting "Blue Tshirt L 499" into
name+color+size+price) -- but a working simple version now beats a
half-built smart version later.
"""
import csv
import re
from app.models.catalog import Catalog, Product, Variant


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def ingest_csv(file_path: str, merchant_id: str) -> Catalog:
    products = []
    with open(file_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["name"].strip()
            price_paise = round(float(row["price_rupees"]) * 100)
            category = row.get("category", "").strip() or None
            sku = row.get("sku", "").strip() or None
            variant_id = _slugify(name)

            products.append(Product(
                id=variant_id,
                title=name,
                variants=[Variant(
                    id=variant_id,
                    title=name,
                    price=price_paise,
                    category=category,
                    sku=sku,
                )],
            ))

    return Catalog(merchant_id=merchant_id, products=products)
