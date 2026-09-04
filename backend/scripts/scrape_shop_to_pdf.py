"""Scrape a real shop's product listing page and write it out as a PDF.

This is a standalone, operator-run script -- not a backend endpoint. It never
takes a URL from a merchant at request time, so it doesn't carry the SSRF risk
an in-app "paste your shop's URL" feature would (an attacker-controlled URL
reaching our server at request time, potentially pointed at internal
infrastructure). Here, a human runs this locally against a URL they chose,
and the output feeds into the already-built /catalog/from-pdf upload path
like any other PDF a merchant might hand us.

Usage:
    venv/Scripts/python scripts/scrape_shop_to_pdf.py <url> <output.pdf>
"""

import sys

import requests
from bs4 import BeautifulSoup
from fpdf import FPDF


def scrape_products(url: str) -> list[str]:
    resp = requests.get(url, timeout=15, headers={"User-Agent": "WarrantCatalogBot/1.0"})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    lines = []
    for article in soup.select("article.product_pod"):
        title_el = article.select_one("h3 a")
        price_el = article.select_one("p.price_color")
        if not title_el or not price_el:
            continue
        title = title_el.get("title", title_el.text).strip()
        # Core PDF fonts (Helvetica) can't encode the £ glyph -- swap it for
        # "GBP " so the price still reads clearly in the generated PDF.
        price = price_el.text.strip().replace("£", "GBP ")
        lines.append(f"{title} - {price}")

    return lines


def write_pdf(lines: list[str], out_path: str) -> None:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    for line in lines:
        pdf.cell(0, 10, text=line, new_x="LMARGIN", new_y="NEXT")
    pdf.output(out_path)


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: scrape_shop_to_pdf.py <url> <output.pdf>")
        sys.exit(1)

    url, out_path = sys.argv[1], sys.argv[2]
    lines = scrape_products(url)
    if not lines:
        print("No products found on that page -- check the selector matches this site's HTML.")
        sys.exit(1)

    write_pdf(lines, out_path)
    print(f"Wrote {len(lines)} products to {out_path}")


if __name__ == "__main__":
    main()
