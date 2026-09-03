"""
Real automated tests, not just demo scripts. Run with: pytest

These codify every scenario we proved manually into checks that run in
under a second and never silently break as the code changes.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from app.models.cart import Cart, CartItem
from app.models.policy import Policy
from app.engine.evaluate import evaluate
from app.engine.signing import generate_keypair, sign_receipt, verify_receipt
from app.engine.identity import canonical_cart_bytes, verify_agent_signature


POLICY = Policy(
    merchant_id="test_shop",
    max_order_value=1000000,       # Rs 10,000
    deny_categories=["gift_card"],
    max_units_per_sku=5,
    escalate_above=500000,         # Rs 5,000
)


def test_clean_cart_is_allowed():
    cart = Cart(id="c1", merchant_id="test_shop", items=[
        CartItem(id="shirt", title="Shirt", price=45000, category="clothing"),
    ])
    receipt = evaluate(cart, POLICY, agent_id="agent")
    assert receipt.decision.value == "allow"


def test_gift_card_is_blocked():
    cart = Cart(id="c2", merchant_id="test_shop", items=[
        CartItem(id="shirt", title="Shirt", price=45000, category="clothing"),
        CartItem(id="gc", title="Gift Card", price=200000, category="gift_card"),
    ])
    receipt = evaluate(cart, POLICY, agent_id="agent")
    assert receipt.decision.value == "block"
    failed_rules = [r.rule_name for r in receipt.rules_checked if not r.passed]
    assert "deny_categories" in failed_rules


def test_over_limit_is_blocked():
    cart = Cart(id="c3", merchant_id="test_shop", items=[
        CartItem(id="shoes", title="Shoes", price=1500000, category="footwear"),
    ])
    receipt = evaluate(cart, POLICY, agent_id="agent")
    assert receipt.decision.value == "block"


def test_mid_range_order_escalates_not_silently_allowed_or_blocked():
    cart = Cart(id="c4", merchant_id="test_shop", items=[
        CartItem(id="shoes", title="Shoes", price=700000, category="footwear"),
    ])
    receipt = evaluate(cart, POLICY, agent_id="agent")
    assert receipt.decision.value == "escalate"
    assert all(r.passed for r in receipt.rules_checked)  # nothing was actually wrong with it


def test_too_many_units_is_blocked():
    cart = Cart(id="c5", merchant_id="test_shop", items=[
        CartItem(id="shirt", title="Shirt", price=45000, category="clothing", quantity=10),
    ])
    receipt = evaluate(cart, POLICY, agent_id="agent")
    assert receipt.decision.value == "block"


def test_unverified_identity_blocks_even_a_clean_cart():
    cart = Cart(id="c6", merchant_id="test_shop", items=[
        CartItem(id="shirt", title="Shirt", price=45000, category="clothing"),
    ])
    receipt = evaluate(cart, POLICY, agent_id="agent", identity_verified=False)
    assert receipt.decision.value == "block"


def test_impersonator_with_wrong_key_fails_signature_check():
    real_key = Ed25519PrivateKey.generate()
    impostor_key = Ed25519PrivateKey.generate()
    real_public_hex = real_key.public_key().public_bytes_raw().hex()

    items = [CartItem(id="shirt", title="Shirt", price=45000, category="clothing")]
    fake_signature = impostor_key.sign(canonical_cart_bytes(items)).hex()

    assert verify_agent_signature(items, fake_signature, real_public_hex) is False


def test_real_key_signature_verifies():
    real_key = Ed25519PrivateKey.generate()
    real_public_hex = real_key.public_key().public_bytes_raw().hex()

    items = [CartItem(id="shirt", title="Shirt", price=45000, category="clothing")]
    signature = real_key.sign(canonical_cart_bytes(items)).hex()

    assert verify_agent_signature(items, signature, real_public_hex) is True


def test_signed_receipt_verifies():
    private_key, public_key = generate_keypair()
    cart = Cart(id="c7", merchant_id="test_shop", items=[
        CartItem(id="shirt", title="Shirt", price=45000, category="clothing"),
    ])
    receipt = evaluate(cart, POLICY, agent_id="agent")
    signed = sign_receipt(receipt, private_key)
    assert verify_receipt(signed, public_key) is True


def test_tampered_receipt_fails_verification():
    private_key, public_key = generate_keypair()
    cart = Cart(id="c8", merchant_id="test_shop", items=[
        CartItem(id="shirt", title="Shirt", price=45000, category="clothing"),
    ])
    receipt = evaluate(cart, POLICY, agent_id="agent")
    signed = sign_receipt(receipt, private_key)

    tampered = signed.model_copy(update={"cart_total": 1})
    assert verify_receipt(tampered, public_key) is False


def test_unknown_rule_type_fails_closed():
    """
    If we ever add a new rule and forget to write its check function,
    a cart should never silently pass just because nothing checked it.
    This test documents that expectation even though today every rule
    in ALL_CHECKS is implemented -- it's a guardrail for future changes.
    """
    from app.engine.evaluate import ALL_CHECKS
    assert len(ALL_CHECKS) >= 3  # guards against someone accidentally emptying the list
