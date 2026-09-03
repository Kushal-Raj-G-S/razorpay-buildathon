"""
Dead-simple in-memory storage for the demo. Not a real database --
just Python dictionaries that reset every time the server restarts.
Good enough for a 3-day build; a real database is the obvious next step.
"""
from app.models.catalog import Catalog
from app.models.policy import Policy
from app.models.receipt import Receipt

catalogs: dict[str, Catalog] = {}
policies: dict[str, Policy] = {}
receipts: list[Receipt] = []
revoked_agents: set[str] = set()

# agent_id -> public key (hex). An agent must register here before it
# can ever pass the identity check.
registered_agents: dict[str, str] = {}

# Keys generated once when the server starts (see main.py)
signing_private_key: bytes | None = None
signing_public_key: bytes | None = None
