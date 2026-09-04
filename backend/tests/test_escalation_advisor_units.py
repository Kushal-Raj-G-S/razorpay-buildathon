"""
Real bug, found live: advise_on_escalation() embedded cart_items with
prices still in paise while the order total was already converted to
rupees -- a Rs 5,000 order's item showed as "price: 500000" right next
to "Order total: Rs 5000" in the prompt, and the model reasonably read
that as a mismatch and recommended "reject, high confidence, looks like
fraud" on a completely ordinary order. Not a hypothetical: this is the
exact advice a live NVIDIA call returned during a walkthrough of the
Escalations page. This test proves the fix without needing a live model
call -- it inspects the actual prompt text that would be sent.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import asyncio
from app import ai_client


def test_advisor_prompt_shows_item_prices_in_the_same_unit_as_the_total(monkeypatch):
    captured = {}

    async def fake_chat_json(system_prompt, user_prompt):
        captured["user_prompt"] = user_prompt
        return {"recommendation": "approve", "reasoning": "fine", "confidence": "high"}

    monkeypatch.setattr(ai_client, "_chat_json", fake_chat_json)

    asyncio.run(ai_client.advise_on_escalation(
        cart_items=[{"id": "earbuds", "title": "Wireless Earbuds", "price": 500000,
                     "category": "clothing", "quantity": 1}],
        cart_total_rupees=5000.0,
        agent_id="test-agent",
        recent_agent_history="",
    ))

    prompt = captured["user_prompt"]
    assert "Order total: Rs 5000" in prompt
    # The raw paise value must never appear next to a rupee total --
    # that juxtaposition is exactly what produced the false fraud signal.
    assert "500000" not in prompt
    assert "price_rupees" in prompt
    assert "5000" in prompt  # the item's own price, now in rupees, matches the total's scale
