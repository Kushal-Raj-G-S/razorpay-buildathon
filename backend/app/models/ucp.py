"""Typed shape of GET /.well-known/ucp. The service names ("dev.ucp.shopping")
are dotted namespace strings, not fixed field names -- a dict[str, ...]
handles that cleanly without forcing awkward field aliases."""
from pydantic import BaseModel


class UcpServiceEndpoint(BaseModel):
    transport: str
    endpoint: str


class UcpPaymentHandler(BaseModel):
    mode: str


class UcpProfile(BaseModel):
    version: str
    services: dict[str, UcpServiceEndpoint]
    payment_handlers: dict[str, UcpPaymentHandler]


class UcpProfileResponse(BaseModel):
    ucp: UcpProfile
