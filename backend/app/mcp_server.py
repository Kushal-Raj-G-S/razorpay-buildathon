"""
WARRANT AS AN MCP SERVER.

Razorpay's own Agent Studio is built on the Claude Agent SDK, and Claude
Agent SDK agents call out to capabilities through MCP (Model Context
Protocol) tools -- the same protocol Razorpay's own official payments
MCP server (github.com/razorpay/razorpay-mcp-server) already speaks.

That means the fastest path to "any agent built inside Agent Studio can
use Warrant" isn't a new UI or a bespoke integration -- it's exposing
the exact same decision engine already proven in main.py as MCP tools.
An agent-builder just adds this server the same way it would add any
other tool, and every purchase it tries to make gets checked before it
happens.

This is a thin adapter, not a second implementation: every tool below
calls the real, running FastAPI backend over HTTP. There is exactly one
place the actual rules live (app/engine/evaluate.py), and this file
never touches it directly -- so the MCP surface can never drift out of
sync with the REST surface real merchants and dashboards use.

Run it:
  WARRANT_MERCHANT_ID=shop_123 python -m app.mcp_server
Configure it in an MCP-aware agent host (Claude Agent SDK, Claude
Desktop, Agent Studio's tool picker) by pointing it at this command.
"""
import os
import httpx
from mcp.server.mcpserver import MCPServer

WARRANT_API_URL = os.environ.get("WARRANT_API_URL", "http://127.0.0.1:8000")
WARRANT_MERCHANT_ID = os.environ.get("WARRANT_MERCHANT_ID", "")
WARRANT_MERCHANT_API_KEY = os.environ.get("WARRANT_MERCHANT_API_KEY", "")  # only needed for red-team

mcp = MCPServer(
    name="warrant",
    title="Warrant — merchant-side agentic commerce trust layer",
    instructions=(
        "Use check_cart before completing ANY purchase on behalf of a user. "
        "It enforces this specific merchant's own rules -- spending limits, "
        "banned categories, identity verification, COD policy, order "
        "velocity -- and returns an allow/block/escalate decision with the "
        "exact reason. A block or escalate result means the purchase MUST "
        "NOT be completed by any other means; do not retry with different "
        "wording or a relabeled item to work around a block."
    ),
)


def _require_merchant() -> str:
    if not WARRANT_MERCHANT_ID:
        raise RuntimeError(
            "WARRANT_MERCHANT_ID is not set -- this server must be configured "
            "for exactly one merchant before it can be used."
        )
    return WARRANT_MERCHANT_ID


@mcp.tool()
async def check_cart(
    agent_id: str,
    items: list[dict],
    payment_mode: str = "prepaid",
) -> dict:
    """
    Check whether this merchant allows a specific cart to be purchased
    by an AI agent, RIGHT NOW. Call this before completing any purchase.

    items: list of {"id": str, "title": str, "price": int (paise),
    "category": str, "quantity": int}. The id should match a real
    product in the merchant's catalog when possible -- Warrant verifies
    against the merchant's own listing and will override or reject
    anything that doesn't match, regardless of what category is claimed
    here.

    payment_mode: "prepaid" or "cod". Most merchants block agentic COD
    by default since it needs no payment authorization to place.

    Returns the decision ("allow" | "block" | "escalate"), the specific
    rule that fired if blocked, and a real Razorpay test-mode payment
    link if allowed.
    """
    merchant_id = _require_merchant()
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"{WARRANT_API_URL}/checkout-sessions",
            json={"merchant_id": merchant_id, "agent_id": agent_id, "items": items, "payment_mode": payment_mode},
        )
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_merchant_policy() -> dict:
    """
    Read this merchant's current rules for AI agents: spending limits,
    banned categories, COD policy, velocity limits, identity
    requirements. Useful for an agent to sanity-check a plan before
    attempting check_cart, though check_cart is still the authoritative
    check.
    """
    merchant_id = _require_merchant()
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(f"{WARRANT_API_URL}/policy/{merchant_id}")
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def search_catalog(query: str = "") -> dict:
    """
    Browse this merchant's real product catalog. Use this to find valid
    product ids before calling check_cart -- an id that doesn't match
    anything here will be treated as unlisted and blocked outright.
    """
    merchant_id = _require_merchant()
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(
            f"{WARRANT_API_URL}/catalog/search",
            params={"merchant_id": merchant_id, "query": query},
        )
        response.raise_for_status()
        return response.json()


if WARRANT_MERCHANT_API_KEY:

    @mcp.tool()
    async def run_red_team(goal: str, max_rounds: int = 5) -> dict:
        """
        Merchant-only. Launch an autonomous AI agent that tries to get
        something past this merchant's own rules, adapting after every
        rejection, and return the full transcript. Use this to test a
        policy after changing it, not as part of a normal checkout flow.
        """
        merchant_id = _require_merchant()
        async with httpx.AsyncClient(timeout=180) as client:
            response = await client.post(
                f"{WARRANT_API_URL}/red-team/run",
                headers={"Authorization": f"Bearer {WARRANT_MERCHANT_API_KEY}"},
                json={"merchant_id": merchant_id, "goal": goal, "max_rounds": max_rounds},
            )
            response.raise_for_status()
            return response.json()


if __name__ == "__main__":
    mcp.run(transport="stdio")
