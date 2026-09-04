"""
allow_categories: the other direction from deny_categories, for a
merchant with a catalog too large to ban categories by hand (Amazon
saying "agents may only buy electronics and daily essentials" would
mean denying every other category, and silently breaking the day a new
one is added). Real feature request, not a hypothetical.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.session import get_session
from app.models.cart import Cart, CartItem
from app.models.policy import Policy
from app.engine.evaluate import evaluate


# ---------- Pure unit tests on the deterministic check itself ----------

def test_allow_categories_empty_means_no_restriction():
    policy = Policy(merchant_id="shop_x", max_order_value=1000000, allow_categories=[])
    cart = Cart(id="c1", merchant_id="shop_x", items=[
        CartItem(id="i1", title="Anything", price=1000, category="anything_at_all"),
    ])
    receipt = evaluate(cart, policy, agent_id="agent")
    assert receipt.decision.value == "allow"


def test_allow_categories_blocks_a_category_not_in_the_list():
    policy = Policy(
        merchant_id="shop_x", max_order_value=1000000,
        allow_categories=["electronics", "daily_essentials"],
    )
    cart = Cart(id="c1", merchant_id="shop_x", items=[
        CartItem(id="i1", title="Fancy Jacket", price=1000, category="clothing"),
    ])
    receipt = evaluate(cart, policy, agent_id="agent")
    assert receipt.decision.value == "block"
    check = next(r for r in receipt.rules_checked if r.rule_name == "allow_categories")
    assert check.passed is False
    assert "clothing" in check.detail


def test_allow_categories_permits_a_category_in_the_list():
    policy = Policy(
        merchant_id="shop_x", max_order_value=1000000,
        allow_categories=["electronics", "daily_essentials"],
    )
    cart = Cart(id="c1", merchant_id="shop_x", items=[
        CartItem(id="i1", title="Headphones", price=1000, category="electronics"),
    ])
    receipt = evaluate(cart, policy, agent_id="agent")
    assert receipt.decision.value == "allow"


def test_allow_categories_and_deny_categories_both_apply():
    """Belt and suspenders: an item could pass allow_categories but still
    be individually banned by deny_categories -- both checks run."""
    policy = Policy(
        merchant_id="shop_x", max_order_value=1000000,
        allow_categories=["electronics", "gift_card"],
        deny_categories=["gift_card"],
    )
    cart = Cart(id="c1", merchant_id="shop_x", items=[
        CartItem(id="i1", title="Gift Card", price=1000, category="gift_card"),
    ])
    receipt = evaluate(cart, policy, agent_id="agent")
    assert receipt.decision.value == "block"
    deny_check = next(r for r in receipt.rules_checked if r.rule_name == "deny_categories")
    assert deny_check.passed is False


# ---------- Real HTTP integration, proving the whole path end to end ----------

@pytest.fixture()
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)

    def override_get_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def register_merchant(client, merchant_id):
    return client.post("/merchants/register", json={"merchant_id": merchant_id}).json()["api_key"]


def auth(key):
    return {"Authorization": f"Bearer {key}"}


def test_amazon_style_allow_list_end_to_end(client):
    """The exact scenario that prompted this feature: a big-catalog
    merchant restricting agents to two categories out of many."""
    merchant_id = "shop_amazon_style"
    key = register_merchant(client, merchant_id)
    client.post("/policy", headers=auth(key), json={
        "merchant_id": merchant_id, "max_order_value": 500000,
        "deny_categories": [], "allow_categories": ["electronics", "daily_essentials"],
        "require_signed_identity": False,
    })

    blocked = client.post("/checkout-sessions", json={
        "merchant_id": merchant_id, "agent_id": "shopper",
        "items": [{"id": "shoes", "title": "Running Shoes", "price": 300000,
                   "category": "footwear", "quantity": 1}],
    })
    assert blocked.json()["receipt"]["decision"] == "block"

    allowed = client.post("/checkout-sessions", json={
        "merchant_id": merchant_id, "agent_id": "shopper",
        "items": [{"id": "phone-case", "title": "Phone Case", "price": 30000,
                   "category": "electronics", "quantity": 1}],
    })
    assert allowed.json()["receipt"]["decision"] == "allow"


def test_saving_a_policy_without_allow_categories_still_works(client):
    """Backward compatible: a merchant who never touches this field gets
    the exact old deny-only behavior."""
    merchant_id = "shop_backward_compat"
    key = register_merchant(client, merchant_id)
    r = client.post("/policy", headers=auth(key), json={
        "merchant_id": merchant_id, "max_order_value": 500000, "deny_categories": ["gift_card"],
    })
    assert r.status_code == 200
    policy = client.get(f"/policy/{merchant_id}").json()
    assert policy["allow_categories"] == []
