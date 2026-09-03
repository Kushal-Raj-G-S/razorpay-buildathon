"""
Static guard against the exact bug found live: POLICY_SYSTEM_PROMPT
silently dropping fields that exist on the Policy model. This test
never calls the live NVIDIA API -- it can't verify the model actually
USES a field correctly, only that the prompt at least MENTIONS every
field name that exists on Policy, so a future field added to the model
without touching the prompt fails CI instead of silently drafting
incomplete policies.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.ai_client import POLICY_SYSTEM_PROMPT
from app.models.policy import Policy


def test_every_policy_field_is_mentioned_in_the_drafting_prompt():
    missing = [
        name for name in Policy.model_fields
        if name != "merchant_id" and name not in POLICY_SYSTEM_PROMPT
    ]
    assert not missing, (
        f"Policy model has field(s) {missing} that POLICY_SYSTEM_PROMPT never mentions -- "
        f"the AI drafter would silently ignore a merchant's instruction about them. "
        f"Add them to the prompt's schema and interpretation rules in ai_client.py."
    )
