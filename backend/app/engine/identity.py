"""
Proving an AI agent is really who it claims to be.

Real-world version of this idea is called RFC 9421 / "Web Bot Auth" --
big companies use it (research/06-protocols.md). We're building a
simplified version of the same core idea, not the full spec:

  1. An agent generates a keypair once (like a fingerprint).
  2. It registers the PUBLIC half with the shop ahead of time.
  3. Every time it sends a cart, it SIGNS that exact cart with its
     PRIVATE half.
  4. We check: does this signature match the public key we have on
     file for this agent_id? If yes, we know this cart really came
     from that agent, unedited, in transit. If no -- someone is lying
     about who they are, or the cart was tampered with en route.
"""
import json
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from app.models.cart import CartItem


def canonical_cart_bytes(items: list[CartItem]) -> bytes:
    """Same idea as receipt signing: turn the cart into one exact,
    repeatable string of bytes, so signing/verifying always agree."""
    data = [item.model_dump(mode="json") for item in items]
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode()


def verify_agent_signature(items: list[CartItem], signature_hex: str, public_key_hex: str) -> bool:
    """Returns True only if this exact cart was really signed by the
    holder of this public key."""
    try:
        public_key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_key_hex))
        public_key.verify(bytes.fromhex(signature_hex), canonical_cart_bytes(items))
        return True
    except Exception:
        return False
