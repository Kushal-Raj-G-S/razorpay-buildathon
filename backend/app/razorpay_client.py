"""
Talks to Razorpay's TEST MODE only. Test mode = fake money, real API,
safe to experiment with. Never touches real payments.

Uses plain HTTP calls (httpx) against Razorpay's REST API directly --
simplest possible way to create a test order and payment link.
"""
import os
import httpx
from dotenv import load_dotenv

load_dotenv()  # reads backend/.env if present -- never committed, see .gitignore

RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "")
BASE_URL = "https://api.razorpay.com/v1"


def _configured() -> bool:
    return bool(RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET)


async def verify_razorpay_credentials(key_id: str, key_secret: str) -> bool:
    """
    Proves a merchant genuinely owns the Razorpay key pair they're
    handing us, by actually calling Razorpay with it -- not just
    checking it's shaped like a key. Used by the alternative
    registration path (see main.py's register_merchant_with_razorpay):
    instead of Nope.ai minting its own separate API key, a merchant's
    real Razorpay test-mode credentials become their Nope.ai credential
    directly. One cheap, read-only call (list payment links, page size
    1) is enough -- Razorpay itself rejects the request with 401 if the
    key pair is wrong, which is the only thing being checked here.

    Returns True only on a genuine 200 from Razorpay. Any other status
    (401/403 = wrong keys) returns False. A network failure raises,
    since that's not the same thing as "these keys are invalid" and the
    caller should surface it differently (503, not "bad credentials").
    """
    async with httpx.AsyncClient(auth=(key_id, key_secret), timeout=15) as client:
        response = await client.get(f"{BASE_URL}/payment_links", params={"count": 1})
        return response.status_code == 200


async def create_payment_link(amount_paise: int, description: str, currency: str = "INR") -> dict:
    """
    Creates a Razorpay TEST payment link for an allowed order.
    If no keys are configured yet, returns a fake stand-in response
    so the rest of the system still works while you're getting keys.
    """
    if not _configured():
        return {
            "id": "plink_DEMO_NOKEYS",
            "short_url": "https://razorpay.me/demo-not-configured",
            "status": "created",
            "note": "Razorpay keys not set -- this is a placeholder response",
        }

    async with httpx.AsyncClient(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)) as client:
        response = await client.post(
            f"{BASE_URL}/payment_links",
            json={
                "amount": amount_paise,
                "currency": currency,
                "description": description,
                "reminder_enable": False,
            },
        )
        response.raise_for_status()
        return response.json()
