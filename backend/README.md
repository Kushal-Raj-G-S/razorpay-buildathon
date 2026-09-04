# Nope.ai — backend

FastAPI + SQLModel. See the [root README](../README.md) for what this project is; this
file is just how to run this half of it.

## Setup

```bash
python -m venv venv
venv\Scripts\pip install -r requirements.txt   # venv/bin/pip on macOS/Linux
copy .env.example .env
```

Fill in `.env`:
- `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET` — test-mode keys from your Razorpay dashboard
  (Account & Settings → API Keys, toggled to Test Mode). Without these, payment-link
  creation returns a labelled placeholder instead of erroring — everything else still works.
- `NVIDIA_API_KEY` — from [build.nvidia.com](https://build.nvidia.com). Without this, the
  three AI-backed endpoints (`/catalog/from-text`, `/policy/draft-from-text`,
  `/red-team/run`) return `503`. Everything else still works.
- `DATABASE_URL` — optional. Defaults to `sqlite:///./warrant.db`. Set to a Postgres URL
  (e.g. Neon) to run against a real database with zero code changes — this was actually
  verified live against Neon during development, not just claimed.

## Run

```bash
venv\Scripts\python -m uvicorn app.main:app --port 8000
```

## Test

```bash
pytest -q
```

29 tests. Real HTTP integration tests via FastAPI's `TestClient`, not just unit tests of
internal functions — see `tests/test_api.py`. Razorpay's API is stubbed in tests (see the
`stub_razorpay` fixture) so the suite doesn't depend on a third party's live rate limit to
pass — that dependency caused real, reproducible failures during development before it was
fixed. The real Razorpay integration is proven separately: see git log for live curl/browser
runs against the actual test-mode API, including opening the resulting payment page in a
browser and confirming it renders as genuine.

## The one design rule that matters most

**Nothing in `app/engine/` imports anything that can make a network call or an inference
request.** That's not a style preference — it's the whole thesis. AI drafts a merchant's
rules and normalizes their catalog (`app/ai_client.py`); it never evaluates whether an
order should be allowed. NIST measured agent-hijacking success rising from 11% to 81%
under adaptive attacks — a bound enforced by a prompt is not a bound. If you're adding a
new rule, it belongs in `app/engine/evaluate.py` as a plain function, added to
`ALL_CHECKS`. If you're tempted to have an LLM decide whether to allow an order, don't —
that's the one thing this codebase is built to refuse.

## Where the real vulnerabilities were, and how they were found

Not by inspection — by deliberately trying to break the system and then fixing what broke.
Worth reading if you're extending this:

- **Catalog-trust bypass** (`app/engine/evaluate.py`'s `check_items_are_listed`,
  `main.py`'s `_resolve_items_against_catalog`) — an agent could declare any category for
  any item; nothing verified it against what the merchant actually sold. Found while
  building the red-team demo, fixed by resolving every item against the merchant's real
  catalog before any rule runs.
- **Negative-quantity exploit** (`app/models/cart.py`) — a cart with `quantity=-9999`
  produced a negative total that trivially passed every value-based check, since nothing
  is ever "greater than" a negative number. Fixed with a Pydantic `Field(gt=0)` constraint,
  proven in `tests/test_money_safety.py`.
- **Double-approval on escalations** (`app/db/repo.py`'s `AlreadyReviewedError`) — nothing
  stopped a double-click or network retry from creating two real Razorpay payment links
  for one order. Fixed with a status guard, same principle as the `Idempotency-Key`
  handling on `/checkout-sessions`.

See the [root README's Known Gaps section](../README.md#known-gaps) for what's still open.
