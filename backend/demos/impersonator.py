"""
Proves identity checking actually works, not just "check a name string".

Two AI agents both claim to be "trusted-agent". Only one of them has the
real private key. The cart they send is IDENTICAL and perfectly clean --
no gift cards, no rule violations. The only difference is who's really
holding the key.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from app.models.cart import Cart, CartItem
from app.models.policy import Policy
from app.engine.evaluate import evaluate
from app.engine.identity import canonical_cart_bytes, verify_agent_signature


def main():
    # The real agent generates its own key and registers the public half
    # with the shop (this would happen once, ahead of time).
    real_key = Ed25519PrivateKey.generate()
    real_public_hex = real_key.public_key().public_bytes_raw().hex()

    # An impersonator has its OWN different key -- but claims the same name.
    impostor_key = Ed25519PrivateKey.generate()

    policy = Policy(merchant_id="shop_123", max_order_value=1000000, deny_categories=["gift_card"])
    items = [CartItem(id="shirt", title="Blue Cotton Shirt L", price=45000, category="clothing")]
    cart_bytes = canonical_cart_bytes(items)

    print("=== The real agent signs with its real key ===")
    real_signature = real_key.sign(cart_bytes).hex()
    verified = verify_agent_signature(items, real_signature, real_public_hex)
    print(f"Signature check: {verified}")
    cart = Cart(id="cart_real", merchant_id="shop_123", items=items)
    receipt = evaluate(cart, policy, agent_id="trusted-agent", identity_verified=verified)
    print(f"Decision: {receipt.decision.value.upper()}\n")

    print("=== An impersonator claims the SAME name, signs with a DIFFERENT key ===")
    fake_signature = impostor_key.sign(cart_bytes).hex()
    # we check against the REAL agent's registered public key, since that's
    # what the shop has on file for "trusted-agent"
    verified = verify_agent_signature(items, fake_signature, real_public_hex)
    print(f"Signature check: {verified}")
    cart = Cart(id="cart_fake", merchant_id="shop_123", items=items)
    receipt = evaluate(cart, policy, agent_id="trusted-agent", identity_verified=verified)
    print(f"Decision: {receipt.decision.value.upper()}")
    for r in receipt.rules_checked:
        if not r.passed:
            print(f"  blocked because: {r.detail}")


if __name__ == "__main__":
    main()
