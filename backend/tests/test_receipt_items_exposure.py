"""
GET /receipts must expose what was actually in the cart, not just a
total in rupees -- a merchant looking at "what did this agent buy"
needs the real product names. Found live: repo.list_receipts_with_items
genuinely returned cart_items, but the route's own
response_model=list[Receipt] silently stripped it on the way out, since
cart_items isn't a field on Receipt (that model's shape is also what
gets signed, so it deliberately excludes it). This test would have
caught it -- checking the field on the ORM/repo return value hides a
response_model bug entirely.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.session import get_session


def test_get_receipts_includes_cart_items_in_the_actual_http_response():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)

    def override_get_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as client:
        key = client.post("/merchants/register", json={"merchant_id": "shop_items"}).json()["api_key"]
        auth = {"Authorization": f"Bearer {key}"}
        client.post("/policy", headers=auth, json={
            "merchant_id": "shop_items", "max_order_value": 1000000,
            "deny_categories": [], "require_signed_identity": False,
        })
        client.post("/checkout-sessions", json={
            "merchant_id": "shop_items", "agent_id": "item-check-agent",
            "items": [{"id": "shirt", "title": "Blue Shirt", "price": 45000,
                       "category": "clothing", "quantity": 2}],
        })

        receipts = client.get("/receipts", headers=auth, params={"merchant_id": "shop_items"}).json()

    app.dependency_overrides.clear()

    assert len(receipts) == 1
    assert "cart_items" in receipts[0]
    assert receipts[0]["cart_items"][0]["title"] == "Blue Shirt"
    assert receipts[0]["cart_items"][0]["quantity"] == 2
