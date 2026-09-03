"""
THE SERVER. This is what actually runs and listens for requests --
from an AI agent trying to shop, or from our own Next.js dashboard.

Endpoints, in plain words:
  GET  /.well-known/ucp          -- "here's how to talk to this shop" (industry standard discovery)
  POST /catalog                   -- upload a clean catalog directly
  POST /catalog/from-text         -- AI turns messy product text into a clean catalog
  POST /catalog/search            -- "what do you sell?"
  POST /policy                    -- shop owner saves their rules directly
  POST /policy/draft-from-text    -- AI drafts rules from plain English (does NOT save)
  GET  /policy/{merchant_id}      -- read the current rules
  POST /agents/register           -- an agent proves it has a real key, ahead of time
  POST /checkout-sessions         -- an agent tries to buy something -- the bouncer runs here
  GET  /receipts                  -- every past decision, signed
  GET  /escalations               -- orders waiting for a human to approve or reject
  POST /escalations/{id}/review   -- a human actually approves or rejects one
  POST /agents/{agent_id}/revoke  -- shop owner kills an agent's access immediately

Every read/write to real data goes through app/db/repo.py, backed by a
real database (SQLite by default, Postgres if DATABASE_URL is set) --
not in-memory dictionaries that vanish on restart.
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlmodel import Session

from app.models.cart import Cart, CartItem
from app.models.catalog import Catalog, Product, Variant
from app.models.policy import Policy
from app.engine.evaluate import evaluate
from app.engine.signing import sign_receipt
from app.engine.identity import verify_agent_signature
from app.razorpay_client import create_payment_link
from app import ai_client
from app.db.session import init_db, get_session
from app.db import repo

app = FastAPI(title="Warrant", description="The merchant's side of agentic commerce")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # demo only -- fine for a hackathon, not for production
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()
    print("Warrant is up. Database ready, signing key loaded (persistent).")


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
def upload_catalog(req: CatalogUploadRequest, session: Session = Depends(get_session)):
    repo.save_catalog(session, req.catalog)
    return {"status": "saved", "product_count": len(req.catalog.products)}


class CatalogFromTextRequest(BaseModel):
    merchant_id: str
    raw_text: str   # e.g. one messy product per line, however the shop owner typed it


@app.post("/catalog/from-text")
async def catalog_from_text(req: CatalogFromTextRequest, session: Session = Depends(get_session)):
    """
    AI reads messy product text and produces a clean structured catalog.
    This is where AI genuinely belongs -- turning fuzzy human input into
    a structured shape. Saved immediately for the demo; a stricter
    production version could show a draft for approval first, same as
    the policy compiler below.
    """
    if not ai_client.is_configured():
        raise HTTPException(503, "AI not configured -- set NVIDIA_API_KEY in backend/.env")

    raw_products = await ai_client.normalize_catalog_text(req.raw_text)
    products = [
        Product(
            id=p["id"],
            title=p["title"],
            variants=[Variant(
                id=p["id"],
                title=p["title"],
                price=round(float(p["price_rupees"]) * 100),
                category=p.get("category"),
                sku=p.get("sku"),
            )],
        )
        for p in raw_products
    ]
    catalog = Catalog(merchant_id=req.merchant_id, products=products)
    repo.save_catalog(session, catalog)
    return {"status": "saved", "product_count": len(products), "catalog": catalog}


@app.post("/catalog/search")
def search_catalog(merchant_id: str, query: str = "", session: Session = Depends(get_session)):
    catalog = repo.get_catalog(session, merchant_id)
    if not catalog:
        raise HTTPException(404, "no catalog for this merchant yet")
    matches = [
        p for p in catalog.products
        if query.lower() in p.title.lower()
    ] if query else catalog.products
    return {"products": matches}


# ---------- Policy ----------

@app.post("/policy")
def save_policy_endpoint(policy: Policy, session: Session = Depends(get_session)):
    repo.save_policy(session, policy)
    return {"status": "saved"}


class PolicyDraftRequest(BaseModel):
    merchant_id: str
    plain_english: str  # e.g. "don't let agents buy gift cards, cap orders at 5000 rupees"


@app.post("/policy/draft-from-text")
async def draft_policy_from_text(req: PolicyDraftRequest):
    """
    AI drafts a policy from plain English. Returns the draft -- does NOT
    save it. The merchant must review it and POST /policy themselves to
    actually apply it. This split (AI drafts, human approves, code
    enforces) is the whole thesis of the project.
    """
    if not ai_client.is_configured():
        raise HTTPException(503, "AI not configured -- set NVIDIA_API_KEY in backend/.env")

    draft = await ai_client.compile_policy_text(req.merchant_id, req.plain_english)
    return {"draft": draft, "note": "review this, then POST it to /policy to actually apply it"}


@app.get("/policy/{merchant_id}")
def get_policy_endpoint(merchant_id: str, session: Session = Depends(get_session)):
    policy = repo.get_policy(session, merchant_id)
    if not policy:
        raise HTTPException(404, "no policy set for this merchant yet")
    return policy


# ---------- Agent identity ----------

class AgentRegisterRequest(BaseModel):
    agent_id: str
    public_key_hex: str


@app.post("/agents/register")
def register_agent_endpoint(req: AgentRegisterRequest, session: Session = Depends(get_session)):
    """An agent must do this once, ahead of time, before it can ever
    pass the identity check on a real checkout."""
    repo.register_agent(session, req.agent_id, req.public_key_hex)
    return {"status": "registered", "agent_id": req.agent_id}


# ---------- The main event: checkout ----------

class CheckoutRequest(BaseModel):
    merchant_id: str
    agent_id: str
    items: list[CartItem]
    signature_hex: str | None = None  # signs the exact `items` list, see engine/identity.py


@app.post("/checkout-sessions")
async def checkout(req: CheckoutRequest, session: Session = Depends(get_session)):
    if repo.is_agent_revoked(session, req.agent_id):
        raise HTTPException(403, "this agent's access has been revoked by the merchant")

    policy = repo.get_policy(session, req.merchant_id)
    if not policy:
        raise HTTPException(404, "merchant has not set a policy -- refusing to guess")

    # Was this cart really signed by the agent it claims to be?
    identity_verified = False
    public_key_hex = repo.get_agent_public_key(session, req.agent_id)
    if public_key_hex and req.signature_hex:
        identity_verified = verify_agent_signature(req.items, req.signature_hex, public_key_hex)

    cart = Cart(id=f"cart_{req.merchant_id}_{req.agent_id}", merchant_id=req.merchant_id, items=req.items)

    receipt = evaluate(cart, policy, agent_id=req.agent_id, identity_verified=identity_verified)

    private_key, _ = repo.get_or_create_signing_key(session)
    signed_receipt = sign_receipt(receipt, private_key)

    receipt_id = repo.save_receipt(session, signed_receipt, req.items)

    result = {"receipt": signed_receipt}

    if signed_receipt.decision.value == "allow":
        payment = await create_payment_link(
            amount_paise=cart.total,
            description=f"Order {cart.id} via agent {req.agent_id}",
        )
        result["payment"] = payment

    elif signed_receipt.decision.value == "escalate":
        escalation_id = repo.create_escalation(
            session, receipt_id, req.merchant_id, req.agent_id, req.items, cart.total,
        )
        result["escalation_id"] = escalation_id
        result["note"] = "every rule passed, but this order needs a human to approve it"

    return result


# ---------- Receipts (for the dashboard) ----------

@app.get("/receipts")
def list_receipts_endpoint(merchant_id: str | None = None, session: Session = Depends(get_session)):
    return repo.list_receipts(session, merchant_id)


@app.get("/signing-public-key")
def get_public_key(session: Session = Depends(get_session)):
    """So anyone can independently verify our receipts are genuine."""
    _, public_key = repo.get_or_create_signing_key(session)
    return {"public_key_hex": public_key.hex()}


# ---------- Escalations: the human-review queue ----------

@app.get("/escalations")
def list_escalations_endpoint(merchant_id: str | None = None, status: str = "pending",
                               session: Session = Depends(get_session)):
    return repo.list_escalations(session, merchant_id, status)


class ReviewRequest(BaseModel):
    approve: bool
    note: str | None = None


@app.post("/escalations/{escalation_id}/review")
async def review_escalation_endpoint(escalation_id: int, req: ReviewRequest,
                                      session: Session = Depends(get_session)):
    """
    A real human decision. If approved, the payment actually gets
    created now -- money only moves after both the automated rules AND
    a person have said yes.
    """
    row = repo.review_escalation(session, escalation_id, req.approve, req.note)
    if not row:
        raise HTTPException(404, "no such escalation")

    result = {"escalation": row}
    if req.approve:
        payment = await create_payment_link(
            amount_paise=row.cart_total,
            description=f"Order {row.receipt_id} (human-approved) via agent {row.agent_id}",
        )
        result["payment"] = payment
    return result


# ---------- Revocation ----------

@app.post("/agents/{agent_id}/revoke")
def revoke_agent(agent_id: str, session: Session = Depends(get_session)):
    repo.set_agent_revoked(session, agent_id, True)
    return {"status": "revoked", "agent_id": agent_id}


@app.post("/agents/{agent_id}/unrevoke")
def unrevoke_agent(agent_id: str, session: Session = Depends(get_session)):
    repo.set_agent_revoked(session, agent_id, False)
    return {"status": "unrevoked", "agent_id": agent_id}
