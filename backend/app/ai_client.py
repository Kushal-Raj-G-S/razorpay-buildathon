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
MODEL = os.environ.get("NVIDIA_MODEL", "openai/gpt-oss-120b")


def is_configured() -> bool:
    return bool(NVIDIA_API_KEY)


async def _chat_json(system_prompt: str, user_prompt: str) -> dict:
    """
    Sends one prompt, asks for JSON back, parses it. Raises if the key
    isn't configured -- callers decide how to degrade (see api routes).
    """
    if not is_configured():
        raise RuntimeError("NVIDIA_API_KEY not configured -- see backend/.env.example")

    async with httpx.AsyncClient(timeout=60) as client:
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
                               otherwise>
}

Rules for interpreting the English:
- If they don't mention a number, use sensible defaults: max_order_value
  10000, max_units_per_sku 5, escalate_above null, require_signed_identity true.
- "no gift cards" / "block gift cards" -> add "gift_card" to deny_categories.
- Category names should be simple lowercase words matching common sense
  categories like clothing, gift_card, electronics, accessories, footwear.
- If they ask for something outside this schema, ignore it silently --
  do not invent new fields.

Respond with ONLY the JSON object. No explanation, no markdown."""


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

    result["max_order_value"] = round(float(result["max_order_value"]) * 100)
    if result["escalate_above"] is not None:
        result["escalate_above"] = round(float(result["escalate_above"]) * 100)

    return result
