"""
POST /catalog/from-pdf -- a real shop's actual product-list PDF becomes
a catalog, the same AI normalization /catalog/from-text already uses.
Generates a genuine PDF with fpdf2 (test-only dependency) and uploads
real bytes through the real endpoint, so the pypdf extraction step is
proven against actual PDF binary format, not a mock. The AI call itself
is stubbed, same reasoning as elsewhere in this suite -- no live
network dependency, and this test is about the PDF plumbing, not model
output quality.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from fpdf import FPDF
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool

import app.main as main_module
from app import ai_client
from app.main import app
from app.db.session import get_session


def _make_real_pdf_bytes(lines: list[str]) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    for line in lines:
        pdf.cell(0, 10, text=line, new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())


async def _fake_normalize_catalog_text(raw_text: str) -> list[dict]:
    # Proves the real extracted PDF text actually reached this function --
    # if extraction failed or returned garbage, this line list wouldn't match.
    assert "Blue Cotton Shirt" in raw_text
    assert "Denim Jeans" in raw_text
    return [
        {"id": "shirt", "title": "Blue Cotton Shirt", "price_rupees": 450, "category": "clothing"},
        {"id": "jeans", "title": "Denim Jeans", "price_rupees": 1500, "category": "clothing"},
    ]


@pytest.fixture()
def client(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)

    def override_get_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    monkeypatch.setattr(ai_client, "is_configured", lambda: True)
    monkeypatch.setattr(ai_client, "normalize_catalog_text", _fake_normalize_catalog_text)
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def register_merchant(client, merchant_id):
    return client.post("/merchants/register", json={"merchant_id": merchant_id}).json()["api_key"]


def auth(key):
    return {"Authorization": f"Bearer {key}"}


def test_real_pdf_gets_extracted_and_becomes_a_saved_catalog(client):
    merchant_id = "shop_pdf_catalog"
    key = register_merchant(client, merchant_id)

    pdf_bytes = _make_real_pdf_bytes([
        "Blue Cotton Shirt L - Rs 450",
        "Denim Jeans 32 waist - Rs 1500",
    ])

    r = client.post(
        "/catalog/from-pdf",
        headers=auth(key),
        data={"merchant_id": merchant_id},
        files={"file": ("products.pdf", BytesIO(pdf_bytes), "application/pdf")},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["product_count"] == 2
    assert body["catalog"]["products"][0]["title"] == "Blue Cotton Shirt"

    # And it's genuinely saved -- a search against the real catalog finds it.
    search = client.post("/catalog/search", params={"merchant_id": merchant_id})
    titles = [p["title"] for p in search.json()["products"]]
    assert "Blue Cotton Shirt" in titles


def test_non_pdf_file_is_rejected(client):
    merchant_id = "shop_pdf_reject"
    key = register_merchant(client, merchant_id)
    r = client.post(
        "/catalog/from-pdf",
        headers=auth(key),
        data={"merchant_id": merchant_id},
        files={"file": ("not-a-pdf.txt", BytesIO(b"hello"), "text/plain")},
    )
    assert r.status_code == 400


def test_empty_pdf_with_no_extractable_text_is_rejected(client):
    """A scanned-image-only PDF has real PDF bytes but no text layer --
    must fail with a clear message, not silently save an empty catalog."""
    merchant_id = "shop_pdf_empty"
    key = register_merchant(client, merchant_id)
    pdf_bytes = _make_real_pdf_bytes([])  # a real, valid, but textless PDF
    r = client.post(
        "/catalog/from-pdf",
        headers=auth(key),
        data={"merchant_id": merchant_id},
        files={"file": ("blank.pdf", BytesIO(pdf_bytes), "application/pdf")},
    )
    assert r.status_code == 400
    assert "couldn't extract" in r.json()["detail"]


def test_from_pdf_requires_merchant_auth(client):
    merchant_id = "shop_pdf_auth"
    register_merchant(client, merchant_id)
    pdf_bytes = _make_real_pdf_bytes(["Item - Rs 100"])
    r = client.post(
        "/catalog/from-pdf",
        data={"merchant_id": merchant_id},
        files={"file": ("products.pdf", BytesIO(pdf_bytes), "application/pdf")},
    )
    assert r.status_code in (401, 403)
