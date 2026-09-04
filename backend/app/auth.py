"""
Proving that whoever is changing a shop's rules is actually that shop's
owner. Before this, any request carrying a merchant_id string could
rewrite that merchant's policy, approve their escalated orders, or
revoke their agents -- there was no login at all. That's a real hole for
anything touching money, so closing it.

Simple API-key model, not a full user/session system (out of scope for
the time left) -- but it's a REAL secret, hashed at rest, checked on
every merchant-facing action. A merchant registers once, gets a key back
exactly once, and must send it as `Authorization: Bearer <key>` on every
request that changes their own data.
"""
import hashlib
import secrets
from fastapi import Header, HTTPException
from sqlmodel import Session
from app.db.models import MerchantRow


def _hash_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()


def generate_api_key() -> str:
    return "wrk_" + secrets.token_urlsafe(32)  # legacy "wrk" prefix, predates the Nope.ai rename


def require_merchant_auth(merchant_id: str, session: Session, authorization: str | None) -> None:
    """
    Raises 401/403 if the caller hasn't proven they own this merchant_id.
    Call this at the top of any endpoint that changes a merchant's data.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "missing Authorization: Bearer <api_key> header")

    api_key = authorization.removeprefix("Bearer ").strip()
    row = session.get(MerchantRow, merchant_id)
    if not row:
        raise HTTPException(403, "unknown merchant -- register first via POST /merchants/register")

    if _hash_key(api_key) != row.api_key_hash:
        raise HTTPException(403, "invalid API key for this merchant")
