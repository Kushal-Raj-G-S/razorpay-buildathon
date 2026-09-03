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
