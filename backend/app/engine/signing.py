"""
Tamper-proofing the receipt.

Plain idea: we create one secret key (once, kept safe). Every receipt
gets "stamped" with that key. Anyone can later check the stamp is real
using the matching public key -- but nobody except us can CREATE a valid
stamp. So if someone edits a receipt afterward, the stamp won't match
anymore and we instantly know it was tampered with.

This uses Ed25519, a standard signing method used across the industry
(same family Visa and the IETF web-bot-auth standard use).
"""
import json
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives import serialization
from app.models.receipt import Receipt


def generate_keypair() -> tuple[bytes, bytes]:
    """Run this ONCE to create the shop's signing key. Save both parts safely."""
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return private_bytes, public_bytes


def _canonical_bytes(receipt: Receipt) -> bytes:
    """
    Turn the receipt into one exact, repeatable string of bytes.
    Same receipt always produces the same bytes -- so the signature
    always matches, no matter when or where we check it.
    """
    data = receipt.model_dump(mode="json", exclude={"signature"})
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode()


def sign_receipt(receipt: Receipt, private_key_bytes: bytes) -> Receipt:
    """Stamp the receipt. Returns a new receipt with the signature filled in."""
    private_key = Ed25519PrivateKey.from_private_bytes(private_key_bytes)
    signature = private_key.sign(_canonical_bytes(receipt))
    return receipt.model_copy(update={"signature": signature.hex()})


def verify_receipt(receipt: Receipt, public_key_bytes: bytes) -> bool:
    """
    Check the stamp is genuine and the receipt hasn't been edited since.
    Returns True only if both are true.
    """
    if receipt.signature is None:
        return False
    public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)
    unsigned = receipt.model_copy(update={"signature": None})
    try:
        public_key.verify(bytes.fromhex(receipt.signature), _canonical_bytes(unsigned))
        return True
    except Exception:
        return False
