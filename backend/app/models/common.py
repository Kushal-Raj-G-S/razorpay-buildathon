"""Small, reused response shapes that don't deserve their own file."""
from pydantic import BaseModel


class StatusResponse(BaseModel):
    status: str


class AgentActionResponse(BaseModel):
    status: str
    agent_id: str


class AgentRegisterResponse(BaseModel):
    status: str
    agent_id: str


class PublicKeyResponse(BaseModel):
    public_key_hex: str
