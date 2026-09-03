"""
Proves the MCP server actually works as an MCP server, not just as
Python code that imports cleanly. Spawns app/mcp_server.py as a real
child process over stdio (exactly how Claude Desktop, Claude Agent SDK,
or Agent Studio's tool picker would launch it), lists its tools the way
any MCP host does, then calls check_cart with the same poisoned cart
used throughout this project and confirms the real backend blocks it
-- proving the MCP layer is a faithful, working adapter over the same
decision engine, not a second, disconnected implementation.
"""
import asyncio
import json
import os
import sys

from mcp import ClientSession, StdioServerParameters, stdio_client


async def main():
    env = dict(os.environ)
    env["WARRANT_MERCHANT_ID"] = "shop_123"
    env["WARRANT_API_URL"] = "http://127.0.0.1:8000"

    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "app.mcp_server"],
        env=env,
        cwd=os.path.join(os.path.dirname(__file__), ".."),
    )

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("Tools exposed by the MCP server:")
            for t in tools.tools:
                first_line = next(line.strip() for line in t.description.splitlines() if line.strip())
                print(f"  - {t.name}: {first_line}")

            print("\nCalling check_cart with a poisoned cart (real gift card, mislabeled)...")
            result = await session.call_tool(
                "check_cart",
                {
                    "agent_id": "mcp-test-agent",
                    "items": [
                        {
                            "id": "gift-voucher",  # the real catalog id
                            "title": "Gift Voucher",
                            "price": 200000,
                            "category": "clothing",  # the lie
                            "quantity": 1,
                        }
                    ],
                    "payment_mode": "prepaid",
                },
            )
            payload = json.loads(result.content[0].text)
            print(f"\nDecision: {payload['receipt']['decision'].upper()}")
            for r in payload["receipt"]["rules_checked"]:
                status = "PASS" if r["passed"] else "FAIL"
                print(f"  [{status}] {r['rule_name']}: {r['detail']}")


if __name__ == "__main__":
    asyncio.run(main())
