"""
POST /merchants/register-with-razorpay: a merchant's own real Razorpay
test-mode key_id/key_secret becomes their Warrant credential directly,
instead of a second, Warrant-only API key. verify_razorpay_credentials
(the live call to Razorpay) is stubbed here, same reasoning as stubbing
create_payment_link elsewhere in this suite -- no live network
dependency in the test run. The live call itself is proven separately,
by hand, against real Razorpay test-mode keys (see git history / README).
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool

import app.main as main_module
from app.main import app
from app.db.session import get_session


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


def auth(credential: str):
    return {"Authorization": f"Bearer {credential}"}


def test_valid_razorpay_keys_register_and_then_authenticate_merchant_actions(client, monkeypatch):
    async def fake_verify(key_id, key_secret):
        assert key_id == "rzp_test_fake123"
        assert key_secret == "supersecretfake"
        return True

    monkeypatch.setattr(main_module, "verify_razorpay_credentials", fake_verify)

    r = client.post("/merchants/register-with-razorpay", json={
        "merchant_id": "shop_via_razorpay",
        "razorpay_key_id": "rzp_test_fake123",
        "razorpay_key_secret": "supersecretfake",
    })
    assert r.status_code == 200
    assert "api_key" not in r.json()  # no separate Warrant key was ever minted

    # The merchant's own Razorpay keys, not anything Warrant generated, now authenticate them.
    save = client.post(
        "/policy",
        headers=auth("rzp_test_fake123:supersecretfake"),
        json={"merchant_id": "shop_via_razorpay", "max_order_value": 100000, "deny_categories": []},
    )
    assert save.status_code == 200


def test_wrong_razorpay_keys_are_rejected_by_razorpay_itself(client, monkeypatch):
    async def fake_verify(key_id, key_secret):
        return False  # Razorpay itself said no

    monkeypatch.setattr(main_module, "verify_razorpay_credentials", fake_verify)

    r = client.post("/merchants/register-with-razorpay", json={
        "merchant_id": "shop_bad_keys",
        "razorpay_key_id": "not_a_real_key",
        "razorpay_key_secret": "not_a_real_secret",
    })
    assert r.status_code == 401
    # Merchant must not have been created on a failed verification.
    again = client.post("/merchants/register", json={"merchant_id": "shop_bad_keys"})
    assert again.status_code == 200


def test_razorpay_unreachable_returns_503_not_401(client, monkeypatch):
    """A network failure talking to Razorpay is not the same claim as
    'these keys are wrong' -- must not be conflated into a 401."""
    async def fake_verify(key_id, key_secret):
        raise httpx.ConnectError("could not reach Razorpay")

    monkeypatch.setattr(main_module, "verify_razorpay_credentials", fake_verify)

    r = client.post("/merchants/register-with-razorpay", json={
        "merchant_id": "shop_network_down",
        "razorpay_key_id": "rzp_test_whatever",
        "razorpay_key_secret": "whatever",
    })
    assert r.status_code == 503


def test_credential_from_a_different_merchant_does_not_authenticate_this_one(client, monkeypatch):
    async def fake_verify(key_id, key_secret):
        return True

    monkeypatch.setattr(main_module, "verify_razorpay_credentials", fake_verify)

    client.post("/merchants/register-with-razorpay", json={
        "merchant_id": "shop_a", "razorpay_key_id": "key_a", "razorpay_key_secret": "secret_a",
    })
    client.post("/merchants/register-with-razorpay", json={
        "merchant_id": "shop_b", "razorpay_key_id": "key_b", "razorpay_key_secret": "secret_b",
    })

    r = client.post(
        "/policy",
        headers=auth("key_a:secret_a"),  # shop_a's real credential
        json={"merchant_id": "shop_b", "max_order_value": 100000, "deny_categories": []},  # targeting shop_b
    )
    assert r.status_code == 403


def test_duplicate_merchant_id_rejected_regardless_of_auth_method(client, monkeypatch):
    async def fake_verify(key_id, key_secret):
        return True

    monkeypatch.setattr(main_module, "verify_razorpay_credentials", fake_verify)
    client.post("/merchants/register", json={"merchant_id": "shop_dup"})

    r = client.post("/merchants/register-with-razorpay", json={
        "merchant_id": "shop_dup", "razorpay_key_id": "k", "razorpay_key_secret": "s",
    })
    assert r.status_code == 409
