"""
THE SERVER. This is what actually runs and listens for requests --
from an AI agent trying to shop, or from our own Next.js dashboard.

Endpoints, in plain words:
  GET  /.well-known/ucp        -- "here's how to talk to this shop" (industry standard discovery)
  POST /catalog/search          -- "what do you sell?"
  POST /policy                  -- shop owner saves their rules
  GET  /policy/{merchant_id}    -- read the current rules
  POST /checkout-sessions       -- an agent tries to buy something -- THIS is where the bouncer runs
  GET  /receipts                -- see every past decision, for the dashboard
  POST /agents/{agent_id}/revoke -- shop owner kills an agent's access immediately
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.models.cart import Cart, CartItem
from app.models.catalog import Catalog
from app.models.policy import Policy
from app.engine.evaluate import evaluate
from app.engine.signing import generate_keypair, sign_receipt
from app.engine.identity import verify_agent_signature
from app.razorpay_client import create_payment_link
from app import storage

app = FastAPI(title="Warrant", description="The merchant's side of agentic commerce")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # demo only -- fine for a hackathon, not for production
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    """Generate the shop's signing key once when the server starts."""
    storage.signing_private_key, storage.signing_public_key = generate_keypair()
    print("Warrant is up. Signing key generated for this session.")


@app.get("/.well-known/ucp")
def ucp_profile():
    """
    Tells any AI agent: "here's how to talk to this shop." Loosely
    modelled on the real UCP industry standard (research/06-protocols.md).
    """
    return {
        "ucp": {
            "version": "2026-08-25-lite",
            "services": {
                "dev.ucp.shopping": {"transport": "rest", "endpoint": "/catalog"},
                "dev.ucp.shopping.checkout": {"transport": "rest", "endpoint": "/checkout-sessions"},
            },
            "payment_handlers": {"razorpay": {"mode": "test"}},
        }
    }


# ---------- Catalog ----------

class CatalogUploadRequest(BaseModel):
    merchant_id: str
    catalog: Catalog


@app.post("/catalog")
def upload_catalog(req: CatalogUploadRequest):
    storage.catalogs[req.merchant_id] = req.catalog
    return {"status": "saved", "product_count": len(req.catalog.products)}


@app.post("/catalog/search")
def search_catalog(merchant_id: str, query: str = ""):
    catalog = storage.catalogs.get(merchant_id)
    if not catalog:
        raise HTTPException(404, "no catalog for this merchant yet")
    matches = [
        p for p in catalog.products
        if query.lower() in p.title.lower()
    ] if query else catalog.products
    return {"products": matches}


# ---------- Policy ----------

@app.post("/policy")
def save_policy(policy: Policy):
    storage.policies[policy.merchant_id] = policy
    return {"status": "saved"}


@app.get("/policy/{merchant_id}")
def get_policy(merchant_id: str):
    policy = storage.policies.get(merchant_id)
    if not policy:
        raise HTTPException(404, "no policy set for this merchant yet")
    return policy


# ---------- Agent identity ----------

class AgentRegisterRequest(BaseModel):
    agent_id: str
    public_key_hex: str


@app.post("/agents/register")
def register_agent(req: AgentRegisterRequest):
    """An agent must do this once, ahead of time, before it can ever
    pass the identity check on a real checkout."""
    storage.registered_agents[req.agent_id] = req.public_key_hex
    return {"status": "registered", "agent_id": req.agent_id}


# ---------- The main event: checkout ----------

class CheckoutRequest(BaseModel):
    merchant_id: str
    agent_id: str
    items: list[CartItem]
    signature_hex: str | None = None  # signs the exact `items` list, see engine/identity.py


@app.post("/checkout-sessions")
async def checkout(req: CheckoutRequest):
    if req.agent_id in storage.revoked_agents:
        raise HTTPException(403, "this agent's access has been revoked by the merchant")

    policy = storage.policies.get(req.merchant_id)
    if not policy:
        raise HTTPException(404, "merchant has not set a policy -- refusing to guess")

    # Was this cart really signed by the agent it claims to be?
    identity_verified = False
    public_key_hex = storage.registered_agents.get(req.agent_id)
    if public_key_hex and req.signature_hex:
        identity_verified = verify_agent_signature(req.items, req.signature_hex, public_key_hex)

    cart = Cart(id=f"cart_{len(storage.receipts)+1}", merchant_id=req.merchant_id, items=req.items)

    receipt = evaluate(cart, policy, agent_id=req.agent_id, identity_verified=identity_verified)
    signed_receipt = sign_receipt(receipt, storage.signing_private_key)
    storage.receipts.append(signed_receipt)

    result = {"receipt": signed_receipt}

    if signed_receipt.decision.value == "allow":
        payment = await create_payment_link(
            amount_paise=cart.total,
            description=f"Order {cart.id} via agent {req.agent_id}",
        )
        result["payment"] = payment

    return result


# ---------- Receipts (for the dashboard) ----------

@app.get("/receipts")
def list_receipts(merchant_id: str | None = None):
    if merchant_id:
        return [r for r in storage.receipts if r.merchant_id == merchant_id]
    return storage.receipts


@app.get("/signing-public-key")
def get_public_key():
    """So anyone can independently verify our receipts are genuine."""
    return {"public_key_hex": storage.signing_public_key.hex()}


# ---------- Revocation ----------

@app.post("/agents/{agent_id}/revoke")
def revoke_agent(agent_id: str):
    storage.revoked_agents.add(agent_id)
    return {"status": "revoked", "agent_id": agent_id}


@app.post("/agents/{agent_id}/unrevoke")
def unrevoke_agent(agent_id: str):
    storage.revoked_agents.discard(agent_id)
    return {"status": "unrevoked", "agent_id": agent_id}
