"""Typed responses for the two registration paths (models/policy.py,
models/digest.py etc. carry the same reasoning: an outside integrator
needs a real schema, not main.py's source, to know what comes back)."""
from pydantic import BaseModel


class MerchantRegisterResponse(BaseModel):
    merchant_id: str
    api_key: str
    warning: str


class MerchantRegisterWithRazorpayResponse(BaseModel):
    merchant_id: str
    note: str
