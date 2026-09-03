"""
The real gap found by trying to build an adversarial demo: nothing
verified that an agent's claimed item category matched what the
merchant actually listed. Before this, an agent could submit
category="clothing" for a real gift card and walk straight past
deny_categories, because that check only ever read the field the AGENT
supplied. These tests prove the fix: main.py resolves every checkout
item against the merchant's own catalog before evaluate() ever runs,
and an unlisted item is blocked outright regardless of what it claims
to be.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

import app.main as main_module
from app.main import app
from app.db.session import get_session
from app.engine.identity import canonical_cart_bytes
from app.models.cart import CartItem


async def _fake_create_payment_link(amount_paise: int, description: str, currency: str = "INR") -> dict:
    return {"id": "plink_FAKE", "short_url": "https://rzp.io/rzp/fake", "status": "created"}


@pytest.fixture()
def client(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)

    def override_get_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    monkeypatch.setattr(main_module, "create_payment_link", _fake_create_payment_link)
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def register_merchant(client, merchant_id):
    return client.post("/merchants/register", json={"merchant_id": merchant_id}).json()["api_key"]


def auth(key):
    return {"Authorization": f"Bearer {key}"}


def _sign(agent_id, items, client):
    key = Ed25519PrivateKey.generate()
    pub = key.public_key().public_bytes_raw().hex()
    client.post("/agents/register", json={"agent_id": agent_id, "public_key_hex": pub})
    return key.sign(canonical_cart_bytes([CartItem(**i) for i in items])).hex()


def _upload_catalog(client, merchant_key, merchant_id):
    catalog = {
        "merchant_id": merchant_id,
        "catalog": {
            "merchant_id": merchant_id,
            "products": [
                {
                    "id": "gift-card-2000",
                    "title": "Rs 2000 Gift Card",
                    "variants": [{
                        "id": "gift-card-2000", "title": "Rs 2000 Gift Card",
                        "price": 200000, "category": "gift_card",
                    }],
                },
                {
                    "id": "blue-shirt",
                    "title": "Blue Shirt",
                    "variants": [{
                        "id": "blue-shirt", "title": "Blue Shirt",
                        "price": 45000, "category": "clothing",
                    }],
                },
            ],
        },
    }
    client.post("/catalog", headers=auth(merchant_key), json=catalog)


def test_agent_cannot_relabel_a_gift_card_as_clothing(client):
    """The core exploit: submit the real gift card's id, but lie about its category."""
    merchant_id = "shop_integrity"
    key = register_merchant(client, merchant_id)
    client.post("/policy", headers=auth(key), json={
        "merchant_id": merchant_id, "max_order_value": 1000000, "deny_categories": ["gift_card"],
    })
    _upload_catalog(client, key, merchant_id)

    # The agent submits the REAL catalog id, but lies about the category
    lying_items = [{
        "id": "gift-card-2000", "title": "Rs 2000 Gift Card",
        "price": 200000, "category": "clothing", "quantity": 1,   # <-- the lie
    }]
    sig = _sign("lying-agent", lying_items, client)

    r = client.post("/checkout-sessions", json={
        "merchant_id": merchant_id, "agent_id": "lying-agent",
        "items": lying_items, "signature_hex": sig,
    })
    receipt = r.json()["receipt"]

    assert receipt["decision"] == "block"
    deny_check = next(x for x in receipt["rules_checked"] if x["rule_name"] == "deny_categories")
    assert deny_check["passed"] is False
    assert "gift_card" in deny_check["detail"]  # caught under its REAL category, not the lied one


def test_completely_invented_item_is_blocked_as_unlisted(client):
    """An agent inventing a product id the merchant never listed at all."""
    merchant_id = "shop_integrity2"
    key = register_merchant(client, merchant_id)
    client.post("/policy", headers=auth(key), json={
        "merchant_id": merchant_id, "max_order_value": 1000000, "deny_categories": [],
    })
    _upload_catalog(client, key, merchant_id)

    fake_items = [{
        "id": "totally-made-up-item", "title": "Nothing Suspicious Here",
        "price": 10000, "category": "clothing", "quantity": 1,
    }]
    sig = _sign("inventing-agent", fake_items, client)

    r = client.post("/checkout-sessions", json={
        "merchant_id": merchant_id, "agent_id": "inventing-agent",
        "items": fake_items, "signature_hex": sig,
    })
    receipt = r.json()["receipt"]

    assert receipt["decision"] == "block"
    listed_check = next(x for x in receipt["rules_checked"] if x["rule_name"] == "items_are_listed")
    assert listed_check["passed"] is False


def test_real_listed_item_with_correct_category_is_allowed(client):
    """Sanity check: the fix doesn't break legitimate, honestly-labelled orders."""
    merchant_id = "shop_integrity3"
    key = register_merchant(client, merchant_id)
    client.post("/policy", headers=auth(key), json={
        "merchant_id": merchant_id, "max_order_value": 1000000, "deny_categories": ["gift_card"],
    })
    _upload_catalog(client, key, merchant_id)

    honest_items = [{
        "id": "blue-shirt", "title": "Blue Shirt",
        "price": 45000, "category": "clothing", "quantity": 1,
    }]
    sig = _sign("honest-agent", honest_items, client)

    r = client.post("/checkout-sessions", json={
        "merchant_id": merchant_id, "agent_id": "honest-agent",
        "items": honest_items, "signature_hex": sig,
    })
    receipt = r.json()["receipt"]
    assert receipt["decision"] == "allow"


def test_merchant_with_no_catalog_uploaded_is_unaffected(client):
    """Backward compatible: no catalog uploaded means nothing to verify against."""
    merchant_id = "shop_no_catalog"
    key = register_merchant(client, merchant_id)
    client.post("/policy", headers=auth(key), json={
        "merchant_id": merchant_id, "max_order_value": 1000000, "deny_categories": ["gift_card"],
    })
    # deliberately no catalog upload here

    items = [{"id": "anything", "title": "Anything", "price": 10000, "category": "clothing", "quantity": 1}]
    sig = _sign("agent-no-catalog", items, client)

    r = client.post("/checkout-sessions", json={
        "merchant_id": merchant_id, "agent_id": "agent-no-catalog",
        "items": items, "signature_hex": sig,
    })
    receipt = r.json()["receipt"]
    assert receipt["decision"] == "allow"
