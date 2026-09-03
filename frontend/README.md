# Warrant — frontend

Next.js 16 (App Router, Turbopack) + Tailwind v4 + framer-motion. See the
[root README](../README.md) for what this project is.

## Setup

```bash
npm install
copy .env.example .env.local
```

`NEXT_PUBLIC_MERCHANT_API_KEY` has to come from a real merchant account — there's no
signup UI yet (see [Known Gaps](../README.md#known-gaps)), so register one against the
running backend first:

```bash
curl -X POST http://127.0.0.1:8000/merchants/register -H "Content-Type: application/json" -d "{\"merchant_id\": \"shop_123\"}"
```

Copy the returned `api_key` into `.env.local`. `NEXT_PUBLIC_API_URL` defaults to
`http://127.0.0.1:8000`.

## Run

```bash
npm run dev
```

Requires the backend running on port 8000 — every page here calls the real API, nothing
is mocked client-side.

## Pages

| Route | What it does |
|---|---|
| `/policy` | Write rules directly, or describe them in plain English and let AI draft the fields (you still click Save — nothing applies itself) |
| `/catalog` | Paste messy product text, AI turns it into a structured catalog |
| `/demo` | Pretend to be an AI agent — fire preset scenarios (clean cart, poisoned cart, over-limit, agentic COD) at the real checkout endpoint |
| `/red-team` | Launch a real autonomous AI against your own rules and watch the transcript as it tries to adapt after every rejection |
| `/escalations` | The human review queue — approve or reject orders that passed every rule but were too large to auto-approve |
| `/receipts` | The full signed audit trail of every decision ever made |

## Design system

Warm-paper background, ledger-green accent, Fraunces serif for headings, monospace for
every number and signature — deliberately not the blue/purple gradient look. Tokens live
in `app/globals.css`; reusable animation primitives (`Reveal`, `staggerParent`/
`staggerChild`) live in `components/Reveal.tsx`.
