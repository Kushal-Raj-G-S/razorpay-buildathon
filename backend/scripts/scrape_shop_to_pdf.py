"""Scrape a real shop's product listing page and write it out as a PDF.

This is a standalone, operator-run script -- not a backend endpoint. It never
takes a URL from a merchant at request time, so it doesn't carry the SSRF risk
an in-app "paste your shop's URL" feature would (an attacker-controlled URL
reaching our server at request time, potentially pointed at internal
infrastructure). Here, a human runs this locally against a URL they chose,
and the output feeds into the already-built /catalog/from-pdf upload path
like any other PDF a merchant might hand us.

Usage:
    venv/Scripts/python scripts/scrape_shop_to_pdf.py <url> [url2 ...] <output.pdf>

Multiple URLs are useful for one shop whose categories live on separate
listing pages (e.g. /fish, /mutton, /vegetables) -- each is scraped and
capped separately, then merged into one PDF so the resulting catalog has
more than one real category to write policy rules against.
"""

import sys

import requests
from bs4 import BeautifulSoup
from fpdf import FPDF

MAX_PRODUCTS_PER_PAGE = 6

# Each entry is (container_selector, title_selector, price_selector). The
# first one whose container_selector matches anything on the page is used --
# real shops differ in markup, this isn't one universal selector.
SITE_PATTERNS = [
    (".product-block", ".product-name", ".price-box .price"),  # Magento-based shops
    ("article.product_pod", "h3 a", "p.price_color"),  # books.toscrape.com
]


def _clean_for_pdf(text: str) -> str:
    # Core PDF fonts (Helvetica) only encode latin-1 -- strip anything outside
    # that (e.g. regional-language product names) rather than crash the PDF
    # writer on a glyph it can't draw.
    return text.encode("latin-1", errors="ignore").decode("latin-1").strip()


def scrape_products(url: str) -> list[str]:
    resp = requests.get(url, timeout=15, headers={"User-Agent": "WarrantCatalogBot/1.0"})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    for container_sel, title_sel, price_sel in SITE_PATTERNS:
        containers = soup.select(container_sel)
        if not containers:
            continue

        lines: list[str] = []
        seen: set[str] = set()
        for container in containers:
            title_el = container.select_one(title_sel)
            price_el = container.select_one(price_sel)
            if not title_el or not price_el:
                continue
            title = _clean_for_pdf(title_el.get("title", title_el.text))
            price = _clean_for_pdf(price_el.text.replace("£", "GBP "))
            if not title or not price or title in seen:
                continue
            seen.add(title)
            lines.append(f"{title} - {price}")
            if len(lines) >= MAX_PRODUCTS_PER_PAGE:
                break
        return lines

    return []


def write_pdf(lines: list[str], out_path: str) -> None:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)
    for line in lines:
        pdf.cell(0, 8, text=line, new_x="LMARGIN", new_y="NEXT")
    pdf.output(out_path)


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: scrape_shop_to_pdf.py <url> [url2 ...] <output.pdf>")
        sys.exit(1)

    *urls, out_path = sys.argv[1:]
    all_lines: list[str] = []
    for url in urls:
        lines = scrape_products(url)
        if not lines:
            print(f"No products found on {url} -- skipping "
                  "(add a matching selector triple to SITE_PATTERNS if this is unexpected).")
            continue
        print(f"{url}: {len(lines)} products")
        all_lines.extend(lines)

    if not all_lines:
        print("No products found on any of the given pages.")
        sys.exit(1)

    write_pdf(all_lines, out_path)
    print(f"Wrote {len(all_lines)} products total to {out_path}")


if __name__ == "__main__":
    main()
