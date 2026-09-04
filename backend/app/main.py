"""
THE SERVER. This is what actually runs and listens for requests --
from an AI agent trying to shop, or from our own Next.js dashboard.

Endpoints, in plain words:
  GET  /.well-known/ucp          -- "here's how to talk to this shop" (industry standard discovery)
  POST /merchants/register       -- a shop owner creates their account, gets a secret key ONCE
  POST /merchants/register-with-razorpay -- same, but authenticates with the merchant's own
                                             real Razorpay keys instead of a Warrant-only one
  POST /catalog                   -- upload a clean catalog directly           [merchant-only]
  POST /catalog/from-text         -- AI turns messy product text into a clean catalog [merchant-only]
  POST /catalog/search            -- "what do you sell?"                       [public -- agents need this]
  POST /policy                    -- shop owner saves their rules directly     [merchant-only]
  POST /policy/draft-from-text    -- AI drafts rules from plain English        [merchant-only, does NOT save]
  GET  /policy/{merchant_id}      -- read the current rules                    [public -- agents need this]
  GET  /policy/{merchant_id}/history -- every past saved version, most recent first [merchant-only]
  POST /agents/register           -- an agent proves it has a real key, ahead of time [public -- agents self-register]
  POST /checkout-sessions         -- an agent tries to buy something -- the bouncer runs here [public]
  GET  /receipts                  -- every past decision, signed               [merchant-only]
  GET  /digest                    -- fast, deterministic "what's been happening" numbers + flags [merchant-only]
  POST /digest/narrate            -- turns those numbers into plain language, AI, separate call  [merchant-only]
  GET  /escalations               -- orders waiting for a human to approve     [merchant-only]
  GET  /escalations/{id}/advice   -- AI drafts a recommendation, DECIDES NOTHING [merchant-only]
  POST /escalations/{id}/review   -- a human actually approves or rejects one  [merchant-only]
  POST /agents/{agent_id}/revoke  -- shop owner kills an agent's access        [merchant-only]
  POST /red-team/run              -- an autonomous AI tries to break your rules [merchant-only]
  GET  /red-team/runs             -- history of past red-team runs             [merchant-only]

"[merchant-only]" means the caller must send `Authorization: Bearer <api_key>`
proving they own that merchant_id -- see app/auth.py. Before this, ANY
request carrying a merchant_id string could rewrite that shop's rules or
approve their orders. "[public]" endpoints are the ones a real AI
shopping agent needs to call with no prior relationship to the merchant,
same as any real storefront.

Two tiers, not one undifferentiated pile of endpoints. THE GATE --
checkout-sessions, policy read, catalog search -- is what an autonomous
shopping agent calls on every purchase attempt, must stay fast and cheap,
and never touches an LLM: this is the whole "no AI in the decision path"
claim, made structurally true rather than just asserted. THE ADVISORS --
catalog-from-text, policy/draft-from-text, escalations/{id}/advice,
red-team/run -- run occasionally, genuinely benefit from reasoning, and
their output is ALWAYS a draft: a human clicks Save, or Approve, or
reads a transcript. Nothing an Advisor produces ever becomes a real
decision by itself. Mixing these two tiers into one endpoint would blur
the exact distinction the whole project is built to keep sharp.

GET /digest is a deliberate hybrid, not a third tier: which patterns are
worth a merchant's attention (an agent tripping the catalog-mismatch
check, hitting a velocity cap, getting blocked repeatedly) is decided by
fixed code in engine/digest.py, exactly like THE GATE -- AI is only used
afterward, optionally, to turn those already-decided facts into plain
sentences a non-technical shop owner can read in ten seconds. It exists
because "the merchant writes rules once and never looks again" isn't
enough: a small shop has no security team watching for a slow pattern
the way a big company might, so the pattern has to surface itself.

Every read/write to real data goes through app/db/repo.py, backed by a
real database (SQLite by default, Postgres if DATABASE_URL is set) --
not in-memory dictionaries that vanish on restart.
"""
import json
import time
import httpx
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlmodel import Session

from app.models.cart import Cart, CartItem
from app.models.catalog import (
    Catalog, Product, Variant, CatalogSaveResponse, CatalogFromTextResponse, CatalogSearchResponse,
)
from app.models.policy import Policy, PolicyHistoryEntry, PolicyDraftResponse
from app.models.escalation import EscalationAdviceResponse, EscalationReviewResponse
from app.models.receipt import Receipt
from app.models.checkout import CheckoutResponse
from app.models.merchant import MerchantRegisterResponse, MerchantRegisterWithRazorpayResponse
from app.models.common import StatusResponse, AgentActionResponse, AgentRegisterResponse, PublicKeyResponse
from app.models.red_team import RedTeamRunResult, RedTeamRunRecord
from app.db.models import EscalationRow
from app.models.ucp import UcpProfileResponse
from app.engine.evaluate import evaluate
from app.engine.digest import compute_digest
from app.models.digest import DigestResponse, DigestNarrateResponse
from app.engine.signing import sign_receipt
from app.engine.identity import verify_agent_signature
from app.razorpay_client import create_payment_link, verify_razorpay_credentials
from app import ai_client
from app.auth import require_merchant_auth, generate_api_key, _hash_key
from app.db.session import init_db, get_session
from app.db import repo


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print("Warrant is up. Database ready, signing key loaded (persistent).")
    yield


app = FastAPI(title="Warrant", description="The merchant's side of agentic commerce", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # demo only -- fine for a hackathon, not for production
    allow_methods=["*"],
    allow_headers=["*"],
)


def _auth(merchant_id: str, session: Session, authorization: str | None) -> None:
    require_merchant_auth(merchant_id, session, authorization)


def _resolve_items_against_catalog(session: Session, merchant_id: str, items: list[CartItem]) -> list[CartItem]:
    """
    Never trust what an agent claims an item is. Look up every incoming
    item against the merchant's own catalog and overwrite title/price/
    category with that authoritative data; anything that doesn't match a
    real listing gets marked unlisted (see engine/evaluate.py's
    check_items_are_listed). Shared by /checkout-sessions and the
    adversarial-agent demo endpoint so both go through the identical
    real defense, not a look-alike copy of it.
    """
    catalog = repo.get_catalog(session, merchant_id)
    if not catalog:
        return items

    resolved = []
    for item in items:
        match = catalog.find_variant(item.id)
        if match:
            resolved.append(CartItem(
                id=item.id, title=match.title, price=match.price,
                category=match.category, quantity=item.quantity, listed=True,
            ))
        else:
            resolved.append(item.model_copy(update={"listed": False}))
    return resolved


@app.get("/.well-known/ucp", response_model=UcpProfileResponse)
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


# ---------- Merchant accounts ----------

class MerchantRegisterRequest(BaseModel):
    merchant_id: str


@app.post("/merchants/register", response_model=MerchantRegisterResponse)
def register_merchant(req: MerchantRegisterRequest, session: Session = Depends(get_session)):
    """
    Creates a shop account. Returns the API key exactly once -- same
    rule as Razorpay's own dashboard: if you lose it, you generate a new
    one, you don't get to see the old one again. We only ever store its
    SHA-256 hash.
    """
    if repo.merchant_exists(session, req.merchant_id):
        raise HTTPException(409, "merchant already registered")

    api_key = generate_api_key()
    repo.create_merchant(session, req.merchant_id, _hash_key(api_key))
    return {
        "merchant_id": req.merchant_id,
        "api_key": api_key,
        "warning": "save this now -- it will never be shown again",
    }


class MerchantRegisterWithRazorpayRequest(BaseModel):
    merchant_id: str
    razorpay_key_id: str
    razorpay_key_secret: str


@app.post("/merchants/register-with-razorpay", response_model=MerchantRegisterWithRazorpayResponse)
async def register_merchant_with_razorpay(req: MerchantRegisterWithRazorpayRequest,
                                           session: Session = Depends(get_session)):
    """
    The alternative to POST /merchants/register: instead of Warrant
    minting its own separate API key -- a second credential on top of
    whatever Razorpay keys a merchant already has, which is exactly the
    kind of extra friction a real Razorpay-integrated feature shouldn't
    add -- a merchant's own real Razorpay test-mode key_id/key_secret
    becomes their Warrant credential directly.

    We don't just check these are shaped like Razorpay keys: we call
    Razorpay with them (see razorpay_client.verify_razorpay_credentials)
    and only register if Razorpay itself accepts them. From then on,
    `Authorization: Bearer <key_id>:<key_secret>` -- the same keys,
    never anything Warrant generated -- authenticates every merchant
    action, through the exact same require_merchant_auth check as the
    other registration path; only the source of the secret differs, not
    how it's verified.

    Real limitation, stated plainly: this proves the caller possesses a
    genuine, working Razorpay key pair, not that Razorpay has vouched
    "this key belongs to merchant X" the way a real OAuth/Partner-API
    integration would. That would require Razorpay approving this as a
    partner application, which is out of reach for a buildathon build --
    see README for the fuller explanation of this boundary.
    """
    if repo.merchant_exists(session, req.merchant_id):
        raise HTTPException(409, "merchant already registered")

    try:
        verified = await verify_razorpay_credentials(req.razorpay_key_id, req.razorpay_key_secret)
    except httpx.HTTPError as e:
        raise HTTPException(503, f"could not reach Razorpay to verify these keys: {e}")

    if not verified:
        raise HTTPException(401, "Razorpay rejected this key_id/key_secret pair -- check they're correct")

    credential = f"{req.razorpay_key_id}:{req.razorpay_key_secret}"
    repo.create_merchant(session, req.merchant_id, _hash_key(credential))
    return {
        "merchant_id": req.merchant_id,
        "note": "Verified with Razorpay. Authenticate as "
                "'Authorization: Bearer <razorpay_key_id>:<razorpay_key_secret>' -- "
                "the same keys you just gave us. Warrant never generated or stored a "
                "separate credential for you.",
    }


# ---------- Catalog ----------

class CatalogUploadRequest(BaseModel):
    merchant_id: str
    catalog: Catalog


@app.post("/catalog", response_model=CatalogSaveResponse)
def upload_catalog(req: CatalogUploadRequest, session: Session = Depends(get_session),
                    authorization: str | None = Header(None)):
    _auth(req.merchant_id, session, authorization)
    repo.save_catalog(session, req.catalog)
    return {"status": "saved", "product_count": len(req.catalog.products)}


class CatalogFromTextRequest(BaseModel):
    merchant_id: str
    raw_text: str   # e.g. one messy product per line, however the shop owner typed it


@app.post("/catalog/from-text", response_model=CatalogFromTextResponse)
async def catalog_from_text(req: CatalogFromTextRequest, session: Session = Depends(get_session),
                             authorization: str | None = Header(None)):
    """
    AI reads messy product text and produces a clean structured catalog.
    This is where AI genuinely belongs -- turning fuzzy human input into
    a structured shape. Saved immediately for the demo; a stricter
    production version could show a draft for approval first, same as
    the policy compiler below.
    """
    _auth(req.merchant_id, session, authorization)

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


@app.post("/catalog/search", response_model=CatalogSearchResponse)
def search_catalog(merchant_id: str, query: str = "", session: Session = Depends(get_session)):
    """No auth -- this is the endpoint a shopping agent calls to browse. Same as a real storefront."""
    catalog = repo.get_catalog(session, merchant_id)
    if not catalog:
        raise HTTPException(404, "no catalog for this merchant yet")
    matches = [
        p for p in catalog.products
        if query.lower() in p.title.lower()
    ] if query else catalog.products
    return {"products": matches}


# ---------- Policy ----------

@app.post("/policy", response_model=StatusResponse)
def save_policy_endpoint(policy: Policy, session: Session = Depends(get_session),
                          authorization: str | None = Header(None)):
    _auth(policy.merchant_id, session, authorization)
    repo.save_policy(session, policy)
    return {"status": "saved"}


class PolicyDraftRequest(BaseModel):
    merchant_id: str
    plain_english: str  # e.g. "don't let agents buy gift cards, cap orders at 5000 rupees"


@app.post("/policy/draft-from-text", response_model=PolicyDraftResponse)
async def draft_policy_from_text(req: PolicyDraftRequest, session: Session = Depends(get_session),
                                  authorization: str | None = Header(None)):
    """
    AI drafts a policy from plain English. Returns the draft -- does NOT
    save it. The merchant must review it and POST /policy themselves to
    actually apply it. This split (AI drafts, human approves, code
    enforces) is the whole thesis of the project.
    """
    _auth(req.merchant_id, session, authorization)

    if not ai_client.is_configured():
        raise HTTPException(503, "AI not configured -- set NVIDIA_API_KEY in backend/.env")

    draft = await ai_client.compile_policy_text(req.merchant_id, req.plain_english)
    return {"draft": draft, "note": "review this, then POST it to /policy to actually apply it"}


@app.get("/policy/{merchant_id}", response_model=Policy)
def get_policy_endpoint(merchant_id: str, session: Session = Depends(get_session)):
    """No auth -- a shopping agent needs to read the rules before it can shop here."""
    policy = repo.get_policy(session, merchant_id)
    if not policy:
        raise HTTPException(404, "no policy set for this merchant yet")
    return policy


@app.get("/policy/{merchant_id}/history", response_model=list[PolicyHistoryEntry])
def get_policy_history_endpoint(merchant_id: str, session: Session = Depends(get_session),
                                 authorization: str | None = Header(None)):
    """
    Every past saved version of this merchant's rules, most recent
    first -- merchant-only, since old spending limits are exactly as
    sensitive as the current ones. POST /policy has no separate
    "restore" action on purpose: loading a past version into the form
    and clicking Save again goes through the exact same review-then-save
    path as any other change, rather than a second, less-checked way to
    make rules live.
    """
    _auth(merchant_id, session, authorization)
    rows = repo.list_policy_history(session, merchant_id)
    return [{"id": r.id, "saved_at": r.saved_at, "policy": r.snapshot} for r in rows]


# ---------- Agent identity ----------

class AgentRegisterRequest(BaseModel):
    agent_id: str
    public_key_hex: str


@app.post("/agents/register", response_model=AgentRegisterResponse)
def register_agent_endpoint(req: AgentRegisterRequest, session: Session = Depends(get_session)):
    """No merchant auth -- this is the AGENT proving its own identity, not a merchant
    management action. Any agent may register itself; whether it can actually buy
    anything is still gated by the merchant's policy at checkout time."""
    repo.register_agent(session, req.agent_id, req.public_key_hex)
    return {"status": "registered", "agent_id": req.agent_id}


# ---------- The main event: checkout ----------

class CheckoutRequest(BaseModel):
    merchant_id: str
    agent_id: str
    items: list[CartItem]
    signature_hex: str | None = None  # signs the exact `items` list, see engine/identity.py
    payment_mode: str = "prepaid"     # "prepaid" | "cod" -- see models/cart.py


@app.post("/checkout-sessions", response_model=CheckoutResponse)
async def checkout(req: CheckoutRequest, session: Session = Depends(get_session),
                    idempotency_key: str | None = Header(None, alias="Idempotency-Key")):
    # If we've seen this exact Idempotency-Key before, hand back the SAME
    # answer instead of processing the cart twice -- a retried request
    # (network hiccup, agent bug) must never create a second real order.
    # Same requirement as the real ACP/UCP specs, see research/06.
    if idempotency_key:
        cached = repo.get_idempotent_response(session, idempotency_key)
        if cached:
            return json.loads(cached)

    if repo.is_agent_revoked(session, req.agent_id):
        raise HTTPException(403, "this agent's access has been revoked by the merchant")

    policy = repo.get_policy(session, req.merchant_id)
    if not policy:
        raise HTTPException(404, "merchant has not set a policy -- refusing to guess")

    # Was this cart really signed by the agent it claims to be? Verify
    # against exactly what the agent submitted, BEFORE any catalog
    # resolution below rewrites it -- the agent must have signed what it
    # actually sent, not a version we've since corrected.
    identity_verified = False
    public_key_hex = repo.get_agent_public_key(session, req.agent_id)
    if public_key_hex and req.signature_hex:
        identity_verified = verify_agent_signature(req.items, req.signature_hex, public_key_hex)

    # Never trust what the agent claims an item is -- resolve against
    # the merchant's own catalog (see helper docstring above).
    resolved_items = _resolve_items_against_catalog(session, req.merchant_id, req.items)

    cart = Cart(id=f"cart_{req.merchant_id}_{req.agent_id}_{time.time_ns()}",
                merchant_id=req.merchant_id, items=resolved_items, payment_mode=req.payment_mode)

    recent_order_count = repo.count_recent_orders(
        session, req.merchant_id, req.agent_id, policy.velocity_window_minutes,
    )

    receipt = evaluate(cart, policy, agent_id=req.agent_id, identity_verified=identity_verified,
                        recent_order_count=recent_order_count)

    private_key, _ = repo.get_or_create_signing_key(session)
    signed_receipt = sign_receipt(receipt, private_key)

    receipt_id = repo.save_receipt(session, signed_receipt, req.items)

    result = {"receipt": signed_receipt.model_dump(mode="json")}

    if signed_receipt.decision.value == "allow":
        if cart.payment_mode == "cod":
            # Explicitly allowed COD (policy.allow_cod_for_agents) -- no prepayment
            # exists to collect, so there's nothing to hand to Razorpay. The order is
            # confirmed on trust the merchant already extended; RTO risk is theirs by
            # choice, not by an unnoticed default.
            result["order"] = {"status": "confirmed_cod", "note": "cash on delivery -- no payment link needed"}
        else:
            # The decision itself (ALLOW) is already signed and saved above --
            # that's the actual product, the payment link is Razorpay
            # integration layered on top of it. So a Razorpay failure here
            # (the same real 429 that used to crash the escalation-review
            # endpoint too, before that was fixed) degrades gracefully
            # instead of turning an already-decided, already-persisted
            # ALLOW into a bare 500: the receipt stands, `payment` comes
            # back null, and the note says plainly what happened.
            try:
                payment = await create_payment_link(
                    amount_paise=cart.total,
                    description=f"Order {cart.id} via agent {req.agent_id}",
                )
                result["payment"] = payment
            except httpx.HTTPError as e:
                result["note"] = (
                    f"Order allowed and signed, but Razorpay could not be reached to create "
                    f"a payment link right now ({e}). The decision itself is final -- "
                    f"contact the merchant to arrange payment."
                )

    elif signed_receipt.decision.value == "escalate":
        escalation_id = repo.create_escalation(
            session, receipt_id, req.merchant_id, req.agent_id, req.items, cart.total,
        )
        result["escalation_id"] = escalation_id
        result["note"] = "every rule passed, but this order needs a human to approve it"

    if idempotency_key:
        repo.save_idempotent_response(session, idempotency_key, req.merchant_id, json.dumps(result))

    return result


# ---------- Receipts (for the dashboard) ----------

@app.get("/receipts", response_model=list[Receipt])
def list_receipts_endpoint(merchant_id: str, session: Session = Depends(get_session),
                            authorization: str | None = Header(None)):
    _auth(merchant_id, session, authorization)
    return repo.list_receipts(session, merchant_id)


@app.get("/digest", response_model=DigestResponse)
def get_digest(merchant_id: str, window_hours: int = 168, session: Session = Depends(get_session),
                authorization: str | None = Header(None)):
    """
    The plain-language answer to "what's actually been happening at my
    store" -- not a receipts list the merchant has to read line by line
    and interpret themselves. Deliberately synchronous and AI-free: every
    number and flag here is decided by fixed code (engine/digest.py), so
    this responds fast regardless of whether AI is configured or slow.
    See POST /digest/narrate for the plain-language version -- kept as a
    separate call so a merchant sees real numbers immediately instead of
    waiting on a live model call before seeing anything at all (measured
    live at ~14s for a week of history -- too slow to gate the whole
    page on).

    window_hours defaults to 168 (one week).

    `response_model=DigestResponse` -- this is one of the routes an
    outside admin panel would actually want to render directly (see
    models/digest.py's docstring): declaring the shape here is what
    makes /docs and /openapi.json describe it accurately instead of
    just "some JSON object", the same way the internal frontend has
    always had to just guess the shape from main.py's source.
    """
    _auth(merchant_id, session, authorization)

    since = datetime.now(timezone.utc) - timedelta(hours=window_hours)
    receipt_rows = repo.list_receipts_since(session, merchant_id, since)
    escalations = repo.list_escalations_since(session, merchant_id, since)

    receipts_for_digest = [
        {
            "agent_id": r.agent_id,
            "decision": r.decision,
            "rules_checked": r.rules_checked,
            "cart_items": r.cart_items,
            "cart_total": r.cart_total,
            "timestamp": r.timestamp,
        }
        for r in receipt_rows
    ]
    stats = compute_digest(receipts_for_digest, len(escalations), window_hours)

    # Awareness without an action is half the point -- the frontend needs
    # to know, per agent, whether it's already revoked so it can offer
    # "revoke" or show "already revoked" instead of a dead-end flag with
    # nothing to do about it.
    for agent in stats["agents"]:
        agent["revoked"] = repo.is_agent_revoked(session, agent["agent_id"])

    return {"stats": stats}


class DigestNarrateRequest(BaseModel):
    merchant_id: str
    stats: dict


@app.post("/digest/narrate", response_model=DigestNarrateResponse)
async def narrate_digest(req: DigestNarrateRequest, session: Session = Depends(get_session),
                          authorization: str | None = Header(None)):
    """
    Turns stats already computed by GET /digest into plain language for a
    non-technical shop owner. Separate call, on purpose (see get_digest's
    docstring) -- the frontend calls this only after the real numbers are
    already on screen, same pattern as the escalation advisor
    (GET /escalations/{id}/advice): AI narrates, nothing here decides or
    changes what was already flagged.
    """
    _auth(req.merchant_id, session, authorization)

    if not ai_client.is_configured():
        raise HTTPException(503, "AI not configured -- set NVIDIA_API_KEY in backend/.env")

    narrative = await ai_client.summarize_digest(req.stats)
    return {"narrative": narrative}


@app.get("/signing-public-key", response_model=PublicKeyResponse)
def get_public_key(session: Session = Depends(get_session)):
    """Public on purpose -- anyone must be able to independently verify our receipts are genuine."""
    _, public_key = repo.get_or_create_signing_key(session)
    return {"public_key_hex": public_key.hex()}


# ---------- Escalations: the human-review queue ----------

@app.get("/escalations", response_model=list[EscalationRow])
def list_escalations_endpoint(merchant_id: str, status: str = "pending",
                               session: Session = Depends(get_session),
                               authorization: str | None = Header(None)):
    _auth(merchant_id, session, authorization)
    return repo.list_escalations(session, merchant_id, status)


@app.get("/escalations/{escalation_id}/advice", response_model=EscalationAdviceResponse)
async def advise_on_escalation_endpoint(escalation_id: int, session: Session = Depends(get_session),
                                         authorization: str | None = Header(None)):
    """
    Drafts a recommendation for the human reviewing this escalation --
    never decides anything itself. Same tier as policy drafting and
    catalog normalization: an AI Advisor whose output is only ever a
    suggestion a human still has to act on via POST .../review.
    """
    existing = repo.get_escalation(session, escalation_id)
    if not existing:
        raise HTTPException(404, "no such escalation")
    _auth(existing.merchant_id, session, authorization)

    if not ai_client.is_configured():
        raise HTTPException(503, "AI not configured -- set NVIDIA_API_KEY in backend/.env")

    history = repo.summarize_agent_history(session, existing.merchant_id, existing.agent_id)
    advice = await ai_client.advise_on_escalation(
        cart_items=existing.cart_items,
        cart_total_rupees=existing.cart_total / 100,
        agent_id=existing.agent_id,
        recent_agent_history=history,
    )
    return {"escalation_id": escalation_id, "advice": advice}


class ReviewRequest(BaseModel):
    approve: bool
    note: str | None = None


@app.post("/escalations/{escalation_id}/review", response_model=EscalationReviewResponse)
async def review_escalation_endpoint(escalation_id: int, req: ReviewRequest,
                                      session: Session = Depends(get_session),
                                      authorization: str | None = Header(None)):
    """
    A real human decision. If approved, the payment actually gets
    created now -- money only moves after both the automated rules AND
    a person have said yes.
    """
    existing = repo.get_escalation(session, escalation_id)
    if not existing:
        raise HTTPException(404, "no such escalation")
    _auth(existing.merchant_id, session, authorization)
    if existing.status != "pending":
        # Cheap pre-check before we do anything expensive below. The
        # authoritative check still happens inside review_escalation()
        # against a freshly re-read row, so this is an optimization, not
        # the actual guard.
        raise HTTPException(409, f"escalation {escalation_id} was already {existing.status}")

    # For an approval, create the REAL payment link BEFORE committing the
    # decision as "approved". This ordering matters: a prior version
    # committed the status first and called Razorpay second, and a live
    # test caught the actual failure mode -- Razorpay's API returned 429
    # (rate limited from earlier testing this same session), the payment
    # call raised, but the escalation was already sitting in the database
    # as "approved" with no payment ever created and no way to retry,
    # since a second call to this endpoint now permanently returns 409.
    # Doing the money-moving step first means a failure here leaves the
    # escalation exactly where it was -- pending, retryable -- instead of
    # stuck in a state that claims something happened when it didn't.
    payment = None
    if req.approve:
        # A real 429 from Razorpay (hit live, from this project's own test
        # traffic) used to propagate as a bare, unhandled 500 -- correct on
        # money-safety (the escalation below is never reached, so nothing
        # gets falsely committed) but useless to any caller, human or an
        # integrator's admin panel, trying to render a real error. Caught
        # here and turned into a typed, honest 503: the escalation is
        # untouched and this exact request is safe to retry once Razorpay
        # recovers, so say so instead of leaking a stack trace.
        try:
            payment = await create_payment_link(
                amount_paise=existing.cart_total,
                description=f"Order {existing.receipt_id} (human-approved) via agent {existing.agent_id}",
            )
        except httpx.HTTPError as e:
            raise HTTPException(
                503,
                f"Could not reach Razorpay to create the payment link ({e}) -- "
                f"this escalation was NOT changed and is still pending. Safe to retry.",
            )

    try:
        row = repo.review_escalation(session, escalation_id, req.approve, req.note)
    except repo.AlreadyReviewedError as e:
        # Rare: this call's own payment succeeded (if approving) but a
        # concurrent request won the race to commit the decision first.
        # The payment link above is real and was already created; it is
        # not automatically voided here, since we have no way to reverse
        # a Razorpay payment link from this endpoint. Surfaced explicitly
        # rather than silently swallowed.
        raise HTTPException(
            409,
            f"{e} -- note: a payment link may have just been created by this "
            f"request before the conflict was detected: {payment}",
        )

    result = {"escalation": row}
    if payment:
        result["payment"] = payment
    return result


# ---------- Revocation ----------

@app.post("/agents/{agent_id}/revoke", response_model=AgentActionResponse)
def revoke_agent(agent_id: str, merchant_id: str, session: Session = Depends(get_session),
                  authorization: str | None = Header(None)):
    _auth(merchant_id, session, authorization)
    repo.set_agent_revoked(session, agent_id, True)
    return {"status": "revoked", "agent_id": agent_id}


@app.post("/agents/{agent_id}/unrevoke", response_model=AgentActionResponse)
def unrevoke_agent(agent_id: str, merchant_id: str, session: Session = Depends(get_session),
                    authorization: str | None = Header(None)):
    _auth(merchant_id, session, authorization)
    repo.set_agent_revoked(session, agent_id, False)
    return {"status": "unrevoked", "agent_id": agent_id}


# ---------- Red team: an autonomous AI tries to break your own rules ----------

class RedTeamRequest(BaseModel):
    merchant_id: str
    goal: str = "Get a gift card purchased for a customer, no matter what it takes."
    max_rounds: int = 5


def _catalog_summary_for_prompt(catalog) -> str:
    if not catalog or not catalog.products:
        return "(no catalog listed for this merchant)"
    lines = []
    for p in catalog.products:
        for v in p.variants:
            lines.append(f"- id={v.id}, title=\"{v.title}\", price=Rs{v.price/100:.0f}, category={v.category}")
    return "\n".join(lines)


@app.post("/red-team/run", response_model=RedTeamRunResult)
async def run_red_team(req: RedTeamRequest, session: Session = Depends(get_session),
                        authorization: str | None = Header(None)):
    """
    A real autonomous AI agent (not a scripted sequence) repeatedly
    tries to get something past this merchant's actual rules, adapting
    its strategy after every rejection -- exactly the adversarial
    pressure the whole engine is built to survive. It sees only the
    catalog and the outcome of its own attempts, never the policy
    itself, same as a real attacker would. The full transcript is
    persisted, not just returned once and forgotten.
    """
    _auth(req.merchant_id, session, authorization)

    if not ai_client.is_configured():
        raise HTTPException(503, "AI not configured -- set NVIDIA_API_KEY in backend/.env")

    policy = repo.get_policy(session, req.merchant_id)
    if not policy:
        raise HTTPException(404, "merchant has not set a policy -- refusing to guess")

    catalog = repo.get_catalog(session, req.merchant_id)
    catalog_summary = _catalog_summary_for_prompt(catalog)

    history: list[dict] = []
    rounds: list[dict] = []
    outcome = "max_rounds_reached"

    for round_number in range(1, req.max_rounds + 1):
        attempt = await ai_client.adversarial_agent_attempt(req.goal, catalog_summary, history)

        if attempt.get("give_up"):
            outcome = "agent_gave_up"
            rounds.append({
                "round": round_number, "reasoning": attempt.get("reasoning", ""),
                "items": [], "decision": "gave_up", "rules_failed": [],
            })
            break

        raw_items = [
            CartItem(
                id=i["id"], title=i["title"],
                price=round(float(i["price_rupees"]) * 100),
                category=i.get("category"), quantity=int(i.get("quantity", 1)),
            )
            for i in attempt.get("items", [])
        ]

        resolved_items = _resolve_items_against_catalog(session, req.merchant_id, raw_items)
        cart = Cart(id=f"redteam_{req.merchant_id}_{time.time_ns()}",
                    merchant_id=req.merchant_id, items=resolved_items)

        receipt = evaluate(
            cart, policy, agent_id="red-team-agent",
            identity_verified=True,  # isolate the catalog/category defense, not identity
            recent_order_count=round_number - 1,
        )

        rules_failed = [r.rule_name for r in receipt.rules_checked if not r.passed]
        rounds.append({
            "round": round_number,
            "reasoning": attempt.get("reasoning", ""),
            "items": [i.model_dump() for i in raw_items],  # what the agent CLAIMED
            "resolved_items": [i.model_dump() for i in resolved_items],  # what it actually was
            "decision": receipt.decision.value,
            "rules_failed": rules_failed,
        })
        history.append({
            "items": [i.model_dump() for i in raw_items],
            "decision": receipt.decision.value,
            "reason": "; ".join(r.detail for r in receipt.rules_checked if not r.passed) or None,
        })

        if receipt.decision.value == "allow":
            outcome = "breached"
            break
    else:
        # Every round ran to completion without a single "allow" and
        # without the agent giving up -- the merchant's rules held
        # against every attempt it made.
        outcome = "held"

    run_id = repo.save_red_team_run(session, req.merchant_id, req.goal, rounds, outcome)

    return {"run_id": run_id, "goal": req.goal, "outcome": outcome, "rounds": rounds}


@app.get("/red-team/runs", response_model=list[RedTeamRunRecord])
def list_red_team_runs_endpoint(merchant_id: str, session: Session = Depends(get_session),
                                 authorization: str | None = Header(None)):
    _auth(merchant_id, session, authorization)
    return repo.list_red_team_runs(session, merchant_id)
