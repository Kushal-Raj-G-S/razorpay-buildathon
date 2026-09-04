# Warrant

**The merchant's side of agentic commerce.**

Every agentic-commerce protocol — AP2, ACP, UCP, even UPI Reserve Pay — lets the *buyer*
put a leash on an AI shopping agent. None of them let the *merchant* declare what it will
accept, or prove afterward what it decided. Nine protocols were read at spec level
(see [`research/06-protocols.md`](research/06-protocols.md)) and every single one refuses
that question. Warrant is the missing half.

Built for [Razorpay's AI Buildathon 2026](https://razorpay.com/buildathon/), Track 01 —
see [`research/`](research/) for the full evidence base and [`DECISION.md`](DECISION.md)
for how the build was scoped.

---

## What it actually does

1. **A merchant writes rules** — spending limits, banned categories, Cash-on-Delivery
   policy, how many orders one agent may place per hour — either by filling in fields, or
   by typing plain English and letting AI draft the fields for them (they still have to
   click Save; nothing applies itself).
2. **Every AI-agent checkout gets checked against those rules, deterministically.** No LLM
   sits in the decision path — see *"Why no AI in the decision path"* below.
3. **Every item in the cart is verified against the merchant's own catalog**, not trusted
   from the agent's claim. An agent cannot mislabel a gift card as "clothing" — the
   category is overwritten with the merchant's real listing before any rule runs.
4. **Every decision is signed** (Ed25519) and persisted, allow or block or escalate, with
   the exact rule that fired.
   Every saved policy also keeps a full version history — no more rewriting the same rules
   from scratch to tweak one number; past versions are listed and can be reloaded (never
   auto-applied — reloading fills the form, you still click Save).
5. **A merchant can send a real autonomous AI to attack their own rules** — `/red-team` —
   and get back a full, unscripted transcript of what it tried and why it failed.
6. **The whole decision engine is exposed as an MCP server**, the same protocol Razorpay's
   own Agent Studio (built on the Claude Agent SDK) uses to call tools — see
   [`backend/app/mcp_server.py`](backend/app/mcp_server.py).
7. **A merchant doesn't have to read receipts one at a time to know what's going on** —
   `/digest` (see [`backend/app/engine/digest.py`](backend/app/engine/digest.py)) turns a
   window of activity into a footprint per agent (attempts, blocks, which rule caught them,
   first/last seen) and a set of flags — an agent trying items that don't match the real
   catalog, one hitting the order-frequency limit, one that kept getting blocked and kept
   trying anyway. What counts as a flag is fixed code, same rule as checkout itself; AI, if
   configured, only turns those already-decided flags into a plain-English sentence a
   non-technical shop owner can read in ten seconds. Exists because "write rules once and
   walk away" isn't enough — a small shop has no security team watching for a slow-burn
   pattern the way a large company might. Every flag has a real action next to it —
   Revoke, right there — not just a warning with nowhere to act on it.

## Authenticating with your own Razorpay keys, not a second credential

`POST /merchants/register` mints a Warrant-only API key — simple, but it's a second
credential on top of whatever Razorpay keys a merchant already has, which is exactly the
kind of friction a real Razorpay-integrated feature shouldn't add. `POST
/merchants/register-with-razorpay` is the alternative: hand over your real Razorpay
test-mode `key_id`/`key_secret`, Warrant calls Razorpay with them
(`razorpay_client.verify_razorpay_credentials`, one cheap `GET /payment_links?count=1`) to
confirm they're genuine — not just shaped like a key — and if Razorpay accepts them, those
same keys become how you authenticate to Warrant from then on
(`Authorization: Bearer <key_id>:<key_secret>`). No separate credential is ever minted.

Verified live against real Razorpay test-mode keys, not just mocked: registering with the
real pair succeeds and mints nothing extra; registering with a fabricated pair gets a 401
because *Razorpay itself* rejects it, not a local format check; the real key pair then
successfully authenticates an actual policy save. 5 additional tests stub the Razorpay call
for the rest of the suite, the same way `create_payment_link` is already stubbed elsewhere.

**The honest boundary, stated plainly**: this proves the caller possesses a genuine,
working Razorpay key pair — it is not the same claim as a real OAuth/Partner-API
integration, where Razorpay itself would vouch "this key belongs to merchant X." That
requires Razorpay approving this as a partner application, which is out of reach for a
buildathon build, so it wasn't faked. If this ever runs *inside* Razorpay's own
infrastructure rather than as an external caller of their public API, this whole question
mostly dissolves — their own session already knows who the merchant is, and this file is
the seam that gets replaced, not the permanent answer.

## For integrators — this is a feature, not a SaaS with its own required frontend

The Next.js dashboard in `frontend/` is a reference implementation, not the product. A
merchant using this through Razorpay would see it inside Razorpay's own dashboard, not ours
— so the real deliverable is the API, and it has to be usable without reading `main.py`'s
source to know what a response looks like.

**Every single endpoint now declares a typed Pydantic `response_model`** — started with the
four most Digest-adjacent routes, then extended to the rest: catalog, policy, checkout,
receipts, escalations, agent revocation, red-team, merchant registration (both paths), and
the UCP discovery profile. New model files: `models/checkout.py`, `models/merchant.py`,
`models/common.py`, `models/red_team.py`, `models/ucp.py`, plus additions to the existing
`models/catalog.py`, `models/policy.py`, and `models/escalation.py`. `GET /docs` and
`GET /openapi.json` now describe every route's real shape — named, browsable, expandable
schemas, not "some JSON object" — which is checkable directly: a small audit script against
`/openapi.json` confirms zero routes left with an untyped response.

One real, honest side effect of typing `POST /checkout-sessions`: the response now always
includes `payment`/`order`/`escalation_id`/`note` (`null` when not applicable) instead of
sometimes omitting the key entirely — a more predictable contract, but it changed one
existing test's assertion from "key absent" to "key is null" (`test_api.py`). Not a
behavior regression for the frontend (JS treats `null` and `undefined` the same in every
place these fields are read), but worth naming since it's the kind of thing that looks like
nothing until a strict outside client checks for key presence instead of value.

**Fixed**: approving an escalation while Razorpay's API is rate-limited (429, which real
testing traffic against a test-mode account hits often — it happened again, for real, while
verifying this exact fix) used to return a bare, unhandled `500 Internal Server Error` —
`create_payment_link`'s `raise_for_status()` wasn't caught anywhere in
`review_escalation_endpoint`. Now caught and turned into a typed `503` naming exactly what
happened and that the escalation is untouched and safe to retry. The escalation itself was
already safely pending and retryable before this fix (that ordering was fixed earlier — see
git history) — only the HTTP response in that moment was opaque; now it's a clean,
renderable error instead of a leaked stack trace. Verified twice: once against a real 429
from Razorpay live (the test account was still rate-limited from earlier testing when this
fix landed), confirming the escalation stayed pending afterward, and once via a mocked
`httpx.HTTPStatusError` in `test_a_failed_payment_leaves_the_escalation_retryable_not_stuck`.

## Why no AI in the decision path

NIST measured agent-hijacking success rising from **11% to 81%** once an attack is
tailored to the specific target agent, not drawn from a generic baseline
([research/04](research/04-trust-fraud-liability.md)). A bound enforced by a prompt is not
a bound. So: **AI drafts the rules and normalizes messy catalog data — deterministic code
enforces them.** That split is checkable in the repo layout itself: nothing in
`backend/app/engine/` imports anything that can make a network or inference call.

## Architecture

```
frontend/          Next.js 16 + Tailwind v4, warm-paper/ledger-green design system
backend/
  app/
    engine/        THE BOUNCER — pure functions, no AI, no I/O. evaluate.py runs every rule.
    ai_client.py   The two places AI is deliberately used: catalog normalization, policy
                   drafting, and the red-team adversary. Nowhere else.
    db/            SQLModel tables + repo functions. SQLite by default, Postgres via
                   DATABASE_URL (verified live against Neon — see git log).
    mcp_server.py  The same engine, exposed as MCP tools for any Claude Agent SDK host.
    main.py        FastAPI routes. Every merchant-facing write requires
                    Authorization: Bearer <api_key> (see app/auth.py) — every agent-facing
                    route (checkout, catalog search) stays open, same as a real storefront.
  tests/           43 tests, real HTTP integration tests via FastAPI's TestClient, not
                   just unit tests of internals. Run: pytest -q
research/           Every claim behind every design decision, sourced.
```

## Running it locally

**Backend:**
```bash
cd backend
python -m venv venv && venv\Scripts\pip install -r requirements.txt
copy .env.example .env   # fill in RAZORPAY_*, NVIDIA_API_KEY — see .env.example
venv\Scripts\python -m uvicorn app.main:app --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
copy .env.example .env.local   # NEXT_PUBLIC_MERCHANT_API_KEY comes from
                                # POST /merchants/register (see below)
npm run dev
```

**First-time setup** (no signup UI exists yet — see Known Gaps):
```bash
curl -X POST http://127.0.0.1:8000/merchants/register -H "Content-Type: application/json" -d "{\"merchant_id\": \"shop_123\"}"
# copy the returned api_key into frontend/.env.local as NEXT_PUBLIC_MERCHANT_API_KEY
```

**Tests:** `cd backend && pytest -q` — 55 passing, no network dependency (Razorpay calls
and AI narration are stubbed in the test suite; the real integrations are proven
separately, live, in git history).

## Running it with Docker

```bash
cp backend/.env.example backend/.env   # fill in real keys first
docker compose up --build
```

That's both services, one command. Actually verified, not just written and assumed —
`docker compose build` was run to completion, both containers started, a merchant was
registered and a policy saved and a poisoned cart checked out **inside the running
container** with the correct signed BLOCK receipt coming back, and the backend container
was restarted mid-session to confirm the SQLite data in the named volume survives a
restart rather than silently resetting. Frontend was checked by opening it in a real
browser too, not just curling for a 200.

Backend health-gates the frontend (`depends_on: condition: service_healthy` in
`docker-compose.yml`), so `frontend` won't even attempt to start until `backend` is
actually answering requests, not just "container running."

The Digest (`/digest`, `/digest/narrate`) was verified the same way after it was built:
rebuilt both images, ran a real checkout inside the running backend container to trip the
catalog-mismatch flag, confirmed `GET /digest` answers in ~1s and `POST /digest/narrate`
completes with a real NVIDIA API response in ~20s (proving the container has outbound
network access and the right key from `backend/.env`), and loaded the actual page in a
browser pointed at the container's port 3000 to watch the numbers render immediately and
the AI summary land a few seconds later, same as local dev.

---

## Known gaps — read this before assuming anything below isn't here for a reason

Built fast, tested hard, but not everything is closed. Listed here explicitly rather than
left for someone to discover, because a security/trust product that hides its own gaps is
not one anyone should trust.

**Not deployed anywhere permanent.** Docker makes this trivially deployable — `docker
compose up --build` is a working, verified one-command boot of both services — but nobody
has actually pointed it at a real host yet. There is still no live URL. Anyone evaluating
it needs to run it themselves, either directly or via Docker, per the instructions above.

**No merchant self-service signup UI.** `POST /merchants/register` works and is tested,
but there's no page for it — account creation happens via curl. A real product needs this
before a second merchant could ever use it without a developer's help.

**No API key rotation endpoint.** If a merchant's key leaks, there is no way to reissue one
without direct database access.

**CORS is wide open** (`allow_origins=["*"]`) — fine for local development, not for
production.

**No rate limiting.** The AI endpoints (`/catalog/from-text`, `/policy/draft-from-text`,
`/red-team/run`) can be called as fast as a client wants, with real NVIDIA API cost behind
every call.

**For a merchant with no catalog uploaded, item price is 100% agent-declared and
unverified.** The catalog-truth defense (see `_resolve_items_against_catalog` in
`main.py`) only activates once a merchant has uploaded one — before that, nothing stops an
agent from declaring a false price for a real transaction. This is disclosed, not hidden:
uploading a catalog is what turns this defense on.

**No structured logging or error monitoring.** Default `print()` and uvicorn logs only —
nothing like Sentry wired in.

**Revoking an agent used to silently fail for any agent that never called
`POST /agents/register` first — the normal case, since an agent only needs to exist by
showing up at `/checkout-sessions`.** `set_agent_revoked` only updated an existing
`AgentRow` and never created one, so clicking Revoke on the Digest page returned 200 OK,
the UI happily flipped to "Unrevoke", and the agent could still check out immediately
afterward. Found by actually clicking the button in a browser and then checking with a
separate curl call whether it did anything — it didn't. Fixed in
[`backend/app/db/repo.py`](backend/app/db/repo.py); regression tests in
[`backend/tests/test_agent_revocation.py`](backend/tests/test_agent_revocation.py) prove
revoke and unrevoke both work for an agent with no prior registration.

**The AI endpoints have no automated regression tests.** They're proven working via
real, logged runs in git history (including two live model retirements caught and fixed
mid-session — see commit history), but nothing in `pytest` calls the live NVIDIA API, so a
third model retirement wouldn't be caught by CI. There is no CI, either. This exact gap is
what let the policy drafter silently ignore two whole fields for a while: `allow_cod_for_agents`
and `max_orders_per_agent_per_window`/`velocity_window_minutes` were added to the `Policy`
model for the India-specific rules, but `POLICY_SYSTEM_PROMPT` in `ai_client.py` was never
updated to match, and its own instructions told the model to silently drop anything outside
its schema — so a merchant typing "allow cash on delivery" or "no more than 3 orders an
hour" would have gotten a draft that quietly ignored both. Found by actually typing that
sentence into the Rules page and checking the saved policy against what was typed, not by
reading the prompt and assuming it was current. Fixed by expanding the schema and its
interpretation rules to cover all eight `Policy` fields, verified live afterward with the
exact same sentence. A static guard now exists for this exact class of bug —
`backend/tests/test_policy_prompt_schema_sync.py` fails if `Policy` ever gains a field
`POLICY_SYSTEM_PROMPT` doesn't mention, no live model call needed. It can't verify the
model actually *uses* a field correctly, only that the prompt hasn't silently fallen behind
the schema again.

**The digest's flag set is intentionally small (three flag types) and only looks at one
merchant's own history.** It catches an agent tripping the catalog-mismatch check, hitting a
velocity cap, or getting blocked repeatedly and trying again — real, deterministic patterns,
but not cross-merchant correlation (the same agent probing many different shops), not
gradual drift in what an agent buys over weeks, and nothing behavioral beyond what the
existing rule checks already look at. Built as the honest answer to a specific critique
during the buildathon (a merchant who writes rules once and never looks again has no way to
notice a pattern), not as a general anomaly-detection system. The first working version
also had a real, live-discovered latency bug worth naming: it originally computed the
plain-language AI summary inline before returning anything, which took ~14-20 seconds per
call against a week of history — long enough that the page just sat on "loading." Fixed by
splitting `/digest` (fast, deterministic, no AI) from `/digest/narrate` (the slow AI step,
called separately once the real numbers are already on screen) — same pattern the
escalation advisor already used, just not one this endpoint had been checked against until
it was actually loaded in a browser.

**Two real money-safety bugs were found and fixed by deliberately auditing for this class
of mistake, not by chance** — see `backend/tests/test_money_safety.py` and its
introducing commit: a negative cart quantity produced a negative total that trivially
passed every value-based rule, and double-clicking "Approve" on an escalated order could
create two separate real Razorpay payment links for one order. Both are now schema- and
status-guarded, with regression tests. The fact that these existed after multiple rounds
of testing is itself the honest finding: testing finds *some* bugs, not *all* of them, and
this repo does not claim otherwise.
