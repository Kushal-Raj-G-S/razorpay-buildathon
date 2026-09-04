"""
Calls NVIDIA NIM (build.nvidia.com) for the two places AI genuinely
belongs in this project:

  1. Turning a shop's messy product text into a clean, structured catalog
  2. Turning a shop owner's plain-English rules into our policy format

NIM speaks the same API shape as OpenAI's chat completions, so this is
a plain HTTP call, no special SDK needed.

Everywhere else in this codebase (the actual rule-checking, the
signatures) has NO AI in it on purpose -- see engine/evaluate.py's
docstring. This file is the two deliberate exceptions.
"""
import os
import json
import httpx
from dotenv import load_dotenv

load_dotenv()

NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY", "")
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
MODEL = os.environ.get("NVIDIA_MODEL", "openai/gpt-oss-20b")


def is_configured() -> bool:
    return bool(NVIDIA_API_KEY)


async def _chat_json(system_prompt: str, user_prompt: str) -> dict:
    """
    Sends one prompt, asks for JSON back, parses it. Raises if the key
    isn't configured -- callers decide how to degrade (see api routes).
    """
    if not is_configured():
        raise RuntimeError("NVIDIA_API_KEY not configured -- see backend/.env.example")

    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            f"{NVIDIA_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {NVIDIA_API_KEY}"},
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.2,
                "response_format": {"type": "json_object"},
            },
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return json.loads(content)


CATALOG_SYSTEM_PROMPT = """You turn messy shop product listings into clean structured data.

For each product line the user gives you, output an object with:
- id: a short url-safe slug, lowercase, hyphens only (e.g. "blue-shirt-l")
- title: a clean human-readable name
- price_rupees: the price as a number, in rupees (not paise)
- category: your best guess at ONE simple category word, lowercase
  (e.g. "clothing", "gift_card", "electronics", "accessories", "footwear")
- sku: a short code if one is implied, otherwise null

Respond with ONLY a JSON object: {"products": [ {...}, {...} ]}
No explanation, no markdown, just the JSON object."""


async def normalize_catalog_text(raw_text: str) -> list[dict]:
    """messy text, one product idea per line -> list of clean product dicts"""
    result = await _chat_json(CATALOG_SYSTEM_PROMPT, raw_text)
    return result.get("products", [])


POLICY_SYSTEM_PROMPT = """You translate a shop owner's plain-English rules for AI shopping
agents into a strict JSON policy object. The shape MUST be exactly:

{
  "max_order_value": <integer, rupees, the largest single order allowed>,
  "deny_categories": [<lowercase category strings that are always banned>],
  "max_units_per_sku": <integer, max quantity of one item per order>,
  "escalate_above": <integer rupees, or null if not mentioned -- orders above
                      this are sent to a human instead of blocked, IF this
                      value is lower than max_order_value>,
  "require_signed_identity": <boolean, default true unless they say
                               otherwise>,
  "allow_cod_for_agents": <boolean, default false -- true only if they
                            explicitly say to allow Cash on Delivery,
                            COD, or "pay on delivery" for agent orders>,
  "max_orders_per_agent_per_window": <integer, or null if they don't
                                       mention a frequency/rate limit --
                                       "no more than N orders per hour/day"
                                       sets this to N>,
  "velocity_window_minutes": <integer minutes matching the window they
                               described (60 for "per hour", 1440 for
                               "per day"); default 60 if they set a
                               frequency limit but don't say a window>
}

Rules for interpreting the English:
- If they don't mention a number, use sensible defaults: max_order_value
  10000, max_units_per_sku 5, escalate_above null, require_signed_identity
  true, allow_cod_for_agents false, max_orders_per_agent_per_window null,
  velocity_window_minutes 60.
- "no gift cards" / "block gift cards" -> add "gift_card" to deny_categories.
- Category names should be simple lowercase words matching common sense
  categories like clothing, gift_card, electronics, accessories, footwear.
- "allow COD" / "allow cash on delivery" / "pay on delivery is fine" ->
  allow_cod_for_agents true. Do not set this true unless they say so
  explicitly -- COD needs zero payment authorization to place, so the
  safe default is false.
- "no more than N orders an hour/day/etc" / "max N orders per agent" ->
  set max_orders_per_agent_per_window to N and velocity_window_minutes to
  match their stated window.
- If they ask for something outside this schema, ignore it silently --
  do not invent new fields.

Respond with ONLY the JSON object. No explanation, no markdown."""


ADVERSARY_SYSTEM_PROMPT = """You are an AI shopping agent working on behalf of a customer.
Your goal is given to you. You do NOT know this merchant's rules in advance -- you find out
only by trying and seeing whether an attempt is allowed or blocked, and why.

If you get blocked, read the reason carefully and try a genuinely different approach next time:
rephrase the item description, pick a different category label, split the order into smaller
pieces, try a different product id if you can guess one, or anything else a resourceful agent
might try. Do not repeat an attempt that already failed the same way.

If you have tried several genuinely different approaches and are out of ideas, set give_up=true.

Respond with ONLY a JSON object of this exact shape:
{
  "reasoning": "<one or two sentences on your strategy for this attempt>",
  "items": [{"id": "<product id>", "title": "<title>", "price_rupees": <number>,
             "category": "<your claimed category>", "quantity": <integer>}],
  "give_up": <true or false>
}
No explanation outside the JSON, no markdown."""


async def adversarial_agent_attempt(goal: str, catalog_summary: str, history: list[dict]) -> dict:
    """
    One round of an autonomous agent trying to get something past the
    merchant's rules, with no visibility into what those rules actually
    are -- only the outcome of its own prior attempts. This is what
    makes the demo real rather than scripted: the model decides its own
    next move.
    """
    history_text = "\n\n".join(
        f"Attempt {i+1}: you submitted {h['items']}\n"
        f"Result: {h['decision'].upper()}"
        + (f" -- reason: {h['reason']}" if h.get("reason") else "")
        for i, h in enumerate(history)
    ) or "(no attempts yet -- this is your first try)"

    user_prompt = f"""Your goal: {goal}

This merchant's product catalog (id, title, price in rupees, category as the merchant lists it):
{catalog_summary}

Your attempt history so far:
{history_text}

Decide your next attempt."""

    return await _chat_json(ADVERSARY_SYSTEM_PROMPT, user_prompt)


ESCALATION_ADVISOR_SYSTEM_PROMPT = """You are helping a human merchant decide whether to approve
or reject an order that passed every automated rule but was flagged for human review because
of its size. You do NOT make the decision -- you draft a recommendation and a short reason, and
a human still has to click Approve or Reject themselves. Never claim certainty you don't have.

Respond with ONLY a JSON object of this exact shape:
{
  "recommendation": "approve" | "reject" | "needs_human_judgment",
  "reasoning": "<one or two sentences, plain language, for a busy merchant to skim>",
  "confidence": "low" | "medium" | "high"
}
No explanation outside the JSON, no markdown."""


async def advise_on_escalation(cart_items: list[dict], cart_total_rupees: float,
                                agent_id: str, recent_agent_history: str) -> dict:
    """
    Drafts a recommendation for a human reviewing an escalated order.
    This is advisory only -- see app/db/repo.py's review_escalation,
    which is the only place a decision actually becomes real, and it
    only ever accepts a decision from the human clicking a button, never
    from this function's output directly.

    Real bug found live: `cart_items` comes in with prices in paise
    (the DB's native unit) while `cart_total_rupees` is already
    converted -- a Rs 5,000 order's item showed as "price: 500000" right
    next to "Order total: Rs 5000" in the prompt. The model reasonably
    read that as a mismatch and called it fraud: a false "reject, high
    confidence" on a completely ordinary order, caused entirely by a
    units bug, not by anything the agent actually did. Converted here so
    every price the model sees is in the same unit as the total.
    """
    items_in_rupees = [
        {**item, "price_rupees": round(item["price"] / 100, 2)} if "price" in item else item
        for item in cart_items
    ]
    for item in items_in_rupees:
        item.pop("price", None)

    user_prompt = f"""Order total: Rs {cart_total_rupees:.0f}
Items (prices in rupees, matching the order total's unit): {items_in_rupees}
Agent: {agent_id}
This agent's recent order history with this merchant: {recent_agent_history or "no prior orders"}

Draft your recommendation."""
    return await _chat_json(ESCALATION_ADVISOR_SYSTEM_PROMPT, user_prompt)


DIGEST_SYSTEM_PROMPT = """You explain a store's AI-agent shopping activity to a shop owner who is
NOT a security expert and does not know terms like "policy", "rule engine", "catalog
resolution", or "velocity limit". You are given facts and a list of flags that have ALREADY
been decided by fixed code before you ever see them -- you do not get to decide what counts
as suspicious, add a flag, remove one, or change its severity. Your only job is to explain,
in plain everyday language, what happened and why it might matter to someone running a shop,
not a security team.

Never invent a fact that isn't in the data you were given. If there are no flags, say so
plainly and reassuringly -- don't manufacture concern where there isn't any. If there are
flags, be calm and specific, not alarmist -- this is information, not a siren.

Respond with ONLY a JSON object of this exact shape:
{
  "headline": "<one short sentence, plain language, e.g. 'Quiet week -- nothing needs your attention'>",
  "summary": "<2-4 sentences, plain language, for someone with zero security background>",
  "flag_explanations": [{"agent_id": "<id>", "plain_english": "<one sentence explaining this one flag like
                          you're talking to a shopkeeper, not an engineer>"}]
}
No explanation outside the JSON, no markdown."""


async def summarize_digest(stats: dict) -> dict:
    """
    Turns engine/digest.py's deterministic output into plain language a
    non-technical merchant can actually read. This is pure narration:
    every number and every flag already exists before this is called: it
    cannot add, remove, or reweight anything, and if this call fails or
    isn't configured the caller still has the real stats to show without
    it (see main.py's /digest).
    """
    user_prompt = json.dumps(stats, default=str)
    return await _chat_json(DIGEST_SYSTEM_PROMPT, user_prompt)


async def compile_policy_text(merchant_id: str, plain_english: str) -> dict:
    """
    Plain English rules -> our Policy schema. The caller MUST show this
    to the merchant for approval before saving it -- this function only
    drafts, it never applies anything by itself.

    The model is prompted to think in whole rupees (easier for it to
    get right), but our Policy schema stores money in paise everywhere
    else (see models/policy.py) -- so we convert here, once, in the one
    place that boundary is crossed. Missing this was a real bug caught
    while testing: a merchant applying an AI-drafted policy directly
    would have gotten a limit 100x smaller than they asked for.
    """
    result = await _chat_json(POLICY_SYSTEM_PROMPT, plain_english)
    result["merchant_id"] = merchant_id

    result.setdefault("max_order_value", 10000)
    result.setdefault("deny_categories", [])
    result.setdefault("max_units_per_sku", 5)
    result.setdefault("escalate_above", None)
    result.setdefault("require_signed_identity", True)
    result.setdefault("allow_cod_for_agents", False)
    result.setdefault("max_orders_per_agent_per_window", None)
    result.setdefault("velocity_window_minutes", 60)

    result["max_order_value"] = round(float(result["max_order_value"]) * 100)
    if result["escalate_above"] is not None:
        result["escalate_above"] = round(float(result["escalate_above"]) * 100)

    return result
