# Razorpay AI Buildathon 2026 — Track 01

**Builder:** Kushal Raj G S (1BY23AI072, BMSIT&M) · B.E. AI&ML, CGPA 8.98, 2023–2027
**Track chosen:** 01 — AI Growth & Agentic Commerce
**Applications close:** 5 September 2026
**Apply form:** https://forms.gle/d9r2gvxp8cmoZhon9
**Program page:** https://razorpay.com/buildathon/

---

## The offer

| Item | Detail |
|---|---|
| Stipend | ₹75,000 / month |
| Duration | 6 or 12 months (builder's choice) |
| Location | In-person, Bangalore, from September |
| Process | Shortlisted → straight to panel. No aptitude test, no GD. |
| Screening | Resume taken but explicitly **not** screened on |

## Track 01 brief (verbatim from site)

> **Grow the merchant's revenue, and make them sellable to AI buyers**
>
> Build an agent that grows revenue for a merchant on Razorpay test-mode APIs, or that
> makes a merchant transactable by an AI buyer end to end.
>
> **WHY NOW** — NPCI's UAP and the global protocol race (ACP, AP2, x402) make
> agent-to-agent commerce the open problem of the year, and Razorpay's in-app pilots
> are already live.
>
> **EXAMPLE DIRECTIONS** — Conversational in-app checkout · Agent-readable catalog ·
> Upsell & cross-sell agent · Campaign orchestrator
>
> **THE BAR** — Every money action explainable, bounded and gated. Show the audit
> trail and one failure handled gracefully.

### Two doors, one pipeline

- **Door A** — grow revenue for a merchant using AI on Razorpay test-mode APIs
- **Door B** — make a merchant transactable by an AI buyer end-to-end

**Decision:** build them as *one* pipeline where Door B feeds Door A (agent-readable +
trust-gated catalog → growth/checkout agent that can only act through that gate), rather
than two disconnected submissions. Single track submission only — the form asks for
"Your track" (singular) and one project.

## Judging criteria (verbatim)

| Criterion | What they said |
|---|---|
| Problem taste | did you pick something that actually matters |
| Build quality | does it run, is it structured, would you trust it |
| AI judgment | the right tool in the right place, **and where you chose not to use one** |
| Failure recovery | what broke, and what you did about it |

## Application form — 12 required fields

**About you (6):** full name · college · graduation year · in-person from September (Y/N) ·
6 or 12 months · resume file

**About the build (6):** track · project name · what it solves · **public** GitHub repo URL ·
5-min pitch video (unlisted OK) · **what broke, and how you got out**

> Site note: *"The last one is the one we read first."* — the failure-recovery answer is the
> highest-leverage field in the whole form.

## Why this track fits (self-assessment)

The track's bar — *explainable, bounded, gated, audit trail* — is structurally the same
problem already solved in prior work:

- **Varinth** — Proof Objects, evidence grounding, Critic–Verifier–Judge swarm,
  deterministic verdict synthesis, bounded verification scopes → maps directly onto
  "every money action explainable and auditable"
- **Roast** — self-evaluating trust layer (RAGAS faithfulness/relevancy), closed-loop
  fix-verification, 4-signal priority engine → maps onto measured, honest metrics
- **Baxel** — hierarchical multi-agent architecture, semantic routing, structured
  generation under Pydantic constraints → maps onto bounded agent orchestration

Domain gap to close: payments/commerce domain knowledge. This is API-integration and
protocol-reading work, **not** finance expertise — which is why Track 01 was chosen over
Tracks 02/03/04 (fraud-ML, revenue-ops and reconciliation respectively, all of which
assume finance-domain intuition).

## Repo layout

```
razorpay-buildathon/
├── README.md          ← this file
└── research/          ← evidence base, every claim sourced
    ├── 00-track-brief.md
    ├── 01-landscape-initial.md
    └── ...            ← deep-dive briefs land here
```
